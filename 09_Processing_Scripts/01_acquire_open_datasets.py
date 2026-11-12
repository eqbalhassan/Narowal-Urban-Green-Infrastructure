"""Phase 1 Data Acquisition Script: Urban Unit Report, Copernicus DEM, CHIRPS, GHSL, JRC GSW."""

import json
import os
import re
import urllib.parse
from datetime import datetime, timezone
import requests

PROJECT_ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAW_DIR = os.path.join(PROJECT_ROOT, "02_Raw_Data")
LOG_PATH = os.path.join(PROJECT_ROOT, "01_Project_Documentation", "acquisition_log.json")

HEADERS = {
    "User-Agent": "Narowal-UGI-GIS-Research/1.0 (https://www.openstreetmap.org)"
}


def download_file(url: str, dest_path: str, timeout: int = 120, verify_ssl: bool = True) -> dict:
    """Stream-download a file with size/status logging and atomic temp rename."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = dest_path + ".part"
    record = {
        "url": url,
        "dest_path": dest_path,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "http_status": None,
        "bytes": 0,
        "error": None,
    }
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        record["status"] = "already_exists"
        record["bytes"] = os.path.getsize(dest_path)
        return record
    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=timeout, verify=verify_ssl) as r:
            record["http_status"] = r.status_code
            r.raise_for_status()
            total = 0
            with open(tmp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
            os.replace(tmp_path, dest_path)
            record["status"] = "downloaded"
            record["bytes"] = total
    except Exception as e:
        record["error"] = str(e)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return record


def probe_url(url: str, verify_ssl: bool = True) -> dict:
    """Fetch a lightweight HTML/JSON directory listing or HEAD check."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, verify=verify_ssl)
        return {"url": url, "status": r.status_code, "text_head": r.text[:4000]}
    except Exception as e:
        return {"url": url, "status": None, "error": str(e)}


def main():
    results = []

    # 1. Urban Unit Narowal Regional Development Master Plan (Water Supply, Sewerage & Env Sector)
    urban_unit_url = (
        "https://urbanunit.gov.pk/Download/publications/Files/13/2021/"
        "Narowal%20Regional%20Development%20Master%20Plan%20-%20Water%20Supply%2C%20Sewerage%20%26%20Env%20Sector.pdf"
    )
    urban_unit_dest = os.path.join(
        RAW_DIR,
        "08_Government_Reports",
        "Narowal_Regional_Development_Master_Plan_Water_Supply_Sewerage_Env.pdf",
    )
    print("Downloading Urban Unit Master Plan PDF...")
    res = download_file(urban_unit_url, urban_unit_dest, timeout=180)
    if res["status"] == "failed" and "CERTIFICATE" in str(res.get("error", "")).upper():
        print("Retrying Urban Unit PDF without strict SSL chain verification if needed...")
        res = download_file(urban_unit_url, urban_unit_dest, timeout=180, verify_ssl=False)
    print(" ->", res["status"], res.get("bytes"), res.get("error"))
    results.append({"name": "Urban Unit Narowal Master Plan", **res})

    # 2. Copernicus DEM GLO-30 tile N32_00_E074_00 (covers 32N-33N, 74E-75E including Narowal ~32.10N, 74.87E)
    dem_url = (
        "https://copernicus-dem-30m.s3.amazonaws.com/"
        "Copernicus_DSM_COG_10_N32_00_E074_00_DEM/"
        "Copernicus_DSM_COG_10_N32_00_E074_00_DEM.tif"
    )
    dem_dest = os.path.join(RAW_DIR, "04_DEM", "Copernicus_DSM_COG_10_N32_00_E074_00_DEM.tif")
    print("Downloading Copernicus DEM GLO-30 N32_00_E074_00...")
    res = download_file(dem_url, dem_dest, timeout=180)
    print(" ->", res["status"], res.get("bytes"), res.get("error"))
    results.append({"name": "Copernicus DEM GLO-30 N32E074", **res})

    # 3. JRC Global Surface Water 2021 (tile 70E_40N covers 70E-80E, 30N-40N)
    for layer in ["occurrence", "seasonality", "extent"]:
        gsw_url = f"https://storage.googleapis.com/global-surface-water/downloads2021/{layer}/{layer}_70E_40Nv1_4_2021.tif"
        gsw_dest = os.path.join(RAW_DIR, "07_Historical_Flood_Data", f"JRC_GSW_{layer}_70E_40Nv1_4_2021.tif")
        print(f"Downloading JRC Global Surface Water ({layer})...")
        res = download_file(gsw_url, gsw_dest, timeout=180)
        print(" ->", res["status"], res.get("bytes"), res.get("error"))
        results.append({"name": f"JRC GSW {layer}", **res})

    # 4. Probe CHIRPS v3.0 and GHSL directories
    probes = {
        "chirps_v3": probe_url("https://data.chc.ucsb.edu/products/CHIRPS/v3.0/"),
        "ghsl_pop": probe_url("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/"),
        "urban_unit_pub": probe_url("https://urbanunit.gov.pk/Download/publications/Files/13/2021/", verify_ssl=False),
    }

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump({"downloads": results, "probes": probes}, f, indent=2)
    print("Saved log to:", LOG_PATH)


if __name__ == "__main__":
    main()
