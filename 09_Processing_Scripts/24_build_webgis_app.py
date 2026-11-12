"""Step 5: Export EPSG:4326 Web-Ready GeoJSON Layers & Build Interactive Leaflet Web GIS Decision-Support App."""

import json
import os
import warnings
warnings.filterwarnings("ignore")

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize, shapes
from scipy import ndimage
from shapely.geometry import shape

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
BASE_DIR = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
LULC_DIR = os.path.join(ROOT, "03_Processed_Data", "02_Land_Use_Land_Cover")
FLOOD_DIR = os.path.join(ROOT, "03_Processed_Data", "04_Historical_Flood_Mapping")
ACC_DIR = os.path.join(ROOT, "03_Processed_Data", "05_Park_Accessibility")
DRAIN_DIR = os.path.join(ROOT, "03_Processed_Data", "06_Drainage_Mapping")
SUIT_DIR = os.path.join(ROOT, "03_Processed_Data", "07_Suitability_Analysis")
STATS_DIR = os.path.join(ROOT, "08_Tables_and_Statistics")

APP_DIR = os.path.join(ROOT, "05_Maps", "Narowal_WebGIS_App")
GEO_DIR = os.path.join(APP_DIR, "geojson")
os.makedirs(GEO_DIR, exist_ok=True)


def to_geojson_dict(gdf, keep_cols=None, simplify_m=3.0, precision=5):
    g = gdf.copy()
    if simplify_m and simplify_m > 0 and g.crs and g.crs.to_epsg() == 32643:
        g["geometry"] = g.geometry.simplify(simplify_m, preserve_topology=True)
    if keep_cols is not None:
        cols = [c for c in keep_cols if c in g.columns] + ["geometry"]
        g = g[cols]
    g = g.to_crs("EPSG:4326")
    # Convert non-serializable types cleanly
    for col in g.columns:
        if col != "geometry":
            g[col] = g[col].apply(lambda x: None if pd.isna(x) else (float(x) if isinstance(x, (np.floating,)) else (int(x) if isinstance(x, (np.integer,)) else str(x) if not isinstance(x, (str, int, float, bool)) else x)))
    raw = json.loads(g.to_json())
    # Round coordinates to keep bundle lightweight
    def round_coords(coords):
        if isinstance(coords[0], (int, float)):
            return [round(coords[0], precision), round(coords[1], precision)]
        return [round_coords(c) for c in coords]
    for feat in raw.get("features", []):
        geom = feat.get("geometry")
        if geom and geom.get("coordinates"):
            geom["coordinates"] = round_coords(geom["coordinates"])
    return raw


