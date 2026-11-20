# Step 8: load the clean tables into MySQL and run the queries in sql/queries.sql.
# Set your login first, for example:
#   export MYSQL_USER=student MYSQL_PASSWORD=student

import os
import pandas as pd
from sqlalchemy import create_engine, text

user = os.getenv("MYSQL_USER", "student")
pwd = os.getenv("MYSQL_PASSWORD", "student")
host = os.getenv("MYSQL_HOST", "localhost") + ":" + os.getenv("MYSQL_PORT", "3306")
server = create_engine(f"mysql+pymysql://{user}:{pwd}@{host}")

# 1. create the database and tables
with server.begin() as con:
    for stmt in open("sql/schema.sql").read().split(";"):
        if stmt.strip():
            con.execute(text(stmt))
db = create_engine(f"mysql+pymysql://{user}:{pwd}@{host}/blr_rush")

# 2. calendar: every day in the study period plus the hand-made holiday list
holidays = pd.read_csv("data/holidays_karnataka.csv", parse_dates=["date"])
cal = pd.DataFrame({"date": pd.date_range("2025-10-01", "2026-10-31")})
cal["weekday"] = cal.date.dt.strftime("%a")
cal["is_weekend"] = cal.date.dt.dayofweek >= 5
cal = cal.merge(holidays[["date", "holiday_name"]], how="left")
cal["is_holiday"] = cal.holiday_name.notna()
season = {12: "winter", 1: "winter", 2: "winter", 3: "summer", 4: "summer", 5: "summer",
          6: "SW monsoon", 7: "SW monsoon", 8: "SW monsoon", 9: "SW monsoon",
          10: "NE monsoon", 11: "NE monsoon"}
cal["season"] = cal.date.dt.month.map(season)

# 3. weather (already in IST)
w = pd.read_csv("data/clean/weather_hourly_ist.csv", parse_dates=["hour_ts"])
w = w.rename(columns={"temperature_2m": "temperature", "relative_humidity_2m": "humidity",
                      "wind_speed_10m": "wind_speed"})
w["date"] = w.hour_ts.dt.date
w = w[w.hour_ts < "2026-11-01"]          # after UTC -> IST the last rows spill into Nov 1

# 4. hourly readings (cleaned, short gaps filled, empty hours dropped)
r = pd.read_csv("data/clean/air_hourly_filled.csv", parse_dates=["hour_ts"])
r = r[["station_id", "hour_ts", "no2", "pm25"]].dropna(subset=["no2", "pm25"], how="all")
r = r[r.hour_ts.isin(w.hour_ts)]         # keep the key link to weather_hourly valid

# 5. reddit titles
p = pd.read_csv("data/raw/reddit_posts.csv")
p["created_ist"] = pd.to_datetime(p.created_utc, unit="s", utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
p["date"] = p.created_ist.dt.date
p["commute_post"] = p.title.str.lower().str.contains(r"\b(?:traffic|jam|jams|commute|stuck|flood|floods|flooded|flooding|waterlogged|waterlogging|pothole|potholes|rain|rains|raining|rainy)\b")
p = p.rename(columns={"id": "post_id"})[["post_id", "created_ist", "date", "title", "commute_post"]]
p = p[p.date.between(pd.Timestamp("2025-10-01").date(), pd.Timestamp("2026-10-31").date())]

tables = [("stations", pd.read_csv("data/stations.csv")), ("calendar", cal),
          ("weather_hourly", w), ("readings_hourly", r), ("reddit_posts", p)]
for name, df in tables:
    df.to_sql(name, db, if_exists="append", index=False, chunksize=5000)
    print(f"loaded {name}: {len(df):,} rows")

# 6. run every query and save the output
out = []
with db.connect() as con:
    for q in open("sql/queries.sql").read().split(";"):
        q = q.strip()
        if q and not q.startswith("USE"):
            res = pd.read_sql(text(q), con)
            out.append(q + "\n\n" + res.to_string(index=False) + "\n")
open("sql/query_results.txt", "w").write("\n" + ("\n" + "-" * 60 + "\n").join(out))
print("query results saved to sql/query_results.txt")
