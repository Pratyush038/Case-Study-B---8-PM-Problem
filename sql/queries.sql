USE blr_rush;

-- Q1. How big is each table?
SELECT 'stations' AS tbl, COUNT(*) AS n FROM stations
UNION ALL SELECT 'calendar', COUNT(*) FROM calendar
UNION ALL SELECT 'weather_hourly', COUNT(*) FROM weather_hourly
UNION ALL SELECT 'readings_hourly', COUNT(*) FROM readings_hourly
UNION ALL SELECT 'reddit_posts', COUNT(*) FROM reddit_posts;

-- Q2. (GROUP BY) Average NO2 by hour of day on working days
SELECT HOUR(r.hour_ts) AS hour, ROUND(AVG(r.no2), 1) AS avg_no2
FROM readings_hourly r
JOIN calendar c ON c.date = DATE(r.hour_ts)
WHERE c.is_weekend = 0 AND c.is_holiday = 0
GROUP BY HOUR(r.hour_ts)
ORDER BY hour;

-- Q3. (JOIN + GROUP BY) Station ranking by evening (7 to 10 PM) NO2
SELECT s.station_name, ROUND(AVG(r.no2), 1) AS evening_no2, ROUND(AVG(r.pm25), 1) AS evening_pm25
FROM readings_hourly r
JOIN stations s ON s.station_id = r.station_id
WHERE HOUR(r.hour_ts) BETWEEN 19 AND 22
GROUP BY s.station_name
ORDER BY evening_no2 DESC;

-- Q4. (3-table JOIN) Evening pollution on wet vs dry hours, monsoon working days
SELECT CASE WHEN w.precipitation >= 0.5 THEN 'raining' ELSE 'dry' END AS hour_type,
       COUNT(*) AS station_hours,
       ROUND(AVG(r.no2), 1) AS avg_no2,
       ROUND(AVG(r.pm25), 1) AS avg_pm25
FROM readings_hourly r
JOIN weather_hourly w ON w.hour_ts = r.hour_ts
JOIN calendar c ON c.date = w.date
WHERE c.season = 'SW monsoon' AND c.is_weekend = 0 AND c.is_holiday = 0
  AND HOUR(r.hour_ts) BETWEEN 17 AND 22
GROUP BY hour_type;

-- Q5. Holidays vs normal working days, evening NO2
SELECT CASE WHEN c.is_holiday = 1 THEN 'holiday'
            WHEN c.is_weekend = 1 THEN 'weekend'
            ELSE 'working day' END AS day_type,
       ROUND(AVG(r.no2), 1) AS evening_no2
FROM readings_hourly r
JOIN calendar c ON c.date = DATE(r.hour_ts)
WHERE HOUR(r.hour_ts) BETWEEN 19 AND 22
GROUP BY day_type;

-- Q6. Reddit: share of commute posts per month next to that month's rain
SELECT DATE_FORMAT(p.date, '%Y-%m') AS month,
       COUNT(*) AS posts,
       ROUND(100 * AVG(p.commute_post), 1) AS pct_commute_posts,
       ROUND(MAX(m.rain_mm), 0) AS month_rain_mm
FROM reddit_posts p
JOIN (SELECT DATE_FORMAT(date, '%Y-%m') AS month, SUM(precipitation) AS rain_mm
      FROM weather_hourly GROUP BY DATE_FORMAT(date, '%Y-%m')) m
  ON m.month = DATE_FORMAT(p.date, '%Y-%m')
GROUP BY DATE_FORMAT(p.date, '%Y-%m')
ORDER BY month;
