"""Phase 2: Sentinel-2 LULC, Urban Baseline Statistics, Pedestrian Network 10-Min Park Accessibility, and Maps 01-03."""

import json
import os
import warnings
warnings.filterwarnings("ignore")

import arcpy
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.colors import ListedColormap, BoundaryNorm
import networkx as nx
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling
from shapely.geometry import Point, LineString, MultiLineString, Polygon
from shapely.ops import unary_union, linemerge, nearest_points
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, cohen_kappa_score

arcpy.env.overwriteOutput = True

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAW_S2 = os.path.join(ROOT, "02_Raw_Data", "03_Sentinel_2")
BASE_DIR = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
LULC_DIR = os.path.join(ROOT, "03_Processed_Data", "02_Land_Use_Land_Cover")
ACC_DIR = os.path.join(ROOT, "03_Processed_Data", "05_Park_Accessibility")
STATS_DIR = os.path.join(ROOT, "08_Tables_and_Statistics")
MAPS_01 = os.path.join(ROOT, "05_Maps", "01_Urban_Baseline")
MAPS_02 = os.path.join(ROOT, "05_Maps", "02_Park_Accessibility")
GDB = os.path.join(ROOT, "04_Geodatabase", "Narowal_Green_Infrastructure.gdb")

for d in [LULC_DIR, ACC_DIR, STATS_DIR, MAPS_01, MAPS_02]:
    os.makedirs(d, exist_ok=True)

WALK_SPEED_KMH = 4.8
THRESHOLD_MIN = 10.0
THRESHOLD_M = (WALK_SPEED_KMH * 1000.0 / 60.0) * THRESHOLD_MIN  # 800.0 m


