"""
=====================================================================
TWO-PANEL STUDY AREA MAP (LOCATOR + MAIN MAP)
No satellite imagery required, no manual shapefile download.
=====================================================================

Builds a standard "study area" figure for a geography / remote
sensing manuscript: a small locator panel showing the country within
its region, and a main panel showing numbered study locations against
open administrative boundaries.

Boundary data is fetched directly from open GitHub-hosted GeoJSON
mirrors, so the script runs with no manual data download and no paid
basemap service.

Adapt STUDY_LOCATIONS and the two GeoJSON source URLs for your own
country/region.
=====================================================================
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

STUDY_LOCATIONS = [
    ("1", "Location A", 124.8421, 1.4748),
    ("2", "Location B", 104.7754, -2.9761),
    # ... add remaining study locations
]

ADMIN_BOUNDARY_URL = "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-province-simple.json"
WORLD_BOUNDARY_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
COUNTRY_ISO3 = "IDN"
REGION_BOUNDS = dict(lon_min=85, lon_max=145, lat_min=-12, lat_max=25)
MAIN_MAP_BOUNDS = dict(lon_min=94, lon_max=128, lat_min=-8, lat_max=6)
SCALE_BAR_KM = 300


def build_study_area_map(output_path="study_area_map.png"):
    admin_boundaries = gpd.read_file(ADMIN_BOUNDARY_URL)
    world_boundaries = gpd.read_file(WORLD_BOUNDARY_URL)

    fig, (ax_locator, ax_main) = plt.subplots(
        1, 2, figsize=(13, 6.2), gridspec_kw={"width_ratios": [1, 2.3]}
    )
    fig.subplots_adjust(wspace=0.08, top=0.90, bottom=0.10, left=0.04, right=0.98)

    # --- Locator panel ---
    region = world_boundaries.cx[
        REGION_BOUNDS["lon_min"]:REGION_BOUNDS["lon_max"],
        REGION_BOUNDS["lat_min"]:REGION_BOUNDS["lat_max"]
    ]
    region.plot(ax=ax_locator, color="#f2f2f2", edgecolor="#999999", linewidth=0.5)
    country = world_boundaries[world_boundaries["id"] == COUNTRY_ISO3]
    country.plot(ax=ax_locator, color="#8fbf7f", edgecolor="#2c3e50", linewidth=0.8)
    ax_locator.set_xlim(REGION_BOUNDS["lon_min"], REGION_BOUNDS["lon_max"])
    ax_locator.set_ylim(REGION_BOUNDS["lat_min"], REGION_BOUNDS["lat_max"])
    ax_locator.set_xticks([]); ax_locator.set_yticks([])
    for spine in ax_locator.spines.values():
        spine.set_edgecolor("#444444")
    ax_locator.set_title("Study area location", fontsize=12, fontweight="bold", pad=8)
    ax_locator.annotate("N", xy=(0.90, 0.90), xytext=(0.90, 0.78), xycoords="axes fraction",
                         ha="center", fontsize=10, fontweight="bold",
                         arrowprops=dict(arrowstyle="-|>", color="black", lw=1.3))

    # --- Main panel ---
    admin_boundaries.plot(ax=ax_main, color="#eeeee6", edgecolor="#aaaaaa", linewidth=0.5)
    for num, name, lon, lat in STUDY_LOCATIONS:
        ax_main.scatter(lon, lat, s=70, color="#c0392b", edgecolor="white", linewidth=1.2, zorder=5)
        ax_main.annotate(num, (lon, lat), textcoords="offset points", xytext=(0, 8),
                          ha="center", fontsize=10, fontweight="bold", color="#1a1a1a",
                          path_effects=[pe.withStroke(linewidth=2.5, foreground="white")], zorder=6)
    ax_main.set_xlim(MAIN_MAP_BOUNDS["lon_min"], MAIN_MAP_BOUNDS["lon_max"])
    ax_main.set_ylim(MAIN_MAP_BOUNDS["lat_min"], MAIN_MAP_BOUNDS["lat_max"])
    ax_main.set_xlabel("Longitude", fontsize=9)
    ax_main.set_ylabel("Latitude", fontsize=9)
    ax_main.set_aspect("equal")
    ax_main.annotate("N", xy=(0.96, 0.93), xytext=(0.96, 0.80), xycoords="axes fraction",
                      ha="center", fontsize=13, fontweight="bold",
                      arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6))

    scale_deg = SCALE_BAR_KM / 111.0
    x0, y0 = MAIN_MAP_BOUNDS["lon_min"] + 2, MAIN_MAP_BOUNDS["lat_min"] + 0.8
    ax_main.plot([x0, x0 + scale_deg], [y0, y0], color="black", linewidth=3)
    ax_main.text(x0 + scale_deg / 2, y0 + 0.35, f"{SCALE_BAR_KM} km", ha="center", fontsize=8)

    legend_text = "\n".join([f"{num}. {name}" for num, name, _, _ in STUDY_LOCATIONS])
    ax_main.text(0.015, 0.98, legend_text, transform=ax_main.transAxes, fontsize=8.5,
                 va="top", ha="left",
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#888888"))
    ax_main.set_title("Study locations", fontsize=12, fontweight="bold", pad=8)

    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    build_study_area_map()
