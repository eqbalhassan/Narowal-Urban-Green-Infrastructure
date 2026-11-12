"""Reliable sequential Sentinel-2 L2A AOI COG downloader + ERDDAP CHIRPS daily year-by-year."""

import json
import os
import time
import pandas as pd
import requests
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
S2_DIR = os.path.join(ROOT, "02_Raw_Data", "03_Sentinel_2")
RAIN_DIR = os.path.join(ROOT, "02_Raw_Data", "05_Rainfall")
AOI_WGS84 = (74.80, 32.04, 74.95, 32.17)
HEADERS = {"User-Agent": "Narowal-UGI-GIS-Research/1.0"}

GDAL_ENV = dict(
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    GDAL_HTTP_MULTIRANGE="NO",
    CPL_VSIL_CURL_CHUNK_SIZE="1048576",
    GDAL_HTTP_TIMEOUT="120",
    GDAL_HTTP_MAX_RETRY="5",
    GDAL_HTTP_RETRY_DELAY="3",
)


def fetch_band_with_retry(scene_dir, scene_id, bname, href, retries=3):
    out_tif = os.path.join(scene_dir, f"{scene_id}_{bname}_AOI.tif")
    if os.path.exists(out_tif) and os.path.getsize(out_tif) > 0:
        return "exists", out_tif
    tmp_tif = out_tif + ".part"
    for attempt in range(1, retries + 1):
        try:
            with rasterio.Env(**GDAL_ENV):
                with rasterio.open(href) as src:
                    bounds_src = transform_bounds("EPSG:4326", src.crs, *AOI_WGS84)
                    win = from_bounds(*bounds_src, transform=src.transform).round_offsets().round_lengths()
                    data = src.read(1, window=win)
                    win_transform = src.window_transform(win)
                    profile = src.profile.copy()
                    profile.update({
                        "driver": "GTiff",
                        "height": data.shape[0],
                        "width": data.shape[1],
                        "transform": win_transform,
                        "compress": "DEFLATE",
                    })
                    with rasterio.open(tmp_tif, "w", **profile) as dst:
                        dst.write(data, 1)
            os.replace(tmp_tif, out_tif)
            return "downloaded", out_tif
        except Exception as e:
            if os.path.exists(tmp_tif):
                os.remove(tmp_tif)
            print(f"    Retry {attempt}/{retries} for {scene_id} {bname}: {e}")
            time.sleep(3 * attempt)
    return "failed", out_tif


def download_s2_scenes():
    cat_path = os.path.join(S2_DIR, "earth_search_sentinel2_catalog_narowal.json")
    with open(cat_path, encoding="utf-8") as f:
        cat = json.load(f)

    # Priority scenes: 2018_dry_historical, 2025_dry, 2025_monsoon (0% cloud), 2022_monsoon
    picks = []
    for group in ["2018_dry_historical", "2025_dry", "2025_monsoon", "2022_monsoon"]:
        items = cat.get(group, [])
        if isinstance(items, list) and items:
            best = sorted(items, key=lambda x: x.get("cloud_cover", 999))[0]
            picks.append((group, best))

    band_keys = [
        ("blue", "blue_href"),
        ("green", "green_href"),
        ("red", "red_href"),
        ("nir", "nir_href"),
        ("swir16", "swir16_href"),
        ("scl", "scl_href"),
    ]
    summary = []
    for label, item in picks:
        dt = item["datetime"][:10]
        scene_id = item["id"]
        scene_dir = os.path.join(S2_DIR, f"{label}_{dt}_{scene_id}")
        os.makedirs(scene_dir, exist_ok=True)
        with open(os.path.join(scene_dir, "scene_metadata.json"), "w", encoding="utf-8") as mf:
            json.dump(item, mf, indent=2)
        print(f"Processing S2 {label} ({dt}, cloud={item['cloud_cover']:.2f}%):")
        scene_res = {}
        for bname, href_key in band_keys:
            href = item.get(href_key)
            if href:
                st, path = fetch_band_with_retry(scene_dir, scene_id, bname, href)
                print(f"  {bname}: {st}")
                scene_res[bname] = st
        summary.append({"label": label, "id": scene_id, "date": dt, "cloud": item["cloud_cover"], "bands": scene_res})

    with open(os.path.join(S2_DIR, "sentinel2_aoi_downloads.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def download_erddap_daily_by_year():
    base_d = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalDailyP05.csv"
    frames = []
    for yr in [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]:
        # Query Jul-Sep monsoon + full year cleanly
        t0 = f"{yr}-01-01T00:00:00Z"
        t1 = f"{yr}-12-31T00:00:00Z" if yr < 2025 else "2025-12-31T00:00:00Z"
        q = f"precip[({t0}):1:({t1})][(32.025):1:(32.175)][(74.825):1:(74.925)]"
        try:
            r = requests.get(f"{base_d}?{q}", headers=HEADERS, timeout=60)
            if r.status_code == 200:
                from io import StringIO
                df = pd.read_csv(StringIO(r.text), skiprows=[1])
                frames.append(df)
                print(f"  ERDDAP daily {yr}: {len(df)} rows, unique_dates={df['time'].nunique()}")
            else:
                print(f"  ERDDAP daily {yr}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  ERDDAP daily {yr} err: {e}")
    if frames:
        all_df = pd.concat(frames, ignore_index=True)
        out_csv = os.path.join(RAIN_DIR, "chirps_v20_narowal_daily_2018_2025_clean.csv")
        all_df.to_csv(out_csv, index=False)
        print("Saved clean daily CHIRPS CSV ->", out_csv, len(all_df))


if __name__ == "__main__":
    download_erddap_daily_by_year()
    download_s2_scenes()
