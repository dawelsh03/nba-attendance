"""
load_to_mysql.py  (v4 - team_name as opponent key)
"""

import pandas as pd
import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv

load_dotenv()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nba_attendance_db"),
}

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


def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print(f"Connected: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("ERROR: Wrong username or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("ERROR: Database not found. Run sql/01_schema.sql first.")
        else:
            print(f"ERROR: {err}")
        raise


def reset_tables(conn):
    """Drop and recreate tables to ensure clean schema."""
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in ["fact_attendance", "dim_weather", "dim_opponent",
                  "dim_date", "dim_team"]:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    # Recreate with correct schema
    statements = [
        """CREATE TABLE dim_team (
            team_id INT AUTO_INCREMENT PRIMARY KEY,
            team_name VARCHAR(50) NOT NULL UNIQUE,
            abbr VARCHAR(4) NOT NULL UNIQUE,
            arena VARCHAR(60), capacity INT,
            market_size VARCHAR(10), conference VARCHAR(5), division VARCHAR(12)
        )""",
        """CREATE TABLE dim_date (
            date_id INT AUTO_INCREMENT PRIMARY KEY,
            game_date DATE NOT NULL UNIQUE,
            season VARCHAR(8) NOT NULL,
            day_of_week VARCHAR(10) NOT NULL,
            is_weekend TINYINT(1) NOT NULL DEFAULT 0,
            month_name VARCHAR(12) NOT NULL,
            month_num TINYINT NOT NULL,
            days_into_season INT NOT NULL DEFAULT 0
        )""",
        """CREATE TABLE dim_opponent (
            opponent_id INT AUTO_INCREMENT PRIMARY KEY,
            team_name VARCHAR(50) NOT NULL UNIQUE,
            tier CHAR(1) NOT NULL,
            is_marquee TINYINT(1) NOT NULL DEFAULT 0
        )""",
        """CREATE TABLE dim_weather (
            weather_id INT AUTO_INCREMENT PRIMARY KEY,
            abbr VARCHAR(4) NOT NULL,
            game_date DATE NOT NULL,
            temp_avg_f DECIMAL(5,1), precip_in DECIMAL(5,2),
            is_bad_weather TINYINT(1) NOT NULL DEFAULT 0,
            is_cold TINYINT(1) NOT NULL DEFAULT 0,
            UNIQUE KEY uq_team_date (abbr, game_date)
        )""",
        """CREATE TABLE fact_attendance (
            game_id VARCHAR(25) PRIMARY KEY,
            team_id INT NOT NULL, date_id INT NOT NULL,
            opponent_id INT NOT NULL, weather_id INT,
            wl CHAR(1), team_pts INT, opp_pts INT,
            win_streak INT NOT NULL DEFAULT 0,
            loss_streak INT NOT NULL DEFAULT 0,
            rolling_win_pct DECIMAL(5,3), season_win_pct DECIMAL(5,3),
            is_back_to_back TINYINT(1) NOT NULL DEFAULT 0,
            days_since_last_home INT,
            attendance INT NOT NULL,
            attendance_pct DECIMAL(6,4) NOT NULL,
            above_avg TINYINT(1), below_85pct TINYINT(1),
            FOREIGN KEY (team_id)     REFERENCES dim_team(team_id),
            FOREIGN KEY (date_id)     REFERENCES dim_date(date_id),
            FOREIGN KEY (opponent_id) REFERENCES dim_opponent(opponent_id),
            FOREIGN KEY (weather_id)  REFERENCES dim_weather(weather_id)
        )""",
    ]
    for stmt in statements:
        cursor.execute(stmt)
    conn.commit()
    cursor.close()
    print("  Tables reset and recreated.")


def load_dim_team(conn, arena_df):
    print("\nLoading dim_team...")
    cursor = conn.cursor()
    sql = """INSERT INTO dim_team
        (team_name,abbr,arena,capacity,market_size,conference,division)
        VALUES (%s,%s,%s,%s,%s,%s,%s)"""
    rows = [(r.team, r.abbr, r.arena, int(r.capacity),
             r.market_size, r.conference, r.division)
            for r in arena_df.itertuples()]
    cursor.executemany(sql, rows)
    conn.commit()
    print(f"  Inserted {cursor.rowcount} teams")
    cursor.close()


def load_dim_date(conn, df):
    print("\nLoading dim_date...")
    cursor = conn.cursor()
    dates = df[["game_date","season","day_of_week","is_weekend",
                "month","month_num","days_into_season"]].drop_duplicates("game_date")
    sql = """INSERT IGNORE INTO dim_date
        (game_date,season,day_of_week,is_weekend,month_name,month_num,days_into_season)
        VALUES (%s,%s,%s,%s,%s,%s,%s)"""
    rows = [(r.game_date.strftime("%Y-%m-%d"), r.season, r.day_of_week,
             int(r.is_weekend), r.month, int(r.month_num),
             int(r.days_into_season))
            for r in dates.itertuples()]
    cursor.executemany(sql, rows)
    conn.commit()
    print(f"  Inserted {cursor.rowcount} dates")
    cursor.close()


def load_dim_opponent(conn, df):
    print("\nLoading dim_opponent...")
    cursor = conn.cursor()
    unique_opps = df["opponent"].dropna().unique()
    print(f"  Found {len(unique_opps)} unique opponents")

    sql = """INSERT IGNORE INTO dim_opponent (team_name, tier, is_marquee)
             VALUES (%s, %s, %s)"""
    rows = []
    for opp in unique_opps:
        tier = OPPONENT_TIERS.get(opp, "B")
        rows.append((opp, tier, 1 if tier == "A" else 0))

    cursor.executemany(sql, rows)
    conn.commit()
    print(f"  Inserted {cursor.rowcount} opponents")
    cursor.close()


def load_dim_weather(conn, df):
    print("\nLoading dim_weather...")
    cursor = conn.cursor()
    if "temp_avg_f" not in df.columns:
        print("  No weather data — skipping")
        cursor.close()
        return
    weather = df[["abbr","game_date","temp_avg_f","precip_in",
                  "is_bad_weather","is_cold"]].drop_duplicates(["abbr","game_date"])
    sql = """INSERT IGNORE INTO dim_weather
        (abbr,game_date,temp_avg_f,precip_in,is_bad_weather,is_cold)
        VALUES (%s,%s,%s,%s,%s,%s)"""
    rows = [(r.abbr, r.game_date.strftime("%Y-%m-%d"),
             float(r.temp_avg_f) if pd.notna(r.temp_avg_f) else None,
             float(r.precip_in)  if pd.notna(r.precip_in)  else None,
             int(r.is_bad_weather), int(r.is_cold))
            for r in weather.itertuples()]
    cursor.executemany(sql, rows)
    conn.commit()
    print(f"  Inserted {cursor.rowcount} weather records")
    cursor.close()


def load_fact_attendance(conn, df):
    print("\nLoading fact_attendance...")
    cursor = conn.cursor()

    # Build lookup maps using correct keys
    cursor.execute("SELECT abbr, team_id FROM dim_team")
    team_map = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT game_date, date_id FROM dim_date")
    date_map = {str(r[0]): r[1] for r in cursor.fetchall()}

    # KEY FIX: look up by team_name not abbr
    cursor.execute("SELECT team_name, opponent_id FROM dim_opponent")
    opp_map = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT abbr, game_date, weather_id FROM dim_weather")
    weather_map = {(r[0], str(r[1])): r[2] for r in cursor.fetchall()}

    # Diagnose
    missing_opps = set(df["opponent"].dropna().unique()) - set(opp_map.keys())
    if missing_opps:
        print(f"  WARNING: {len(missing_opps)} unmapped opponents: {sorted(missing_opps)}")

    sql = """INSERT IGNORE INTO fact_attendance
        (game_id,team_id,date_id,opponent_id,weather_id,
         wl,team_pts,opp_pts,
         win_streak,loss_streak,rolling_win_pct,season_win_pct,
         is_back_to_back,days_since_last_home,
         attendance,attendance_pct,above_avg,below_85pct)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    skipped = 0
    for row in df.itertuples():
        date_str   = row.game_date.strftime("%Y-%m-%d")
        team_id    = team_map.get(row.abbr)
        date_id    = date_map.get(date_str)
        opp_id     = opp_map.get(row.opponent)   # full team name lookup
        weather_id = weather_map.get((row.abbr, date_str))

        if not team_id or not date_id or not opp_id:
            skipped += 1
            continue

        rows.append((
            row.game_id,
            team_id, date_id, opp_id, weather_id,
            str(row.wl) if pd.notna(row.wl) else None,
            int(row.team_pts) if pd.notna(row.team_pts) else None,
            int(row.opp_pts)  if pd.notna(row.opp_pts)  else None,
            int(row.win_streak), int(row.loss_streak),
            float(row.rolling_win_pct) if pd.notna(row.rolling_win_pct) else None,
            float(row.season_win_pct)  if pd.notna(row.season_win_pct)  else None,
            int(row.is_back_to_back),
            int(row.days_since_last_home) if pd.notna(row.days_since_last_home) else None,
            int(row.attendance),
            float(row.attendance_pct),
            int(row.above_avg)   if pd.notna(row.above_avg)   else None,
            int(row.below_85pct) if pd.notna(row.below_85pct) else None,
        ))

    if skipped:
        print(f"  Skipped {skipped} rows due to missing foreign keys")

    chunk = 1000
    loaded = 0
    for i in range(0, len(rows), chunk):
        cursor.executemany(sql, rows[i:i+chunk])
        conn.commit()
        loaded += len(rows[i:i+chunk])
        print(f"  {loaded:,} / {len(rows):,} rows...", end="\r")

    print(f"\n  Inserted {loaded:,} game records")
    cursor.close()


def verify(conn):
    print("\n── Verification ─────────────────────────────")
    cursor = conn.cursor()
    for table in ["dim_team","dim_date","dim_opponent",
                  "dim_weather","fact_attendance"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table:<25} {cursor.fetchone()[0]:>8,} rows")

    # Quick sanity check
    cursor.execute("""
        SELECT season, COUNT(*) as games, ROUND(AVG(attendance_pct)*100,1) as avg_pct
        FROM fact_attendance fa
        JOIN dim_date d ON fa.date_id = d.date_id
        GROUP BY season ORDER BY season
    """)
    print("\n  Season summary:")
    for row in cursor.fetchall():
        print(f"    {row[0]}  {row[1]:>5} games  {row[2]}% avg capacity")
    cursor.close()


if __name__ == "__main__":
    features_path = f"{BASE}/data/processed/nba_features.csv"
    if not os.path.exists(features_path):
        print("ERROR: Run build_features.py first.")
        exit(1)

    print("NBA Attendance Intelligence Platform — MySQL Loader v4")
    print("=" * 52)

    df = pd.read_csv(features_path, parse_dates=["game_date"])
    arena = pd.read_csv(f"{BASE}/data/manual/arena_info.csv")
    print(f"Loaded {len(df):,} games")

    conn = get_connection()
    print("\nResetting tables with clean schema...")
    reset_tables(conn)
    load_dim_team(conn, arena)
    load_dim_date(conn, df)
    load_dim_opponent(conn, df)
    load_dim_weather(conn, df)
    load_fact_attendance(conn, df)
    verify(conn)
    conn.close()
    print("\nDatabase loaded successfully.")
