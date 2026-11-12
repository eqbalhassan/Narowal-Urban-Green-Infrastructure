"""Acquire CHIRPS precipitation datasets for Narowal via NOAA ERDDAP (NetCDF + CSV) and UCSB CHIRPS v3.0."""

import os
import time
import pandas as pd
import requests

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAIN_DIR = os.path.join(ROOT, "02_Raw_Data", "05_Rainfall")
os.makedirs(RAIN_DIR, exist_ok=True)
HEADERS = {"User-Agent": "Narowal-UGI-GIS-Research/1.0"}


def fetch_erddap():
    # 1. CHIRPS Daily 0.05 deg (2014-01-01 to latest) over Narowal District/City bbox (31.95N-32.25N, 74.70E-75.05E)
    daily_csv = os.path.join(RAIN_DIR, "chirps_v20_narowal_daily_2014_present.csv")
    daily_nc = os.path.join(RAIN_DIR, "chirps_v20_narowal_daily_2014_present.nc")
    base_d = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalDailyP05"
    q_d = "precip[(2014-01-01T00:00:00Z):1:(last)][(31.95):1:(32.25)][(74.70):1:(75.05)]"

    for ext, path in [("csv", daily_csv), ("nc", daily_nc)]:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            print(f"Downloading ERDDAP CHIRPS daily ({ext})...")
            r = requests.get(f"{base_d}.{ext}?{q_d}", headers=HEADERS, timeout=120)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            print(f" -> Saved {path} ({os.path.getsize(path):,} bytes)")

    # 2. CHIRPS Monthly 0.05 deg (1981-01-01 to latest) over Narowal region
    mon_csv = os.path.join(RAIN_DIR, "chirps_v20_narowal_monthly_1981_present.csv")
    mon_nc = os.path.join(RAIN_DIR, "chirps_v20_narowal_monthly_1981_present.nc")
    base_m = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalMonthlyP05"
    q_m = "precip[(1981-01-01T00:00:00Z):1:(last)][(31.95):1:(32.25)][(74.70):1:(75.05)]"
    for ext, path in [("csv", mon_csv), ("nc", mon_nc)]:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            print(f"Downloading ERDDAP CHIRPS monthly ({ext})...")
            r = requests.get(f"{base_m}.{ext}?{q_m}", headers=HEADERS, timeout=120)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            print(f" -> Saved {path} ({os.path.getsize(path):,} bytes)")

    # Summarize Narowal center pixel (nearest 32.125 N, 74.875 E) annual totals & top extreme daily events
    df = pd.read_csv(daily_csv, skiprows=[1])
    df["time"] = pd.to_datetime(df["time"])
    df["year"] = df["time"].dt.year
    # Pick closest grid cell to Narowal (32.102, 74.873) -> 32.125, 74.875
    lats = df["latitude"].unique()
    lons = df["longitude"].unique()
    clat = min(lats, key=lambda x: abs(x - 32.102))
    clon = min(lons, key=lambda x: abs(x - 74.873))
    sub = df[(df["latitude"] == clat) & (df["longitude"] == clon)].copy()
    print(f"CHIRPS cell ({clat:.3f}N, {clon:.3f}E): {sub['time'].min().date()} to {sub['time'].max().date()} ({len(sub)} days)")
    ann = sub.groupby("year")["precip"].sum().round(1)
    print("Annual totals (mm):", ann.to_dict())
    top_days = sub.sort_values("precip", ascending=False).head(12)[["time", "precip"]]
    print("Top 12 extreme daily rainfall events since 2014:")
    print(top_days.to_string(index=False))

    # Also try polite single-file fetch of CHIRPS v3.0 2024 & 2025 annual GeoTIFFs (if UCSB 429 cooldown cleared)
    ann_v3_dir = os.path.join(RAIN_DIR, "chirps_v3_annual_tifs")
    os.makedirs(ann_v3_dir, exist_ok=True)
    for yr in [2022, 2023, 2024, 2025]:
        u = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/annual/global/tifs/chirps-v3.0.{yr}.tif"
        dest = os.path.join(ann_v3_dir, f"chirps-v3.0.{yr}.tif")
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue
        try:
            r = requests.get(u, headers=HEADERS, timeout=45)
            if r.status_code == 200:
                with open(dest, "wb") as f:
                    f.write(r.content)
                print(f"CHIRPS v3.0 {yr} annual GeoTIFF downloaded ({len(r.content):,} bytes)")
            else:
                print(f"CHIRPS v3.0 {yr} HTTP {r.status_code}")
        except Exception as e:
            print(f"CHIRPS v3.0 {yr} err: {e}")
        time.sleep(5)


if __name__ == "__main__":
    fetch_erddap()
