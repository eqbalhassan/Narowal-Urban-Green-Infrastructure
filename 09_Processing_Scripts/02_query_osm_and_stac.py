"""Phase 1 OSM & Satellite Catalog Query Script (Overpass, Nominatim, CDSE, Earth Search)."""

import json
import os
from datetime import datetime, timezone
import requests

PROJECT_ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
OSM_DIR = os.path.join(PROJECT_ROOT, "02_Raw_Data", "01_OSM")
S1_DIR = os.path.join(PROJECT_ROOT, "02_Raw_Data", "02_Sentinel_1")
S2_DIR = os.path.join(PROJECT_ROOT, "02_Raw_Data", "03_Sentinel_2")

HEADERS = {"User-Agent": "Narowal-UGI-GIS-Research/1.0 (contact: gis-research@example.org)"}

# Expanded Narowal city + buffer bounding box (south, west, north, east)
# Narowal City center ~ 32.102 N, 74.873 E
BBOX_SWNE = (32.04, 74.80, 32.17, 74.95)
BBOX_WSEN = [74.80, 32.04, 74.95, 32.17]
NAROWAL_POINT_WKT = "POINT(74.873 32.102)"


def query_nominatim():
    """Search Nominatim for Narowal boundaries and places."""
    url = "https://nominatim.openstreetmap.org/search"
    results = {}
    for q in ["Narowal, Punjab, Pakistan", "Municipal Committee Narowal", "Narowal Tehsil, Punjab, Pakistan"]:
        r = requests.get(
            url,
            params={"q": q, "format": "jsonv2", "polygon_geojson": 1, "limit": 10},
            headers=HEADERS,
            timeout=60,
        )
        r.raise_for_status()
        results[q] = r.json()
    out_path = os.path.join(OSM_DIR, "nominatim_narowal_search.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Nominatim search -> {out_path}")
    return results


def query_overpass():
    """Download raw OSM data for Narowal urban area + generous buffer via Overpass API."""
    s, w, n, e = BBOX_SWNE
    overpass_url = "https://overpass-api.de/api/interpreter"

    # 1. Full OSM XML extract of Narowal urban bounding box (streets, buildings, parks, waterways, amenities)
    q_full = f"""[out:xml][timeout:180];
(
  node({s},{w},{n},{e});
  way({s},{w},{n},{e});
  relation({s},{w},{n},{e});
);
out body;
>;
out skel qt;"""
    raw_osm_path = os.path.join(OSM_DIR, "narowal_urban_bbox_raw.osm")
    if not os.path.exists(raw_osm_path) or os.path.getsize(raw_osm_path) == 0:
        print("Querying Overpass for full OSM XML extract of Narowal bbox...")
        r = requests.post(overpass_url, data={"data": q_full}, headers=HEADERS, timeout=240)
        r.raise_for_status()
        with open(raw_osm_path, "wb") as f:
            f.write(r.content)
        print(f"Saved raw OSM XML ({os.path.getsize(raw_osm_path):,} bytes) -> {raw_osm_path}")
    else:
        print(f"Raw OSM XML already exists -> {raw_osm_path}")

    # 2. Administrative boundaries in wider Narowal area
    q_admin = """[out:json][timeout:120];
(
  relation["boundary"="administrative"](31.95,74.70,32.25,75.05);
  way["boundary"="administrative"](31.95,74.70,32.25,75.05);
);
out body;
>;
out skel qt;"""
    admin_json_path = os.path.join(OSM_DIR, "narowal_admin_boundaries_raw.json")
    print("Querying Overpass for administrative boundaries...")
    r = requests.post(overpass_url, data={"data": q_admin}, headers=HEADERS, timeout=180)
    r.raise_for_status()
    with open(admin_json_path, "wb") as f:
        f.write(r.content)
    print(f"Saved admin boundaries JSON ({os.path.getsize(admin_json_path):,} bytes) -> {admin_json_path}")


