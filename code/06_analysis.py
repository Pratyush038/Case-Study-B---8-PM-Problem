# Step 6: findings and charts.
# Stations differ a lot in scale, and different stations go offline on
# different days. A plain average would jump around depending on who reported.
# So every reading is first turned into "% of that station's normal level"
# (100 = normal for that station), then averaged across stations.

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
notes = []                                     # numbers we quote in the report


def say(text):
    print(text)
    notes.append(text)


# ---------- load ----------
air = pd.read_csv("data/clean/air_hourly_filled.csv", parse_dates=["hour_ts"])
holidays = pd.read_csv("data/holidays_karnataka.csv", parse_dates=["date"])
stations = pd.read_csv("data/stations.csv")
names = stations.set_index("station_id").station_name
good = air[air.used_in_city_avg].copy()

# ---------- normalise each station to its own normal ----------
for col in ["no2", "pm25"]:
    good[col + "_idx"] = 100 * good[col] / good.groupby("station_id")[col].transform("mean")

city = good.groupby("hour_ts").agg(no2=("no2_idx", "mean"), pm25=("pm25_idx", "mean"),
                                   rain=("precipitation", "first")).reset_index()
city["date"] = city.hour_ts.dt.normalize()
city["hour"] = city.hour_ts.dt.hour
city["weekday"] = city.hour_ts.dt.strftime("%a")
city["month"] = city.hour_ts.dt.month
city["workday"] = (city.hour_ts.dt.dayofweek < 5) & ~city.date.isin(holidays.date)
city["monsoon"] = city.month.isin([6, 7, 8, 9])

# ---------- chart 2: hour by weekday heatmap ----------
heat = city.pivot_table(index="weekday", columns="hour", values="no2", aggfunc="mean").loc[DAYS]
plt.figure(figsize=(11, 4))
sns.heatmap(heat, cmap="rocket_r", cbar_kws={"label": "NO2, % of normal"})
work = city[city.workday].groupby("hour")[["no2", "pm25"]].mean()
say(f"Workday NO2 5-8 PM: {work.no2.loc[17:20].mean():.0f}% of normal, "
    f"7-10 AM: {work.no2.loc[7:10].mean():.0f}%, 2-5 AM: {work.no2.loc[2:5].mean():.0f}%")
say(f"Workday PM2.5 evening peak at {work.pm25.loc[12:23].idxmax()}:00 ({work.pm25.loc[12:23].max():.0f}%)")
plt.title("NO2 is highest from 5 to 9 PM every day, the morning rush barely shows")
plt.xlabel("Hour of day (IST)"); plt.ylabel("")
plt.tight_layout(); plt.savefig("charts/02_heatmap_no2.png", dpi=150); plt.close()

# ---------- chart 3: rainy vs dry evenings (monsoon workdays only) ----------
# rainy evening = 2 mm or more between 4 PM and 9 PM, dry evening = no rain then
eve_rain = city[city.hour.between(16, 21)].groupby("date").rain.sum()
rainy_days = eve_rain[eve_rain >= 2].index
dry_days = eve_rain[eve_rain == 0].index
city["day_type"] = "other"
city.loc[city.date.isin(rainy_days), "day_type"] = "rainy evening"
city.loc[city.date.isin(dry_days), "day_type"] = "dry evening"

m = city[city.monsoon & city.workday & (city.day_type != "other")]
prof = m.groupby(["day_type", "hour"])[["no2", "pm25"]].mean()
n_days = m.groupby("day_type").date.nunique()
say(f"Monsoon workdays compared: {n_days.to_dict()}")

fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharex=True)
for ax, col, label in zip(axes, ["no2", "pm25"], ["NO2", "PM2.5"]):
    for t, c in [("dry evening", "#1b9e77"), ("rainy evening", "#386cb0")]:
        s = prof.loc[t, col]
        ax.plot(s.index, s.values, label=f"{t} ({n_days[t]} days)", color=c, lw=2)
        say(f"{label} {t}: 5-7 PM {s.loc[17:19].mean():.0f}%, 8-10 PM {s.loc[20:22].mean():.0f}%")
    ax.axvspan(16, 21, color="grey", alpha=0.1)
    ax.axhline(100, color="black", lw=0.5)
    ax.set_title(label); ax.set_xlabel("Hour of day (IST)"); ax.set_ylabel("% of normal")
axes[0].legend()
fig.suptitle("On rainy monsoon evenings the NO2 peak comes later (about 9 PM), and PM2.5 is washed down by half")
plt.tight_layout(); plt.savefig("charts/03_rain_vs_dry.png", dpi=150); plt.close()

# same comparison station by station, to see who drives it
gm = good[good.hour_ts.dt.month.isin([6, 7, 8, 9]) & (good.hour_ts.dt.dayofweek < 5)
          & good.hour_ts.dt.hour.between(20, 22)].copy()
gm["date"] = gm.hour_ts.dt.normalize()
by_station = pd.DataFrame({
    "dry": gm[gm.date.isin(dry_days)].groupby("station_id").no2_idx.mean(),
    "rainy": gm[gm.date.isin(rainy_days)].groupby("station_id").no2_idx.mean(),
}).round(0)
by_station.index = by_station.index.map(names)
say("NO2 8-10 PM by station, monsoon workdays (% of normal):\n" + by_station.to_string())

# ---------- chart 4: stations on one scale (z-scores) ----------
wk = good[good.hour_ts.dt.dayofweek < 5].copy()
wk["hour"] = wk.hour_ts.dt.hour
st = wk.groupby(["station_id", "hour"]).no2.mean().reset_index()
st["z"] = st.groupby("station_id").no2.transform(lambda s: (s - s.mean()) / s.std())
raw_means = good.groupby("station_id").no2.mean().round(1)
say("Raw mean NO2 by station (µg/m³): " + ", ".join(f"{names[i]} {v}" for i, v in raw_means.items()))

plt.figure(figsize=(10, 4.5))
for sid, g in st.groupby("station_id"):
    plt.plot(g.hour, g.z, lw=1.8, alpha=0.85, label=f"{names[sid]} (avg {raw_means[sid]:.0f} µg/m³)")
plt.axhline(0, color="black", lw=0.5)
plt.title("Three stations peak around 7 PM, BTM Layout is highest after midnight (NO2 z-scores)")
plt.xlabel("Hour of day (IST), weekdays"); plt.ylabel("NO2, z-score within station")
plt.legend(fontsize=8); plt.tight_layout(); plt.savefig("charts/04_station_zscores.png", dpi=150); plt.close()

# ---------- chart 5: Reddit titles joined with rain ----------
posts = pd.read_csv("data/raw/reddit_posts.csv")
posts["time_ist"] = pd.to_datetime(posts.created_utc, unit="s", utc=True).dt.tz_convert("Asia/Kolkata")
posts["date"] = posts.time_ist.dt.tz_localize(None).dt.normalize()
words = r"\b(?:traffic|jam|jams|commute|stuck|flood|floods|flooded|flooding|waterlogged|waterlogging|pothole|potholes|rain|rains|raining|rainy)\b"   # whole words only, so "grains" or "train" do not count
posts["commute_post"] = posts.title.str.lower().str.contains(words, regex=True)
say(f"Reddit: {len(posts)} titles on {posts.date.nunique()} days, "
    f"{posts.commute_post.mean()*100:.1f}% about traffic or rain")

day_rain = city.groupby("date").rain.sum()
daily = posts.groupby("date").agg(share=("commute_post", "mean")).reset_index()
daily = daily.merge(day_rain.rename("rain_mm").reset_index(), on="date")
daily["rain_band"] = pd.cut(daily.rain_mm, [-0.1, 0, 5, 500], labels=["dry", "0-5 mm", "5 mm or more"])
band = daily.groupby("rain_band", observed=True).agg(share=("share", "mean"), days=("date", "size"))
band["share"] *= 100
say(f"Commute post share, dry days {100*daily[daily.rain_mm == 0].share.mean():.1f}% vs any rain {100*daily[daily.rain_mm > 0].share.mean():.1f}%")
say("Commute post share by rain band: " + ", ".join(f"{i} {r.share:.1f}% ({r.days} days)" for i, r in band.iterrows()))

