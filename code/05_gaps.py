# Step 5: count missing hours per station and fill only the short gaps.
# Rule: gaps of 3 hours or less -> straight-line fill (pollution changes smoothly).
#       longer gaps -> left empty, we do not invent data.
#       stations missing more than half their hours -> left out of city averages.
#       the industrial station (Peenya) -> left out of city averages too.

import pandas as pd
import matplotlib.pyplot as plt

air = pd.read_csv("data/clean/air_hourly.csv", parse_dates=["hour_ts"])
stations = pd.read_csv("data/stations.csv")
weather = pd.read_csv("data/clean/weather_hourly_ist.csv", parse_dates=["hour_ts"])

all_hours = pd.date_range("2025-10-01 00:00", "2026-10-31 23:00", freq="h")

# Spike rule (sensor fault vs real event):
# a reading more than 4x its station's median of the surrounding 24 hours is a
# spike. If most other stations are normal at that hour, it is one faulty
# sensor and we remove it. If the whole city rises (Deepavali), it is real.
spikes = []
for col in ["no2", "pm25"]:
    wide = air.pivot(index="hour_ts", columns="station_id", values=col).reindex(all_hours)
    ratio = wide / wide.rolling(24, center=True, min_periods=6).median()
    city_ratio = ratio.median(axis=1)
    bad = ratio.gt(4) & city_ratio.lt(1.5).values[:, None]
    for sid in wide.columns:
        for ts in wide.index[bad[sid]]:
            spikes.append({"station_id": sid, "hour_ts": ts, "pollutant": col,
                           "value": wide.at[ts, sid], "times_local_median": round(ratio.at[ts, sid], 1)})
spikes = pd.DataFrame(spikes)
for r in spikes.itertuples():
    air.loc[(air.station_id == r.station_id) & (air.hour_ts == r.hour_ts), r.pollutant] = None
spikes.to_csv("data/clean/spikes_removed.csv", index=False)
print("single-station spikes removed:", len(spikes))
print(spikes.groupby(["station_id", "pollutant"]).size())

rows, filled = [], []

for sid, g in air.groupby("station_id"):
    g = g.set_index("hour_ts")[["no2", "pm25"]].reindex(all_hours)
    for col in ["no2", "pm25"]:
        missing = g[col].isna()
        run_id = (missing != missing.shift()).cumsum()
        gap_lengths = missing.groupby(run_id).sum()
        gap_lengths = gap_lengths[gap_lengths > 0]
        rows.append({"station_id": sid, "pollutant": col,
                     "hours_missing": int(missing.sum()),
                     "pct_missing": round(100 * missing.mean(), 1),
                     "short_gaps_le3h": int((gap_lengths <= 3).sum()),
                     "long_gaps_gt3h": int((gap_lengths > 3).sum()),
                     "longest_gap_h": int(gap_lengths.max()) if len(gap_lengths) else 0})
        g[col] = g[col].interpolate(limit=3, limit_area="inside")
    g["station_id"] = sid
    filled.append(g.rename_axis("hour_ts").reset_index())

gaps = pd.DataFrame(rows).merge(stations[["station_id", "station_name"]])
gaps.to_csv("data/clean/gap_summary.csv", index=False)

# decide which stations go into the city average:
# enough NO2 data (half the hours or more) and not an industrial area,
# because we use NO2 as a sign of traffic and Peenya's NO2 is mostly factories
no2_gaps = gaps[gaps.pollutant == "no2"].set_index("station_id")["pct_missing"]
industrial = stations[stations.area_type.str.contains("industrial")].station_id
keep = [s for s in no2_gaps[no2_gaps <= 50].index if s not in set(industrial)]
print("stations kept:", len(keep), "of", len(no2_gaps))

air_filled = pd.concat(filled)
air_filled["used_in_city_avg"] = air_filled.station_id.isin(keep)
air_filled = air_filled.merge(weather, on="hour_ts", how="left")
air_filled.to_csv("data/clean/air_hourly_filled.csv", index=False)

# gap chart
p = gaps.pivot(index="station_name", columns="pollutant", values="pct_missing").sort_values("no2")
ax = p.plot.barh(figsize=(8, 6), color=["#d95f02", "#7570b3"])
ax.axvline(50, color="grey", ls="--", lw=1)
ax.set_xlabel("% of hours with no reading (Oct 2025 to Oct 2026)")
ax.set_ylabel("")
ax.set_title("Every station misses at least a fifth of its hours")
plt.tight_layout()
plt.savefig("charts/01_gap_chart.png", dpi=150)
print(gaps.to_string())
