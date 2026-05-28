-- ============================================================
-- NBA Attendance Intelligence Platform
-- Business Analytics Queries
-- Run in MySQL Workbench after loading data
-- ============================================================

USE nba_attendance_db;

-- Q1: League-wide attendance utilization by team and season
SELECT
    t.team_name,
    t.market_size,
    d.season,
    COUNT(*)                           AS games,
    ROUND(AVG(f.attendance_pct)*100,1) AS avg_capacity_pct,
    ROUND(MIN(f.attendance_pct)*100,1) AS min_capacity_pct,
    ROUND(MAX(f.attendance_pct)*100,1) AS max_capacity_pct,
    ROUND(STDDEV(f.attendance_pct)*100,1) AS volatility
FROM fact_attendance f
JOIN dim_team t   ON f.team_id = t.team_id
JOIN dim_date d   ON f.date_id = d.date_id
GROUP BY t.team_name, t.market_size, d.season
ORDER BY avg_capacity_pct DESC;

-- Q2: Day of week effect across the league
SELECT
    d.day_of_week,
    d.is_weekend,
    COUNT(*)                           AS games,
    ROUND(AVG(f.attendance_pct)*100,1) AS avg_capacity_pct,
    ROUND(AVG(f.attendance))           AS avg_attendance
FROM fact_attendance f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.day_of_week, d.is_weekend
ORDER BY avg_capacity_pct DESC;

-- Q3: Win streak threshold analysis
SELECT
    CASE
        WHEN f.win_streak >= 7 THEN '7+ wins'
        WHEN f.win_streak >= 5 THEN '5-6 wins'
        WHEN f.win_streak >= 3 THEN '3-4 wins'
        WHEN f.win_streak >= 1 THEN '1-2 wins'
        ELSE 'Losing'
    END                                AS streak_bucket,
    COUNT(*)                           AS games,
    ROUND(AVG(f.attendance_pct)*100,1) AS avg_capacity_pct,
    ROUND(AVG(f.attendance))           AS avg_attendance
FROM fact_attendance f
GROUP BY streak_bucket
ORDER BY avg_capacity_pct DESC;

-- Q4: Games below 85% capacity by team
SELECT
    t.team_name,
    t.market_size,
    COUNT(*)                           AS total_games,
    SUM(f.below_85pct)                 AS games_below_85pct,
    ROUND(AVG(f.below_85pct)*100,1)    AS pct_below_85,
    ROUND(AVG(f.attendance_pct)*100,1) AS avg_capacity_pct
FROM fact_attendance f
JOIN dim_team t ON f.team_id = t.team_id
GROUP BY t.team_name, t.market_size
ORDER BY pct_below_85 DESC;

-- Q5: Back-to-back effect
SELECT
    f.is_back_to_back,
    COUNT(*)                           AS games,
    ROUND(AVG(f.attendance_pct)*100,1) AS avg_capacity_pct,
    ROUND(AVG(f.attendance))           AS avg_attendance
FROM fact_attendance f
GROUP BY f.is_back_to_back;

-- Q6: Opponent tier impact
SELECT
    o.tier                             AS opponent_tier,
    COUNT(*)                           AS games,
    ROUND(AVG(f.attendance_pct)*100,1) AS avg_capacity_pct,
    ROUND(AVG(f.attendance))           AS avg_attendance
FROM fact_attendance f
JOIN dim_opponent o ON f.opponent_id = o.opponent_id
GROUP BY o.tier
ORDER BY avg_capacity_pct DESC;

-- Q7: Weather impact
SELECT
    CASE w.is_bad_weather
        WHEN 1 THEN 'Bad weather'
        ELSE 'Good weather'
    END                                AS weather,
    COUNT(*)                           AS games,
    ROUND(AVG(f.attendance_pct)*100,1) AS avg_capacity_pct
FROM fact_attendance f
JOIN dim_weather w ON f.weather_id = w.weather_id
GROUP BY w.is_bad_weather;
