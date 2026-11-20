# Step 3: download post titles from r/bangalore (text source).
# Uses the free Arctic Shift Reddit archive API, which returns JSON.
# We only ask for id, time and title. No usernames are ever downloaded.

import os
import json
import time
import requests
import pandas as pd

URL = "https://arctic-shift.photon-reddit.com/api/posts/search"
OUT = "data/raw/reddit"
# every 6th day keeps the download short (the API is slow) and still
# rotates through all weekdays
DAYS = pd.date_range("2025-10-01", "2026-10-31", freq="6D")
os.makedirs(OUT, exist_ok=True)


def get(params):
    """Call the API, wait and retry if it says slow down."""
    for attempt in range(6):
        try:
            d = requests.get(URL, params=params, timeout=90).json()
            if d.get("data") is not None:
                return d["data"]
        except Exception:
            pass
        time.sleep(5 * (attempt + 1))
    return []


for day in DAYS:
    path = f"{OUT}/{day.date()}.json"
    if os.path.exists(path):
        continue
    # windows start at midnight IST (UTC + 5:30), so a day here is an Indian day
    start = int((day - pd.Timedelta(hours=5, minutes=30)).timestamp())
    end = start + 24 * 3600
    posts = []
    while True:                       # page through the day, 100 posts at a time
        batch = get({"subreddit": "bangalore", "after": start, "before": end,
                     "limit": 100, "sort": "asc", "fields": "id,created_utc,title"})
        posts += batch
        if len(batch) < 100:
            break
        start = batch[-1]["created_utc"]
        time.sleep(1)
    with open(path, "w") as f:
        json.dump(posts, f)
    print(day.date(), len(posts), flush=True)
    time.sleep(1)

# flatten all days into one table
rows = []
for day in DAYS:
    rows += json.load(open(f"{OUT}/{day.date()}.json"))
df = pd.DataFrame(rows).drop_duplicates("id")
df.to_csv("data/raw/reddit_posts.csv", index=False)
print("posts:", len(df))