plt.figure(figsize=(7, 4))
bars = plt.bar(band.index.astype(str), band.share, color="#386cb0")
for b, d in zip(bars, band.days):
    plt.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{d} days", ha="center", va="bottom", fontsize=9)
plt.title("Rain days bring a few more traffic and rain posts, heavy rain no more than light")
plt.xlabel("Rain that day (Open-Meteo)"); plt.ylabel("% of post titles about traffic or rain")
plt.tight_layout(); plt.savefig("charts/05_reddit_vs_rain.png", dpi=150); plt.close()

# ---------- chart 6: Deepavali, a real extreme we kept ----------
d = city[(city.hour_ts >= "2025-10-17") & (city.hour_ts < "2025-10-25")]
normal = city[(city.month == 10) & city.workday
              & ~city.date.between("2025-10-17", "2025-10-24")].groupby("hour").pm25.mean()
top = d.loc[d.pm25.idxmax()]
raw_top = good[good.hour_ts.between("2025-10-17", "2025-10-25")].dropna(subset=["pm25"]).sort_values("pm25").iloc[-1]
say(f"Deepavali: city PM2.5 hit {top.pm25:.0f}% of normal at {top.hour_ts}; normal October at that hour "
    f"{normal[top.hour]:.0f}%. Highest station-hour {raw_top.pm25:.0f} µg/m³ at {names[raw_top.station_id]}, {raw_top.hour_ts}")

plt.figure(figsize=(11, 4))
plt.plot(d.hour_ts, d.pm25, color="#e7298a", lw=2, label="Oct 17 to 24, 2025 (Deepavali Oct 20 to 22)")
plt.plot(d.hour_ts, d.hour.map(normal), color="grey", ls="--", label="normal October workday")
plt.title("Deepavali nights push PM2.5 to several times a normal October night")
plt.ylabel("PM2.5, % of normal"); plt.legend()
plt.tight_layout(); plt.savefig("charts/06_diwali.png", dpi=150); plt.close()

# ---------- chart 7: which months have the worst evenings ----------
eve = city[city.workday & city.hour.between(17, 21)]
by_month = eve.groupby(eve.hour_ts.dt.to_period("M"))[["no2", "pm25"]].mean().round(0)
say("Workday 5-9 PM by month (% of normal):\n" + by_month.to_string())
ax = by_month.plot.bar(figsize=(10, 4), color=["#d95f02", "#7570b3"], width=0.8)
ax.axhline(100, color="black", lw=0.5)
ax.set_xticklabels([p.strftime("%b %y") for p in by_month.index], rotation=0)
ax.set_xlabel(""); ax.set_ylabel("% of normal, workdays 5 to 9 PM")
ax.set_title("Evenings are dirtiest from December to April, cleanest in the monsoon")
plt.tight_layout(); plt.savefig("charts/07_months.png", dpi=150); plt.close()


# ---------- AQI category (ordinal) for PM2.5, CPCB bands ----------
bands = [0, 30, 60, 90, 120, 250, 10000]
labels = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
good["pm25_category"] = pd.cut(good.pm25, bands, labels=labels)   # ordered categories
ev = good[good.hour_ts.dt.hour.between(17, 21) & (good.hour_ts.dt.dayofweek < 5)]
share = (ev.pm25_category.value_counts(normalize=True).reindex(labels) * 100).round(1)
say("Workday 5-9 PM station-hours by PM2.5 category (%): " + ", ".join(f"{k} {v}" for k, v in share.items()))

with open("data/clean/findings.txt", "w") as f:
    f.write("\n".join(notes))
