# The 8 PM Problem (Bengaluru)

Our Case Study B project. We looked at when Bengaluru's evening pollution rush is worst and whether rain makes it worse.

In short, the bad hours are 5 to 9 PM, the bad months are January to April, and rain pushes the evening peak later at big junctions like Silk Board. The full story is in `report/report.pdf`.

## What's in here

```
code/      the scripts, numbered in the order you run them
data/      station list, holiday list, raw downloads, cleaned files
sql/       MySQL schema, queries and their output
charts/    every chart in the report
report/    report (Markdown, Word and PDF)
slides/    10 slide deck
team_contribution.md
```

## Setup

You need Python 3.10+, Java 17 (for PySpark), MySQL 8 and LibreOffice (only for the spreadsheet check).

```
pip install -r requirements.txt
```

## Run it

Run everything from this folder, one step at a time.

```
python code/01_get_air_data.py     # air quality files, about 5 min
python code/02_get_weather.py      # weather, a few seconds
python code/03_get_reddit.py       # Reddit titles, about 20 min (the API is slow)
python code/04_spark_clean.py      # PySpark cleaning and hourly resample
python code/05_gaps.py             # spikes, gaps, gap chart
python code/06_analysis.py         # all the finding charts
python code/07_pivot_check.py      # spreadsheet vs pandas pivot
python code/08_load_mysql.py       # load MySQL and run the queries
python code/09_diagrams.py         # ER diagram and pipeline picture
python code/10_make_slides.py      # slide deck
python code/11_build_report.py     # report to Word and PDF
```

Steps 1 to 3 download the raw data. If you already have `data/raw/`, you can skip them. The download scripts skip files you already have, so it's safe to rerun them if one stops halfway.

## MySQL

The loader logs in as user `student` with password `student` on localhost. Make that user once with this command.

```
sudo mysql -e "CREATE USER 'student'@'localhost' IDENTIFIED BY 'student'; GRANT ALL ON blr_rush.* TO 'student'@'localhost';"
```

Or use your own login like this.

```
MYSQL_USER=me MYSQL_PASSWORD=secret python code/08_load_mysql.py
```

## Data

* Air quality from the OpenAQ archive of CPCB and KSPCB stations, https://openaq-data-archive.s3.amazonaws.com
* Weather from the Open-Meteo archive API, https://archive-api.open-meteo.com
* Reddit titles from r/bangalore through the Arctic Shift API (no usernames)
* Holidays typed by hand from the Karnataka government list

The raw air files are about 12 MB zipped. Cleaned files are in `data/clean/`.

GitHub repo : https://github.com/RahulPatnaik/Case-Study-B---8-PM-Problem.git
