"""Download Sentinel-2 L2A AOI bands fast from Microsoft Planetary Computer (open anonymous SAS COGs)."""

import json
import os
import requests
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
S2_DIR = os.path.join(ROOT, "02_Raw_Data", "03_Sentinel_2")
AOI_WGS84 = (74.80, 32.04, 74.95, 32.17)


def sign_pc_url(unsigned_url: str) -> str:
    r = requests.get(
        "https://planetarycomputer.microsoft.com/api/sas/v1/sign",
        params={"href": unsigned_url},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["href"]


def fetch_scene(label: str, datetime_range: str, max_cloud: float = 10.0):
    r = requests.post(
        "https://planetarycomputer.microsoft.com/api/stac/v1/search",
        json={
            "collections": ["sentinel-2-l2a"],
            "intersects": {"type": "Point", "coordinates": [74.873, 32.102]},
            "datetime": datetime_range,
            "query": {"eo:cloud_cover": {"lt": max_cloud}},
            "limit": 15,
        },
        timeout=30,
    )
    r.raise_for_status()
    feats = r.json().get("features", [])
    if not feats:
        print(f"No scenes for {label}")
        return None
    best = sorted(feats, key=lambda f: f["properties"]["eo:cloud_cover"])[0]
    dt = best["properties"]["datetime"][:10]
    sid = best["id"]
    cc = best["properties"]["eo:cloud_cover"]
    scene_dir = os.path.join(S2_DIR, f"PC_{label}_{dt}_{sid}")
    os.makedirs(scene_dir, exist_ok=True)
    with open(os.path.join(scene_dir, "scene_metadata.json"), "w", encoding="utf-8") as mf:
        json.dump(best, mf, indent=2)

    print(f"Fetching PC S2 {label}: {sid} ({dt}, cloud={cc:.2f}%)")
    band_map = [("blue", "B02"), ("green", "B03"), ("red", "B04"), ("nir", "B08"), ("swir16", "B11"), ("scl", "SCL")]
    saved = []
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MULTIRANGE="YES", CPL_VSIL_CURL_CHUNK_SIZE="2097152"):
        for bname, asset_key in band_map:
            out_tif = os.path.join(scene_dir, f"{sid}_{bname}_AOI.tif")
            if os.path.exists(out_tif) and os.path.getsize(out_tif) > 0:
                saved.append(out_tif)
                continue
            href = sign_pc_url(best["assets"][asset_key]["href"])
            with rasterio.open(href) as src:
                bounds_src = transform_bounds("EPSG:4326", src.crs, *AOI_WGS84)
                win = from_bounds(*bounds_src, transform=src.transform).round_offsets().round_lengths()
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
            print(f"  saved {bname} ({os.path.getsize(out_tif):,} B)")
            saved.append(out_tif)
    return {"label": label, "id": sid, "date": dt, "cloud": cc, "files": saved}


def main():
    targets = [
        ("2025_dry", "2025-04-01T00:00:00Z/2025-06-15T23:59:59Z", 5.0),
        ("2025_monsoon", "2025-08-15T00:00:00Z/2025-09-30T23:59:59Z", 5.0),
        ("2022_monsoon", "2022-07-01T00:00:00Z/2022-09-30T23:59:59Z", 5.0),
        ("2026_recent", "2026-04-01T00:00:00Z/2026-11-11T23:59:59Z", 5.0),
    ]
    res = []
    for lbl, dt_rng, cc in targets:
        r = fetch_scene(lbl, dt_rng, cc)
        if r:
            res.append(r)
    with open(os.path.join(S2_DIR, "pc_sentinel2_downloads.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)


if __name__ == "__main__":
    main()
