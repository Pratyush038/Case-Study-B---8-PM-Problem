# Step 2: download hourly weather for Bengaluru from the Open-Meteo archive API.
# The API returns JSON. Times come back in UTC (GMT), we convert to IST later.

import json
import requests
import pandas as pd

URL = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 12.97,
    "longitude": 77.59,
    "start_date": "2025-10-01",
    "end_date": "2026-10-31",
    "hourly": "precipitation,temperature_2m,relative_humidity_2m,wind_speed_10m",
}

data = requests.get(URL, params=params, timeout=120).json()

# keep the raw JSON exactly as received
with open("data/raw/weather/open_meteo_raw.json", "w") as f:
    json.dump(data, f)

# flatten: the "hourly" block is a dict of equal length lists, one per field
weather = pd.DataFrame(data["hourly"])
weather = weather.rename(columns={"time": "time_utc"})
weather.to_csv("data/raw/weather/weather_hourly_utc.csv", index=False)

print(weather.shape)
print(weather.head())
