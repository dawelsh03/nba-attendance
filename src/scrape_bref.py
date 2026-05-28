"""
scrape_bref.py  (v3 - fixed opp_name key)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NBA_TEAMS = [
    ("Boston Celtics",         "BOS"),
    ("Brooklyn Nets",          "BRK"),
    ("New York Knicks",        "NYK"),
    ("Philadelphia 76ers",     "PHI"),
    ("Toronto Raptors",        "TOR"),
    ("Chicago Bulls",          "CHI"),
    ("Cleveland Cavaliers",    "CLE"),
    ("Detroit Pistons",        "DET"),
    ("Indiana Pacers",         "IND"),
    ("Milwaukee Bucks",        "MIL"),
    ("Atlanta Hawks",          "ATL"),
    ("Charlotte Hornets",      "CHO"),
    ("Miami Heat",             "MIA"),
    ("Orlando Magic",          "ORL"),
    ("Washington Wizards",     "WAS"),
    ("Denver Nuggets",         "DEN"),
    ("Minnesota Timberwolves", "MIN"),
    ("Oklahoma City Thunder",  "OKC"),
    ("Portland Trail Blazers", "POR"),
    ("Utah Jazz",              "UTA"),
    ("Golden State Warriors",  "GSW"),
    ("Los Angeles Clippers",   "LAC"),
    ("Los Angeles Lakers",     "LAL"),
    ("Phoenix Suns",           "PHO"),
    ("Sacramento Kings",       "SAC"),
    ("Dallas Mavericks",       "DAL"),
    ("Houston Rockets",        "HOU"),
    ("Memphis Grizzlies",      "MEM"),
    ("New Orleans Pelicans",   "NOP"),
    ("San Antonio Spurs",      "SAS"),
]

SEASONS = [
    ("2022-23", 2023),
    ("2023-24", 2024),
    ("2024-25", 2025),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

VALID_MONTHS = {10, 11, 12, 1, 2, 3, 4}


def scrape_team_season(team_name, abbr, season, bref_year):
    url = (f"https://www.basketball-reference.com"
           f"/teams/{abbr}/{bref_year}_games.html")

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table", {"id": "games"})
    if not table:
        raise ValueError(f"No games table for {abbr} {season}")

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        if tr.get("class") and "thead" in tr.get("class", []):
            continue

        cells = {td.get("data-stat", ""): td.get_text(strip=True)
                 for td in tr.find_all(["td", "th"])}

        if not cells.get("date_game"):
            continue
        if cells.get("game_location") == "@":
            continue

        try:
            game_date = pd.to_datetime(cells["date_game"])
        except Exception:
            continue

        if game_date.month not in VALID_MONTHS:
            continue

        att_raw = cells.get("attendance", "").replace(",", "").strip()
        if not att_raw:
            continue
        try:
            attendance = int(att_raw)
        except ValueError:
            continue

        if attendance < 1000:
            continue

        result = cells.get("game_result", "")
        wl = result[0] if result and result[0] in ("W", "L") else None

        try:
            pts     = int(cells.get("pts", 0) or 0)
            opp_pts = int(cells.get("opp_pts", 0) or 0)
        except ValueError:
            pts, opp_pts = None, None

        # Use opp_name (full team name) — confirmed correct key
        opponent = cells.get("opp_name", "")

        rows.append({
            "season":     season,
            "team":       team_name,
            "abbr":       abbr,
            "game_date":  game_date.strftime("%Y-%m-%d"),
            "opponent":   opponent,
            "wl":         wl,
            "team_pts":   pts,
            "opp_pts":    opp_pts,
            "attendance": attendance,
        })

    return pd.DataFrame(rows)


def main():
    all_games = []
    total = len(NBA_TEAMS) * len(SEASONS)
    count = 0

    print(f"Scraping {len(NBA_TEAMS)} teams x {len(SEASONS)} seasons = {total} requests")
    print("This will take approximately 15 minutes.\n")

    for team_name, abbr in NBA_TEAMS:
        for season, bref_year in SEASONS:
            count += 1
            print(f"  [{count:>3}/{total}] {abbr} {season}...", end=" ", flush=True)

            try:
                df = scrape_team_season(team_name, abbr, season, bref_year)
                all_games.append(df)
                print(f"{len(df)} home games")
            except Exception as e:
                print(f"ERROR: {e}")

            time.sleep(3)

    if not all_games:
        print("No data collected.")
        return

    combined = pd.concat(all_games, ignore_index=True)
    combined["game_id"] = (
        combined["abbr"] + "_" +
        combined["game_date"].str.replace("-", "")
    )
    combined = combined.sort_values(
        ["team", "season", "game_date"]
    ).reset_index(drop=True)

    # Remove neutral site games above any real arena capacity
    before = len(combined)
    combined = combined[combined["attendance"] <= 25000]
    removed = before - len(combined)
    if removed:
        print(f"\nRemoved {removed} neutral-site games (attendance > 25,000)")

    output = f"{BASE}/data/raw/nba_attendance_raw.csv"
    combined.to_csv(output, index=False)

    print(f"\n{'='*55}")
    print(f"Saved {len(combined):,} home games -> data/raw/nba_attendance_raw.csv")
    print(f"\nOpponent sample: {combined['opponent'].dropna().unique()[:5].tolist()}")
    print(f"\nBreakdown by season:")
    print(combined.groupby("season").agg(
        games=("game_id", "count"),
        teams=("team", "nunique"),
        avg_att=("attendance", "mean"),
        min_att=("attendance", "min"),
        max_att=("attendance", "max"),
    ).round(0).to_string())


if __name__ == "__main__":
    main()
