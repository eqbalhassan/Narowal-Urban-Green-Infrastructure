"""Phase 1 Acquisition: Fast parallel Sentinel-2 L2A AOI COGs + GHSL R6_C25."""

import json
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

PROJECT_ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAW_DIR = os.path.join(PROJECT_ROOT, "02_Raw_Data")
POP_DIR = os.path.join(RAW_DIR, "06_Population")
S2_DIR = os.path.join(RAW_DIR, "03_Sentinel_2")

HEADERS = {"User-Agent": "Narowal-UGI-GIS-Research/1.0"}
AOI_WGS84 = (74.80, 32.04, 74.95, 32.17)

GDAL_ENV = dict(
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    GDAL_HTTP_MULTIRANGE="YES",
    GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
    CPL_VSIL_CURL_CHUNK_SIZE="4194304",
    GDAL_HTTP_TIMEOUT="60",
    GDAL_HTTP_MAX_RETRY="4",
)


def fetch_band(task):
    scene_dir, scene_id, bname, href = task
    out_tif = os.path.join(scene_dir, f"{scene_id}_{bname}_AOI.tif")
    if os.path.exists(out_tif) and os.path.getsize(out_tif) > 0:
        return (scene_id, bname, "exists", out_tif)
    tmp_tif = out_tif + ".part"
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
    return (scene_id, bname, "downloaded", out_tif)


def acquire_sentinel2_aoi_cogs():
    cat_path = os.path.join(S2_DIR, "earth_search_sentinel2_catalog_narowal.json")
    with open(cat_path, encoding="utf-8") as f:
        cat = json.load(f)

    picks = []
    for group in ["2018_dry_historical", "2022_monsoon", "2025_dry", "2025_monsoon", "2026_recent"]:
        items = cat.get(group, [])
        if isinstance(items, list) and items:
            best = sorted(items, key=lambda x: x.get("cloud_cover", 999))[0]
            picks.append((group, best))
            if group == "2025_monsoon":
                for it in items:
                    if it["datetime"].startswith("2025-08-21") and it["id"] != best["id"]:
                        picks.append(("2025_monsoon_aug21", it))

    band_keys = [
        ("blue", "blue_href"),
        ("green", "green_href"),
        ("red", "red_href"),
        ("nir", "nir_href"),
        ("swir16", "swir16_href"),
        ("scl", "scl_href"),
    ]

    tasks = []
    for label, item in picks:
        dt = item["datetime"][:10]
        scene_id = item["id"]
        scene_dir = os.path.join(S2_DIR, f"{label}_{dt}_{scene_id}")
        os.makedirs(scene_dir, exist_ok=True)
        with open(os.path.join(scene_dir, "scene_metadata.json"), "w", encoding="utf-8") as mf:
            json.dump(item, mf, indent=2)
        for bname, href_key in band_keys:
            href = item.get(href_key)
            if href:
                tasks.append((scene_dir, scene_id, bname, href))

    print(f"Submitting {len(tasks)} S2 AOI COG band tasks across 6 scenes...")
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_band, t): t for t in tasks}
        for fut in as_completed(futs):
            t = futs[fut]
            try:
                res = fut.result()
                print(" ->", res[0], res[1], res[2])
                results.append(res)
            except Exception as e:
                print(" -> ERR", t[1], t[2], e)
                results.append((t[1], t[2], "error", str(e)))

    with open(os.path.join(S2_DIR, "sentinel2_aoi_downloads.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def acquire_ghsl():
    out = []
    for epoch in ["2020", "2025"]:
        fname = f"GHS_POP_E{epoch}_GLOBE_R2023A_54009_100_V1_0_R6_C25.zip"
        url = f"https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E{epoch}_GLOBE_R2023A_54009_100/V1-0/tiles/{fname}"
        dest = os.path.join(POP_DIR, fname)
        tmp = dest + ".part"
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            out.append({"epoch": epoch, "status": "exists", "bytes": os.path.getsize(dest)})
            continue
        try:
            print(f"Downloading GHSL {epoch} R6_C25...")
            with requests.get(url, headers=HEADERS, stream=True, timeout=(15, 60)) as r:
                r.raise_for_status()
                total = 0
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
                            total += len(chunk)
            os.replace(tmp, dest)
            with zipfile.ZipFile(dest, "r") as zf:
                zf.extractall(POP_DIR)
            print(f" -> GHSL {epoch} downloaded ({total:,} bytes)")
            out.append({"epoch": epoch, "status": "downloaded", "bytes": total})
        except Exception as e:
            if os.path.exists(tmp):
                os.remove(tmp)
            print(f" -> GHSL {epoch} failed: {e}")
            out.append({"epoch": epoch, "status": "failed", "error": str(e)})
    with open(os.path.join(POP_DIR, "ghsl_download_log.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    acquire_ghsl()
    acquire_sentinel2_aoi_cogs()
