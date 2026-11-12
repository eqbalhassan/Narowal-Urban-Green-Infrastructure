"""Phase 3: Sentinel-1/2 Flood Evidence, DEM Hydrology, CHIRPS Summary, Drainage Assessment, Flood Susceptibility & Maps 04-08."""

import heapq
import json
import os
import warnings
warnings.filterwarnings("ignore")

import arcpy
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize, shapes
from rasterio.mask import mask
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from scipy import ndimage
from shapely.geometry import shape

arcpy.env.overwriteOutput = True

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAW_S1 = os.path.join(ROOT, "02_Raw_Data", "02_Sentinel_1")
RAW_S2 = os.path.join(ROOT, "02_Raw_Data", "03_Sentinel_2")
RAW_RAIN = os.path.join(ROOT, "02_Raw_Data", "05_Rainfall")
BASE_DIR = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
LULC_DIR = os.path.join(ROOT, "03_Processed_Data", "02_Land_Use_Land_Cover")
HYDRO_DIR = os.path.join(ROOT, "03_Processed_Data", "03_Hydrological_Analysis")
FLOOD_DIR = os.path.join(ROOT, "03_Processed_Data", "04_Historical_Flood_Mapping")
DRAIN_DIR = os.path.join(ROOT, "03_Processed_Data", "06_Drainage_Mapping")
STATS_DIR = os.path.join(ROOT, "08_Tables_and_Statistics")
MAPS_03 = os.path.join(ROOT, "05_Maps", "03_Flood_Assessment")
MAPS_04 = os.path.join(ROOT, "05_Maps", "04_Drainage")
GDB = os.path.join(ROOT, "04_Geodatabase", "Narowal_Green_Infrastructure.gdb")

for d in [HYDRO_DIR, FLOOD_DIR, DRAIN_DIR, MAPS_03, MAPS_04]:
    os.makedirs(d, exist_ok=True)


