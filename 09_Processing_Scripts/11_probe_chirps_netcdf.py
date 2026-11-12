"""Download CHIRPS v3.0 NetCDF or GeoTIFFs politely without triggering 429."""

import csv
import os
import re
import time
import requests

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAIN_DIR = os.path.join(ROOT, "02_Raw_Data", "05_Rainfall")
BASE = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/"
HEADERS = {"User-Agent": "Narowal-UGI-GIS-Research/1.0"}


def main():
    for sub in ["annual/global/netcdf/", "monthly/global/netcdf/", "daily/final/rnl/netcdf/"]:
        r = requests.get(BASE + sub, headers=HEADERS, timeout=30)
        print(sub, r.status_code)
        if r.status_code == 200:
            links = re.findall(r'href="([^"]+)"', r.text)
            print("  files:", [l for l in links if not l.startswith("?") and l != "../"][:12])
        time.sleep(2.0)


if __name__ == "__main__":
    main()
