"""
build_features.py
-----------------
Joins all data sources and engineers features for analysis and modeling.

INPUT:
  data/raw/nba_attendance_raw.csv
  data/raw/weather_data.csv        (optional - from collect_weather.py)
  data/manual/arena_info.csv

OUTPUT:
  data/processed/nba_features.csv

Run from project root:
  python3 src/build_features.py
"""

import pandas as pd
import numpy as np
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Opponent tiers - based on market size and national appeal
OPPONENT_TIERS = {
    "Boston Celtics":          "A",
    "Los Angeles Lakers":      "A",
    "Golden State Warriors":   "A",
    "Miami Heat":              "A",
    "New York Knicks":         "A",
    "Chicago Bulls":           "A",
    "Milwaukee Bucks":         "A",
    "Dallas Mavericks":        "A",
    "Philadelphia 76ers":      "A",
    "Denver Nuggets":          "B",
    "Phoenix Suns":            "B",
    "Brooklyn Nets":           "B",
    "Atlanta Hawks":           "B",
    "Toronto Raptors":         "B",
    "Minnesota Timberwolves":  "B",
    "Los Angeles Clippers":    "B",
    "New Orleans Pelicans":    "B",
    "Memphis Grizzlies":       "B",
    "Indiana Pacers":          "B",
    "Oklahoma City Thunder":   "B",
    "Cleveland Cavaliers":     "B",
    "Sacramento Kings":        "B",
    "Detroit Pistons":         "C",
    "Washington Wizards":      "C",
    "Charlotte Hornets":       "C",
    "Orlando Magic":           "C",
    "Utah Jazz":               "C",
    "Portland Trail Blazers":  "C",
    "San Antonio Spurs":       "C",
    "Houston Rockets":         "C",
}

DOW_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


def add_date_features(df):
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["day_of_week"] = df["game_date"].dt.day_name()
    df["day_num"]     = df["game_date"].dt.dayofweek
    df["is_weekend"]  = df["day_num"].isin([4, 5, 6]).astype(int)
    df["month"]       = df["game_date"].dt.month_name()
    df["month_num"]   = df["game_date"].dt.month

    # Days into season per team per season
    df = df.sort_values(["team", "season", "game_date"])
    df["season_start"] = df.groupby(["team","season"])["game_date"].transform("min")
    df["days_into_season"] = (df["game_date"] - df["season_start"]).dt.days
    df = df.drop(columns=["season_start"])
    return df


def add_opponent_features(df):
    df["opponent_tier"] = df["opponent"].map(OPPONENT_TIERS).fillna("B")
    df["is_marquee"]    = (df["opponent_tier"] == "A").astype(int)
    df["tier_numeric"]  = df["opponent_tier"].map({"A": 3, "B": 2, "C": 1})
    return df


def add_performance_features(df):
    df = df.sort_values(["team", "season", "game_date"]).copy()
    df["win"] = (df["wl"] == "W").astype(int)

    def calc_streaks(series):
        streaks = []
        current = 0
        for val in series:
            streaks.append(current)
            current = (max(0, current) + 1) if val == 1 else (min(0, current) - 1)
        return streaks

    win_streaks, loss_streaks = [], []
    for (team, season), grp in df.groupby(["team","season"]):
        grp = grp.sort_values("game_date")
        raw = calc_streaks(grp["win"].tolist())
        win_streaks.extend([max(0, s) for s in raw])
        loss_streaks.extend([abs(min(0, s)) for s in raw])

    df["win_streak"]  = win_streaks
    df["loss_streak"] = loss_streaks

    # Rolling win pct - last 10 games, shift 1 to avoid leakage
    df["rolling_win_pct"] = (
        df.groupby(["team","season"])["win"]
        .transform(lambda x: x.shift(1).rolling(10, min_periods=3).mean())
        .round(3)
    )

    # Season win pct to date before this game
    df["season_win_pct"] = (
        df.groupby(["team","season"])["win"]
        .transform(lambda x: x.shift(1).expanding().mean())
        .round(3)
    )
    return df


def add_rest_features(df):
    df = df.sort_values(["team","season","game_date"]).copy()
    df["days_since_last_home"] = (
        df.groupby(["team","season"])["game_date"].diff().dt.days
    )
    df["is_back_to_back"] = (df["days_since_last_home"] <= 2).astype(int)
    df.loc[df["days_since_last_home"].isna(), "is_back_to_back"] = 0
    return df


def add_target_features(df):
    df["attendance_pct"] = (df["attendance"] / df["capacity"]).round(4)
    overall_avg = df["attendance_pct"].mean()
    df["above_avg"]    = (df["attendance_pct"] > overall_avg).astype(int)
    df["below_85pct"]  = (df["attendance_pct"] < 0.85).astype(int)
    return df, overall_avg


def main():
    # Load raw attendance
    games_path = f"{BASE}/data/raw/nba_attendance_raw.csv"
    if not os.path.exists(games_path):
        print("ERROR: data/raw/nba_attendance_raw.csv not found.")
        print("Run src/scrape_bref.py first.")
        return

    df = pd.read_csv(games_path, parse_dates=["game_date"])
    print(f"Loaded {len(df):,} games from {len(df['team'].unique())} teams")

    # Join arena info
    arena = pd.read_csv(f"{BASE}/data/manual/arena_info.csv")
    df = df.merge(arena[["abbr","arena","capacity","market_size",
                          "conference","division"]],
                  on="abbr", how="left")
    print(f"Joined arena info")

    # Join weather if available
    weather_path = f"{BASE}/data/raw/weather_data.csv"
    if os.path.exists(weather_path):
        weather = pd.read_csv(weather_path, parse_dates=["game_date"])
        df = df.merge(weather, on=["abbr","game_date"], how="left")
        print(f"Joined weather data")
    else:
        print("Weather data not found - skipping (run collect_weather.py)")
        df["temp_avg_f"]     = np.nan
        df["is_bad_weather"] = 0
        df["precip_in"]      = np.nan

    # Feature engineering
    print("Engineering features...")
    df = add_date_features(df)
    df = add_opponent_features(df)
    df = add_performance_features(df)
    df = add_rest_features(df)
    df, overall_avg = add_target_features(df)

    # Save
    output = f"{BASE}/data/processed/nba_features.csv"
    df.to_csv(output, index=False)

    print(f"\n{'='*55}")
    print(f"Saved: data/processed/nba_features.csv")
    print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"\nLeague avg attendance utilization: {overall_avg:.1%}")
    print(f"Games below 85% capacity: {df['below_85pct'].sum():,} "
          f"({df['below_85pct'].mean():.1%})")
    print(f"\nSample columns:\n{list(df.columns)}")


if __name__ == "__main__":
    main()
