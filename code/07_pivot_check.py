# Step 7: build the hour-by-weekday pivot two ways and compare.
#   a) spreadsheet: AVERAGEIFS formulas in Excel (recalculated by LibreOffice)
#   b) pandas: pivot_table
# Needs LibreOffice installed (the "soffice" command).

import subprocess
import pandas as pd
from openpyxl import Workbook, load_workbook

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
air = pd.read_csv("data/clean/air_hourly_filled.csv", parse_dates=["hour_ts"])
city = air[air.used_in_city_avg].groupby("hour_ts").no2.mean().dropna().reset_index()
city["weekday"] = city.hour_ts.dt.strftime("%a")
city["hour"] = city.hour_ts.dt.hour

# a) spreadsheet with raw rows in one sheet and formulas in another
wb = Workbook()
ws = wb.active
ws.title = "data"
ws.append(["hour_ts", "weekday", "hour", "no2"])
for r in city.itertuples():
    ws.append([str(r.hour_ts), r.weekday, r.hour, round(r.no2, 3)])
n = len(city) + 1

pv = wb.create_sheet("pivot")
pv.append(["weekday"] + list(range(24)))
for i, day in enumerate(DAYS, start=2):
    pv.cell(i, 1, day)
    for h in range(24):
        col = pv.cell(1, h + 2).column_letter
        pv.cell(i, h + 2, f'=AVERAGEIFS(data!$D$2:$D${n},data!$B$2:$B${n},$A{i},data!$C$2:$C${n},{col}$1)')
wb.save("data/clean/pivot_spreadsheet.xlsx")

# let LibreOffice open and re-save it so the formulas get calculated
subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", "data/clean/recalc",
                "data/clean/pivot_spreadsheet.xlsx"], check=True, capture_output=True)
sheet = load_workbook("data/clean/recalc/pivot_spreadsheet.xlsx", data_only=True)["pivot"]
excel = pd.DataFrame([[c.value for c in row[1:]] for row in sheet.iter_rows(min_row=2, max_row=8)],
                     index=DAYS, columns=range(24)).astype(float)

# b) pandas
pandas_pivot = city.pivot_table(index="weekday", columns="hour", values="no2", aggfunc="mean").loc[DAYS]

diff = (excel - pandas_pivot).abs().max().max()
print("largest difference between spreadsheet and pandas:", round(diff, 6))
print(pandas_pivot.round(1).iloc[:, 17:23])