def add_cartographic_frame(ax, bounds, title, subtitle, sources_text, date_str="2026-11-12"):
    minx, miny, maxx, maxy = bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect("equal")
    ax.tick_params(labelsize=7, colors="#444444")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{int(y):,}"))
    ax.set_xlabel("Easting (m) — WGS 84 / UTM Zone 43N (EPSG:32643)", fontsize=8, color="#333333")
    ax.set_ylabel("Northing (m)", fontsize=8, color="#333333")
    ax.set_title(f"{title}\n{subtitle}", fontsize=12, fontweight="bold", loc="left", pad=10, color="#1A1A1A")

    nx_x, nx_y = maxx - (maxx - minx) * 0.05, miny + (maxy - miny) * 0.055
    arrow_len = (maxy - miny) * 0.055
    ax.annotate("N", xy=(nx_x, nx_y + arrow_len), xytext=(nx_x, nx_y),
                arrowprops=dict(facecolor="#1A1A1A", edgecolor="#1A1A1A", width=3, headwidth=9, headlength=9),
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#1A1A1A", zorder=20)

    span = maxx - minx
    bar_m = 1000 if span > 4500 else 500
    sb_x0 = minx + span * 0.04
    sb_y0 = miny + (maxy - miny) * 0.045
    sb_h = (maxy - miny) * 0.012
    ax.add_patch(mpatches.Rectangle((sb_x0, sb_y0), bar_m / 2, sb_h, facecolor="#1A1A1A", edgecolor="#1A1A1A", zorder=20))
    ax.add_patch(mpatches.Rectangle((sb_x0 + bar_m / 2, sb_y0), bar_m / 2, sb_h, facecolor="#FFFFFF", edgecolor="#1A1A1A", zorder=20))
    for off, lbl in [(0, "0"), (bar_m / 2, f"{bar_m // 2} m"), (bar_m, f"{bar_m:,} m")]:
        ax.text(sb_x0 + off, sb_y0 + sb_h * 1.35, lbl, fontsize=7.5, fontweight="bold", ha="center", zorder=20,
                bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none", alpha=0.75))

    footer = (
        f"CRS: WGS 84 / UTM Zone 43N (EPSG:32643)  |  Date: {date_str}  |  "
        f"Project: Narowal Urban Green Infrastructure & Flood Resilience Initiative\n"
        f"Sources: {sources_text}"
    )
    ax.figure.text(0.015, 0.01, footer, fontsize=7, color="#444444", va="bottom")


def match_to_ref(src_path, ref_prof, resamp=Resampling.bilinear, dtype=np.float32, fill_nodata=0.0):
    with rasterio.open(src_path) as src:
        with WarpedVRT(
            src,
            crs=ref_prof["crs"],
            transform=ref_prof["transform"],
            width=ref_prof["width"],
            height=ref_prof["height"],
            resampling=resamp,
            nodata=fill_nodata,
        ) as vrt:
            out = vrt.read(1).astype(dtype)
    if np.issubdtype(np.dtype(dtype), np.floating):
        out = np.where(np.isnan(out) | (out <= -9000.0), fill_nodata, out)
    return out


def save_raster(path, arr, ref_prof, dtype="float32", nodata=-9999.0):
    p = ref_prof.copy()
    p.update({"dtype": dtype, "count": 1, "compress": "DEFLATE", "nodata": nodata})
    with rasterio.open(path, "w", **p) as dst:
        dst.write(arr.astype(dtype), 1)


def process_sentinel1_and_s2_flood(ref_prof, bld_mask_10m, gsw_occ_10m):
    """Extract August 2025 SAR inundation evidence (Asc-100 & Desc-34) + S2 MNDWI cross-check."""
    print("=== Step 3.1: Sentinel-1 SAR & Sentinel-2 Flood Evidence ===")
    s1_scenes = {
        "pre_asc": os.path.join(RAW_S1, "S1RTC_20250815_pre_event_asc100"),
        "post_asc": os.path.join(RAW_S1, "S1RTC_20250827_post_event_asc100"),
        "pre_desc": os.path.join(RAW_S1, "S1RTC_20250805_pre_event_desc34"),
        "post_desc": os.path.join(RAW_S1, "S1RTC_20250823_post_event_desc34"),
    }

    def load_db_pair(folder):
        vv_p = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith("_vv_AOI.tif")][0]
        vh_p = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith("_vh_AOI.tif")][0]
        vv_lin = match_to_ref(vv_p, ref_prof, Resampling.bilinear)
        vh_lin = match_to_ref(vh_p, ref_prof, Resampling.bilinear)
        vv_db = 10.0 * np.log10(np.clip(vv_lin, 1e-6, None))
        vh_db = 10.0 * np.log10(np.clip(vh_lin, 1e-6, None))
        # 3x3 median speckle filter
        return ndimage.median_filter(vv_db, size=3), ndimage.median_filter(vh_db, size=3)

    pre_asc_vv, pre_asc_vh = load_db_pair(s1_scenes["pre_asc"])
    post_asc_vv, post_asc_vh = load_db_pair(s1_scenes["post_asc"])
    pre_desc_vv, pre_desc_vh = load_db_pair(s1_scenes["pre_desc"])
    post_desc_vv, post_desc_vh = load_db_pair(s1_scenes["post_desc"])

    # Change detection (post - pre dB)
    diff_asc_vv = post_asc_vv - pre_asc_vv
    diff_asc_vh = post_asc_vh - pre_asc_vh
    diff_desc_vv = post_desc_vv - pre_desc_vv
    diff_desc_vh = post_desc_vh - pre_desc_vh

    # Permanent water & urban building mask (do NOT classify buildings/radar shadow or permanent water as floodwater)
    perm_water = gsw_occ_10m >= 50.0
    urban_excl = bld_mask_10m == 1

    # Floodwater criteria: low post backscatter (VV < -14.5 dB or VH < -20.5 dB) AND negative change (drop >= 2.0 dB)
    flood_asc = (((post_asc_vv < -14.5) & (diff_asc_vv <= -2.0)) | ((post_asc_vh < -20.5) & (diff_asc_vh <= -2.0))) & (~perm_water) & (~urban_excl)
    flood_desc = (((post_desc_vv < -14.5) & (diff_desc_vv <= -2.0)) | ((post_desc_vh < -20.5) & (diff_desc_vh <= -2.0))) & (~perm_water) & (~urban_excl)

    # Remove tiny isolated speckle (< 3 pixels = < 300 m2)
    def clean_speckle(mask_arr):
        lbl, n = ndimage.label(mask_arr)
        if n == 0:
            return mask_arr.astype(np.uint8)
        sizes = ndimage.sum(mask_arr, lbl, range(1, n + 1))
        keep = np.isin(lbl, [i + 1 for i, sz in enumerate(sizes) if sz >= 3])
        return keep.astype(np.uint8)

    flood_asc_c = clean_speckle(flood_asc)
    flood_desc_c = clean_speckle(flood_desc)

    # Sentinel-2 optical water/wetness check (2022-08-10 & 2025-09-23 MNDWI > 0.15)
    # Note: 0.15 threshold suppresses irrigated rice-paddy moisture while capturing standing floodwater/deep waterlogging
    s2_mndwi_max = np.full((ref_prof["height"], ref_prof["width"]), -1.0, dtype=np.float32)
    for pref in ["PC_2022_monsoon", "PC_2025_monsoon"]:
        dirs = [d for d in os.listdir(RAW_S2) if d.startswith(pref)]
        if dirs:
            sdir = os.path.join(RAW_S2, dirs[0])
            grn_p = [os.path.join(sdir, f) for f in os.listdir(sdir) if f.endswith("_green_AOI.tif")][0]
            swr_p = [os.path.join(sdir, f) for f in os.listdir(sdir) if f.endswith("_swir16_AOI.tif")][0]
            g_arr = np.clip((match_to_ref(grn_p, ref_prof, Resampling.bilinear) - 1000.0) / 10000.0, 0.0001, 1.0)
            s_arr = np.clip((match_to_ref(swr_p, ref_prof, Resampling.bilinear) - 1000.0) / 10000.0, 0.0001, 1.0)
            mndwi = (g_arr - s_arr) / (g_arr + s_arr + 1e-6)
            s2_mndwi_max = np.maximum(s2_mndwi_max, mndwi)

    s2_wet = ((s2_mndwi_max > 0.15) & (~perm_water) & (~urban_excl)).astype(np.uint8)

    # Combined flood evidence score (0=None, 1=Single-date SAR or S2 wetness, 2=Multi-sensor / persistent SAR flood)
    combined = np.zeros_like(flood_asc_c, dtype=np.uint8)
    evidence_cnt = flood_asc_c + flood_desc_c + s2_wet
    combined[evidence_cnt == 1] = 1
    combined[evidence_cnt >= 2] = 2

    save_raster(os.path.join(FLOOD_DIR, "S1_20250827_Asc100_Inundation_UTM43N.tif"), flood_asc_c, ref_prof, dtype="uint8", nodata=255)
    save_raster(os.path.join(FLOOD_DIR, "S1_20250823_Desc34_Inundation_UTM43N.tif"), flood_desc_c, ref_prof, dtype="uint8", nodata=255)
    save_raster(os.path.join(FLOOD_DIR, "S1_20250827_VV_Change_dB_UTM43N.tif"), diff_asc_vv, ref_prof, dtype="float32", nodata=-9999.0)
    save_raster(os.path.join(FLOOD_DIR, "Flood_Evidence_Combined_UTM43N.tif"), combined, ref_prof, dtype="uint8", nodata=255)

    print(f"  S1 Asc-100 (2025-08-27) candidate pixels: {flood_asc_c.sum():,} ({flood_asc_c.sum()*100/1e4:.1f} ha)")
    print(f"  S1 Desc-34 (2025-08-23) candidate pixels: {flood_desc_c.sum():,} ({flood_desc_c.sum()*100/1e4:.1f} ha)")
    print(f"  S2 Monsoon wetness (MNDWI>0) pixels: {s2_wet.sum():,} ({s2_wet.sum()*100/1e4:.1f} ha)")
    return flood_asc_c, flood_desc_c, s2_wet, combined