def add_cartographic_frame(ax, bounds, title, subtitle, sources_text, date_str="2026-11-12"):
    """Apply consistent cartographic frame: North arrow, metric scale bar, CRS, source, author."""
    minx, miny, maxx, maxy = bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect("equal")
    ax.tick_params(labelsize=7, colors="#444444")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{int(y):,}"))
    ax.set_xlabel("Easting (m) — WGS 84 / UTM Zone 43N (EPSG:32643)", fontsize=8, color="#333333")
    ax.set_ylabel("Northing (m)", fontsize=8, color="#333333")

    ax.set_title(f"{title}\n{subtitle}", fontsize=12, fontweight="bold", loc="left", pad=10, color="#1A1A1A")

    # North Arrow (bottom-right inside plot, clear of legend)
    nx_x, nx_y = maxx - (maxx - minx) * 0.05, miny + (maxy - miny) * 0.055
    arrow_len = (maxy - miny) * 0.055
    ax.annotate(
        "N",
        xy=(nx_x, nx_y + arrow_len),
        xytext=(nx_x, nx_y),
        arrowprops=dict(facecolor="#1A1A1A", edgecolor="#1A1A1A", width=3, headwidth=9, headlength=9),
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color="#1A1A1A",
        zorder=20,
    )

    # Metric Scale Bar (bottom-left inside plot)
    span = maxx - minx
    bar_m = 1000 if span > 4500 else 500
    sb_x0 = minx + span * 0.04
    sb_y0 = miny + (maxy - miny) * 0.045
    sb_h = (maxy - miny) * 0.012
    ax.add_patch(mpatches.Rectangle((sb_x0, sb_y0), bar_m / 2, sb_h, facecolor="#1A1A1A", edgecolor="#1A1A1A", zorder=20))
    ax.add_patch(mpatches.Rectangle((sb_x0 + bar_m / 2, sb_y0), bar_m / 2, sb_h, facecolor="#FFFFFF", edgecolor="#1A1A1A", zorder=20))
    ax.text(sb_x0, sb_y0 + sb_h * 1.35, "0", fontsize=7.5, fontweight="bold", ha="center", zorder=20,
            bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none", alpha=0.75))
    ax.text(sb_x0 + bar_m / 2, sb_y0 + sb_h * 1.35, f"{bar_m // 2} m", fontsize=7.5, fontweight="bold", ha="center", zorder=20,
            bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none", alpha=0.75))
    ax.text(sb_x0 + bar_m, sb_y0 + sb_h * 1.35, f"{bar_m:,} m", fontsize=7.5, fontweight="bold", ha="center", zorder=20,
            bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none", alpha=0.75))

    # Footer metadata
    footer = (
        f"CRS: WGS 84 / UTM Zone 43N (EPSG:32643)  |  Date: {date_str}  |  "
        f"Project: Narowal Urban Green Infrastructure & Flood Resilience Initiative\n"
        f"Sources: {sources_text}"
    )
    ax.figure.text(0.015, 0.01, footer, fontsize=7, color="#444444", va="bottom")


def load_s2_scene(scene_prefix):
    """Load 10m Blue, Green, Red, NIR and resample 20m SWIR16 & SCL onto the 10m grid."""
    dirs = [d for d in os.listdir(RAW_S2) if d.startswith(scene_prefix) and os.path.isdir(os.path.join(RAW_S2, d))]
    if not dirs:
        raise FileNotFoundError(f"No S2 folder matching {scene_prefix}")
    sdir = os.path.join(RAW_S2, sorted(dirs)[0])
    files = {fn.split("_")[-2]: os.path.join(sdir, fn) for fn in os.listdir(sdir) if fn.endswith("_AOI.tif")}

    with rasterio.open(files["red"]) as ref:
        profile = ref.profile.copy()
        h, w = ref.height, ref.width
        tr = ref.transform
        crs = ref.crs
        red = ref.read(1).astype(np.float32)

    def read_match(key, resamp=Resampling.bilinear):
        with rasterio.open(files[key]) as src:
            if src.height == h and src.width == w:
                return src.read(1).astype(np.float32)
            return src.read(1, out_shape=(h, w), resampling=resamp).astype(np.float32)

    blue = read_match("blue")
    green = read_match("green")
    nir = read_match("nir")
    swir16 = read_match("swir16", Resampling.bilinear)
    scl = read_match("scl", Resampling.nearest)

    # Convert Sentinel-2 L2A PB 04.00+ DN (offset 1000, scale 10000) to true surface reflectance [0, 1]
    def to_refl(a):
        return np.clip((a - 1000.0) / 10000.0, 0.0001, 1.0)

    arrs = {
        "blue": to_refl(blue),
        "green": to_refl(green),
        "red": to_refl(red),
        "nir": to_refl(nir),
        "swir16": to_refl(swir16),
        "scl": scl,
    }
    return arrs, profile


def run_sentinel2_lulc():
    """Compute NDVI, NDWI, NDBI and 6-class LULC with accuracy assessment for Narowal AOI."""
    print("=== Step 2.1: Sentinel-2 Indices & 6-Class LULC ===")
    dry, prof = load_s2_scene("PC_2025_dry")
    mon, _ = load_s2_scene("PC_2025_monsoon")

    eps = 1e-6
    ndvi_dry = (dry["nir"] - dry["red"]) / (dry["nir"] + dry["red"] + eps)
    ndwi_dry = (dry["green"] - dry["nir"]) / (dry["green"] + dry["nir"] + eps)
    mndwi_dry = (dry["green"] - dry["swir16"]) / (dry["green"] + dry["swir16"] + eps)
    ndbi_dry = (dry["swir16"] - dry["nir"]) / (dry["swir16"] + dry["nir"] + eps)

    ndvi_mon = (mon["nir"] - mon["red"]) / (mon["nir"] + mon["red"] + eps)
    ndwi_mon = (mon["green"] - mon["nir"]) / (mon["green"] + mon["nir"] + eps)
    ndbi_mon = (mon["swir16"] - mon["nir"]) / (mon["swir16"] + mon["nir"] + eps)

    # Save spectral indices
    idx_prof = prof.copy()
    idx_prof.update({"dtype": "float32", "count": 1, "compress": "DEFLATE", "nodata": -9999.0})
    for name, arr in [
        ("S2_20250516_NDVI.tif", ndvi_dry),
        ("S2_20250516_NDWI.tif", ndwi_dry),
        ("S2_20250516_MNDWI.tif", mndwi_dry),
        ("S2_20250516_NDBI.tif", ndbi_dry),
        ("S2_20250923_NDVI.tif", ndvi_mon),
        ("S2_20250923_NDWI.tif", ndwi_mon),
    ]:
        with rasterio.open(os.path.join(LULC_DIR, name), "w", **idx_prof) as dst:
            dst.write(arr.astype(np.float32), 1)

    # Build rasterized training masks from independent authoritative layers:
    # 1=Built-up (MS Buildings), 2=Vegetation (Urban trees/parks), 3=Agricultural land (outside built-up core),
    # 4=Bare soil, 5=Water (JRC GSW / MNDWI>0.1)
    from rasterio.features import rasterize
    h, w = prof["height"], prof["width"]
    tr = prof["transform"]

    ms_bld = gpd.read_file(os.path.join(BASE_DIR, "Narowal_MS_Buildings_AOI.gpkg"), layer="ms_buildings_utm43n")
    ms_bld["geometry"] = ms_bld.geometry.make_valid()
    mc = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="mc_boundary_preliminary")
    bu = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="builtup_urban_boundary_preliminary")
    parks = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_parks_green_poly_raw")

    bld_mask = rasterize([(g, 1) for g in ms_bld.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    bu_mask = rasterize([(g, 1) for g in bu.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    mc_mask = rasterize([(g, 1) for g in mc.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    park_mask = rasterize([(g, 1) for g in parks.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)

    with rasterio.open(os.path.join(BASE_DIR, "JRC_GSW_occurrence_Narowal_AOI_UTM43N.tif")) as gsrc:
        gsw_10m = np.empty((h, w), dtype=np.float32)
        reproject(gsrc.read(1).astype(np.float32), gsw_10m, src_transform=gsrc.transform, src_crs=gsrc.crs, dst_transform=tr, dst_crs=prof["crs"], resampling=Resampling.nearest)

    # Feature stack (11 features across dry & monsoon phenology)
    feats = np.stack([
        dry["blue"], dry["green"], dry["red"], dry["nir"], dry["swir16"],
        ndvi_dry, ndwi_dry, ndbi_dry,
        ndvi_mon, ndwi_mon, ndbi_mon,
    ], axis=-1)

    # 1: Built-up (MS building footprints with low NDVI)
    # 2: Vegetation (high NDVI in dry OR monsoon inside urban/park areas)
    # 3: Agricultural land (strong crop phenology outside built-up urban boundary)
    # 4: Bare soil / vacant open earth (non-building, non-water, low NDVI in both seasons, non-roadway or open plots)
    # 5: Water (JRC GSW >= 25% or MNDWI > 0.05 & NDVI < 0.05)
    train_lbl = np.zeros((h, w), dtype=np.uint8)
    train_lbl[(bld_mask == 1) & (ndvi_dry < 0.28) & (ndvi_mon < 0.28)] = 1
    train_lbl[((park_mask == 1) & (ndvi_dry > 0.25)) | ((bu_mask == 1) & (bld_mask == 0) & (ndvi_dry > 0.35) & (ndvi_mon > 0.38))] = 2
    train_lbl[(bu_mask == 0) & (bld_mask == 0) & ((ndvi_mon > 0.45) | (ndvi_dry > 0.45)) & (gsw_10m < 5)] = 3
    train_lbl[(bld_mask == 0) & (ndvi_dry < 0.22) & (ndvi_mon < 0.25) & (ndbi_dry > -0.10) & (gsw_10m == 0) & (mndwi_dry < 0.0)] = 4
    train_lbl[(gsw_10m >= 20) | ((mndwi_dry > 0.05) & (ndvi_dry < 0.05))] = 5

    # Stratified sample (up to 2,500 px per class; 70% train / 30% validation)
    rng = np.random.default_rng(42)
    X_tr, y_tr, X_val, y_val = [], [], [], []
    for cls in [1, 2, 3, 4, 5]:
        ys, xs = np.where(train_lbl == cls)
        n_avail = len(ys)
        n_samp = min(2500, n_avail)
        if n_samp < 30:
            print(f"  Warning: class {cls} only {n_avail} samples")
        idx = rng.choice(n_avail, size=n_samp, replace=False)
        split = int(0.7 * n_samp)
        tr_i, val_i = idx[:split], idx[split:]
        X_tr.append(feats[ys[tr_i], xs[tr_i]])
        y_tr.append(np.full(len(tr_i), cls, dtype=np.uint8))
        X_val.append(feats[ys[val_i], xs[val_i]])
        y_val.append(np.full(len(val_i), cls, dtype=np.uint8))

    X_tr = np.vstack(X_tr)
    y_tr = np.concatenate(y_tr)
    X_val = np.vstack(X_val)
    y_val = np.concatenate(y_val)

    clf = RandomForestClassifier(n_estimators=120, max_depth=16, random_state=42, n_jobs=1)
    clf.fit(X_tr, y_tr)
    val_pred = clf.predict(X_val)
    oa = float(accuracy_score(y_val, val_pred))
    kappa = float(cohen_kappa_score(y_val, val_pred))
    cm = confusion_matrix(y_val, val_pred, labels=[1, 2, 3, 4, 5])
    print(f"  RF LULC Validation OA = {oa*100:.2f}%, Kappa = {kappa:.3f}")

    # Predict full AOI
    flat = feats.reshape(-1, feats.shape[-1])
    probs = clf.predict_proba(flat)
    max_p = probs.max(axis=1)
    pred = clf.classes_[probs.argmax(axis=1)].reshape(h, w).astype(np.uint8)
    # Assign class 6 (Other / Uncertain) where max class probability < 0.45 or SCL cloud/shadow (3,8,9,10)
    uncertain = (max_p.reshape(h, w) < 0.45) | np.isin(dry["scl"].astype(int), [3, 8, 9, 10])
    pred[uncertain] = 6
    # Enforce rule: do not label agricultural fields outside urban built-up area as urban vacant/bare or vice versa
    # Post-classification refinement: agricultural outside built-up remains class 3 if classified as 2 (urban veg)
    pred[(pred == 2) & (bu_mask == 0)] = 3
    # Keep MS building footprints firmly in Built-up (class 1) if probability wasn't water
    pred[(bld_mask == 1) & (pred != 5)] = 1

    lulc_tif = os.path.join(LULC_DIR, "Narowal_S2_LULC_6Class_UTM43N.tif")
    lulc_prof = prof.copy()
    lulc_prof.update({"dtype": "uint8", "count": 1, "compress": "DEFLATE", "nodata": 0})
    with rasterio.open(lulc_tif, "w", **lulc_prof) as dst:
        dst.write(pred, 1)

    # Calculate class areas inside mc_boundary_preliminary (10m px = 100 m2 = 0.0001 km2)
    class_names = {
        1: "Built-up",
        2: "Vegetation",
        3: "Agricultural land",
        4: "Bare soil",
        5: "Water",
        6: "Other / Uncertain",
    }
    mc_classes = pred[mc_mask == 1]
    lulc_stats = {}
    for k, cname in class_names.items():
        cnt = int((mc_classes == k).sum())
        area_km2 = round(cnt * 100.0 / 1e6, 4)
        area_ha = round(cnt * 100.0 / 1e4, 2)
        lulc_stats[cname] = {"pixels": cnt, "area_km2": area_km2, "area_ha": area_ha, "pct": round(100.0 * cnt / len(mc_classes), 2)}

    acc_report = {
        "overall_accuracy": round(oa, 4),
        "kappa": round(kappa, 4),
        "confusion_matrix_labels": [1, 2, 3, 4, 5],
        "confusion_matrix": cm.tolist(),
        "mc_boundary_lulc_area": lulc_stats,
    }
    with open(os.path.join(STATS_DIR, "lulc_accuracy_and_areas.json"), "w", encoding="utf-8") as f:
        json.dump(acc_report, f, indent=2)
    print("  LULC MC areas (km2):", {k: v["area_km2"] for k, v in lulc_stats.items()})
    return lulc_tif, lulc_stats, acc_report


def build_clean_walking_network():
    """Clean OSM road network and build planarized NetworkX pedestrian graph in EPSG:32643."""
    print("=== Step 2.2: Pedestrian Road Network Cleaning ===")
    roads = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_roads_raw")
    buf = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="study_buffer_1km")
    mc = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="mc_boundary_preliminary")

    # Exclude non-walkable / under-construction / private access segments
    excl_hw = {"motorway", "motorway_link", "construction", "proposed"}
    walk = roads[~roads["highway"].isin(excl_hw)].copy()
    walk = walk[~walk["foot"].isin(["no", "private"])].copy()
    walk = walk[~walk["access"].isin(["private", "no"])].copy()

    # Clip to 1 km buffer + 500 m margin to preserve perimeter routes
    clip_poly = buf.geometry.buffer(500.0).union_all()
    walk = gpd.clip(walk, clip_poly)
    walk = walk[walk.geometry.length > 0.5].copy()

    # Node / planarize all intersections via unary_union of MultiLineString segments
    all_lines = []
    for geom in walk.geometry:
        if geom.geom_type == "LineString":
            all_lines.append(geom)
        elif geom.geom_type == "MultiLineString":
            all_lines.extend(list(geom.geoms))
    noded = unary_union(all_lines)
    segs = list(noded.geoms) if hasattr(noded, "geoms") else [noded]
    segs = [s for s in segs if s.geom_type == "LineString" and s.length > 0.2]

    # Build graph and snap dangling nodes <= 8 m to nearest node/edge to fix minor OSM digitization gaps
    G = nx.Graph()
    for idx, seg in enumerate(segs):
        coords = list(seg.coords)
        u = (round(coords[0][0], 1), round(coords[0][1], 1))
        v = (round(coords[-1][0], 1), round(coords[-1][1], 1))
        if u == v:
            continue
        length = float(seg.length)
        G.add_edge(u, v, length_m=length, walk_min=length / (WALK_SPEED_KMH * 1000.0 / 60.0), geometry=seg, edge_id=idx)

    # Snap degree-1 endpoints to nearby nodes within 8 m if disconnected
    deg1 = [n for n, d in G.degree() if d == 1]
    all_nodes = list(G.nodes())
    if all_nodes:
        coords_arr = np.array(all_nodes)
        snapped_edges = 0
        for n in deg1:
            dists = np.linalg.norm(coords_arr - np.array(n), axis=1)
            order = np.argsort(dists)
            for idx_cand in order[1:6]:
                if dists[idx_cand] <= 8.0:
                    nbr = all_nodes[idx_cand]
                    if not G.has_edge(n, nbr):
                        # Only snap if in different components or endpoint gap
                        if not nx.has_path(G, n, nbr):
                            seg = LineString([n, nbr])
                            d_m = float(dists[idx_cand])
                            G.add_edge(n, nbr, length_m=d_m, walk_min=d_m / (WALK_SPEED_KMH * 1000.0 / 60.0), geometry=seg, edge_id=999000 + snapped_edges)
                            snapped_edges += 1
                            break
        print(f"  Snapped {snapped_edges} disconnected OSM gaps (<= 8 m)")

    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    main_nodes = comps[0]
    G_main = G.subgraph(main_nodes).copy()
    print(f"  Noded network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(comps)} components; Main component = {len(main_nodes)} nodes ({G_main.number_of_edges()} edges)")

    # Save cleaned edge GeoDataFrame
    edge_rows = []
    for u, v, data in G_main.edges(data=True):
        edge_rows.append({"u": str(u), "v": str(v), "length_m": round(data["length_m"], 2), "walk_min": round(data["walk_min"], 3), "geometry": data["geometry"]})
    edges_gdf = gpd.GeoDataFrame(edge_rows, crs="EPSG:32643")
    edges_gdf.to_file(os.path.join(ACC_DIR, "Narowal_Walk_Network_Clean_UTM43N.gpkg"), layer="walk_network_edges", driver="GPKG")

    # Compute total street length inside preliminary MC boundary
    mc_poly = mc.geometry.union_all()
    edges_mc = gpd.clip(edges_gdf, mc_poly)
    total_mc_km = float(edges_mc.geometry.length.sum()) / 1000.0
    print(f"  Total walkable street length inside MC boundary: {total_mc_km:.2f} km")
    return G_main, edges_gdf, edges_mc


def define_park_entrances(G, parks):
    """Define explicit park entrance points (inferred frontage access points, NOT all boundary vertices)."""
    print("=== Step 2.3: Defining Park Entrance Points ===")
    # Extract boundary points of park polygons and select 1-2 closest road-network nodes on frontage sides
    net_nodes = list(G.nodes())
    net_pts = [Point(xy) for xy in net_nodes]
    net_gdf = gpd.GeoDataFrame({"node_xy": net_nodes, "geometry": net_pts}, crs="EPSG:32643")

    entrances = []
    for _, pk in parks.iterrows():
        oid = pk["osm_id"]
        pname = pk["name"] or f"Unnamed_{pk['leisure']}_{oid}"
        area_ac = float(pk.geometry.area) / 4046.8564
        # Determine category
        is_formal_park = (pk["leisure"] == "park")
        is_10ac_plus = area_ac >= 10.0

        # Find nearest network node to north/frontage side AND overall nearest network node
        poly = pk.geometry
        b_ring = poly.boundary
        # Compute distance from every network node to park boundary
        dists = net_gdf.geometry.distance(b_ring)
        close_idx = dists.nsmallest(12).index

        # Pick 1 primary entrance (closest road node) + up to 1 secondary entrance >= 120 m away on another side (if within 60 m of park)
        chosen = []
        for idx in close_idx:
            cand_pt = net_gdf.loc[idx, "geometry"]
            d_val = float(dists.loc[idx])
            if not chosen:
                chosen.append((net_gdf.loc[idx, "node_xy"], cand_pt, d_val))
            elif d_val <= 60.0 and all(cand_pt.distance(c[1]) >= 120.0 for c in chosen):
                chosen.append((net_gdf.loc[idx, "node_xy"], cand_pt, d_val))
            if len(chosen) >= 2:
                break

        for e_i, (nxy, pt, d_val) in enumerate(chosen, 1):
            entrances.append({
                "park_osm_id": oid,
                "park_name": pname,
                "leisure": pk["leisure"],
                "area_ha": round(float(pk.geometry.area) / 1e4, 2),
                "area_acres": round(area_ac, 2),
                "is_formal_park": is_formal_park,
                "is_10ac_plus": is_10ac_plus,
                "entrance_id": f"{oid}_E{e_i}",
                "node_x": nxy[0],
                "node_y": nxy[1],
                "snap_dist_m": round(d_val, 1),
                "verification_status": "Inferred Frontage Entrance - Field Verification Required",
                "geometry": pt,
            })

    ent_gdf = gpd.GeoDataFrame(entrances, crs="EPSG:32643")
    ent_gdf.to_file(os.path.join(ACC_DIR, "Narowal_Park_Entrances_Preliminary_UTM43N.gpkg"), layer="park_entrances", driver="GPKG")
    print(ent_gdf[["park_name", "leisure", "area_acres", "entrance_id", "snap_dist_m"]].to_string())
    return ent_gdf


def compute_service_area(G, edges_gdf, mc_poly, ms_bld, ghsl_tif, entrance_nodes, tag):
    """Run multi-source Dijkstra (<=800 m) and compute street, building, and GHSL population metrics inside MC."""
    if not entrance_nodes:
        mc_bld = gpd.clip(ms_bld, mc_poly)
        edges_mc = gpd.clip(edges_gdf, mc_poly)
        tot_len_km = float(edges_mc.geometry.length.sum()) / 1000.0
        with rasterio.open(ghsl_tif) as src:
            out_arr, _ = mask(src, [mc_poly], crop=True, filled=True, nodata=0)
            tot_pop = float(out_arr[out_arr > 0].sum())
        return {
            "category": tag,
            "total_street_km": round(tot_len_km, 2),
            "accessible_street_km": 0.0,
            "inaccessible_street_km": round(tot_len_km, 2),
            "pct_street_accessible": 0.0,
            "pct_street_inaccessible": 100.0,
            "total_pop_ghsl2025": round(tot_pop),
            "pop_within_10min": 0,
            "pop_outside_10min": round(tot_pop),
            "pct_pop_accessible": 0.0,
            "total_buildings_mc": int(len(mc_bld)),
            "buildings_within_10min": 0,
            "buildings_outside_10min": int(len(mc_bld)),
            "pct_buildings_accessible": 0.0,
        }, None, edges_mc.assign(dist_m=9999.0, accessible=False)

    lengths = nx.multi_source_dijkstra_path_length(G, entrance_nodes, cutoff=THRESHOLD_M, weight="length_m")
    # Also compute full nearest distance (without cutoff) for continuous deficit mapping
    all_dists = nx.multi_source_dijkstra_path_length(G, entrance_nodes, weight="length_m")

    # Classify each edge inside MC boundary
    edges_mc = gpd.clip(edges_gdf, mc_poly).copy()
    acc_flags, dist_vals = [], []
    for _, row in edges_mc.iterrows():
        u = eval(row["u"])
        v = eval(row["v"])
        du = all_dists.get(u, 99999.0)
        dv = all_dists.get(v, 99999.0)
        dmin = min(du, dv) + row["length_m"] * 0.5
        dist_vals.append(round(dmin, 1))
        acc_flags.append((u in lengths) or (v in lengths))
    edges_mc["dist_m"] = dist_vals
    edges_mc["walk_min"] = (edges_mc["dist_m"] / (WALK_SPEED_KMH * 1000.0 / 60.0)).round(2)
    edges_mc["accessible_10min"] = acc_flags

    # Also build network-based service-area polygon from accessible edges across full network (buffered 60m to cover fronting lots)
    acc_edges_all = []
    for _, row in edges_gdf.iterrows():
        u = eval(row["u"])
        v = eval(row["v"])
        if (u in lengths) or (v in lengths):
            acc_edges_all.append(row.geometry)
    sa_poly = unary_union([g.buffer(60.0) for g in acc_edges_all]) if acc_edges_all else None

    tot_len_km = float(edges_mc.geometry.length.sum()) / 1000.0
    acc_len_km = float(edges_mc[edges_mc["accessible_10min"]].geometry.length.sum()) / 1000.0
    inacc_len_km = tot_len_km - acc_len_km

    # Buildings inside MC
    mc_bld = gpd.clip(ms_bld, mc_poly).copy()
    mc_bld_pts = mc_bld.geometry.centroid
    if sa_poly is not None:
        bld_in = mc_bld_pts.within(sa_poly)
        n_bld_in = int(bld_in.sum())
    else:
        n_bld_in = 0
    n_bld_tot = int(len(mc_bld))

    # GHSL 2025 population inside MC vs within service area
    with rasterio.open(ghsl_tif) as src:
        mc_arr, _ = mask(src, [mc_poly], crop=True, filled=True, nodata=0)
        tot_pop = float(mc_arr[mc_arr > 0].sum())
        if sa_poly is not None:
            inter = mc_poly.intersection(sa_poly)
            if not inter.is_empty:
                sa_arr, _ = mask(src, [inter], crop=True, filled=True, nodata=0)
                pop_in = float(sa_arr[sa_arr > 0].sum())
            else:
                pop_in = 0.0
        else:
            pop_in = 0.0
    pop_in = min(pop_in, tot_pop)
    pop_out = tot_pop - pop_in

    stats = {
        "category": tag,
        "total_street_km": round(tot_len_km, 2),
        "accessible_street_km": round(acc_len_km, 2),
        "inaccessible_street_km": round(inacc_len_km, 2),
        "pct_street_accessible": round(100.0 * acc_len_km / tot_len_km, 2) if tot_len_km else 0.0,
        "pct_street_inaccessible": round(100.0 * inacc_len_km / tot_len_km, 2) if tot_len_km else 100.0,
        "total_pop_ghsl2025": round(tot_pop),
        "pop_within_10min": round(pop_in),
        "pop_outside_10min": round(pop_out),
        "pct_pop_accessible": round(100.0 * pop_in / tot_pop, 2) if tot_pop else 0.0,
        "total_buildings_mc": n_bld_tot,
        "buildings_within_10min": n_bld_in,
        "buildings_outside_10min": n_bld_tot - n_bld_in,
        "pct_buildings_accessible": round(100.0 * n_bld_in / n_bld_tot, 2) if n_bld_tot else 0.0,
    }
    return stats, sa_poly, edges_mc


def produce_maps_01_02_03(mc, bu, buf, roads, parks, waterways, waterbodies, fac_poly, uu_assets, ms_bld, ghsl_tif, lulc_tif, ent_gdf, sa_all, sa_formal, edges_all, edges_formal, acc_stats):
    """Generate cartographic MAP 01, MAP 02, and MAP 03 in PDF and 300 DPI PNG."""
    print("=== Step 2.4: Producing MAP 01, MAP 02, MAP 03 ===")
    view_b = buf.total_bounds
    mc_b = mc.total_bounds
    pad_mc = (mc_b[0] - 400, mc_b[1] - 400, mc_b[2] + 400, mc_b[3] + 400)

    # ---------------------------------------------------------
    # MAP 01: Narowal Urban Baseline Map
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    with rasterio.open(lulc_tif) as src:
        lulc_arr = src.read(1)
        ext = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
    # 1=Built-up(#9E9E9E), 2=Vegetation(#2E7D32), 3=Agri(#D7E4C0), 4=Bare(#E6D3A7), 5=Water(#1976D2), 6=Other(#ECEFF1)
    cmap_lulc = ListedColormap(["#9E9E9E", "#2E7D32", "#DCE8C6", "#E5D3A6", "#1976D2", "#ECEFF1"])
    norm_lulc = BoundaryNorm([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5], cmap_lulc.N)
    ax.imshow(lulc_arr, extent=ext, cmap=cmap_lulc, norm=norm_lulc, alpha=0.65, interpolation="nearest", zorder=1)

    roads.plot(ax=ax, color="#555555", linewidth=0.55, alpha=0.8, zorder=3)
    waterways.plot(ax=ax, color="#1565C0", linewidth=1.4, zorder=4)
    waterbodies.plot(ax=ax, color="#1565C0", alpha=0.85, zorder=4)
    fac_poly.plot(ax=ax, facecolor="#F57C00", edgecolor="#BF360C", linewidth=0.8, alpha=0.55, zorder=5)
    parks.plot(ax=ax, facecolor="#1B5E20", edgecolor="#0A3D0A", linewidth=1.3, alpha=0.9, zorder=6)
    bu.boundary.plot(ax=ax, color="#424242", linewidth=1.2, linestyle="--", zorder=7)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=8)
    buf.boundary.plot(ax=ax, color="#757575", linewidth=1.1, linestyle=":", zorder=8)
    uu_assets.plot(ax=ax, color="#6A1B9A", marker="^", markersize=55, edgecolor="white", linewidth=0.7, zorder=9)

    # Annotate key landmarks
    for _, r in uu_assets[uu_assets["asset_id"].isin(["UU_PARK_01", "UU_PARK_02", "UU_DISP_01", "UU_DISP_02"])].iterrows():
        lbl = r["name"].replace("Proposed Public Park - ", "Prop. Park: ").replace(" Disposal Station", " Disp.")
        ax.annotate(lbl, (r.geometry.x, r.geometry.y), xytext=(6, 6), textcoords="offset points",
                    fontsize=7, fontweight="bold", color="#1A1A1A",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#999999", alpha=0.85), zorder=12)

    handles = [
        mpatches.Patch(facecolor="#9E9E9E", alpha=0.65, label="Built-up (S2 LULC + MS Buildings)"),
        mpatches.Patch(facecolor="#2E7D32", alpha=0.65, label="Urban Vegetation"),
        mpatches.Patch(facecolor="#DCE8C6", alpha=0.65, label="Agricultural Land (Peri-urban)"),
        mpatches.Patch(facecolor="#E5D3A6", alpha=0.65, label="Bare Soil / Open Ground"),
        mpatches.Patch(facecolor="#1B5E20", edgecolor="#0A3D0A", label="Mapped Parks & Sports Grounds"),
        mpatches.Patch(facecolor="#F57C00", alpha=0.55, label="Major Public Facilities"),
        mlines.Line2D([], [], color="#1565C0", linewidth=1.6, label="Mapped Waterways"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary (24.91 km²)"),
        mlines.Line2D([], [], color="#424242", linewidth=1.2, linestyle="--", label="Built-Up Urban Extent (17.84 km²)"),
        mlines.Line2D([], [], color="#757575", linewidth=1.1, linestyle=":", label="1 km External Study Buffer"),
        mlines.Line2D([], [], color="#6A1B9A", marker="^", linestyle="None", markersize=7, label="Urban Unit 2021 Key Assets"),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.92, title="Legend", title_fontsize=8.5)
    add_cartographic_frame(
        ax, view_b,
        "MAP 01: Narowal City Urban Baseline & Land Cover (2025/2026)",
        "Preliminary Municipal Boundary (Urban Unit 2021), Built-Up Core, Parks, Waterways & Sentinel-2 LULC",
        "Urban Unit Master Plan (2021), Sentinel-2 L2A (2025-05-16/09-23), OSM (2026), Microsoft ML Buildings (2026-02)"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_01, f"MAP_01_Narowal_Urban_Baseline.{ext_f}"), dpi=300)
    plt.close(fig)

    # ---------------------------------------------------------
    # MAP 02: Ten-Minute Park Accessibility (Street Network)
    # ---------------------------------------------------------
    s_all = [x for x in acc_stats if x["category"] == "All_Mapped_Parks_And_Sports"][0]
    s_frm = [x for x in acc_stats if x["category"] == "Formal_Public_Parks_Only"][0]

    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    ms_bld.plot(ax=ax, facecolor="#E0E0E0", edgecolor="none", alpha=0.75, zorder=1)
    if sa_all is not None:
        gpd.GeoDataFrame(geometry=[sa_all], crs="EPSG:32643").plot(ax=ax, facecolor="#C8E6C9", edgecolor="#388E3C", linewidth=0.9, alpha=0.5, zorder=2)
    if sa_formal is not None:
        gpd.GeoDataFrame(geometry=[sa_formal], crs="EPSG:32643").plot(ax=ax, facecolor="#81C784", edgecolor="#1B5E20", linewidth=1.1, alpha=0.55, zorder=3)

    edges_all[~edges_all["accessible_10min"]].plot(ax=ax, color="#9E1B32", linewidth=0.75, alpha=0.85, zorder=4)
    edges_all[edges_all["accessible_10min"]].plot(ax=ax, color="#1B5E20", linewidth=1.25, alpha=0.95, zorder=5)
    parks.plot(ax=ax, facecolor="#0D4F14", edgecolor="#002904", linewidth=1.4, zorder=6)
    ent_gdf.plot(ax=ax, color="#FFD600", edgecolor="#111111", marker="o", markersize=42, zorder=7)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=8)

    # Label parks & summary box
    info_txt = (
        f"Network Threshold: 10 min (800 m @ 4.8 km/h)\n"
        f"MC Street Length: {s_all['total_street_km']:.1f} km\n"
        f"• All Parks + Sports Complex: {s_all['pct_street_accessible']:.1f}% accessible ({s_all['accessible_street_km']:.1f} km)\n"
        f"• Formal Public Park Only (Faiz Park): {s_frm['pct_street_accessible']:.1f}% accessible ({s_frm['accessible_street_km']:.1f} km)\n"
        f"• Formal Parks >= 10 Acres: 0.0% (none mapped)"
    )
    ax.text(0.02, 0.97, info_txt, transform=ax.transAxes, va="top", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="#333333", alpha=0.93), zorder=15)

    handles2 = [
        mlines.Line2D([], [], color="#1B5E20", linewidth=2.0, label="Streets <= 10-Min Walk (800 m)"),
        mlines.Line2D([], [], color="#9E1B32", linewidth=1.6, label="Streets > 10-Min Walk (Underserved)"),
        mpatches.Patch(facecolor="#81C784", edgecolor="#1B5E20", alpha=0.65, label="10-Min Service Area: Faiz Ahmad Faiz Park"),
        mpatches.Patch(facecolor="#C8E6C9", edgecolor="#388E3C", alpha=0.65, label="10-Min Service Area: Narowal Sports Complex (Access TBD)"),
        mpatches.Patch(facecolor="#0D4F14", label="Mapped Parks / Sports Centre"),
        mlines.Line2D([], [], color="#FFD600", marker="o", markeredgecolor="#111111", linestyle="None", markersize=7, label="Inferred Park Entrances (Verify in Field)"),
        mpatches.Patch(facecolor="#E0E0E0", label="Building Footprints (MS Buildings)"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles2, loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.92, title="Legend", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 02: Ten-Minute Pedestrian Park Accessibility (Network Analysis)",
        "Street-Network Service Areas (800 m @ 4.8 km/h) from Inferred Park Entrances",
        "OSM Road Network (cleaned topology), OSM Parks, Microsoft ML Buildings (2026-02), Urban Unit MC Boundary (2021)"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_02, f"MAP_02_Ten_Minute_Park_Accessibility.{ext_f}"), dpi=300)
    plt.close(fig)

    # ---------------------------------------------------------
    # MAP 03: Population-Based Park Accessibility (GHSL 2025)
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    with rasterio.open(ghsl_tif) as src:
        pop_arr, pop_tr = mask(src, [mc.geometry.union_all()], crop=True, filled=True, nodata=-200)
        pop_arr = np.where(pop_arr[0] > 0, pop_arr[0], np.nan)
        from rasterio.transform import array_bounds
        pb = array_bounds(pop_arr.shape[0], pop_arr.shape[1], pop_tr)
        pop_ext = [pb[0], pb[2], pb[1], pb[3]]

    im = ax.imshow(pop_arr, extent=pop_ext, cmap="YlOrRd", vmin=0, vmax=250, alpha=0.85, interpolation="nearest", zorder=2)
    cbar = fig.colorbar(im, ax=ax, shrink=0.55, pad=0.02)
    cbar.set_label("GHSL 2025 Modelled Population (people / 100 m cell)", fontsize=8)

    if sa_all is not None:
        gpd.GeoDataFrame(geometry=[sa_all], crs="EPSG:32643").boundary.plot(ax=ax, color="#1B5E20", linewidth=2.0, linestyle="-", zorder=5)
    if sa_formal is not None:
        gpd.GeoDataFrame(geometry=[sa_formal], crs="EPSG:32643").boundary.plot(ax=ax, color="#004D40", linewidth=2.2, linestyle="--", zorder=6)
    parks.plot(ax=ax, facecolor="#1B5E20", edgecolor="white", linewidth=1.2, zorder=7)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=8)

    pop_txt = (
        f"GHSL 2025 Modelled Pop. inside MC: {s_all['total_pop_ghsl2025']:,}*\n"
        f"(Urban Unit 2025 Projection: 132,194)\n"
        f"• Within 10-Min (All Parks + Sports): {s_all['pct_pop_accessible']:.1f}% ({s_all['pop_within_10min']:,})\n"
        f"• Within 10-Min (Faiz Park Only): {s_frm['pct_pop_accessible']:.1f}% ({s_frm['pop_within_10min']:,})\n"
        f"• Underserved Pop. (outside Faiz Park): {s_frm['pop_outside_10min']:,} ({100 - s_frm['pct_pop_accessible']:.1f}%)\n"
        f"*Gridded disaggregation estimate, not municipal census."
    )
    ax.text(0.02, 0.97, pop_txt, transform=ax.transAxes, va="top", fontsize=7.8,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="#333333", alpha=0.93), zorder=15)

    handles3 = [
        mlines.Line2D([], [], color="#004D40", linewidth=2.2, linestyle="--", label="10-Min Boundary: Faiz Park Only"),
        mlines.Line2D([], [], color="#1B5E20", linewidth=2.0, label="10-Min Boundary: All Parks + Sports Complex"),
        mpatches.Patch(facecolor="#1B5E20", edgecolor="white", label="Mapped Parks / Sports Complex"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles3, loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.92, title="Legend", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 03: Population-Based Ten-Minute Park Accessibility (GHSL 2025)",
        "Underserved High-Density Residential Zones Beyond 800 m Walking Network Threshold",
        "JRC GHSL GHS-POP R2023A (Epoch 2025, 100 m), OSM Network, Urban Unit MC Boundary (2021)"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_02, f"MAP_03_Population_Based_Park_Accessibility.{ext_f}"), dpi=300)
    plt.close(fig)
    print("  Saved MAP 01, MAP 02, MAP 03 (PNG + PDF)")


def main():
    lulc_tif, lulc_stats, acc_report = run_sentinel2_lulc()

    mc = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="mc_boundary_preliminary")
    bu = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="builtup_urban_boundary_preliminary")
    buf = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="study_buffer_1km")
    roads = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_roads_raw")
    parks = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_parks_green_poly_raw")
    waterways = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_waterways_raw")
    waterbodies = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_waterbodies_raw")
    fac_poly = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_facilities_poly_raw")
    places = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_places_pts_raw")
    ms_bld = gpd.read_file(os.path.join(BASE_DIR, "Narowal_MS_Buildings_AOI.gpkg"), layer="ms_buildings_utm43n")
    ms_bld["geometry"] = ms_bld.geometry.make_valid()
    uu_assets = gpd.read_file(os.path.join(BASE_DIR, "Narowal_UrbanUnit_2021_Assets_UTM43N.gpkg"), layer="uu2021_key_assets_preliminary")
    ghsl_tif = os.path.join(BASE_DIR, "GHSL_POP_E2025_Narowal_AOI_UTM43N.tif")

    G_main, edges_gdf, edges_mc = build_clean_walking_network()
    ent_gdf = define_park_entrances(G_main, parks)
    mc_poly = mc.geometry.union_all()

    # Category A (All mapped parks + sports complex), Category A-strict (Faiz Park only), Category B (>=10 ac), Category C (<10 ac)
    ent_all = [(r["node_x"], r["node_y"]) for _, r in ent_gdf[ent_gdf["leisure"].isin(["park", "sports_centre"])].iterrows()]
    ent_formal = [(r["node_x"], r["node_y"]) for _, r in ent_gdf[ent_gdf["is_formal_park"]].iterrows()]
    ent_10ac_sports = [(r["node_x"], r["node_y"]) for _, r in ent_gdf[ent_gdf["is_10ac_plus"]].iterrows()]
    ent_small = [(r["node_x"], r["node_y"]) for _, r in ent_gdf[~ent_gdf["is_10ac_plus"]].iterrows()]

    s_all, sa_all, edges_all = compute_service_area(G_main, edges_gdf, mc_poly, ms_bld, ghsl_tif, ent_all, "All_Mapped_Parks_And_Sports")
    s_frm, sa_frm, edges_frm = compute_service_area(G_main, edges_gdf, mc_poly, ms_bld, ghsl_tif, ent_formal, "Formal_Public_Parks_Only")
    s_10ac_s, sa_10ac_s, _ = compute_service_area(G_main, edges_gdf, mc_poly, ms_bld, ghsl_tif, ent_10ac_sports, "Parks_10Ac_Plus_Incl_SportsComplex")
    s_10ac_f, _, _ = compute_service_area(G_main, edges_gdf, mc_poly, ms_bld, ghsl_tif, [], "Formal_Parks_10Ac_Plus_None")
    s_small, sa_small, _ = compute_service_area(G_main, edges_gdf, mc_poly, ms_bld, ghsl_tif, ent_small, "Small_Neighbourhood_Parks_Under10Ac")

    acc_stats = [s_all, s_frm, s_10ac_s, s_10ac_f, s_small]
    df_acc = pd.DataFrame(acc_stats)
    df_acc.to_csv(os.path.join(STATS_DIR, "phase2_park_accessibility_summary.csv"), index=False)
    print("\n=== Phase 2 Accessibility Summary ===")
    print(df_acc.to_string(index=False))

    # Save service-area polygons & street accessibility layers (UTM43N + WGS84 for web app)
    sa_rows = []
    for tag, geom in [("All_Parks_And_Sports", sa_all), ("Formal_Public_Park_Only", sa_frm)]:
        if geom is not None:
            sa_rows.append({"category": tag, "area_km2": round(geom.area / 1e6, 3), "geometry": geom})
    sa_gdf = gpd.GeoDataFrame(sa_rows, crs="EPSG:32643")
    sa_gpkg = os.path.join(ACC_DIR, "Narowal_Park_Accessibility_UTM43N.gpkg")
    sa_gdf.to_file(sa_gpkg, layer="service_areas_10min", driver="GPKG")
    edges_all.to_file(sa_gpkg, layer="streets_accessibility_all", driver="GPKG")
    edges_frm.to_file(sa_gpkg, layer="streets_accessibility_formal", driver="GPKG")

    # Identify worst-deficit 300m grid cells (high GHSL pop + >800 m from formal park)
    from shapely.geometry import box
    minx, miny, maxx, maxy = mc_poly.bounds
    cells = []
    step = 300.0
    for x in np.arange(minx, maxx, step):
        for y in np.arange(miny, maxy, step):
            b = box(x, y, x + step, y + step).intersection(mc_poly)
            if not b.is_empty and b.area > 10000:
                cells.append(b)
    grid_gdf = gpd.GeoDataFrame({"cell_id": range(1, len(cells) + 1), "geometry": cells}, crs="EPSG:32643")
    with rasterio.open(ghsl_tif) as src:
        pops, bld_cnts, out_10m = [], [], []
        mc_bld_c = gpd.clip(ms_bld, mc_poly).copy()
        mc_bld_c["centroid"] = mc_bld_c.geometry.centroid
        for _, cg in grid_gdf.iterrows():
            arr, _ = mask(src, [cg.geometry], crop=True, filled=True, nodata=0)
            pops.append(round(float(arr[arr > 0].sum())))
            in_cell = mc_bld_c[mc_bld_c["centroid"].within(cg.geometry)]
            bld_cnts.append(int(len(in_cell)))
            if sa_frm is not None:
                uncov = cg.geometry.difference(sa_frm).area / cg.geometry.area
            else:
                uncov = 1.0
            out_10m.append(round(uncov * 100.0, 1))
    grid_gdf["ghsl_pop_2025"] = pops
    grid_gdf["ms_buildings"] = bld_cnts
    grid_gdf["pct_outside_formal_park_10min"] = out_10m
    grid_gdf["deficit_pop_score"] = (grid_gdf["ghsl_pop_2025"] * grid_gdf["pct_outside_formal_park_10min"] / 100.0).round(0)
    grid_gdf.to_file(sa_gpkg, layer="accessibility_deficit_grid_300m", driver="GPKG")
    top_def = grid_gdf.sort_values("deficit_pop_score", ascending=False).head(10)
    top_def.drop(columns=["geometry"]).to_csv(os.path.join(STATS_DIR, "top10_accessibility_deficit_cells.csv"), index=False)

    # Urban Baseline Metrics Table
    mc_bld_count = int(len(gpd.clip(ms_bld, mc_poly)))
    mc_bld_area_km2 = round(float(gpd.clip(ms_bld, mc_poly).geometry.area.sum()) / 1e6, 4)
    faiz_ha = round(float(parks[parks["leisure"] == "park"].geometry.area.sum()) / 1e4, 2)
    tot_green_ha = round(float(parks.geometry.area.sum()) / 1e4, 2)
    baseline = {
        "mc_area_km2": round(mc_poly.area / 1e6, 3),
        "builtup_footprint_cluster_km2": round(float(bu.geometry.area.sum()) / 1e6, 3),
        "ms_buildings_count_mc": mc_bld_count,
        "ms_buildings_roof_area_km2": mc_bld_area_km2,
        "lulc_builtup_km2": lulc_stats["Built-up"]["area_km2"],
        "lulc_vegetation_km2": lulc_stats["Vegetation"]["area_km2"],
        "lulc_agriculture_km2": lulc_stats["Agricultural land"]["area_km2"],
        "lulc_bare_soil_km2": lulc_stats["Bare soil"]["area_km2"],
        "formal_park_count": 1,
        "formal_park_area_ha": faiz_ha,
        "all_mapped_leisure_polygons_count": int(len(parks)),
        "all_mapped_leisure_area_ha": tot_green_ha,
        "walkable_street_length_mc_km": s_all["total_street_km"],
        "ghsl_2025_pop_mc": s_all["total_pop_ghsl2025"],
        "urban_unit_2025_pop_projection": 132194,
        "formal_park_m2_per_capita_uu2025": round((faiz_ha * 10000.0) / 132194.0, 2),
        "formal_park_m2_per_capita_ghsl2025": round((faiz_ha * 10000.0) / s_all["total_pop_ghsl2025"], 2),
        "who_min_standard_m2_per_capita": 9.0,
    }
    with open(os.path.join(STATS_DIR, "phase2_urban_baseline_summary.json"), "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)
    print("Baseline summary:", json.dumps(baseline, indent=2))

    # Load Phase 2 layers into FileGDB
    for gpkg_p, lyr, gdb_fc in [
        (os.path.join(ACC_DIR, "Narowal_Walk_Network_Clean_UTM43N.gpkg"), "walk_network_edges", "p2_walk_network_clean"),
        (os.path.join(ACC_DIR, "Narowal_Park_Entrances_Preliminary_UTM43N.gpkg"), "park_entrances", "p2_park_entrances_preliminary"),
        (sa_gpkg, "service_areas_10min", "p2_service_areas_10min"),
        (sa_gpkg, "streets_accessibility_all", "p2_streets_accessibility_all"),
        (sa_gpkg, "streets_accessibility_formal", "p2_streets_accessibility_formal"),
        (sa_gpkg, "accessibility_deficit_grid_300m", "p2_accessibility_deficit_grid_300m"),
    ]:
        tmp_shp = os.path.join(ACC_DIR, f"_tmp_{gdb_fc}.shp")
        gpd.read_file(gpkg_p, layer=lyr).to_file(tmp_shp)
        arcpy.conversion.ExportFeatures(tmp_shp, os.path.join(GDB, gdb_fc))
        for ext_rm in [".shp", ".dbf", ".shx", ".prj", ".cpg"]:
            p_rm = tmp_shp.replace(".shp", ext_rm)
            if os.path.exists(p_rm):
                os.remove(p_rm)
    arcpy.management.CopyRaster(lulc_tif, os.path.join(GDB, "S2_2025_LULC_6Class_UTM43N"))
    print("Loaded Phase 2 layers into FileGDB.")

    produce_maps_01_02_03(mc, bu, buf, roads, parks, waterways, waterbodies, fac_poly, uu_assets, ms_bld, ghsl_tif, lulc_tif, ent_gdf, sa_all, sa_frm, edges_all, edges_frm, acc_stats)


if __name__ == "__main__":
    main()
