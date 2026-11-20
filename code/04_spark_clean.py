# Step 4: clean the big air table with PySpark and resample it to hourly.
# Input : thousands of daily .csv.gz files, readings every 15 minutes
# Output: data/clean/air_hourly.csv, data/clean/hour_weekday.csv, row counts

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

spark = (SparkSession.builder.appName("8pm-problem")
         .config("spark.sql.session.timeZone", "Asia/Kolkata")   # show all times in IST
         .config("spark.driver.memory", "4g")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

counts = []                                   # row counts after each step


def log(step, df):
    n = df.count()
    counts.append((step, n))
    print(f"{step:45s} {n:>10,}")


# 1. load everything as plain text (no type guessing)
raw = spark.read.csv("data/raw/openaq/*.csv.gz", header=True)
log("1. raw rows (all pollutants)", raw)

# 2. keep the two pollutants we study: NO2 (traffic signal) and PM2.5
df = raw.filter(F.col("parameter").isin("no2", "pm25"))
log("2. only no2 and pm25", df)

# 3. type casting: text -> number, text with +05:30 offset -> timestamp
df = (df.withColumn("value", F.col("value").cast("double"))
        .withColumn("ts", F.to_timestamp("datetime"))
        .withColumn("station_id", F.col("location_id").cast("int"))
        .select("station_id", "parameter", "ts", "value"))
df = df.dropna(subset=["value", "ts"])
log("3. after casting, unreadable rows dropped", df)

# 4. exact duplicate readings
df = df.dropDuplicates(["station_id", "parameter", "ts"])
log("4. duplicates removed", df)

# 5. sensor failure codes: negatives, zero and 999 or more
df = df.filter((F.col("value") > 0) & (F.col("value") < 999))
log("5. negatives, zeros and 999+ removed", df)

# 6. flat-lines: the same value repeated for 4+ hours (16 readings) = stuck sensor
w = Window.partitionBy("station_id", "parameter").orderBy("ts")
df = df.withColumn("changed", (F.col("value") != F.lag("value").over(w)).cast("int"))
df = df.fillna({"changed": 1})
df = df.withColumn("run_id", F.sum("changed").over(w))
run = Window.partitionBy("station_id", "parameter", "run_id")
df = df.withColumn("run_len", F.count("*").over(run))
df = df.filter(F.col("run_len") < 16).drop("changed", "run_id", "run_len").cache()
log("6. flat-line runs (4h+) removed", df)

# 7. resample 15 minute readings to hourly averages
hourly = (df.withColumn("hour_ts", F.date_trunc("hour", "ts"))
            .groupBy("station_id", "hour_ts")
            .pivot("parameter", ["no2", "pm25"])
            .agg(F.round(F.avg("value"), 2)))
log("7. hourly station rows", hourly)

# 8. weather: times are UTC strings, add +00:00 so Spark reads them as UTC.
#    In IST they land on half hours (00:00 UTC = 05:30 IST), so we round
#    down to the whole hour, otherwise no weather row would match an air row.
weather = spark.read.csv("data/raw/weather/weather_hourly_utc.csv", header=True, inferSchema=True)
weather = (weather.withColumn("ist", F.to_timestamp(F.concat(F.col("time_utc").cast("string"), F.lit("+00:00"))))
                  .withColumn("hour_ts", F.date_trunc("hour", "ist"))
                  .drop("time_utc", "ist"))
log("8. weather hours", weather)

# 9. join each station-hour with that hour's weather
joined = hourly.join(weather, on="hour_ts", how="left")
log("9. joined air + weather", joined)

# 10. city average by weekday and hour of day
hw = (joined.withColumn("weekday", F.date_format("hour_ts", "E"))
            .withColumn("hour", F.hour("hour_ts"))
            .groupBy("weekday", "hour")
            .agg(F.round(F.avg("no2"), 2).alias("no2"), F.round(F.avg("pm25"), 2).alias("pm25"))
            .orderBy("weekday", "hour"))
log("10. hour x weekday table", hw)

# save small results with pandas (they fit in memory easily)
out = joined.withColumn("hour_ts", F.date_format("hour_ts", "yyyy-MM-dd HH:mm")).orderBy("station_id", "hour_ts")
out.toPandas().to_csv("data/clean/air_hourly.csv", index=False)
hw.toPandas().to_csv("data/clean/hour_weekday.csv", index=False)
(weather.withColumn("hour_ts", F.date_format("hour_ts", "yyyy-MM-dd HH:mm")).orderBy("hour_ts")
        .toPandas().to_csv("data/clean/weather_hourly_ist.csv", index=False))
spark.createDataFrame(counts, ["step", "rows"]).toPandas().to_csv("data/clean/spark_row_counts.csv", index=False)

spark.stop()
