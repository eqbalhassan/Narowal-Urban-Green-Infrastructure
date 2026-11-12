"""Phase 1 Supplemental Acquisition: Microsoft Global ML Building Footprints for Narowal QuadKey 123103232."""

import gzip
import json
import os
import time
import requests
import geopandas as gpd
from shapely.geometry import shape

PROJECT_ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
OSM_DIR = os.path.join(PROJECT_ROOT, "02_Raw_Data", "01_OSM")
PROC_DIR = os.path.join(PROJECT_ROOT, "03_Processed_Data", "01_Base_Mapping")
AOI_WGS84 = (74.78, 32.02, 74.98, 32.20)
TARGET_QUADKEY = "123103232"
TILE_URL = (
    "https://minedbuildings.z5.web.core.windows.net/global-buildings/2026-02-03/"
    "global-buildings.geojsonl/RegionName=Pakistan/quadkey=123103232/"
    "part-00197-4feead82-d499-422b-94cb-c036c212127a.c000.csv.gz"
)


def download_with_resume(url: str, dest: str, max_retries: int = 8):
    tmp = dest + ".part"
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        # Remove if possibly incomplete from prior non-part run (verify gzip)
        try:
            with gzip.open(dest, "rt", encoding="utf-8") as gf:
                for _ in gf:
                    pass
            print("Verified existing complete gzip:", dest)
            return
        except Exception:
            print("Existing gzip incomplete; re-downloading safely via .part")
            os.replace(dest, tmp)

    for attempt in range(1, max_retries + 1):
        downloaded = os.path.getsize(tmp) if os.path.exists(tmp) else 0
        headers = {"Range": f"bytes={downloaded}-"} if downloaded > 0 else {}
        try:
            with requests.get(url, headers=headers, stream=True, timeout=(15, 60)) as r:
                if r.status_code == 416:
                    os.replace(tmp, dest)
                    return
                r.raise_for_status()
                mode = "ab" if (downloaded > 0 and r.status_code == 206) else "wb"
                if mode == "wb":
                    downloaded = 0
                with open(tmp, mode) as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
            # Verify gzip integrity
            with gzip.open(tmp, "rt", encoding="utf-8") as gf:
                for _ in gf:
                    pass
            os.replace(tmp, dest)
            print(f"Downloaded & verified ({downloaded:,} bytes) -> {dest}")
            return
        except Exception as e:
            print(f"Attempt {attempt}/{max_retries} failed at {downloaded:,} bytes: {e}")
            time.sleep(2 * attempt)
    raise RuntimeError("Failed to download complete MS Buildings tile after retries")


def main():
    raw_gz = os.path.join(OSM_DIR, f"ms_buildings_pakistan_qk_{TARGET_QUADKEY}.csv.gz")
    download_with_resume(TILE_URL, raw_gz)

    minx, miny, maxx, maxy = AOI_WGS84
    features = []
    total = 0
    with gzip.open(raw_gz, "rt", encoding="utf-8") as gf:
        for line in gf:
            total += 1
            feat = json.loads(line)
            coords = feat["geometry"]["coordinates"][0]
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            if max(xs) >= minx and min(xs) <= maxx and max(ys) >= miny and min(ys) <= maxy:
                geom = shape(feat["geometry"])
                props = feat.get("properties", {})
                features.append({
                    "height": props.get("height"),
                    "confidence": props.get("confidence"),
                    "geometry": geom,
                })
    print(f"Filtered {len(features):,} buildings in Narowal AOI out of {total:,} in quadkey {TARGET_QUADKEY}")
    if features:
        gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
        out_gpkg = os.path.join(PROC_DIR, "Narowal_MS_Buildings_AOI.gpkg")
        gdf.to_file(out_gpkg, layer="ms_buildings_wgs84", driver="GPKG")
        gdf.to_crs("EPSG:32643").to_file(out_gpkg, layer="ms_buildings_utm43n", driver="GPKG")
        print("Saved MS Buildings GPKG ->", out_gpkg)


if __name__ == "__main__":
    main()
