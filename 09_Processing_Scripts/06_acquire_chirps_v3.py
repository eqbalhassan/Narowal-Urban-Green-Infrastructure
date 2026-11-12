"""Polite CHIRPS v3.0 acquisition with User-Agent, throttling, and NetCDF/COG support."""

import csv
import os
import re
import time
import requests
import rasterio
from rasterio.windows import from_bounds

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAIN_DIR = os.path.join(ROOT, "02_Raw_Data", "05_Rainfall")
BASE = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/"
HEADERS = {"User-Agent": "Narowal-UGI-GIS-Research/1.0 (academic-urban-planning-study)"}
REGION_BBOX = (74.0, 31.5, 75.5, 32.8)
NAROWAL_LON, NAROWAL_LAT = 74.873, 32.102


def polite_get(url, stream=False, timeout=60, retries=5):
    for attempt in range(retries):
        r = requests.get(url, headers=HEADERS, stream=stream, timeout=timeout)
        if r.status_code in (429, 503):
            wait = int(r.headers.get("Retry-After", 5 * (attempt + 1)))
            print(f"  HTTP {r.status_code} on {os.path.basename(url)}; sleeping {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()


def main():
    # 1. Check NetCDF options under annual/global/ and monthly/global/ first
    for sub in ["annual/global/", "monthly/global/"]:
        r = polite_get(BASE + sub, timeout=30)
        links = re.findall(r'href="([^"]+)"', r.text)
        print(sub, "links:", [l for l in links if not l.startswith("?")])
        time.sleep(1.5)

    # 2. Download annual global GeoTIFFs 2018-2025 politely (1.5s sleep between files)
    ann_url = BASE + "annual/global/tifs/"
    r = polite_get(ann_url, timeout=30)
    ann_files = sorted(set(re.findall(r'href="(chirps-v3\.0\.[^"]+\.tif)"', r.text)))
    ann_dir = os.path.join(RAIN_DIR, "annual_global_tifs")
    os.makedirs(ann_dir, exist_ok=True)
    ann_records = []
    for fn in ann_files:
        m = re.search(r"\.(\d{4})\.", fn)
        if not m or int(m.group(1)) < 2014:
            continue
        yr = int(m.group(1))
        dest = os.path.join(ann_dir, fn)
        if not os.path.exists(dest) or os.path.getsize(dest) == 0:
            print(f"Downloading annual {fn}...")
            resp = polite_get(ann_url + fn, timeout=60)
            with open(dest, "wb") as f:
                f.write(resp.content)
            time.sleep(2.0)
        with rasterio.open(dest) as src:
            row, col = src.index(NAROWAL_LON, NAROWAL_LAT)
            val = float(src.read(1)[row, col])
        ann_records.append({"year": yr, "narowal_mm": round(val, 2), "file": fn})
        print(f"  Annual {yr}: {val:.1f} mm")

    with open(os.path.join(RAIN_DIR, "chirps_v3_narowal_annual_2014_2025.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "narowal_mm", "file"])
        w.writeheader()
        w.writerows(ann_records)

    # 3. Download monthly global COGs clipped to Punjab/Narowal region for 2020-2025 (polite 1.0s sleep)
    mon_url = BASE + "monthly/global/cogs/"
    r = polite_get(mon_url, timeout=30)
    mon_files = sorted(set(re.findall(r'href="(chirps-v3\.0\.[^"]+\.tif)"', r.text)))
    mon_dir = os.path.join(RAIN_DIR, "monthly_narowal_region_tifs")
    os.makedirs(mon_dir, exist_ok=True)
    mon_records = []
    gdal_env = dict(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        GDAL_HTTP_MULTIRANGE="YES",
        CPL_VSIL_CURL_CHUNK_SIZE="1048576",
        GDAL_HTTP_USERAGENT=HEADERS["User-Agent"],
    )
    with rasterio.Env(**gdal_env):
        for fn in mon_files:
            m = re.search(r"\.(\d{4})\.(\d{2})\.", fn)
            if not m or int(m.group(1)) < 2018:
                continue
            yr, mo = int(m.group(1)), int(m.group(2))
            out_tif = os.path.join(mon_dir, fn.replace(".tif", "_punjab_subset.tif"))
            if not os.path.exists(out_tif):
                with rasterio.open(mon_url + fn) as src:
                    win = from_bounds(*REGION_BBOX, transform=src.transform).round_offsets().round_lengths()
                    arr = src.read(1, window=win)
                    prof = src.profile.copy()
                    prof.update({
                        "driver": "GTiff",
                        "height": arr.shape[0],
                        "width": arr.shape[1],
                        "transform": src.window_transform(win),
                        "compress": "DEFLATE",
                    })
                    with rasterio.open(out_tif, "w", **prof) as dst:
                        dst.write(arr, 1)
                time.sleep(0.5)
            with rasterio.open(out_tif) as src:
                row, col = src.index(NAROWAL_LON, NAROWAL_LAT)
                val = float(src.read(1)[row, col])
            mon_records.append({"year": yr, "month": mo, "narowal_mm": round(val, 2), "file": os.path.basename(out_tif)})
    print(f"Saved {len(mon_records)} monthly Narowal region GeoTIFFs (2018-2025).")
    with open(os.path.join(RAIN_DIR, "chirps_v3_narowal_monthly_2018_2025.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "month", "narowal_mm", "file"])
        w.writeheader()
        w.writerows(mon_records)


if __name__ == "__main__":
    main()
