"""Catalog & download Sentinel-1 RTC (VV, VH) AOI COGs from Microsoft Planetary Computer for Narowal monsoon events."""

import json
import os
import requests
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
S1_DIR = os.path.join(ROOT, "02_Raw_Data", "02_Sentinel_1")
AOI_WGS84 = (74.80, 32.04, 74.95, 32.17)


def sign_pc_url(unsigned_url: str) -> str:
    r = requests.get(
        "https://planetarycomputer.microsoft.com/api/sas/v1/sign",
        params={"href": unsigned_url},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["href"]


def main():
    # 1. Query Planetary Computer sentinel-1-rtc catalog across monsoon months 2018-2026
    periods = [
        ("2018_monsoon", "2018-06-01T00:00:00Z/2018-09-30T23:59:59Z"),
        ("2019_monsoon", "2019-06-01T00:00:00Z/2019-09-30T23:59:59Z"),
        ("2020_monsoon", "2020-06-01T00:00:00Z/2020-09-30T23:59:59Z"),
        ("2022_monsoon", "2022-06-01T00:00:00Z/2022-09-30T23:59:59Z"),
        ("2023_monsoon", "2023-06-01T00:00:00Z/2023-09-30T23:59:59Z"),
        ("2024_monsoon", "2024-06-01T00:00:00Z/2024-09-30T23:59:59Z"),
        ("2025_monsoon", "2025-06-01T00:00:00Z/2025-09-30T23:59:59Z"),
        ("2026_monsoon", "2026-06-01T00:00:00Z/2026-09-30T23:59:59Z"),
    ]
    pc_cat = {}
    for label, dt in periods:
        r = requests.post(
            "https://planetarycomputer.microsoft.com/api/stac/v1/search",
            json={
                "collections": ["sentinel-1-rtc"],
                "intersects": {"type": "Point", "coordinates": [74.873, 32.102]},
                "datetime": dt,
                "limit": 50,
            },
            timeout=30,
        )
        r.raise_for_status()
        feats = r.json().get("features", [])
        pc_cat[label] = [
            {
                "id": f["id"],
                "datetime": f["properties"].get("datetime"),
                "orbit_state": f["properties"].get("sat:orbit_state"),
                "relative_orbit": f["properties"].get("sat:relative_orbit"),
                "instrument_mode": f["properties"].get("sar:instrument_mode"),
                "polarizations": f["properties"].get("sar:polarizations"),
                "vv_href": f["assets"].get("vv", {}).get("href"),
                "vh_href": f["assets"].get("vh", {}).get("href"),
            }
            for f in feats
        ]
        print(f"PC S1-RTC {label}: {len(feats)} scenes")

    with open(os.path.join(S1_DIR, "pc_sentinel1_rtc_catalog_narowal.json"), "w", encoding="utf-8") as f:
        json.dump(pc_cat, f, indent=2)

    # 2. Download verified pre/post pairs for August 2025 Narowal Flood Event (Orbit 100 Ascending: Aug 15 pre vs Aug 27 post)
    # and Orbit 34 Descending (Aug 05 pre vs Aug 23 post)
    target_dates = {
        "2025-08-15": "pre_event_asc100",
        "2025-08-27": "post_event_asc100",
        "2025-08-05": "pre_event_desc34",
        "2025-08-23": "post_event_desc34",
    }
    mon25 = pc_cat.get("2025_monsoon", [])
    dl_records = []
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MULTIRANGE="NO", CPL_VSIL_CURL_CHUNK_SIZE="2097152"):
        for it in mon25:
            dt_day = it["datetime"][:10]
            if dt_day not in target_dates:
                continue
            role = target_dates[dt_day]
            sdir = os.path.join(S1_DIR, f"S1RTC_{dt_day.replace('-', '')}_{role}")
            os.makedirs(sdir, exist_ok=True)
            with open(os.path.join(sdir, "scene_metadata.json"), "w", encoding="utf-8") as mf:
                json.dump(it, mf, indent=2)
            for pol in ["vv", "vh"]:
                href = it.get(f"{pol}_href")
                if not href:
                    continue
                out_tif = os.path.join(sdir, f"S1RTC_{dt_day.replace('-', '')}_{pol}_AOI.tif")
                if os.path.exists(out_tif) and os.path.getsize(out_tif) > 0:
                    continue
                signed = sign_pc_url(href)
                with rasterio.open(signed) as src:
                    b_src = transform_bounds("EPSG:4326", src.crs, *AOI_WGS84)
                    win = from_bounds(*b_src, transform=src.transform).round_offsets().round_lengths()
                    data = src.read(1, window=win)
                    prof = src.profile.copy()
                    prof.update({
                        "driver": "GTiff",
                        "height": data.shape[0],
                        "width": data.shape[1],
                        "transform": src.window_transform(win),
                        "compress": "DEFLATE",
                    })
                    with rasterio.open(out_tif, "w", **prof) as dst:
                        dst.write(data, 1)
                print(f"Saved S1-RTC {role} ({dt_day}) {pol}: {os.path.getsize(out_tif):,} B")
                dl_records.append({"role": role, "date": dt_day, "pol": pol, "file": out_tif})
    with open(os.path.join(S1_DIR, "pc_sentinel1_rtc_downloads.json"), "w", encoding="utf-8") as f:
        json.dump(dl_records, f, indent=2)


if __name__ == "__main__":
    main()
