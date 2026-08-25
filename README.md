# Cross-City Spatial Temperature Modeling: GIS, Remote Sensing & Statistical Pipeline

A set of Python and Google Earth Engine scripts developed for an academic
research project testing whether satellite-derived temperature models
generalize across cities, applied to seven cities in Indonesia.

## What this project does

This repository contains the geospatial data engineering and statistical
modeling pipeline behind an academic manuscript examining the relationship
between satellite land surface temperature (LST) and ground-level air
temperature (Ta) across multiple cities. The pipeline:

- Extracts 8-day composite satellite land surface temperature from MODIS
  imagery via Google Earth Engine, with quality-control masking calibrated
  through direct diagnostic testing rather than default assumptions
- Retrieves and temporally aligns ground station air temperature data from
  an open global synoptic network, matched to satellite overpass windows
- Merges satellite and ground-station time series into a single analysis
  dataset
- Builds and cross-validates a Random Forest model against a simple
  regression baseline, using **leave-one-location-out validation** to test
  genuine spatial generalization rather than in-sample fit
- Includes a custom diagnostic metric (anomaly-based R²) that separates
  two distinct sources of model error: getting a new location's average
  level wrong versus getting its temporal pattern wrong
- Generates a publication-style two-panel study area map from open
  boundary data, with no manual shapefile download required

## Why this project is useful

Most tutorials on satellite-ground temperature modeling stop at a single
train/test split within one study area. This pipeline instead demonstrates
a stricter and more decision-relevant test: **whether a model trained on
some locations actually holds up in a location it has never seen** — the
condition that matters if the model is ever meant to be applied somewhere
new. The anomaly-based R² component is a reusable pattern for diagnosing
*why* a spatial model fails to generalize, not just confirming that it
does.

The scripts are written to be adapted rather than copied verbatim: city
lists, boundary sources, feature sets, and file paths are isolated at the
top of each script.

## How to get started

**Requirements:** Python 3.10+, a Google Earth Engine account (free for
research/non-commercial use), and the following packages:

```bash
pip install pandas geopandas matplotlib scikit-learn scipy meteostat
```

**Suggested order:**

1. `scripts/01_gee_lst_extraction.js` — run in the [Earth Engine Code
   Editor](https://code.earthengine.google.com); exports per-city CSV
   files to Google Drive
2. `scripts/02_station_data_pipeline.py` — retrieves ground station data,
   aligns it to the same 8-day periods, and merges it with the GEE export
3. `scripts/03_cross_location_validation.py` — trains and cross-validates
   the models on the merged dataset
4. `scripts/04_study_area_map.py` — generates the locator + main study
   area map (independent of the other three scripts)

Each script has its configuration values (city names, coordinates, file
paths, feature lists) isolated near the top for easy adaptation to a new
study area or prediction problem.

## Data status

This pipeline was built for, and run on, real observational data: MODIS
satellite imagery, ground station records from an open synoptic network,
and open administrative boundary data. The example city names and
coordinates in these scripts have been generalized as placeholders so the
code can be reused for a different study area; the underlying methodology,
parameter choices, and validation design reflect the actual approach used
in the original research.

## Where to get help

Questions about adapting this pipeline, or interested in similar work?
Email: giflyjeremy@gmail.com

## Who maintains this project

Maintained by Gifly Jeremy Tambajong — GIS and remote sensing analyst with
a background in spatial planning, currently working on tropical urban
climate research using Google Earth Engine, Python, and R.