def priority_flood_fill(dem):
    """Barnes et al. (2014) Priority-Flood depression filling (returns hydrologically conditioned DEM)."""
    rows, cols = dem.shape
    filled = dem.copy()
    visited = np.zeros((rows, cols), dtype=bool)
    pq = []

    for r in range(rows):
        for c in (0, cols - 1):
            visited[r, c] = True
            heapq.heappush(pq, (float(filled[r, c]), r, c))
    for c in range(1, cols - 1):
        for r in (0, rows - 1):
            visited[r, c] = True
            heapq.heappush(pq, (float(filled[r, c]), r, c))

    nbrs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    eps = 1e-4
    while pq:
        elev, r, c = heapq.heappop(pq)
        for dr, dc in nbrs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr, nc]:
                visited[nr, nc] = True
                if filled[nr, nc] <= elev:
                    filled[nr, nc] = elev + eps
                heapq.heappush(pq, (float(filled[nr, nc]), nr, nc))
    return filled


def run_dem_hydrology(dem_path, ref_prof):
    """Compute Slope, Hillshade, D8 Flow Direction, Flow Accumulation, TWI, HAND, and inferred drainage lines."""
    print("=== Step 3.2: Copernicus DEM Hydrological Conditioning & Terrain Analysis ===")
    with rasterio.open(dem_path) as dsrc:
        dem_raw = dsrc.read(1).astype(np.float64)
        dem_prof = dsrc.profile.copy()
        cell_size = abs(dsrc.transform.a)

    dem_fill = priority_flood_fill(dem_raw)
    sink_depth = dem_fill - dem_raw

    # Slope (degrees) & Hillshade
    dy, dx = np.gradient(dem_fill, cell_size, cell_size)
    slope_rad = np.arctan(np.hypot(dx, dy))
    slope_deg = np.degrees(slope_rad)
    aspect = np.arctan2(-dy, dx)
    az, alt = np.radians(315.0), np.radians(45.0)
    hillshade = 255.0 * (np.sin(alt) * np.cos(slope_rad) + np.cos(alt) * np.sin(slope_rad) * np.cos(az - aspect))
    hillshade = np.clip(hillshade, 0, 255)

    # D8 Flow Direction & Accumulation directly on epsilon-graded dem_fill (guarantees connected flat routing)
    rows, cols = dem_fill.shape
    dem_route = dem_fill
    nbrs = [(-1, -1, np.sqrt(2)), (-1, 0, 1.0), (-1, 1, np.sqrt(2)),
            (0, -1, 1.0), (0, 1, 1.0),
            (1, -1, np.sqrt(2)), (1, 0, 1.0), (1, 1, np.sqrt(2))]
    down_r = np.full((rows, cols), -1, dtype=np.int32)
    down_c = np.full((rows, cols), -1, dtype=np.int32)
    fdir_code = np.zeros((rows, cols), dtype=np.uint8)

    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            e0 = dem_route[r, c]
            best_s = 0.0
            br, bc, bcode = -1, -1, 0
            for idx_n, (dr, dc, dist) in enumerate(nbrs, 1):
                s = (e0 - dem_route[r + dr, c + dc]) / (dist * cell_size)
                if s > best_s:
                    best_s = s
                    br, bc, bcode = r + dr, c + dc, idx_n
            down_r[r, c] = br
            down_c[r, c] = bc
            fdir_code[r, c] = bcode

    # Topological sort order (highest elevation first) for fast O(N) D8 accumulation
    order = np.argsort(dem_route.ravel())[::-1]
    facc = np.ones((rows, cols), dtype=np.float64)
    for flat_idx in order:
        r, c = divmod(int(flat_idx), cols)
        nr, nc = int(down_r[r, c]), int(down_c[r, c])
        if nr >= 0:
            facc[nr, nc] += facc[r, c]

    # Topographic Wetness Index (TWI)
    sca = (facc * cell_size)
    tan_b = np.maximum(np.tan(slope_rad), 0.005)
    twi = np.log(sca / tan_b)

    # Height Above Nearest Drainage (HAND / relative elevation above cells with facc >= 120)
    stream_mask = facc >= 120
    # Propagate stream elevation upward via BFS/distance-nearest stream pixel
    _, indices = ndimage.distance_transform_edt(~stream_mask, return_indices=True)
    nearest_stream_elev = dem_fill[indices[0], indices[1]]
    hand = np.maximum(dem_fill - nearest_stream_elev, 0.0)

    # Save 30m hydrological products
    for fn, arr, dt in [
        ("Narowal_DEM_Filled_30m_UTM43N.tif", dem_fill, "float32"),
        ("Narowal_DEM_SinkDepth_30m_UTM43N.tif", sink_depth, "float32"),
        ("Narowal_Slope_Deg_30m_UTM43N.tif", slope_deg, "float32"),
        ("Narowal_Hillshade_30m_UTM43N.tif", hillshade, "float32"),
        ("Narowal_FlowAccumulation_30m_UTM43N.tif", facc, "float32"),
        ("Narowal_TWI_30m_UTM43N.tif", twi, "float32"),
        ("Narowal_HAND_RelElev_30m_UTM43N.tif", hand, "float32"),
    ]:
        save_raster(os.path.join(HYDRO_DIR, fn), arr, dem_prof, dtype=dt)

    # Extract inferred drainage convergence lines (facc >= 120 cells = ~10.8 ha catchment)
    stream_bin = (facc >= 120).astype(np.uint8)
    stream_polys = [shape(g) for g, v in shapes(stream_bin, mask=(stream_bin == 1), transform=dem_prof["transform"]) if v == 1]
    # Extract connected cell links directly along D8 down_r/down_c
    from shapely.geometry import LineString
    stream_lines = []
    rs, cs = np.where(stream_bin)
    tr = dem_prof["transform"]
    for r, c in zip(rs, cs):
        nr, nc = int(down_r[r, c]), int(down_c[r, c])
        if nr >= 0 and stream_bin[nr, nc]:
            x0, y0 = tr * (c + 0.5, r + 0.5)
            x1, y1 = tr * (nc + 0.5, nr + 0.5)
            stream_lines.append({"facc_cells": float(facc[r, c]), "geometry": LineString([(x0, y0), (x1, y1)])})
    inferred_gdf = gpd.GeoDataFrame(stream_lines, crs="EPSG:32643")
    inferred_gdf["source_note"] = "DEM-inferred drainage convergence (Copernicus GLO-30 >=120 cells) - NOT observed municipal drain"
    inferred_gdf.to_file(os.path.join(DRAIN_DIR, "Narowal_Inferred_Drainage_Convergence_UTM43N.gpkg"), layer="dem_inferred_drainage", driver="GPKG")

    # Resample key hydro layers to 10 m ref_prof for multi-indicator overlay
    facc_10m = np.maximum(match_to_ref(os.path.join(HYDRO_DIR, "Narowal_FlowAccumulation_30m_UTM43N.tif"), ref_prof, Resampling.bilinear, fill_nodata=1.0), 1.0)
    hand_10m = np.maximum(match_to_ref(os.path.join(HYDRO_DIR, "Narowal_HAND_RelElev_30m_UTM43N.tif"), ref_prof, Resampling.bilinear, fill_nodata=2.0), 0.0)
    twi_10m = np.maximum(match_to_ref(os.path.join(HYDRO_DIR, "Narowal_TWI_30m_UTM43N.tif"), ref_prof, Resampling.bilinear, fill_nodata=7.5), 4.0)
    sink_10m = np.maximum(match_to_ref(os.path.join(HYDRO_DIR, "Narowal_DEM_SinkDepth_30m_UTM43N.tif"), ref_prof, Resampling.bilinear, fill_nodata=0.0), 0.0)
    return dem_fill, hillshade, slope_deg, facc, hand, inferred_gdf, facc_10m, hand_10m, twi_10m, sink_10m


