-- ============================================================
-- NBA Attendance Intelligence Platform
-- MySQL Schema v2
-- ============================================================

CREATE DATABASE IF NOT EXISTS nba_attendance_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE nba_attendance_db;

CREATE TABLE IF NOT EXISTS dim_team (
    team_id      INT           AUTO_INCREMENT PRIMARY KEY,
    team_name    VARCHAR(50)   NOT NULL UNIQUE,
    abbr         VARCHAR(4)    NOT NULL UNIQUE,
    arena        VARCHAR(60),
    capacity     INT,
    market_size  VARCHAR(10),
    conference   VARCHAR(5),
    division     VARCHAR(12)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id          INT          AUTO_INCREMENT PRIMARY KEY,
    game_date        DATE         NOT NULL UNIQUE,
    season           VARCHAR(8)   NOT NULL,
    day_of_week      VARCHAR(10)  NOT NULL,
    is_weekend       TINYINT(1)   NOT NULL DEFAULT 0,
    month_name       VARCHAR(12)  NOT NULL,
    month_num        TINYINT      NOT NULL,
    days_into_season INT          NOT NULL DEFAULT 0
);

-- team_name stores full name e.g. "Boston Celtics"
CREATE TABLE IF NOT EXISTS dim_opponent (
    opponent_id  INT           AUTO_INCREMENT PRIMARY KEY,
    team_name    VARCHAR(50)   NOT NULL UNIQUE,
    tier         CHAR(1)       NOT NULL,
    is_marquee   TINYINT(1)    NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dim_weather (
    weather_id     INT           AUTO_INCREMENT PRIMARY KEY,
    abbr           VARCHAR(4)    NOT NULL,
    game_date      DATE          NOT NULL,
    temp_avg_f     DECIMAL(5,1),
    precip_in      DECIMAL(5,2),
    is_bad_weather TINYINT(1)    NOT NULL DEFAULT 0,
    is_cold        TINYINT(1)    NOT NULL DEFAULT 0,
    UNIQUE KEY uq_team_date (abbr, game_date)
);

CREATE TABLE IF NOT EXISTS fact_attendance (
    game_id              VARCHAR(25)   PRIMARY KEY,
    team_id              INT           NOT NULL,
    date_id              INT           NOT NULL,
    opponent_id          INT           NOT NULL,
    weather_id           INT,
    wl                   CHAR(1),
    team_pts             INT,
    opp_pts              INT,
    win_streak           INT           NOT NULL DEFAULT 0,
    loss_streak          INT           NOT NULL DEFAULT 0,
    rolling_win_pct      DECIMAL(5,3),
    season_win_pct       DECIMAL(5,3),
    is_back_to_back      TINYINT(1)    NOT NULL DEFAULT 0,
    days_since_last_home INT,
    attendance           INT           NOT NULL,
    attendance_pct       DECIMAL(6,4)  NOT NULL,
    above_avg            TINYINT(1),
    below_85pct          TINYINT(1),
    FOREIGN KEY (team_id)     REFERENCES dim_team(team_id),
    FOREIGN KEY (date_id)     REFERENCES dim_date(date_id),
    FOREIGN KEY (opponent_id) REFERENCES dim_opponent(opponent_id),
    FOREIGN KEY (weather_id)  REFERENCES dim_weather(weather_id)
);

CREATE INDEX idx_fa_team     ON fact_attendance(team_id);
CREATE INDEX idx_fa_date     ON fact_attendance(date_id);
CREATE INDEX idx_fa_opponent ON fact_attendance(opponent_id);

SELECT 'Schema created successfully.' AS status;
