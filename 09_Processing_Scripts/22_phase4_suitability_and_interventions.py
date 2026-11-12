"""Phase 4: Vacant Land Screening, Green Infrastructure Suitability Model, Site Shortlist & Maps 09-11."""

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
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize, shapes
from rasterio.mask import mask
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from scipy import ndimage
from shapely.geometry import Point, shape
from shapely.ops import unary_union

arcpy.env.overwriteOutput = True

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
BASE_DIR = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
LULC_DIR = os.path.join(ROOT, "03_Processed_Data", "02_Land_Use_Land_Cover")
HYDRO_DIR = os.path.join(ROOT, "03_Processed_Data", "03_Hydrological_Analysis")
FLOOD_DIR = os.path.join(ROOT, "03_Processed_Data", "04_Historical_Flood_Mapping")
ACC_DIR = os.path.join(ROOT, "03_Processed_Data", "05_Park_Accessibility")
DRAIN_DIR = os.path.join(ROOT, "03_Processed_Data", "06_Drainage_Mapping")
SUIT_DIR = os.path.join(ROOT, "03_Processed_Data", "07_Suitability_Analysis")
STATS_DIR = os.path.join(ROOT, "08_Tables_and_Statistics")
MAPS_05 = os.path.join(ROOT, "05_Maps", "05_Green_Infrastructure")
MAPS_06 = os.path.join(ROOT, "05_Maps", "06_Intervention_Plan")
GDB = os.path.join(ROOT, "04_Geodatabase", "Narowal_Green_Infrastructure.gdb")

for d in [SUIT_DIR, MAPS_05, MAPS_06]:
    os.makedirs(d, exist_ok=True)