def analyze_chirps_rainfall():
    """Summarize CHIRPS 1981-2025 monthly climatology & annual/monsoon rainfall for Narowal."""
    print("=== Step 3.3: CHIRPS Rainfall Summary ===")
    mon_csv = os.path.join(RAW_RAIN, "chirps_v20_narowal_monthly_1981_present.csv")
    df = pd.read_csv(mon_csv, skiprows=[1])
    df["time"] = pd.to_datetime(df["time"])
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    clat = min(df["latitude"].unique(), key=lambda x: abs(x - 32.102))
    clon = min(df["longitude"].unique(), key=lambda x: abs(x - 74.873))
    sub = df[(df["latitude"] == clat) & (df["longitude"] == clon)].copy()

    # Complete years 1981-2024
    full_yrs = sub[sub["year"] <= 2024]
    ann = full_yrs.groupby("year")["precip"].sum().reset_index(name="annual_mm")
    monsoon = full_yrs[full_yrs["month"].isin([7, 8, 9])].groupby("year")["precip"].sum().reset_index(name="jas_monsoon_mm")
    ann_df = ann.merge(monsoon, on="year")
    ann_df["monsoon_share_pct"] = (100.0 * ann_df["jas_monsoon_mm"] / ann_df["annual_mm"]).round(1)
    ann_df.to_csv(os.path.join(STATS_DIR, "chirps_narowal_annual_1981_2024.csv"), index=False)

    clim = full_yrs.groupby("month")["precip"].mean().round(1).reset_index(name="mean_1981_2024_mm")
    clim.to_csv(os.path.join(STATS_DIR, "chirps_narowal_monthly_climatology.csv"), index=False)

    summary = {
        "grid_cell_lat": float(clat),
        "grid_cell_lon": float(clon),
        "spatial_resolution_deg": 0.05,
        "mean_annual_1981_2024_mm": round(float(ann_df["annual_mm"].mean()), 1),
        "mean_jas_monsoon_mm": round(float(ann_df["jas_monsoon_mm"].mean()), 1),
        "wettest_years": ann_df.sort_values("annual_mm", ascending=False).head(5).to_dict(orient="records"),
        "wettest_months_since_2014": sub[sub["year"] >= 2014].sort_values("precip", ascending=False).head(5)[["time", "precip"]].assign(time=lambda x: x["time"].dt.strftime("%Y-%m")).to_dict(orient="records"),
        "limitation": "0.05 deg (~5.5 km) grid; cannot resolve street-to-street rainfall differences.",
    }
    with open(os.path.join(STATS_DIR, "chirps_rainfall_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  CHIRPS cell ({clat:.3f}N, {clon:.3f}E): Mean annual = {summary['mean_annual_1981_2024_mm']} mm; Mean JAS monsoon = {summary['mean_jas_monsoon_mm']} mm")
    return summary


def build_drainage_and_susceptibility(ref_prof, mc, bu, parks, roads, waterways, waterbodies, uu_assets, ms_bld, combined_flood, facc_10m, hand_10m, twi_10m, sink_10m, inferred_gdf):
    """Map drainage deficiency, run renormalized 5-indicator Flood Susceptibility + sensitivity analysis, and produce Maps 04-08."""
    print("=== Step 3.4: Drainage Assessment & Flood Susceptibility Model ===")
    h, w = ref_prof["height"], ref_prof["width"]
    tr = ref_prof["transform"]

    # 1. Observed drainage / waterways vs Urban Unit sewerage corridors
    # Compute distance to mapped OSM waterways + disposal stations (m)
    obs_drain_geoms = list(waterways.geometry) + list(waterbodies.geometry)
    obs_mask = rasterize([(g.buffer(15.0), 1) for g in obs_drain_geoms], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    dist_obs_drain_m = ndimage.distance_transform_edt(obs_mask == 0) * 10.0

    # Distance to DEM-inferred convergence lines
    inf_mask = rasterize([(g.buffer(15.0), 1) for g in inferred_gdf.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    dist_inf_m = ndimage.distance_transform_edt(inf_mask == 0) * 10.0

    # Imperviousness indicator: Sentinel-2 NDBI + MS Building density (30m smoothing)
    with rasterio.open(os.path.join(LULC_DIR, "S2_20250516_NDBI.tif")) as s:
        ndbi = s.read(1)
    bld_r = rasterize([(g, 1) for g in ms_bld.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.float32)
    bld_dens = ndimage.uniform_filter(bld_r, size=5)  # 50m x 50m local building density [0..1]

    # Continuous standardized [1.0 .. 5.0] sub-indicators for smooth percentile classification:
    # A. Historical inundation (combined SAR + S2 wetness + smoothed focal proximity)
    ind_inund_raw = np.ones((h, w), dtype=np.float32)
    ind_inund_raw[combined_flood == 1] = 3.5
    ind_inund_raw[combined_flood >= 2] = 5.0
    ind_inund = np.maximum(ind_inund_raw, ndimage.uniform_filter(ind_inund_raw, size=5))

    # B. Flow accumulation + TWI (continuous log10(facc) + TWI adjustment)
    log_facc = np.log10(np.maximum(facc_10m, 1.0))
    ind_facc = np.clip(1.0 + 3.5 * np.clip((log_facc - 0.1) / 2.6, 0.0, 1.0) + 0.5 * np.clip((twi_10m - 7.0) / 5.0, 0.0, 1.0), 1.0, 5.0)

    # C. Relative elevation (HAND in meters + depression sink depth)
    ind_hand = np.clip(1.0 + 3.5 * np.clip((4.5 - hand_10m) / 4.5, 0.0, 1.0) + 0.5 * np.clip(sink_10m / 0.8, 0.0, 1.0), 1.0, 5.0)

    # D. Imperviousness (building density + NDBI)
    imp_score = 0.65 * bld_dens + 0.35 * np.clip((ndbi + 0.25) / 0.5, 0.0, 1.0)
    ind_imp = np.clip(1.0 + 4.0 * np.clip((imp_score - 0.05) / 0.65, 0.0, 1.0), 1.0, 5.0)

    # E. Drainage deficiency (distance from observed waterways + proximity to DEM convergence lines)
    ind_drain = np.clip(1.0 + 2.6 * np.clip(dist_obs_drain_m / 1800.0, 0.0, 1.0) + 1.4 * np.clip(1.0 - dist_inf_m / 300.0, 0.0, 1.0), 1.0, 5.0)

    # Primary renormalized weights (Indicator F 15% unavailable -> renormalized over 85% = 100%)
    w_primary = {
        "inund": 25.0 / 85.0,   # 29.41%
        "facc": 20.0 / 85.0,    # 23.53%
        "hand": 15.0 / 85.0,    # 17.65%
        "imp": 15.0 / 85.0,     # 17.65%
        "drain": 10.0 / 85.0,   # 11.76%
    }
    sus_cont = (
        w_primary["inund"] * ind_inund
        + w_primary["facc"] * ind_facc
        + w_primary["hand"] * ind_hand
        + w_primary["imp"] * ind_imp
        + w_primary["drain"] * ind_drain
    )
    # Classify continuous [1..5] score into 5 susceptibility classes using transparent quantile/break thresholds
    mc_poly = mc.geometry.union_all()
    mc_mask = rasterize([(mc_poly, 1)], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    mc_vals = sus_cont[mc_mask == 1]
    breaks = [np.percentile(mc_vals, p) for p in [20, 45, 70, 88]]

    def classify_5(arr, brks):
        cls = np.ones_like(arr, dtype=np.uint8)
        cls[arr >= brks[0]] = 2
        cls[arr >= brks[1]] = 3
        cls[arr >= brks[2]] = 4
        cls[arr >= brks[3]] = 5
        return cls

    sus_cls = classify_5(sus_cont, breaks)

    # Sensitivity Analysis (3 alternative schemes: Equal, Terrain-Heavy, Impervious-Urban-Pluvial)
    schemes = {
        "Primary_Renormalized": w_primary,
        "Equal_Weights": {"inund": 0.20, "facc": 0.20, "hand": 0.20, "imp": 0.20, "drain": 0.20},
        "Terrain_Dominant": {"inund": 0.15, "facc": 0.30, "hand": 0.30, "imp": 0.15, "drain": 0.10},
        "Urban_Pluvial_Dominant": {"inund": 0.20, "facc": 0.20, "hand": 0.10, "imp": 0.35, "drain": 0.15},
    }
    sens_rows = []
    for sname, sw in schemes.items():
        sc = sw["inund"] * ind_inund + sw["facc"] * ind_facc + sw["hand"] * ind_hand + sw["imp"] * ind_imp + sw["drain"] * ind_drain
        sc_cls = classify_5(sc, [np.percentile(sc[mc_mask == 1], p) for p in [20, 45, 70, 88]])
        corr = float(np.corrcoef(sus_cont[mc_mask == 1], sc[mc_mask == 1])[0, 1])
        exact_agree = float(np.mean(sus_cls[mc_mask == 1] == sc_cls[mc_mask == 1]) * 100.0)
        high_vh_km2 = float(((sc_cls >= 4) & (mc_mask == 1)).sum() * 100.0 / 1e6)
        sens_rows.append({
            "scheme": sname,
            "pearson_r_vs_primary": round(corr, 4),
            "exact_class_agreement_pct": round(exact_agree, 2),
            "high_plus_veryhigh_km2_mc": round(high_vh_km2, 3),
        })
    pd.DataFrame(sens_rows).to_csv(os.path.join(STATS_DIR, "phase3_flood_sensitivity_analysis.csv"), index=False)

    # Save susceptibility rasters
    sus_cont_tif = os.path.join(FLOOD_DIR, "Narowal_Flood_Susceptibility_Score_10m_UTM43N.tif")
    sus_cls_tif = os.path.join(FLOOD_DIR, "Narowal_Flood_Susceptibility_5Class_UTM43N.tif")
    drain_def_tif = os.path.join(DRAIN_DIR, "Narowal_Drainage_Deficiency_Score_10m_UTM43N.tif")
    save_raster(sus_cont_tif, sus_cont, ref_prof, dtype="float32")
    save_raster(sus_cls_tif, sus_cls, ref_prof, dtype="uint8", nodata=0)
    save_raster(drain_def_tif, ind_drain, ref_prof, dtype="float32")

    # Summary stats inside MC boundary
    cls_names = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
    mc_sus = sus_cls[mc_mask == 1]
    sus_summary = []
    for k, cname in cls_names.items():
        cnt = int((mc_sus == k).sum())
        sus_summary.append({"class_id": k, "class_name": cname, "area_km2": round(cnt * 100.0 / 1e6, 3), "pct_mc": round(100.0 * cnt / len(mc_sus), 2)})
    pd.DataFrame(sus_summary).to_csv(os.path.join(STATS_DIR, "phase3_flood_susceptibility_areas.csv"), index=False)
    print("  Flood Susceptibility MC Breakdown:", sus_summary)

    # Extract top Drainage Investigation Priority Zones (High/Very High convergence + distant from mapped drains)
    prio_mask = ((ind_drain >= 3.5) & (sus_cls >= 4) & (mc_mask == 1)).astype(np.uint8)
    prio_mask = ndimage.binary_opening(prio_mask, iterations=1).astype(np.uint8)
    prio_polys = [shape(g) for g, v in shapes(prio_mask, mask=(prio_mask == 1), transform=tr) if v == 1]
    prio_polys = [p for p in prio_polys if p.area >= 15000]  # >= 1.5 ha hotspots
    prio_gdf = gpd.GeoDataFrame(
        [{"priority_id": f"DRN_PRIO_{i:02d}", "area_ha": round(p.area / 1e4, 2), "investigation_need": "Field Drain Survey & Invert Level Check", "geometry": p} for i, p in enumerate(sorted(prio_polys, key=lambda x: x.area, reverse=True)[:12], 1)],
        crs="EPSG:32643",
    )
    prio_gdf.to_file(os.path.join(DRAIN_DIR, "Narowal_Drainage_Investigation_Priorities_UTM43N.gpkg"), layer="drainage_priority_zones", driver="GPKG")

    # Load Phase 3 layers into FileGDB
    for rpath, rname in [
        (sus_cont_tif, "p3_flood_susceptibility_score"),
        (sus_cls_tif, "p3_flood_susceptibility_5class"),
        (os.path.join(FLOOD_DIR, "Flood_Evidence_Combined_UTM43N.tif"), "p3_flood_evidence_combined"),
        (os.path.join(HYDRO_DIR, "Narowal_FlowAccumulation_30m_UTM43N.tif"), "p3_dem_flow_accumulation"),
        (os.path.join(HYDRO_DIR, "Narowal_HAND_RelElev_30m_UTM43N.tif"), "p3_dem_hand_rel_elev"),
    ]:
        arcpy.management.CopyRaster(rpath, os.path.join(GDB, rname))

    for gpkg_p, lyr, gdb_fc in [
        (os.path.join(DRAIN_DIR, "Narowal_Inferred_Drainage_Convergence_UTM43N.gpkg"), "dem_inferred_drainage", "p3_dem_inferred_drainage"),
        (os.path.join(DRAIN_DIR, "Narowal_Drainage_Investigation_Priorities_UTM43N.gpkg"), "drainage_priority_zones", "p3_drainage_investigation_priorities"),
    ]:
        if len(gpd.read_file(gpkg_p, layer=lyr)) > 0:
            tmp_shp = os.path.join(DRAIN_DIR, f"_tmp_{gdb_fc}.shp")
            gpd.read_file(gpkg_p, layer=lyr).to_file(tmp_shp)
            arcpy.conversion.ExportFeatures(tmp_shp, os.path.join(GDB, gdb_fc))
            for ext_rm in [".shp", ".dbf", ".shx", ".prj", ".cpg"]:
                p_rm = tmp_shp.replace(".shp", ext_rm)
                if os.path.exists(p_rm):
                    os.remove(p_rm)

    # Produce MAPS 04, 05, 06, 07, 08
    produce_maps_04_to_08(ref_prof, mc, bu, roads, parks, waterways, waterbodies, uu_assets, ms_bld, combined_flood, sus_cls, inferred_gdf, prio_gdf)


def produce_maps_04_to_08(ref_prof, mc, bu, roads, parks, waterways, waterbodies, uu_assets, ms_bld, combined_flood, sus_cls, inferred_gdf, prio_gdf):
    print("=== Step 3.5: Producing MAP 04 through MAP 08 ===")
    mc_b = mc.total_bounds
    pad_mc = (mc_b[0] - 500, mc_b[1] - 500, mc_b[2] + 500, mc_b[3] + 500)
    ext_10m = [ref_prof["transform"].c, ref_prof["transform"].c + ref_prof["width"] * ref_prof["transform"].a,
               ref_prof["transform"].f + ref_prof["height"] * ref_prof["transform"].e, ref_prof["transform"].f]

    # MAP 04: Historical Flood Evidence
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    ms_bld.plot(ax=ax, facecolor="#E0E0E0", edgecolor="none", alpha=0.65, zorder=1)
    roads.plot(ax=ax, color="#888888", linewidth=0.45, alpha=0.7, zorder=2)
    cmap_fe = ListedColormap(["none", "#42A5F5", "#0D47A1"])
    norm_fe = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap_fe.N)
    ax.imshow(np.ma.masked_equal(combined_flood, 0), extent=ext_10m, cmap=cmap_fe, norm=norm_fe, alpha=0.85, interpolation="nearest", zorder=4)
    waterways.plot(ax=ax, color="#0288D1", linewidth=1.4, zorder=5)
    waterbodies.plot(ax=ax, color="#0288D1", zorder=5)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=7)
    handles4 = [
        mpatches.Patch(facecolor="#42A5F5", label="Single-Sensor Candidate Wetness (S1 Aug 2025 or S2 MNDWI)"),
        mpatches.Patch(facecolor="#0D47A1", label="Multi-Sensor Persistent Flood / Waterlogging Evidence"),
        mlines.Line2D([], [], color="#0288D1", linewidth=1.6, label="Mapped Waterways / Waterbodies"),
        mpatches.Patch(facecolor="#E0E0E0", label="Urban Building Footprints (Masked from SAR False Positives)"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles4, loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.92, title="Legend", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 04: Historical Monsoon Flood & Wetness Evidence (2022–2025)",
        "Sentinel-1 RTC (Aug 2025 Asc-100 & Desc-34 Change Detection) & Sentinel-2 MNDWI Cross-Check",
        "Copernicus Sentinel-1 RTC (2025-08-05/15/23/27), Sentinel-2 L2A (2022-08-10, 2025-09-23), JRC GSW v1.4"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_03, f"MAP_04_Historical_Flood_Evidence.{ext_f}"), dpi=300)
    plt.close(fig)

    # MAP 05: Terrain and Surface Drainage Analysis
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    with rasterio.open(os.path.join(HYDRO_DIR, "Narowal_HAND_RelElev_30m_UTM43N.tif")) as hsrc:
        hand_arr = hsrc.read(1)
        h_ext = [hsrc.bounds.left, hsrc.bounds.right, hsrc.bounds.bottom, hsrc.bounds.top]
    with rasterio.open(os.path.join(HYDRO_DIR, "Narowal_Hillshade_30m_UTM43N.tif")) as hs_src:
        hs_arr = hs_src.read(1)
    ax.imshow(hs_arr, extent=h_ext, cmap="gray", alpha=0.35, zorder=1)
    im5 = ax.imshow(hand_arr, extent=h_ext, cmap="YlGnBu_r", vmin=0, vmax=6.0, alpha=0.72, zorder=2)
    cbar5 = fig.colorbar(im5, ax=ax, shrink=0.55, pad=0.02)
    cbar5.set_label("Relative Elevation / HAND (m above nearest drainage)", fontsize=8)
    inferred_gdf.plot(ax=ax, color="#0D47A1", linewidth=1.1, alpha=0.85, zorder=4)
    roads.plot(ax=ax, color="#444444", linewidth=0.35, alpha=0.45, zorder=3)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=7)
    ax.text(0.02, 0.97, "Screening Note: Copernicus GLO-30 (30 m DSM)\nCannot resolve street curbs or engineering depths.",
            transform=ax.transAxes, va="top", fontsize=7.8,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#666666", alpha=0.92), zorder=12)
    handles5 = [
        mlines.Line2D([], [], color="#0D47A1", linewidth=1.4, label="DEM-Inferred Surface Drainage Convergence (>=120 cells)"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles5, loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.92, title="Legend", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 05: Terrain & Surface Drainage Convergence (Preliminary Screening)",
        "Relative Elevation (HAND) & D8 Flow Convergence from Conditioned Copernicus DEM GLO-30",
        "ESA Copernicus DEM GLO-30 (30 m DSM), Priority-Flood Hydrological Conditioning"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_03, f"MAP_05_Terrain_Surface_Drainage.{ext_f}"), dpi=300)
    plt.close(fig)

    # MAP 06: Preliminary Urban Flood Susceptibility (5 classes)
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    cmap_sus = ListedColormap(["#2E7D32", "#A5D6A7", "#FFF176", "#EF6C00", "#8E001C"])
    norm_sus = BoundaryNorm([0.5, 1.5, 2.5, 3.5, 4.5, 5.5], cmap_sus.N)
    ax.imshow(sus_cls, extent=ext_10m, cmap=cmap_sus, norm=norm_sus, alpha=0.78, interpolation="nearest", zorder=1)
    ms_bld.plot(ax=ax, facecolor="#424242", edgecolor="none", alpha=0.35, zorder=2)
    roads.plot(ax=ax, color="#333333", linewidth=0.45, alpha=0.5, zorder=3)
    inferred_gdf.plot(ax=ax, color="#1565C0", linewidth=0.9, alpha=0.75, zorder=4)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=6)
    handles6 = [
        mpatches.Patch(facecolor="#2E7D32", label="1 - Very Low Susceptibility"),
        mpatches.Patch(facecolor="#A5D6A7", label="2 - Low Susceptibility"),
        mpatches.Patch(facecolor="#FFF176", label="3 - Moderate Susceptibility"),
        mpatches.Patch(facecolor="#EF6C00", label="4 - High Susceptibility"),
        mpatches.Patch(facecolor="#8E001C", label="5 - Very High Susceptibility"),
        mlines.Line2D([], [], color="#1565C0", linewidth=1.2, label="DEM-Inferred Flow Convergence"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles6, loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.93, title="Susceptibility Class", title_fontsize=8.5)
    ax.text(0.02, 0.97, "Provisional Multi-Indicator Screening Model\nWeights renormalized over 5 available indicators\n(Municipal waterlogging log pending Rescue 1122/MC).",
            transform=ax.transAxes, va="top", fontsize=7.6,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#8E001C", alpha=0.93), zorder=12)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 06: Preliminary Urban Flood & Waterlogging Susceptibility",
        "Renormalized Weighted Overlay (Inundation 29.4%, Flow Acc 23.5%, HAND 17.6%, Imperviousness 17.6%, Drainage 11.8%)",
        "Sentinel-1 RTC, Sentinel-2 L2A, Copernicus DEM GLO-30, MS Buildings, OSM Waterways (Provisional Screening)"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_03, f"MAP_06_Preliminary_Flood_Susceptibility.{ext_f}"), dpi=300)
    plt.close(fig)

    # MAP 07: Existing Drainage and Sewerage Infrastructure (Observed vs Inferred clearly separated)
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    ms_bld.plot(ax=ax, facecolor="#E0E0E0", edgecolor="none", alpha=0.75, zorder=1)
    roads.plot(ax=ax, color="#9E9E9E", linewidth=0.5, alpha=0.7, zorder=2)
    inferred_gdf.plot(ax=ax, color="#64B5F6", linewidth=1.1, linestyle="--", alpha=0.85, zorder=3)
    waterways.plot(ax=ax, color="#0D47A1", linewidth=2.0, zorder=4)
    waterbodies.plot(ax=ax, color="#1565C0", alpha=0.85, zorder=4)
    disp = uu_assets[uu_assets["asset_id"].str.contains("DISP|WWTP")]
    disp.plot(ax=ax, color="#6A1B9A", marker="s", markersize=70, edgecolor="white", linewidth=0.8, zorder=7)
    for _, r in disp.iterrows():
        ax.annotate(r["name"].replace("Proposed Wastewater Treatment Plant (Ghausia Road Ext)", "Proposed WWTP (Ghausia Rd Ext)"),
                    (r.geometry.x, r.geometry.y), xytext=(6, 6), textcoords="offset points", fontsize=7.5, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#6A1B9A", alpha=0.9), zorder=12)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=8)
    handles7 = [
        mlines.Line2D([], [], color="#0D47A1", linewidth=2.2, label="Observed Natural Waterways (OSM)"),
        mlines.Line2D([], [], color="#64B5F6", linewidth=1.4, linestyle="--", label="Inferred Natural Drainage Convergence (DEM - Unverified)"),
        mlines.Line2D([], [], color="#6A1B9A", marker="s", linestyle="None", markersize=7, label="Sewerage Disposal Stations & Proposed WWTP (Urban Unit 2021)"),
        mpatches.Patch(facecolor="#E0E0E0", label="Urban Building Footprints"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles7, loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.93, title="Legend", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 07: Existing Drainage & Sewerage Infrastructure (Observed vs. Inferred)",
        "Distinguishing Mapped Waterways & Disposal Stations from DEM-Inferred Surface Flow Pathways",
        "Urban Unit Master Plan (2021), OSM Waterways (2026), Copernicus DEM GLO-30 (Note: Detailed municipal pipe GIS missing)"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_04, f"MAP_07_Existing_Drainage_Sewerage.{ext_f}"), dpi=300)
    plt.close(fig)

    # MAP 08: Drainage Investigation Priority Areas
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    ms_bld.plot(ax=ax, facecolor="#E0E0E0", edgecolor="none", alpha=0.75, zorder=1)
    roads.plot(ax=ax, color="#888888", linewidth=0.5, alpha=0.65, zorder=2)
    inferred_gdf.plot(ax=ax, color="#1976D2", linewidth=1.0, alpha=0.8, zorder=3)
    waterways.plot(ax=ax, color="#0D47A1", linewidth=1.8, zorder=4)
    if len(prio_gdf) > 0:
        prio_gdf.plot(ax=ax, facecolor="#8E001C", edgecolor="#4A000E", linewidth=1.4, alpha=0.55, zorder=5)
        for _, r in prio_gdf.head(6).iterrows():
            c = r.geometry.centroid
            ax.annotate(r["priority_id"], (c.x, c.y), fontsize=7, fontweight="bold", color="#4A000E",
                        bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFEBEE", edgecolor="#8E001C", alpha=0.9), zorder=11)
    disp.plot(ax=ax, color="#6A1B9A", marker="s", markersize=60, edgecolor="white", zorder=7)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=8)
    handles8 = [
        mpatches.Patch(facecolor="#8E001C", alpha=0.55, edgecolor="#4A000E", label="Drainage Investigation Priority Hotspots (High Convergence + No Mapped Drain)"),
        mlines.Line2D([], [], color="#0D47A1", linewidth=1.8, label="Observed Natural Waterways"),
        mlines.Line2D([], [], color="#1976D2", linewidth=1.1, label="DEM-Inferred Drainage Convergence"),
        mlines.Line2D([], [], color="#6A1B9A", marker="s", linestyle="None", markersize=7, label="Disposal Stations / Proposed WWTP"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles8, loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.93, title="Legend", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 08: Drainage Investigation Priority Areas",
        "High-Susceptibility Convergence Zones Distant from Mapped Drainage Channels Requiring Field Survey",
        "Derived from Flood Susceptibility, DEM Flow Convergence, OSM Waterways & Urban Unit Assets (2021)"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_04, f"MAP_08_Drainage_Investigation_Priorities.{ext_f}"), dpi=300)
    plt.close(fig)
    print("  Saved MAP 04, MAP 05, MAP 06, MAP 07, MAP 08 (PNG + PDF)")


def main():
    # Use Sentinel-2 LULC 10m grid as common spatial reference for Phase 3 overlay
    lulc_path = os.path.join(LULC_DIR, "Narowal_S2_LULC_6Class_UTM43N.tif")
    with rasterio.open(lulc_path) as ref:
        ref_prof = ref.profile.copy()
        h, w = ref.height, ref.width
        tr = ref.transform

    mc = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="mc_boundary_preliminary")
    bu = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="builtup_urban_boundary_preliminary")
    roads = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_roads_raw")
    parks = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_parks_green_poly_raw")
    waterways = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_waterways_raw")
    waterbodies = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_waterbodies_raw")
    ms_bld = gpd.read_file(os.path.join(BASE_DIR, "Narowal_MS_Buildings_AOI.gpkg"), layer="ms_buildings_utm43n")
    ms_bld["geometry"] = ms_bld.geometry.make_valid()
    uu_assets = gpd.read_file(os.path.join(BASE_DIR, "Narowal_UrbanUnit_2021_Assets_UTM43N.gpkg"), layer="uu2021_key_assets_preliminary")

    bld_mask_10m = rasterize([(g.buffer(3.0), 1) for g in ms_bld.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    gsw_occ_10m = match_to_ref(os.path.join(BASE_DIR, "JRC_GSW_occurrence_Narowal_AOI_UTM43N.tif"), ref_prof, Resampling.nearest)

    _, _, _, combined_flood = process_sentinel1_and_s2_flood(ref_prof, bld_mask_10m, gsw_occ_10m)
    dem_path = os.path.join(BASE_DIR, "Copernicus_DEM_GLO30_Narowal_AOI_UTM43N.tif")
    _, _, _, _, _, inferred_gdf, facc_10m, hand_10m, twi_10m, sink_10m = run_dem_hydrology(dem_path, ref_prof)
    analyze_chirps_rainfall()
    build_drainage_and_susceptibility(ref_prof, mc, bu, parks, roads, waterways, waterbodies, uu_assets, ms_bld, combined_flood, facc_10m, hand_10m, twi_10m, sink_10m, inferred_gdf)


if __name__ == "__main__":
    main()
