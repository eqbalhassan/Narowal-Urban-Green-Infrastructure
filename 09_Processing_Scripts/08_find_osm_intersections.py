"""Extract exact OSM road intersection & landmark coordinates (WGS84 & UTM43N) for georeferencing Urban Unit maps."""

import os
import geopandas as gpd
from shapely.geometry import Point

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
GPKG = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping", "Narowal_OSM_Extracted_WGS84.gpkg")

roads = gpd.read_file(GPKG, layer="osm_roads_raw")
# Find intersection points of named primary/secondary/tertiary roads
named = roads[roads["name"].notna() & roads["highway"].isin(["primary", "secondary", "tertiary"])].copy()
print("Named major roads:", sorted(named["name"].unique()))

seen = set()
for i, r1 in named.iterrows():
    for j, r2 in named.iterrows():
        if j <= i or r1["name"] == r2["name"]:
            continue
        inter = r1.geometry.intersection(r2.geometry)
        if not inter.is_empty:
            pts = [inter] if inter.geom_type == "Point" else (list(inter.geoms) if hasattr(inter, "geoms") else [])
            for p in pts:
                if p.geom_type == "Point":
                    key = (round(p.x, 4), round(p.y, 4), tuple(sorted([r1["name"], r2["name"]])))
                    if key not in seen:
                        seen.add(key)
                        print(f"  {r1['name']} X {r2['name']}: ({p.x:.6f}, {p.y:.6f})")