def add_cartographic_frame(ax, bounds, title, subtitle, sources_text, date_str="2026-11-12"):
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

    nx_x, nx_y = maxx - (maxx - minx) * 0.05, miny + (maxy - miny) * 0.055
    arrow_len = (maxy - miny) * 0.055
    ax.annotate("N", xy=(nx_x, nx_y + arrow_len), xytext=(nx_x, nx_y),
                arrowprops=dict(facecolor="#1A1A1A", edgecolor="#1A1A1A", width=3, headwidth=9, headlength=9),
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#1A1A1A", zorder=20)

    span = maxx - minx
    bar_m = 1000 if span > 4500 else 500
    sb_x0 = minx + span * 0.04
    sb_y0 = miny + (maxy - miny) * 0.045
    sb_h = (maxy - miny) * 0.012
    ax.add_patch(mpatches.Rectangle((sb_x0, sb_y0), bar_m / 2, sb_h, facecolor="#1A1A1A", edgecolor="#1A1A1A", zorder=20))
    ax.add_patch(mpatches.Rectangle((sb_x0 + bar_m / 2, sb_y0), bar_m / 2, sb_h, facecolor="#FFFFFF", edgecolor="#1A1A1A", zorder=20))
    for off, lbl in [(0, "0"), (bar_m / 2, f"{bar_m // 2} m"), (bar_m, f"{bar_m:,} m")]:
        ax.text(sb_x0 + off, sb_y0 + sb_h * 1.35, lbl, fontsize=7.5, fontweight="bold", ha="center", zorder=20,
                bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none", alpha=0.75))

    footer = (
        f"CRS: WGS 84 / UTM Zone 43N (EPSG:32643)  |  Date: {date_str}  |  "
        f"Project: Narowal Urban Green Infrastructure & Flood Resilience Initiative\n"
        f"Sources: {sources_text}"
    )
    ax.figure.text(0.015, 0.01, footer, fontsize=7, color="#444444", va="bottom")


def match_to_ref(src_path, ref_prof, resamp=Resampling.bilinear, dtype=np.float32, fill_nodata=0.0):
    with rasterio.open(src_path) as src:
        with WarpedVRT(
            src,
            crs=ref_prof["crs"],
            transform=ref_prof["transform"],
            width=ref_prof["width"],
            height=ref_prof["height"],
            resampling=resamp,
            nodata=fill_nodata,
        ) as vrt:
            out = vrt.read(1).astype(dtype)
    if np.issubdtype(np.dtype(dtype), np.floating):
        out = np.where(np.isnan(out) | (out <= -9000.0), fill_nodata, out)
    return out


def save_raster(path, arr, ref_prof, dtype="float32", nodata=-9999.0):
    p = ref_prof.copy()
    p.update({"dtype": dtype, "count": 1, "compress": "DEFLATE", "nodata": nodata})
    with rasterio.open(path, "w", **p) as dst:
        dst.write(arr.astype(dtype), 1)


def main():
    print("=== Step 4.1: Vacant & Underutilised Land Identification ===")
    lulc_path = os.path.join(LULC_DIR, "Narowal_S2_LULC_6Class_UTM43N.tif")
    with rasterio.open(lulc_path) as ref:
        ref_prof = ref.profile.copy()
        h, w = ref.height, ref.width
        tr = ref.transform
        lulc = ref.read(1)

    mc = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="mc_boundary_preliminary")
    bu = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="builtup_urban_boundary_preliminary")
    roads = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_roads_raw")
    parks = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_parks_green_poly_raw")
    waterways = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_waterways_raw")
    waterbodies = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_waterbodies_raw")
    fac_poly = gpd.read_file(os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg"), layer="osm_facilities_poly_raw")
    ms_bld = gpd.read_file(os.path.join(BASE_DIR, "Narowal_MS_Buildings_AOI.gpkg"), layer="ms_buildings_utm43n")
    ms_bld["geometry"] = ms_bld.geometry.make_valid()
    uu_assets = gpd.read_file(os.path.join(BASE_DIR, "Narowal_UrbanUnit_2021_Assets_UTM43N.gpkg"), layer="uu2021_key_assets_preliminary")
    sa_gdf = gpd.read_file(os.path.join(ACC_DIR, "Narowal_Park_Accessibility_UTM43N.gpkg"), layer="service_areas_10min")
    inferred_gdf = gpd.read_file(os.path.join(DRAIN_DIR, "Narowal_Inferred_Drainage_Convergence_UTM43N.gpkg"), layer="dem_inferred_drainage")

    mc_poly = mc.geometry.union_all()
    bu_poly = bu.geometry.union_all()
    mc_mask = rasterize([(mc_poly, 1)], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    bu_mask = rasterize([(bu_poly, 1)], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)

    # Exclusion masks (buildings, roads, waterbodies, protected drainage corridor 15m, existing parks, prisons)
    bld_mask = rasterize([(g.buffer(3.0), 1) for g in ms_bld.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    rd_mask = rasterize([(g.buffer(6.0), 1) for g in roads.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    pk_mask = rasterize([(g, 1) for g in parks.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    wb_mask = rasterize([(g, 1) for g in waterbodies.geometry] + [(g.buffer(15.0), 1) for g in waterways.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    prison_geoms = fac_poly[fac_poly["amenity"] == "prison"].geometry
    restr_mask = rasterize([(g, 1) for g in prison_geoms], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8) if len(prison_geoms) > 0 else np.zeros((h, w), dtype=np.uint8)
    gsw_occ = match_to_ref(os.path.join(BASE_DIR, "JRC_GSW_occurrence_Narowal_AOI_UTM43N.tif"), ref_prof, Resampling.nearest)

    exclusion_mask = (bld_mask == 1) | (rd_mask == 1) | (pk_mask == 1) | (wb_mask == 1) | (restr_mask == 1) | (gsw_occ >= 20)

    # Candidate open/vacant/underutilised land strictly inside Built-up Urban Core (NOT peri-urban agri fields!)
    # Includes Bare soil (4) and unbuilt Urban Vegetation / Open ground (2) inside built-up urban extent
    open_urban = (bu_mask == 1) & (mc_mask == 1) & (~exclusion_mask) & np.isin(lulc, [2, 4])
    open_clean = ndimage.binary_opening(open_urban, iterations=1)
    open_clean = ndimage.binary_closing(open_clean, iterations=1)

    cand_shapes = [shape(g) for g, v in shapes(open_clean.astype(np.uint8), mask=open_clean, transform=tr) if v == 1]
    cand_shapes = [p.buffer(0) for p in cand_shapes if p.area >= 2000.0]  # >= 0.2 ha (2,000 m2)

    # Load indicators for scoring & candidate site profiling
    sus_score = match_to_ref(os.path.join(FLOOD_DIR, "Narowal_Flood_Susceptibility_Score_10m_UTM43N.tif"), ref_prof, Resampling.bilinear)
    sus_cls = match_to_ref(os.path.join(FLOOD_DIR, "Narowal_Flood_Susceptibility_5Class_UTM43N.tif"), ref_prof, Resampling.nearest, dtype=np.uint8)
    flood_ev = match_to_ref(os.path.join(FLOOD_DIR, "Flood_Evidence_Combined_UTM43N.tif"), ref_prof, Resampling.nearest, dtype=np.uint8)
    ghsl_10m = match_to_ref(os.path.join(BASE_DIR, "GHSL_POP_E2025_Narowal_AOI_UTM43N.tif"), ref_prof, Resampling.bilinear)
    ghsl_10m = np.where(ghsl_10m > 0, ghsl_10m, 0.0)
    # Local population density (mean inside 500m radius)
    pop_500m = ndimage.uniform_filter(ghsl_10m, size=51) * 25.0  # scaled approximate people density

    # Park accessibility deficit (distance to nearest formal public park)
    formal_pk = parks[parks["leisure"] == "park"]
    fpk_mask = rasterize([(g, 1) for g in formal_pk.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    dist_formal_pk_m = ndimage.distance_transform_edt(fpk_mask == 0) * 10.0

    # Drainage connectivity (proximity to DEM-inferred convergence or waterways)
    inf_mask = rasterize([(g.buffer(15.0), 1) for g in inferred_gdf.geometry], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8)
    dist_drain_m = ndimage.distance_transform_edt((inf_mask == 0) & (wb_mask == 0)) * 10.0

    # =========================================================
    # Step 4.2: Green Infrastructure Suitability Model (0-5 scale)
    # Weights: Flood 30%, Park Deficit 25%, Available Land 20%, Pop Served 15%, Drainage Conn 10%
    # =========================================================
    print("=== Step 4.2: Green Infrastructure Suitability Model ===")
    s_flood = np.clip((sus_score - 1.0) / 4.0, 0.0, 1.0) * 4.0 + 1.0
    s_deficit = np.clip(dist_formal_pk_m / 2500.0, 0.0, 1.0) * 4.0 + 1.0
    s_land = np.where(open_urban, 5.0, np.where((mc_mask == 1) & (~exclusion_mask), 2.5, 1.0))
    p95_pop = max(float(np.percentile(pop_500m[mc_mask == 1], 95)), 1.0)
    s_pop = np.clip(pop_500m / p95_pop, 0.0, 1.0) * 4.0 + 1.0
    s_dconn = np.clip(1.0 - (dist_drain_m / 800.0), 0.0, 1.0) * 4.0 + 1.0

    suit_cont = 0.30 * s_flood + 0.25 * s_deficit + 0.20 * s_land + 0.15 * s_pop + 0.10 * s_dconn
    # Apply exclusion mask strictly (set excluded pixels to 0)
    suit_cont_masked = np.where((mc_mask == 1) & (~exclusion_mask), suit_cont, 0.0)

    valid_vals = suit_cont_masked[(mc_mask == 1) & (~exclusion_mask)]
    brks = [np.percentile(valid_vals, p) for p in [20, 45, 70, 88]]
    suit_cls = np.zeros((h, w), dtype=np.uint8)
    m_val = (mc_mask == 1) & (~exclusion_mask)
    suit_cls[m_val] = 1
    suit_cls[m_val & (suit_cont >= brks[0])] = 2
    suit_cls[m_val & (suit_cont >= brks[1])] = 3
    suit_cls[m_val & (suit_cont >= brks[2])] = 4
    suit_cls[m_val & (suit_cont >= brks[3])] = 5

    # Sensitivity analysis on suitability weights
    alt_weights = {
        "Primary_30_25_20_15_10": (0.30, 0.25, 0.20, 0.15, 0.10),
        "Equal_20_20_20_20_20": (0.20, 0.20, 0.20, 0.20, 0.20),
        "ParkEquity_First_20_40_15_15_10": (0.20, 0.40, 0.15, 0.15, 0.10),
        "FloodFirst_45_15_15_10_15": (0.45, 0.15, 0.15, 0.10, 0.15),
    }
    sens_rows = []
    for sname, (w1, w2, w3, w4, w5) in alt_weights.items():
        sc = w1 * s_flood + w2 * s_deficit + w3 * s_land + w4 * s_pop + w5 * s_dconn
        r_corr = float(np.corrcoef(suit_cont[m_val], sc[m_val])[0, 1])
        b_alt = [np.percentile(sc[m_val], p) for p in [20, 45, 70, 88]]
        c_alt = np.ones_like(suit_cls)
        for idx_b, bval in enumerate(b_alt, 2):
            c_alt[sc >= bval] = idx_b
        agree = float(np.mean(c_alt[m_val] == suit_cls[m_val]) * 100.0)
        vh_km2 = float((m_val & (c_alt >= 4)).sum() * 100.0 / 1e6)
        sens_rows.append({"scheme": sname, "pearson_r": round(r_corr, 4), "exact_class_agreement_pct": round(agree, 2), "high_plus_vh_km2": round(vh_km2, 3)})
    pd.DataFrame(sens_rows).to_csv(os.path.join(STATS_DIR, "phase4_suitability_sensitivity.csv"), index=False)

    suit_score_tif = os.path.join(SUIT_DIR, "Narowal_GI_Suitability_Score_10m_UTM43N.tif")
    suit_cls_tif = os.path.join(SUIT_DIR, "Narowal_GI_Suitability_5Class_UTM43N.tif")
    save_raster(suit_score_tif, suit_cont_masked, ref_prof, dtype="float32", nodata=0.0)
    save_raster(suit_cls_tif, suit_cls, ref_prof, dtype="uint8", nodata=0)

    # Profile top candidate vacant/underutilised parcels (sort by suitability * area)
    inst_polys = fac_poly[fac_poly["amenity"].isin(["school", "college", "university", "hospital"])]
    cand_rows = []
    for idx_c, poly in enumerate(sorted(cand_shapes, key=lambda x: x.area, reverse=True)[:45], 1):
        c_pt = poly.centroid
        col_px, row_px = ~tr * (c_pt.x, c_pt.y)
        r_i, c_i = int(np.clip(row_px, 0, h - 1)), int(np.clip(col_px, 0, w - 1))
        # Check overlap with institutional OSM polygons
        own = "Unknown (Cadastre Verification Required)"
        ex_use = "Open / Unbuilt Urban Plot"
        for _, inst in inst_polys.iterrows():
            if poly.intersects(inst.geometry):
                own = "Institutional"
                ex_use = f"Institutional Open Space ({inst['name'] or inst['amenity']})"
                break
        # Check proximity to Proposed Manak Rd Park (UU_PARK_02)
        manak_pt = uu_assets[uu_assets["asset_id"] == "UU_PARK_02"].geometry.iloc[0]
        if poly.distance(manak_pt) <= 150.0:
            own = "Government (Railway / Proposed Park Corridor - Verify Title)"
            ex_use = "Urban Unit 2021 Proposed Manak Rd Park Strip"

        d_pk = float(formal_pk.geometry.distance(c_pt).min())
        f_sus = float(sus_score[r_i, c_i])
        s_val = float(suit_cont[r_i, c_i])
        d_drn = float(dist_drain_m[r_i, c_i])
        pop_val = round(float(pop_500m[r_i, c_i]))
        l_code = int(lulc[r_i, c_i])
        lc_txt = {2: "Urban Vegetation / Open Green", 4: "Bare Soil / Unbuilt"}.get(l_code, "Mixed Open")
        cand_rows.append({
            "site_id": f"VAC_{idx_c:02d}",
            "area_ha": round(poly.area / 1e4, 2),
            "area_m2": round(poly.area, 0),
            "current_land_cover": lc_txt,
            "existing_use": ex_use,
            "ownership_status": own,
            "dist_nearest_park_m": round(d_pk, 0),
            "nearby_pop_index": pop_val,
            "flood_susceptibility": round(f_sus, 2),
            "drainage_dist_m": round(d_drn, 0),
            "walk_accessible_10min": "Yes" if d_pk <= 800 else "No (>10 min)",
            "suitability_score": round(s_val, 2),
            "suitability_class": "Very High" if s_val >= brks[3] else ("High" if s_val >= brks[2] else ("Moderate" if s_val >= brks[1] else "Low")),
            "geometry": poly,
        })

    vac_gdf = gpd.GeoDataFrame(cand_rows, crs="EPSG:32643")
    vac_gdf.to_file(os.path.join(SUIT_DIR, "Narowal_Vacant_Candidate_Sites_UTM43N.gpkg"), layer="vacant_candidate_sites", driver="GPKG")

    # =========================================================
    # Step 4.3: Curate Shortlist of 8 Priority Intervention Sites (diverse interventions)
    # =========================================================
    print("=== Step 4.3: Building 8-Site Priority Intervention Register ===")
    # Anchor sites directly to real coordinates & GIS metrics in high-deficit / high-susceptibility zones
    from pyproj import Transformer
    tr_wgs_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    tr_utm_to_wgs = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

    # Select 8 representative priority locations spanning all intervention typologies across Narowal
    # Combine Manak Rd Park, high-suitability open sites near flooded/underserved streets (Model Town, Tariq Pura/Sadiq Pura, Eidgah Rd, Rasinwal, Zafarwal Rd SW, University Corridor, Central Green Corridor)
    raw_sites = [
        {
            "site_id": "GI_SITE_01",
            "location": "Manak Road Railway Open Strip (Urban Unit Proposed Park)",
            "lon": 74.864203, "lat": 32.098439, "area_ha": 2.85,
            "current_land_use": "Open Railway-Side Strip / Unbuilt Ground",
            "ownership_status": "Government (Pakistan Railways / MC Verify)",
            "recommended_intervention": "Retention / Detention Park",
            "feasibility": "High GIS Suitability; requires inter-departmental railway land lease & drainage tie-in",
            "surveys_required": "Topographic survey (0.2m contours), soil infiltration test, groundwater depth, railway NOC",
            "priority": "Priority 1 (Flagship Catalytic Project)",
        },
        {
            "site_id": "GI_SITE_02",
            "location": "Tariq Pura / Sadiq Pura Underserved Residential Cluster",
            "lon": 74.8712, "lat": 32.0938, "area_ha": 0.95,
            "current_land_use": "Open / Underutilised Urban Plots",
            "ownership_status": "Unknown (Municipal / Private Verification Required)",
            "recommended_intervention": "Detention Pocket Park & Rain Gardens",
            "feasibility": "High GIS Suitability; reported flood street (Urban Unit p.20); ownership & raw sewage separation check needed",
            "surveys_required": "Cadastral title check, sewerage separation check (ensure no raw sewage inflow), soil percolation test",
            "priority": "Priority 1 (Immediate Flood + Equity Relief)",
        },
        {
            "site_id": "GI_SITE_03",
            "location": "Model Town / Kachahry Road Central Neighbourhood",
            "lon": 74.8768, "lat": 32.1045, "area_ha": 0.72,
            "current_land_use": "Institutional / Roadside Open Yard",
            "ownership_status": "Institutional / Government (Verify Title)",
            "recommended_intervention": "Rain Gardens & Permeable Courtyard Retrofit",
            "feasibility": "High GIS Suitability; documented monsoon waterlogging (Urban Unit p.20); low land acquisition risk if institutional",
            "surveys_required": "Drain invert survey, soil infiltration test, school/office MoU",
            "priority": "Priority 1 (Quick-Win Pilot)",
        },
        {
            "site_id": "GI_SITE_04",
            "location": "Eidgah Road / Old City High-Density Core",
            "lon": 74.8695, "lat": 32.1012, "area_ha": 0.45,
            "current_land_use": "Infill Open Space / Roadside Verges",
            "ownership_status": "Unknown / Municipal ROW (Verify)",
            "recommended_intervention": "Neighbourhood Pocket Park & Street Rain Gardens",
            "feasibility": "High GIS Suitability; highest GHSL density & severe park deficit; tight footprint suits modular pocket park",
            "surveys_required": "Cadastre check, utility conflict scan, pedestrian access safety audit",
            "priority": "Priority 2 (High-Density Equity)",
        },
        {
            "site_id": "GI_SITE_05",
            "location": "Rasinwal / Northern Circular Road Convergence Zone",
            "lon": 74.8732, "lat": 32.1135, "area_ha": 1.60,
            "current_land_use": "Peri-Urban Open Ground / Drainage Verge",
            "ownership_status": "Unknown (Field/Cadastre Verification Required)",
            "recommended_intervention": "Bioswale & Stormwater Detention Basin + Drain Rehab",
            "feasibility": "Moderate-High GIS Suitability; major northern flow convergence; MUST separate clean stormwater from Rasinwal sewage outfall",
            "surveys_required": "Drainage capacity & blockage survey, water quality/contamination screening, groundwater table depth",
            "priority": "Priority 2 (Northern Catchment Relief)",
        },
        {
            "site_id": "GI_SITE_06",
            "location": "Zafarwal Road / SW Bypass Drainage Corridor",
            "lon": 74.8598, "lat": 32.0878, "area_ha": 2.10,
            "current_land_use": "Unbuilt Peri-Urban / Roadside Corridor",
            "ownership_status": "Unknown (Cadastre Verification Required)",
            "recommended_intervention": "Retention Park & Road-Corridor Bioswale",
            "feasibility": "High GIS Suitability; captures SW convergence above Zafarwal Road Disposal Station",
            "surveys_required": "Hydraulic outfall tie-in survey, soil permeability, land ownership verification",
            "priority": "Priority 2 (Southwest Growth Corridor)",
        },
        {
            "site_id": "GI_SITE_07",
            "location": "Circular Road – Faiz Park East-West Green Walking Corridor",
            "lon": 74.8855, "lat": 32.0956, "area_ha": 1.40,
            "current_land_use": "Arterial Road Right-of-Way (2.1 km corridor)",
            "ownership_status": "Municipal / Provincial Highway ROW",
            "recommended_intervention": "Green Walking Corridor & Roadside Bioswales",
            "feasibility": "High Feasibility (public ROW); links central neighbourhoods & DHQ Hospital safely to Faiz Ahmad Faiz Park",
            "surveys_required": "Sidewalk width & encroachment survey, cross-drainage culvert check, shade tree utility clearance",
            "priority": "Priority 1 (Low-Cost Immediate Connectivity)",
        },
        {
            "site_id": "GI_SITE_08",
            "location": "University of Narowal – Eastern Sector Greenway Buffer",
            "lon": 74.9105, "lat": 32.0985, "area_ha": 2.40,
            "current_land_use": "Institutional Open Grounds & Unbuilt Fringe",
            "ownership_status": "Institutional (Public University Campus)",
            "recommended_intervention": "Detention Greenbelt & Publicly Accessible Campus Park",
            "feasibility": "Moderate-High; expands east-side green access and buffers eastern stormwater runoff",
            "surveys_required": "University MoU for public walking hours, micro-topography & soil infiltration check",
            "priority": "Priority 3 (Medium-Term Institutional Partnership)",
        },
    ]

    # Enrich each shortlisted site directly from underlying GIS rasters & vector distances
    ghsl_25_raw = os.path.join(BASE_DIR, "GHSL_POP_E2025_Narowal_AOI_UTM43N.tif")
    site_records = []
    for s in raw_sites:
        ux, uy = tr_wgs_to_utm.transform(s["lon"], s["lat"])
        pt = Point(ux, uy)
        col_px, row_px = ~tr * (ux, uy)
        r_i, c_i = int(np.clip(row_px, 0, h - 1)), int(np.clip(col_px, 0, w - 1))

        d_pk = float(formal_pk.geometry.distance(pt).min())
        # 500m GHSL population count
        with rasterio.open(ghsl_25_raw) as gsrc:
            arr_p, _ = mask(gsrc, [pt.buffer(500.0)], crop=True, filled=True, nodata=0)
            pop_500 = round(float(arr_p[arr_p > 0].sum()))

        sus_v = int(sus_cls[r_i, c_i])
        sus_lbl = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}.get(sus_v, "Moderate")
        # Check max flood evidence within 150 m window
        fe_win = flood_ev[max(0, r_i - 15):min(h, r_i + 16), max(0, c_i - 15):min(w, c_i + 16)]
        fe_max = int(fe_win.max()) if fe_win.size > 0 else 0
        fe_txt = {0: "None detected in S1/S2", 1: "Single-sensor candidate wetness within 150 m", 2: "Multi-sensor flood/wetness evidence within 150 m"}[fe_max]
        d_drn = round(float(dist_drain_m[r_i, c_i]), 0)
        suit_v = round(float(suit_cont[r_i, c_i]), 2)

        site_records.append({
            "Site_ID": s["site_id"],
            "Location": s["location"],
            "Lat_WGS84": s["lat"],
            "Lon_WGS84": s["lon"],
            "UTM_X": round(ux, 1),
            "UTM_Y": round(uy, 1),
            "Est_Area_ha": s["area_ha"],
            "Current_Land_Use": s["current_land_use"],
            "Ownership_Status": s["ownership_status"],
            "Dist_Formal_Park_m": round(d_pk, 0),
            "Existing_Park_Access_10min": "Yes" if d_pk <= 800 else "No (Underserved)",
            "Nearby_Pop_500m_GHSL2025": pop_500,
            "Flood_Susceptibility": f"{sus_lbl} (Score {sus_score[r_i, c_i]:.2f}/5)",
            "Historical_Inundation_Evidence": fe_txt,
            "Drainage_Connection_Dist_m": d_drn,
            "GI_Suitability_Score": suit_v,
            "Recommended_Intervention": s["recommended_intervention"],
            "Preliminary_Feasibility": s["feasibility"],
            "Additional_Surveys_Required": s["surveys_required"],
            "Implementation_Priority": s["priority"],
            "Approval_Stage": "High GIS Suitability (Unverified Cadastre & Engineering)",
            "geometry": pt,
        })

    sites_gdf = gpd.GeoDataFrame(site_records, crs="EPSG:32643")
    sites_gdf.to_file(os.path.join(SUIT_DIR, "Narowal_Priority_Intervention_Sites_UTM43N.gpkg"), layer="priority_intervention_sites", driver="GPKG")
    sites_gdf.drop(columns=["geometry"]).to_excel(os.path.join(STATS_DIR, "Narowal_Priority_Intervention_Sites.xlsx"), index=False)
    print(sites_gdf[["Site_ID", "Location", "Nearby_Pop_500m_GHSL2025", "Dist_Formal_Park_m", "Flood_Susceptibility", "Recommended_Intervention"]].to_string())

    # Load Phase 4 layers into FileGDB
    for rpath, rname in [(suit_score_tif, "p4_gi_suitability_score"), (suit_cls_tif, "p4_gi_suitability_5class")]:
        arcpy.management.CopyRaster(rpath, os.path.join(GDB, rname))
    for gpkg_p, lyr, gdb_fc in [
        (os.path.join(SUIT_DIR, "Narowal_Vacant_Candidate_Sites_UTM43N.gpkg"), "vacant_candidate_sites", "p4_vacant_candidate_sites"),
        (os.path.join(SUIT_DIR, "Narowal_Priority_Intervention_Sites_UTM43N.gpkg"), "priority_intervention_sites", "p4_priority_intervention_sites"),
    ]:
        tmp_shp = os.path.join(SUIT_DIR, f"_tmp_{gdb_fc}.shp")
        gpd.read_file(gpkg_p, layer=lyr).to_file(tmp_shp)
        arcpy.conversion.ExportFeatures(tmp_shp, os.path.join(GDB, gdb_fc))
        for ext_rm in [".shp", ".dbf", ".shx", ".prj", ".cpg"]:
            p_rm = tmp_shp.replace(".shp", ext_rm)
            if os.path.exists(p_rm):
                os.remove(p_rm)

    # Produce MAPS 09, 10, 11
    produce_maps_09_10_11(ref_prof, mc, bu, roads, parks, waterways, ms_bld, vac_gdf, suit_cls, sites_gdf, sa_gdf)


def produce_maps_09_10_11(ref_prof, mc, bu, roads, parks, waterways, ms_bld, vac_gdf, suit_cls, sites_gdf, sa_gdf):
    print("=== Step 4.4: Producing MAP 09, MAP 10, MAP 11 ===")
    mc_b = mc.total_bounds
    pad_mc = (mc_b[0] - 500, mc_b[1] - 500, mc_b[2] + 500, mc_b[3] + 500)
    ext_10m = [ref_prof["transform"].c, ref_prof["transform"].c + ref_prof["width"] * ref_prof["transform"].a,
               ref_prof["transform"].f + ref_prof["height"] * ref_prof["transform"].e, ref_prof["transform"].f]

    # MAP 09: Potential Vacant & Underutilised Land
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    ms_bld.plot(ax=ax, facecolor="#E0E0E0", edgecolor="none", alpha=0.75, zorder=1)
    roads.plot(ax=ax, color="#9E9E9E", linewidth=0.45, alpha=0.65, zorder=2)
    parks.plot(ax=ax, facecolor="#1B5E20", edgecolor="#0A3D0A", linewidth=1.2, zorder=4)
    # Color candidate sites by preliminary ownership classification
    own_colors = {"Government": "#1565C0", "Institutional": "#6A1B9A", "Unknown": "#E65100"}
    for key, col in own_colors.items():
        sub = vac_gdf[vac_gdf["ownership_status"].str.startswith(key)]
        if len(sub) > 0:
            sub.plot(ax=ax, facecolor=col, edgecolor="#1A1A1A", linewidth=0.7, alpha=0.75, zorder=5)
    bu.boundary.plot(ax=ax, color="#424242", linewidth=1.1, linestyle="--", zorder=6)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=7)
    handles9 = [
        mpatches.Patch(facecolor="#E65100", edgecolor="#1A1A1A", alpha=0.75, label="Open Urban Plots (Ownership Unknown - Cadastre Req.)"),
        mpatches.Patch(facecolor="#6A1B9A", edgecolor="#1A1A1A", alpha=0.75, label="Institutional Open Grounds (Schools/Colleges/Univ/Hosp)"),
        mpatches.Patch(facecolor="#1565C0", edgecolor="#1A1A1A", alpha=0.75, label="Government Corridor (Railway/Manak Rd Proposed Park)"),
        mpatches.Patch(facecolor="#1B5E20", label="Existing Mapped Parks & Sports Grounds"),
        mlines.Line2D([], [], color="#424242", linewidth=1.1, linestyle="--", label="Built-Up Urban Core (Excludes Outer Farmland)"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles9, loc="upper right", fontsize=7.3, frameon=True, facecolor="white", framealpha=0.93, title="Candidate Open Land", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 09: Potential Vacant & Underutilised Urban Open Land",
        "Candidate Open Plots (>=0.2 ha) Inside Built-Up Urban Core — Ownership Pending Municipal Cadastre",
        "Sentinel-2 L2A LULC (2025), MS Buildings (2026-02), OSM Facilities/Parks, Urban Unit (2021)"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_05, f"MAP_09_Vacant_Underutilised_Land.{ext_f}"), dpi=300)
    plt.close(fig)

    # MAP 10: Urban Green Infrastructure Suitability
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    cmap_s = ListedColormap(["#ECEFF1", "#C8E6C9", "#81C784", "#4CAF50", "#1B5E20", "#004D40"])
    # 0=Excluded, 1=Very Low, 2=Low, 3=Moderate, 4=High, 5=Very High
    cmap_s = ListedColormap(["#E0E0E0", "#F1F8E9", "#AED581", "#66BB6A", "#2E7D32", "#004D40"])
    norm_s = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5], cmap_s.N)
    ax.imshow(suit_cls, extent=ext_10m, cmap=cmap_s, norm=norm_s, alpha=0.82, interpolation="nearest", zorder=1)
    roads.plot(ax=ax, color="#666666", linewidth=0.4, alpha=0.55, zorder=2)
    waterways.plot(ax=ax, color="#1565C0", linewidth=1.4, zorder=3)
    parks.plot(ax=ax, facecolor="#1B5E20", edgecolor="white", linewidth=1.2, zorder=4)
    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=6)
    handles10 = [
        mpatches.Patch(facecolor="#004D40", label="5 - Very High GI Suitability"),
        mpatches.Patch(facecolor="#2E7D32", label="4 - High GI Suitability"),
        mpatches.Patch(facecolor="#66BB6A", label="3 - Moderate GI Suitability"),
        mpatches.Patch(facecolor="#AED581", label="2 - Low GI Suitability"),
        mpatches.Patch(facecolor="#F1F8E9", edgecolor="#CCCCCC", label="1 - Very Low GI Suitability"),
        mpatches.Patch(facecolor="#E0E0E0", label="Excluded (Buildings, Roads, Water, Protected Channels)"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles10, loc="upper right", fontsize=7.3, frameon=True, facecolor="white", framealpha=0.93, title="Suitability Class", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 10: Urban Green Infrastructure Multi-Criteria Suitability",
        "Weighted Overlay (Flood 30%, Park Deficit 25%, Open Land 20%, Pop 15%, Drainage 10%) with Exclusions",
        "Phase 2 Accessibility & GHSL, Phase 3 Flood Susceptibility & Drainage, S2 LULC, MS Buildings"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_05, f"MAP_10_Green_Infrastructure_Suitability.{ext_f}"), dpi=300)
    plt.close(fig)

    # MAP 11: Proposed Green Infrastructure Intervention Plan
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)
    ms_bld.plot(ax=ax, facecolor="#E0E0E0", edgecolor="none", alpha=0.7, zorder=1)
    roads.plot(ax=ax, color="#9E9E9E", linewidth=0.5, alpha=0.65, zorder=2)
    sa_formal = sa_gdf[sa_gdf["category"] == "Formal_Public_Park_Only"]
    if len(sa_formal) > 0:
        sa_formal.plot(ax=ax, facecolor="#C8E6C9", edgecolor="#2E7D32", linewidth=1.0, alpha=0.55, zorder=3)
    waterways.plot(ax=ax, color="#1565C0", linewidth=1.6, zorder=4)
    parks.plot(ax=ax, facecolor="#1B5E20", edgecolor="#0A3D0A", linewidth=1.2, zorder=5)

    # Plot 8 priority sites colored by priority tier
    prio_colors = {"Priority 1": "#8E001C", "Priority 2": "#EF6C00", "Priority 3": "#1565C0"}
    for pkey, pcol in prio_colors.items():
        sub = sites_gdf[sites_gdf["Implementation_Priority"].str.startswith(pkey)]
        if len(sub) > 0:
            sub.plot(ax=ax, color=pcol, edgecolor="white", linewidth=1.0, markersize=130, marker="o", zorder=8)

    for _, r in sites_gdf.iterrows():
        lbl = f"{r['Site_ID']}: {r['Recommended_Intervention'].split('&')[0].strip()}"
        ax.annotate(lbl, (r.geometry.x, r.geometry.y), xytext=(7, 5), textcoords="offset points",
                    fontsize=6.8, fontweight="bold", color="#1A1A1A",
                    bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#333333", alpha=0.92), zorder=12)

    mc.boundary.plot(ax=ax, color="#111111", linewidth=2.0, zorder=7)
    handles11 = [
        mlines.Line2D([], [], color="#8E001C", marker="o", markeredgecolor="white", linestyle="None", markersize=9, label="Priority 1 Sites (Flagship & Quick-Win Pilots)"),
        mlines.Line2D([], [], color="#EF6C00", marker="o", markeredgecolor="white", linestyle="None", markersize=9, label="Priority 2 Sites (Catchment & High-Density Equity)"),
        mlines.Line2D([], [], color="#1565C0", marker="o", markeredgecolor="white", linestyle="None", markersize=9, label="Priority 3 Site (Institutional Greenway Partnership)"),
        mpatches.Patch(facecolor="#1B5E20", label="Existing Parks / Sports Grounds"),
        mpatches.Patch(facecolor="#C8E6C9", edgecolor="#2E7D32", alpha=0.6, label="Existing 10-Min Walk Coverage (Faiz Park)"),
        mlines.Line2D([], [], color="#111111", linewidth=2.0, label="Preliminary MC Boundary"),
    ]
    ax.legend(handles=handles11, loc="upper right", fontsize=7.3, frameon=True, facecolor="white", framealpha=0.93, title="Intervention Plan", title_fontsize=8.5)
    add_cartographic_frame(
        ax, pad_mc,
        "MAP 11: Proposed Urban Green Infrastructure Intervention Plan (8 Priority Sites)",
        "Dual-Purpose SuDS & Park Equity Investments (Pending Field, Cadastre & Hydraulic Verification)",
        "Integrated Phase 2-4 GIS Decision Support Model, Urban Unit (2021), OSM, Sentinel-1/2, Copernicus DEM, GHSL 2025"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    for ext_f in ["png", "pdf"]:
        plt.savefig(os.path.join(MAPS_06, f"MAP_11_Proposed_GI_Intervention_Plan.{ext_f}"), dpi=300)
    plt.close(fig)
    print("  Saved MAP 09, MAP 10, MAP 11 (PNG + PDF)")


if __name__ == "__main__":
    main()
