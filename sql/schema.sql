-- MySQL schema for the 8 PM Problem (Bengaluru)
-- 5 tables linked by keys. See charts/er_diagram.png

DROP DATABASE IF EXISTS blr_rush;
CREATE DATABASE blr_rush;
USE blr_rush;

-- one row per air quality station
CREATE TABLE stations (
    station_id   INT PRIMARY KEY,
    station_name VARCHAR(60) NOT NULL,
    agency       VARCHAR(10),
    area_type    VARCHAR(40),
    lat          DOUBLE,
    lon          DOUBLE
);

-- one row per day, built by hand (holidays) plus code (weekday, season)
CREATE TABLE calendar (
    date         DATE PRIMARY KEY,
    weekday      CHAR(3),
    is_weekend   BOOLEAN,
    is_holiday   BOOLEAN,
    holiday_name VARCHAR(60),
    season       VARCHAR(20)
);

-- one row per hour of weather, times in IST
CREATE TABLE weather_hourly (
    hour_ts       DATETIME PRIMARY KEY,
    date          DATE,
    precipitation DOUBLE,
    temperature   DOUBLE,
    humidity      DOUBLE,
    wind_speed    DOUBLE,
    FOREIGN KEY (date) REFERENCES calendar(date)
);

-- one row per station per hour (the big table)
CREATE TABLE readings_hourly (
    station_id INT,
    hour_ts    DATETIME,
    no2        DOUBLE,
    pm25       DOUBLE,
    PRIMARY KEY (station_id, hour_ts),
    FOREIGN KEY (station_id) REFERENCES stations(station_id),
    FOREIGN KEY (hour_ts) REFERENCES weather_hourly(hour_ts)
);

-- Reddit post titles (no usernames), times in IST
CREATE TABLE reddit_posts (
    post_id      VARCHAR(12) PRIMARY KEY,
    created_ist  DATETIME,
    date         DATE,
    title        TEXT,
    commute_post BOOLEAN,
    FOREIGN KEY (date) REFERENCES calendar(date)
);
