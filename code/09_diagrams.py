# Draws the ER diagram (charts/er_diagram.png) and the pipeline (charts/pipeline.png).

import matplotlib.pyplot as plt

tables = {
    "stations":        (0.05, 0.62, ["PK station_id", "station_name", "agency", "area_type", "lat, lon"]),
    "readings_hourly": (0.38, 0.62, ["PK,FK station_id", "PK,FK hour_ts", "no2", "pm25"]),
    "weather_hourly":  (0.71, 0.62, ["PK hour_ts", "FK date", "precipitation", "temperature, humidity", "wind_speed"]),
    "calendar":        (0.71, 0.08, ["PK date", "weekday", "is_weekend", "is_holiday", "holiday_name", "season"]),
    "reddit_posts":    (0.38, 0.08, ["PK post_id", "created_ist", "FK date", "title", "commute_post"]),
}
W, LINE = 0.24, 0.045

fig, ax = plt.subplots(figsize=(11, 6))
for name, (x, y, cols) in tables.items():
    h = LINE * (len(cols) + 1)
    ax.add_patch(plt.Rectangle((x, y), W, h, fill=False, lw=1.5))
    ax.add_patch(plt.Rectangle((x, y + h - LINE), W, LINE, color="#386cb0"))
    ax.text(x + 0.01, y + h - LINE / 2, name, color="white", va="center", weight="bold")
    for i, c in enumerate(cols):
        ax.text(x + 0.01, y + h - LINE * (i + 1.5), c, va="center", fontsize=9)

arrows = [((0.29, 0.75), (0.38, 0.75), "1 : many"),
          ((0.71, 0.75), (0.62, 0.75), "1 : many"),
          ((0.83, 0.62), (0.83, 0.40), "many : 1"),
          ((0.62, 0.20), (0.71, 0.20), "many : 1")]
for (x1, y1), (x2, y2), label in arrows:
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.02, label, fontsize=8, ha="center")

ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("ER diagram: blr_rush database (MySQL)")
plt.tight_layout()
plt.savefig("charts/er_diagram.png", dpi=150)
plt.close()

# ---------- pipeline diagram ----------
steps = [
    ("Sources", ["OpenAQ archive\n(CSV.gz, 15 min)", "Open-Meteo API\n(JSON, hourly)", "Reddit API\n(JSON, text)", "Holiday list\n(hand-made CSV)"]),
    ("Download\n01, 02, 03", ["data/raw/"]),
    ("PySpark\n04_spark_clean", ["cast types", "UTC -> IST", "drop faults", "15 min -> hourly", "join weather"]),
    ("pandas\n05_gaps", ["drop spikes", "count gaps", "fill gaps <= 3 h"]),
    ("Outputs\n06, 07, 08", ["charts/", "spreadsheet pivot", "MySQL (5 tables)"]),
]
fig, ax = plt.subplots(figsize=(12, 4))
for i, (title, items) in enumerate(steps):
    x = 0.02 + i * 0.2
    ax.text(x + 0.08, 0.93, title, ha="center", va="top", weight="bold", fontsize=10)
    for j, item in enumerate(items):
        y = 0.70 - j * 0.14
        ax.add_patch(plt.Rectangle((x, y - 0.055), 0.16, 0.11, color="#dbe5f1"))
        ax.text(x + 0.08, y, item, ha="center", va="center", fontsize=8)
    if i < len(steps) - 1:
        ax.annotate("", xy=(x + 0.195, 0.45), xytext=(x + 0.165, 0.45),
                    arrowprops=dict(arrowstyle="->", lw=1.5))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
plt.tight_layout()
plt.savefig("charts/pipeline.png", dpi=150)
