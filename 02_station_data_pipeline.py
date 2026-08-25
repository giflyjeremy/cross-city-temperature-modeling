"""
=====================================================================
STATION AIR TEMPERATURE PIPELINE: RETRIEVAL, TEMPORAL ALIGNMENT,
AND MERGE WITH SATELLITE DATA
=====================================================================

Retrieves hourly air temperature from the global synoptic station
network (no institutional data request required), aggregates it to
the same 8-day compositing scheme used by MODIS satellite products,
and merges it with independently exported satellite land surface
temperature (LST) data on a matching key.

Designed for scenarios where:
  - a formal data request process is impractical or too slow, and
  - satellite composite periods must be reproduced exactly in Python
    so that ground and satellite time series can be joined without
    manual date reconciliation.

Run as three stages (can be split into separate scripts/notebook
cells for a Colab / Jupyter workflow):
  Stage A: pull_hourly_station_data()
  Stage B: aggregate_to_8day_periods()
  Stage C: merge_with_satellite_lst()
=====================================================================
"""

import os
import glob
import pandas as pd
from meteostat import Stations, hourly, Parameter, config

config.block_large_requests = False  # needed for multi-year pulls

# ---------------------------------------------------------------
# CONFIGURATION -- edit for your own study area
# ---------------------------------------------------------------
CITY_COORDINATES = {
    # "City label": (latitude, longitude)
    "CityA": (1.4748, 124.8421),
    "CityB": (-2.9761, 104.7754),
}

CITY_TIMEZONE = {
    "CityA": "Asia/Makassar",
    "CityB": "Asia/Jakarta",
}

DATE_START = pd.Timestamp("2015-01-01")
DATE_END = pd.Timestamp("2025-12-31")

DAYTIME_WINDOW = (13, 14)   # local hour range matching satellite overpass
NIGHTTIME_WINDOW = (1, 2)

OUTPUT_DIR = "output"
os.makedirs(os.path.join(OUTPUT_DIR, "hourly"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "8day"), exist_ok=True)


# =====================================================================
# STAGE A: RETRIEVE HOURLY DATA FROM THE OPEN STATION NETWORK
# =====================================================================
def pull_hourly_station_data():
    station_finder = Stations()
    metadata = []

    for city, (lat, lon) in CITY_COORDINATES.items():
        nearby = station_finder.nearby(lat, lon, radius=60_000)
        if len(nearby) == 0:
            print(f"[!] {city}: no station found within search radius")
            continue

        station_id = nearby.index[0]
        distance_km = round(nearby.iloc[0]["distance"] / 1000, 1)
        print(f"[OK] {city}: nearest station '{nearby.iloc[0]['name']}' "
              f"({distance_km} km away)")

        df = hourly(
            station_id, start=DATE_START, end=DATE_END,
            parameters=[Parameter.TEMP, Parameter.RHUM, Parameter.PRES],
        ).fetch()

        df.to_csv(os.path.join(OUTPUT_DIR, "hourly", f"{city}.csv"))
        metadata.append({"city": city, "station_id": station_id,
                          "distance_km": distance_km})

    pd.DataFrame(metadata).to_csv(
        os.path.join(OUTPUT_DIR, "station_metadata.csv"), index=False
    )


# =====================================================================
# STAGE B: AGGREGATE TO 8-DAY PERIODS MATCHING MODIS COMPOSITING
# =====================================================================
def _period_start(date):
    """Return the start date of the 8-day period containing `date`,
    following the same convention MODIS uses for compositing
    (periods restart every January 1st, in fixed 8-day steps)."""
    year_start = pd.Timestamp(year=date.year, month=1, day=1)
    day_offset = (date - year_start).days
    period_offset = (day_offset // 8) * 8
    return year_start + pd.Timedelta(days=period_offset)


def aggregate_to_8day_periods():
    for city, tz in CITY_TIMEZONE.items():
        path = os.path.join(OUTPUT_DIR, "hourly", f"{city}.csv")
        if not os.path.exists(path):
            continue

        df = pd.read_csv(path, index_col=0, parse_dates=True)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        df_local = df.copy()
        df_local.index = df_local.index.tz_convert(tz)
        df_local["period"] = df_local.index.normalize().tz_localize(None).map(_period_start)

        daytime = df_local[df_local.index.hour.isin(range(DAYTIME_WINDOW[0], DAYTIME_WINDOW[1] + 1))]
        nighttime = df_local[df_local.index.hour.isin(range(NIGHTTIME_WINDOW[0], NIGHTTIME_WINDOW[1] + 1))]

        day_agg = daytime.groupby("period")["temp"].mean().rename("ta_day_c")
        night_agg = nighttime.groupby("period")["temp"].mean().rename("ta_night_c")

        merged = pd.concat([day_agg, night_agg], axis=1).reset_index()
        merged.columns = ["period_start_date", "ta_day_c", "ta_night_c"]
        merged["city"] = city
        merged.to_csv(os.path.join(OUTPUT_DIR, "8day", f"{city}.csv"), index=False)


# =====================================================================
# STAGE C: MERGE WITH SATELLITE LST EXPORTS
# =====================================================================
def merge_with_satellite_lst(lst_dir="lst_gee"):
    lst_files = sorted(glob.glob(os.path.join(lst_dir, "LST_8day_*.csv")))
    ta_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "8day", "*.csv")))

    lst_df = pd.concat(
        [pd.read_csv(f, parse_dates=["period_start_date"]) for f in lst_files],
        ignore_index=True
    )
    ta_df = pd.concat(
        [pd.read_csv(f, parse_dates=["period_start_date"]) for f in ta_files],
        ignore_index=True
    )

    merged = pd.merge(lst_df, ta_df, on=["city", "period_start_date"], how="inner")
    complete = merged.dropna(subset=["lst_day_c", "lst_night_c", "ta_day_c", "ta_night_c"])

    out_path = os.path.join(OUTPUT_DIR, "merged_lst_ta.csv")
    complete.to_csv(out_path, index=False)
    print(f"Merged dataset: {len(complete)} complete rows -> {out_path}")
    return complete


if __name__ == "__main__":
    pull_hourly_station_data()
    aggregate_to_8day_periods()
    merge_with_satellite_lst()