def query_cdse_sentinel1():
    """Query CDSE OData catalog for Sentinel-1 IW GRD over Narowal across candidate monsoon years."""
    base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    periods = [
        ("2014_monsoon_post", "2014-09-01T00:00:00.000Z", "2014-12-31T23:59:59.999Z"),
        ("2018_monsoon", "2018-06-01T00:00:00.000Z", "2018-09-30T23:59:59.999Z"),
        ("2019_monsoon", "2019-06-01T00:00:00.000Z", "2019-09-30T23:59:59.999Z"),
        ("2020_monsoon", "2020-06-01T00:00:00.000Z", "2020-09-30T23:59:59.999Z"),
        ("2022_monsoon", "2022-06-01T00:00:00.000Z", "2022-09-30T23:59:59.999Z"),
        ("2023_monsoon", "2023-06-01T00:00:00.000Z", "2023-09-30T23:59:59.999Z"),
        ("2024_monsoon", "2024-06-01T00:00:00.000Z", "2024-09-30T23:59:59.999Z"),
        ("2025_monsoon", "2025-06-01T00:00:00.000Z", "2025-09-30T23:59:59.999Z"),
        ("2026_all", "2026-01-01T00:00:00.000Z", "2026-11-11T23:59:59.999Z"),
    ]
    all_s1 = {}
    for label, start, end in periods:
        flt = (
            f"Collection/Name eq 'SENTINEL-1' "
            f"and contains(Name,'IW_GRDH') "
            f"and OData.CSC.Intersects(area=geography'SRID=4326;{NAROWAL_POINT_WKT}') "
            f"and ContentDate/Start ge {start} and ContentDate/Start le {end}"
        )
        params = {
            "$filter": flt,
            "$orderby": "ContentDate/Start asc",
            "$top": 100,
            "$expand": "Attributes",
        }
        r = requests.get(base_url, params=params, headers=HEADERS, timeout=60)
        if r.status_code == 200:
            items = r.json().get("value", [])
            cleaned = []
            for it in items:
                attrs = {a["Name"]: a["Value"] for a in it.get("Attributes", []) if "Name" in a and "Value" in a}
                cleaned.append({
                    "Id": it.get("Id"),
                    "Name": it.get("Name"),
                    "ContentDate": it.get("ContentDate"),
                    "ContentLength": it.get("ContentLength"),
                    "orbitDirection": attrs.get("orbitDirection"),
                    "relativeOrbitNumber": attrs.get("relativeOrbitNumber"),
                    "polarisationChannels": attrs.get("polarisationChannels"),
                    "operationalMode": attrs.get("operationalMode"),
                    "productType": attrs.get("productType"),
                    "platformSerialIdentifier": attrs.get("platformSerialIdentifier"),
                })
            all_s1[label] = cleaned
            print(f"Sentinel-1 {label}: {len(cleaned)} IW_GRDH scenes")
        else:
            all_s1[label] = {"error": r.status_code, "text": r.text[:300]}
            print(f"Sentinel-1 {label} HTTP {r.status_code}")

    out_path = os.path.join(S1_DIR, "cdse_sentinel1_catalog_narowal.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_s1, f, indent=2)
    print(f"Saved Sentinel-1 catalog -> {out_path}")


def query_earth_search_sentinel2():
    """Query Element84 Earth Search STAC (open AWS COGs) for Sentinel-2 L2A over Narowal."""
    stac_url = "https://earth-search.aws.element84.com/v1/search"
    windows = [
        ("2018_dry_historical", "2018-03-01T00:00:00Z/2018-05-31T23:59:59Z"),
        ("2022_monsoon", "2022-07-01T00:00:00Z/2022-09-30T23:59:59Z"),
        ("2024_dry", "2024-03-01T00:00:00Z/2024-05-31T23:59:59Z"),
        ("2025_dry", "2025-03-01T00:00:00Z/2025-05-31T23:59:59Z"),
        ("2025_monsoon", "2025-07-01T00:00:00Z/2025-09-30T23:59:59Z"),
        ("2026_recent", "2026-01-01T00:00:00Z/2026-11-11T23:59:59Z"),
    ]
    out = {}
    for label, dt in windows:
        payload = {
            "collections": ["sentinel-2-l2a"],
            "intersects": {"type": "Point", "coordinates": [74.873, 32.102]},
            "datetime": dt,
            "query": {"eo:cloud_cover": {"lt": 20}},
            "limit": 25,
        }
        r = requests.post(stac_url, json=payload, headers=HEADERS, timeout=60)
        if r.status_code == 200:
            feats = r.json().get("features", [])
            cleaned = []
            for ft in feats:
                p = ft.get("properties", {})
                assets = ft.get("assets", {})
                cleaned.append({
                    "id": ft.get("id"),
                    "datetime": p.get("datetime"),
                    "cloud_cover": p.get("eo:cloud_cover"),
                    "mgrs_tile": f"{p.get('grid:code','')}",
                    "platform": p.get("platform"),
                    "red_href": assets.get("red", {}).get("href"),
                    "green_href": assets.get("green", {}).get("href"),
                    "blue_href": assets.get("blue", {}).get("href"),
                    "nir_href": assets.get("nir", {}).get("href"),
                    "swir16_href": assets.get("swir16", {}).get("href"),
                    "scl_href": assets.get("scl", {}).get("href"),
                })
            out[label] = cleaned
            print(f"Sentinel-2 {label}: {len(cleaned)} scenes (<20% cloud)")
        else:
            out[label] = {"error": r.status_code, "text": r.text[:300]}
            print(f"Sentinel-2 {label} HTTP {r.status_code}")

    out_path = os.path.join(S2_DIR, "earth_search_sentinel2_catalog_narowal.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved Sentinel-2 catalog -> {out_path}")


if __name__ == "__main__":
    try:
        query_nominatim()
    except Exception as e:
        print("Nominatim skipped/unavailable:", e)
    query_overpass()
    query_cdse_sentinel1()
    query_earth_search_sentinel2()
