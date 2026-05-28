"""
collect_weather.py
------------------
Pulls historical weather for all 30 NBA arena cities
on each game date using the free Open-Meteo API.

No API key required.

Run AFTER scrape_bref.py:
  python3 src/collect_weather.py
"""

import requests
import pandas as pd
import time
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"

# Arena coordinates for all 30 NBA cities
ARENA_COORDS = {
    "BOS": (42.3662, -71.0621),
    "BRK": (40.6826, -73.9754),
    "NYK": (40.7505, -73.9934),
    "PHI": (39.9012, -75.1720),
    "TOR": (43.6435, -79.3791),
    "CHI": (41.8807, -87.6742),
    "CLE": (41.4965, -81.6882),
    "DET": (42.3410, -83.0550),
    "IND": (39.7640, -86.1555),
    "MIL": (43.0450, -87.9170),
    "ATL": (33.7573, -84.3963),
    "CHO": (35.2251, -80.8392),
    "MIA": (25.7814, -80.1870),
    "ORL": (28.5392, -81.3839),
    "WAS": (38.8981, -77.0209),
    "DEN": (39.7487, -105.0077),
    "MIN": (44.9795, -93.2762),
    "OKC": (35.4634, -97.5151),
    "POR": (45.5316, -122.6668),
    "UTA": (40.7683, -111.9011),
    "GSW": (37.7680, -122.3877),
    "LAC": (33.9584, -118.3396),
    "LAL": (34.0430, -118.2673),
    "PHO": (33.4457, -112.0712),
    "SAC": (38.5802, -121.4997),
    "DAL": (32.7905, -96.8103),
    "HOU": (29.7508, -95.3621),
    "MEM": (35.1382, -90.0505),
    "NOP": (29.9490, -90.0812),
    "SAS": (29.4270, -98.4375),
}


def fetch_weather(abbr, lat, lon, dates):
    """Fetch weather for one arena across all its game dates."""
    dates = pd.to_datetime(dates).dt.normalize().drop_duplicates().sort_values()
    date_df = pd.DataFrame({"game_date": dates})
    date_df["year"] = date_df["game_date"].dt.year

    all_weather = []

    for year, group in date_df.groupby("year"):
        start = group["game_date"].min().strftime("%Y-%m-%d")
        end   = group["game_date"].max().strftime("%Y-%m-%d")

        params = {
            "latitude":           lat,
            "longitude":          lon,
            "start_date":         start,
            "end_date":           end,
            "daily":              ["temperature_2m_max", "temperature_2m_min",
                                   "precipitation_sum", "snowfall_sum"],
            "temperature_unit":   "fahrenheit",
            "precipitation_unit": "inch",
            "timezone":           "America/New_York",
        }

        try:
            r = requests.get(WEATHER_URL, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()["daily"]

            wdf = pd.DataFrame({
                "game_date":   pd.to_datetime(data["time"]),
                "temp_max_f":  data["temperature_2m_max"],
                "temp_min_f":  data["temperature_2m_min"],
                "precip_in":   data["precipitation_sum"],
                "snowfall_in": data["snowfall_sum"],
            })

            game_dates = group["game_date"].dt.normalize()
            wdf = wdf[wdf["game_date"].isin(game_dates)].copy()
            all_weather.append(wdf)
            time.sleep(0.5)

        except Exception as e:
            print(f"    Weather error {abbr} {year}: {e}")

    if not all_weather:
        return pd.DataFrame()

    combined = pd.concat(all_weather, ignore_index=True)
    combined["abbr"]        = abbr
    combined["temp_avg_f"]  = ((combined["temp_max_f"] + combined["temp_min_f"]) / 2).round(1)
    combined["is_bad_weather"] = (
        (combined["temp_avg_f"] < 25) | (combined["precip_in"] > 0.25)
    ).astype(int)
    combined["is_cold"]    = (combined["temp_avg_f"] < 32).astype(int)
    combined["has_precip"] = (combined["precip_in"] > 0.1).astype(int)
    return combined


def main():
    games_path = f"{BASE}/data/raw/nba_attendance_raw.csv"
    if not os.path.exists(games_path):
        print("ERROR: Run scrape_bref.py first.")
        return

    games = pd.read_csv(games_path, parse_dates=["game_date"])
    print(f"Collecting weather for {games['abbr'].nunique()} arenas...")

    all_weather = []
    for abbr, (lat, lon) in ARENA_COORDS.items():
        team_games = games[games["abbr"] == abbr]
        if team_games.empty:
            continue

        print(f"  {abbr}...", end=" ", flush=True)
        wdf = fetch_weather(abbr, lat, lon, team_games["game_date"])
        if not wdf.empty:
            all_weather.append(wdf)
            print(f"{len(wdf)} dates")
        else:
            print("no data")

        time.sleep(1)

    if not all_weather:
        print("No weather data collected.")
        return

    combined = pd.concat(all_weather, ignore_index=True)
    output = f"{BASE}/data/raw/weather_data.csv"
    combined.to_csv(output, index=False)

    print(f"\nSaved {len(combined):,} weather records -> data/raw/weather_data.csv")
    print(f"Bad weather games: {combined['is_bad_weather'].sum():,}")


if __name__ == "__main__":
    main()
