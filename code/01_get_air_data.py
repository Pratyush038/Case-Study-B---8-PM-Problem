# Step 1: download air quality readings for Bengaluru stations.
# Source: OpenAQ public archive on AWS (CPCB and KSPCB stations).
# One small .csv.gz file per station per day, readings every 15 minutes.

import os
import re
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

BUCKET = "https://openaq-data-archive.s3.amazonaws.com/"
OUT = "data/raw/openaq"
MONTHS = pd.period_range("2025-10", "2026-10", freq="M")

stations = pd.read_csv("data/stations.csv")


def list_files(station_id, month):
    """Ask the bucket which daily files exist for one station and month."""
    prefix = f"records/csv.gz/locationid={station_id}/year={month.year}/month={month.month:02d}/"
    for attempt in range(5):          # retry if the network is slow
        try:
            r = requests.get(BUCKET, params={"list-type": "2", "prefix": prefix}, timeout=60)
            return re.findall(r"<Key>(.*?)</Key>", r.text)
        except requests.RequestException:
            pass
    return []


def download(key):
    path = os.path.join(OUT, os.path.basename(key))
    if os.path.exists(path):          # skip files we already have
        return
    for attempt in range(5):          # retry a few times if the network is slow
        try:
            r = requests.get(BUCKET + key, timeout=60)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                return
        except requests.RequestException:
            pass
    print("could not download", key)


os.makedirs(OUT, exist_ok=True)

jobs = [(sid, m) for sid in stations.station_id for m in MONTHS]

with ThreadPoolExecutor(16) as pool:
    lists = pool.map(lambda job: list_files(*job), jobs)
    keys = [k for one_list in lists for k in one_list]
    print("files to download:", len(keys), flush=True)
    list(pool.map(download, keys))

print("done, files on disk:", len(os.listdir(OUT)))