def main():
    print("=== Building EPSG:4326 GeoJSONs & Web GIS Bundle ===")
    mc = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="mc_boundary_preliminary")
    bu = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="builtup_urban_boundary_preliminary")
    buf = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="study_buffer_1km")
    parks = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_parks_green_poly_raw")
    waterways = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_waterways_raw")
    waterbodies = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_waterbodies_raw")
    uu_assets = gpd.read_file(os.path.join(BASE_DIR, "Narowal_UrbanUnit_2021_Assets_UTM43N.gpkg"), layer="uu2021_key_assets_preliminary")

    entrances = gpd.read_file(os.path.join(ACC_DIR, "Narowal_Park_Entrances_Preliminary_UTM43N.gpkg"), layer="park_entrances")
    sa = gpd.read_file(os.path.join(ACC_DIR, "Narowal_Park_Accessibility_UTM43N.gpkg"), layer="service_areas_10min")
    edges = gpd.read_file(os.path.join(ACC_DIR, "Narowal_Park_Accessibility_UTM43N.gpkg"), layer="streets_accessibility_formal")
    # Clip walkable street network to MC boundary for clean lightweight rendering
    edges_mc = gpd.clip(edges, mc)
    edges_mc["dist_formal_pk_m"] = edges_mc["dist_m"]
    edges_mc["highway"] = "walkable_street"
    edges_mc["formal_access"] = np.where(edges_mc["dist_formal_pk_m"] <= 800, "Within 10-Min Walk (<=800m)", "Outside 10-Min Walk (>800m)")

    inferred = gpd.read_file(os.path.join(DRAIN_DIR, "Narowal_Inferred_Drainage_Convergence_UTM43N.gpkg"), layer="dem_inferred_drainage")
    # Dissolve adjacent DEM convergence segments cleanly or clip to MC + 500m
    inferred_clip = gpd.clip(inferred, mc.buffer(500))
    drn_prio = gpd.read_file(os.path.join(DRAIN_DIR, "Narowal_Drainage_Investigation_Priorities_UTM43N.gpkg"), layer="drainage_priority_zones")

    vac = gpd.read_file(os.path.join(SUIT_DIR, "Narowal_Vacant_Candidate_Sites_UTM43N.gpkg"), layer="vacant_candidate_sites")
    sites = gpd.read_file(os.path.join(SUIT_DIR, "Narowal_Priority_Intervention_Sites_UTM43N.gpkg"), layer="priority_intervention_sites")

    # Vectorize High / Very High Flood Susceptibility (Class 4 & 5) inside MC >= 0.4 ha for crisp WebGIS polygon display
    with rasterio.open(os.path.join(FLOOD_DIR, "Narowal_Flood_Susceptibility_5Class_UTM43N.tif")) as ssrc:
        sus_arr = ssrc.read(1)
        tr = ssrc.transform
        h, w = ssrc.height, ssrc.width
    mc_m = rasterize([(mc.geometry.union_all(), 1)], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    vh_polys = []
    for cls_v, cls_lbl in [(4, "High Susceptibility (Class 4)"), (5, "Very High Susceptibility (Class 5)")]:
        m = ((sus_arr == cls_v) & (mc_m == 1)).astype(np.uint8)
        m = ndimage.binary_opening(m, iterations=1).astype(np.uint8)
        for g, val in shapes(m, mask=(m == 1), transform=tr):
            if val == 1:
                poly = shape(g)
                if poly.area >= 4000.0:  # >= 0.4 ha generalized polygons
                    vh_polys.append({"class_id": cls_v, "class_name": cls_lbl, "area_ha": round(poly.area / 1e4, 2), "geometry": poly})
    flood_vh_gdf = gpd.GeoDataFrame(vh_polys, crs="EPSG:32643")

    # Export individual GeoJSONs AND consolidated JS bundle
    layers_cfg = {
        "mc_boundary": (mc, ["area_km2", "note"], 10.0),
        "builtup_boundary": (bu, ["area_km2", "note"], 10.0),
        "study_buffer_1km": (buf, ["area_km2", "note"], 15.0),
        "parks": (parks, ["osm_id", "name", "leisure", "area_ha"], 2.0),
        "park_entrances": (entrances, ["park_name", "leisure", "is_formal_park", "entrance_id", "verification_status"], 0.0),
        "service_areas_10min": (sa, ["category", "area_ha"], 8.0),
        "streets_accessibility": (edges_mc, ["highway", "length_m", "dist_formal_pk_m", "formal_access"], 5.0),
        "waterways": (waterways, ["osm_id", "name", "waterway"], 5.0),
        "waterbodies": (waterbodies, ["osm_id", "name", "natural"], 3.0),
        "dem_inferred_drainage": (inferred_clip, ["facc_cells", "source_note"], 0.0),
        "drainage_priority_zones": (drn_prio, ["priority_id", "area_ha", "investigation_need"], 8.0),
        "flood_high_veryhigh": (flood_vh_gdf, ["class_id", "class_name", "area_ha"], 10.0),
        "vacant_candidate_sites": (vac, ["site_id", "area_ha", "current_land_cover", "existing_use", "ownership_status", "dist_nearest_park_m", "flood_susceptibility", "suitability_score", "suitability_class"], 5.0),
        "uu2021_key_assets": (uu_assets, ["asset_id", "name", "category", "capacity_or_size", "source_page", "status"], 0.0),
        "priority_intervention_sites": (sites, None, 0.0),
    }

    js_bundle = {}
    for name, (gdf, cols, simp) in layers_cfg.items():
        gj = to_geojson_dict(gdf, cols, simp)
        js_bundle[name] = gj
        with open(os.path.join(GEO_DIR, f"{name}.geojson"), "w", encoding="utf-8") as f:
            json.dump(gj, f)
        print(f"  Exported {name}.geojson ({len(gj.get('features', []))} features)")

    # Also export KML of Priority Intervention Sites & Preliminary Boundaries for Mayor / Google Earth
    for kname, gdf in [("Narowal_Priority_GI_Sites.kml", sites.to_crs("EPSG:4326")), ("Narowal_MC_Preliminary_Boundary.kml", mc.to_crs("EPSG:4326"))]:
        try:
            gdf.to_file(os.path.join(APP_DIR, kname), driver="KML")
            print(f"  Exported {kname}")
        except Exception as exc:
            print(f"  Note: KML driver skipped ({exc})")

    # Load verified KPI tables to embed into JS bundle
    acc_df = pd.read_csv(os.path.join(STATS_DIR, "phase2_park_accessibility_summary.csv")).to_dict(orient="records")
    sus_df = pd.read_csv(os.path.join(STATS_DIR, "phase3_flood_susceptibility_areas.csv")).to_dict(orient="records")
    with open(os.path.join(STATS_DIR, "phase2_urban_baseline_summary.json"), encoding="utf-8") as f:
        base_sum = json.load(f)
    with open(os.path.join(STATS_DIR, "chirps_rainfall_summary.json"), encoding="utf-8") as f:
        rain_sum = json.load(f)

    kpis = {"baseline": base_sum, "accessibility": acc_df, "flood_susceptibility": sus_df, "rainfall": rain_sum}

    data_js_path = os.path.join(APP_DIR, "data.js")
    with open(data_js_path, "w", encoding="utf-8") as f:
        f.write("window.NAROWAL_GIS_DATA = ")
        json.dump(js_bundle, f, separators=(",", ":"))
        f.write(";\nwindow.NAROWAL_KPIS = ")
        json.dump(kpis, f, separators=(",", ":"))
        f.write(";\n")
    sz_mb = os.path.getsize(data_js_path) / (1024 * 1024)
    print(f"Saved {data_js_path} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    main()
