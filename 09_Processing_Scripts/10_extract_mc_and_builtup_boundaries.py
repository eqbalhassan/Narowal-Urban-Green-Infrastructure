"""Extract true outer Urban Unit 2021 MC Boundary from Figure 18 (page_53) & verify against Annexure 2 (page_70) and OSM."""

import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import Affine
from rasterio.features import shapes
from PIL import Image
from scipy import ndimage
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union
import matplotlib.pyplot as plt

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
MAPS_DIR = os.path.join(ROOT, "02_Raw_Data", "08_Government_Reports", "extracted_maps")
OUT_DIR = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
GPKG_OSM_UTM = os.path.join(OUT_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg")
GPKG_MS = os.path.join(OUT_DIR, "Narowal_MS_Buildings_AOI.gpkg")


def fit_affine(src_pts, dst_pts):
    A = np.column_stack([src_pts[:, 0], src_pts[:, 1], np.ones(len(src_pts))])
    cx, _, _, _ = np.linalg.lstsq(A, dst_pts[:, 0], rcond=None)
    cy, _, _, _ = np.linalg.lstsq(A, dst_pts[:, 1], rcond=None)
    pred = np.column_stack([A @ cx, A @ cy])
    errs = np.linalg.norm(pred - dst_pts, axis=1)
    rmse = float(np.sqrt(np.mean(errs ** 2)))
    return Affine(cx[0], cx[1], cx[2], cy[0], cy[1], cy[2]), errs, rmse


def extract_mc_polygon_from_page53(img_path, affine_53):
    """Extract the complete outer MC Boundary black ring from Figure 18 (page_53_img_5.jpg)."""
    rgb = np.array(Image.open(img_path).convert("RGB")).astype(np.int16)
    h, w, _ = rgb.shape

    # Neutral dark grey/black pixels (MC boundary line), plus semi-transparent yellow-over-black segments
    spread = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    lum = np.mean(rgb, axis=2)
    mc_line = ((lum < 190) & (spread < 35)) | (np.min(rgb, axis=2) < 130)

    # Mask out outer map neatline border, legend/scale bar (bottom-left), compass (top-right), Urban Unit logo (bottom-right)
    mc_line[:35, :] = False
    mc_line[h - 50:, :] = False
    mc_line[:, :40] = False
    mc_line[:, w - 40:] = False
    mc_line[832:, :520] = False
    mc_line[:215, 1150:] = False
    mc_line[895:, 1060:] = False

    # Bridge the faint crossing segments: eastern edge (1194,642)->(1230,600), NW edge (386,265)->(415,214), SW scalebar edge (288,818)->(362,800)
    for (x0, y0, x1, y1) in [(1194, 642, 1230, 600), (386, 265, 415, 214), (390, 255, 396, 240), (288, 818, 362, 800)]:
        for t in np.linspace(0, 1, 100):
            xx = int(round(x0 + t * (x1 - x0)))
            yy = int(round(y0 + t * (y1 - y0)))
            mc_line[yy - 2:yy + 3, xx - 2:xx + 3] = True

    # Dilate by 10 px (with 4-connected diamond/cross) to seal any small crossing gaps, then erode back 10 px after floodfill
    d = ndimage.binary_dilation(mc_line, iterations=10)
    lbl_bg, _ = ndimage.label(~d)
    print("Check separation bg(50,50) vs city(500,600):", lbl_bg[50, 50], "vs", lbl_bg[500, 600])
    inside_union = (lbl_bg != lbl_bg[50, 50])
    # Keep largest component (excludes any stray isolated specks outside the boundary)
    lbl_in, n_in = ndimage.label(inside_union)
    sizes_in = ndimage.sum(inside_union, lbl_in, range(1, n_in + 1))
    main_in = (lbl_in == (int(np.argmax(sizes_in)) + 1))
    filled = ndimage.binary_erosion(main_in, iterations=10)
    filled = ndimage.binary_fill_holes(filled)
    print(f"Filled MC pixels: {filled.sum():,}")

    # Vectorize in EPSG:32643
    mc_mask = filled.astype(np.uint8)
    geoms = [shape(g) for g, v in shapes(mc_mask, mask=(mc_mask == 1), transform=affine_53) if v == 1]
    poly = unary_union(geoms)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda p: p.area)
    poly = poly.simplify(5.0, preserve_topology=True)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def main():
    tif_70 = os.path.join(OUT_DIR, "UrbanUnit_2021_Annexure2_Georef_UTM43N.tif")
    with rasterio.open(tif_70) as src70:
        aff70 = src70.transform
        img70 = np.moveaxis(src70.read(), 0, -1)
        b70 = src70.bounds

    # 6 exact road-junction & sharp corner GCPs between page_53 and page_70
    shared_gcps = [
        ("zafarwal_circular_N", (706, 405), (583, 288)),
        ("pasrur_circular_NW", (602, 412), (418, 296)),
        ("circular_NE_fork", (783, 435), (712, 335)),
        ("sw_bypass_chowk", (607, 694), (442, 639)),
        ("south_circular_T", (793, 658), (730, 602)),
        ("nw_mc_corner", (412, 216), (158, 63)),
    ]
    p53_pts = np.array([g[1] for g in shared_gcps], dtype=float)
    utm_pts = np.array([aff70 * g[2] for g in shared_gcps], dtype=float)

    aff53, errs, rmse = fit_affine(p53_pts, utm_pts)
    print(f"Page 53 affine RMSE (7 spread GCPs): {rmse:.2f} m")
    for (name, _, _), e in zip(shared_gcps, errs):
        print(f"  {name}: residual = {e:.2f} m")

    p53_path = os.path.join(MAPS_DIR, "page_53_img_5.jpg")
    mc_poly = extract_mc_polygon_from_page53(p53_path, aff53)
    print(f"Extracted MC Boundary area: {mc_poly.area / 1e6:.3f} km2 ({mc_poly.area / 1e4:.1f} ha)")

    buf_1km = mc_poly.buffer(1000.0)

    # Built-Up Urban Footprint from 51,497 MS Building Footprints
    bld = gpd.read_file(GPKG_MS, layer="ms_buildings_utm43n")
    bld_buf = unary_union(bld.geometry.buffer(75.0))
    if bld_buf.geom_type == "MultiPolygon":
        cores = [p for p in bld_buf.geoms if p.area > 250000]
        built_up = unary_union(cores).buffer(-45.0)
    else:
        built_up = bld_buf.buffer(-45.0)
    if built_up.geom_type == "MultiPolygon":
        built_up = max(built_up.geoms, key=lambda p: p.area)
    clean_interiors = [ring for ring in built_up.interiors if Polygon(ring).area > 50000]
    built_up = Polygon(built_up.exterior, clean_interiors).simplify(15.0, preserve_topology=True)
    print(f"Built-up Urban Core area (MS Buildings cluster): {built_up.area / 1e6:.3f} km2")

    gpkg_bnd_utm = os.path.join(OUT_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg")
    gpkg_bnd_wgs = os.path.join(OUT_DIR, "Narowal_Study_Boundaries_WGS84.gpkg")

    gdf_mc = gpd.GeoDataFrame([{
        "boundary_name": "Narowal Municipal Committee Boundary (Preliminary)",
        "source": "Digitized & georeferenced from Urban Unit Narowal Regional Development Master Plan (2021, Fig. 18 & Annexure 2)",
        "status": "Preliminary - Pending official GIS shapefile from MC Narowal / Urban Unit / LG&CD",
        "area_km2": round(mc_poly.area / 1e6, 4),
        "area_ha": round(mc_poly.area / 1e4, 2),
        "geometry": mc_poly,
    }], crs="EPSG:32643")

    gdf_buf = gpd.GeoDataFrame([{
        "boundary_name": "Narowal Study Area 1 km External Buffer",
        "source": "1,000 m buffer around preliminary MC Boundary (EPSG:32643)",
        "area_km2": round(buf_1km.area / 1e6, 4),
        "geometry": buf_1km,
    }], crs="EPSG:32643")

    gdf_bu = gpd.GeoDataFrame([{
        "boundary_name": "Narowal Built-Up Urban Footprint (Preliminary)",
        "source": "Derived from Microsoft Global ML Building Footprints (2026-02 release, 75m aggregation)",
        "status": "Preliminary satellite/ML-derived urban built-up extent",
        "area_km2": round(built_up.area / 1e6, 4),
        "area_ha": round(built_up.area / 1e4, 2),
        "geometry": built_up,
    }], crs="EPSG:32643")

    for lyr, gdf in [
        ("mc_boundary_preliminary", gdf_mc),
        ("study_buffer_1km", gdf_buf),
        ("builtup_urban_boundary_preliminary", gdf_bu),
    ]:
        gdf.to_file(gpkg_bnd_utm, layer=lyr, driver="GPKG")
        gdf.to_crs("EPSG:4326").to_file(gpkg_bnd_wgs, layer=lyr, driver="GPKG")

    # Verification overlay
    roads = gpd.read_file(GPKG_OSM_UTM, layer="osm_roads_raw")
    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
    ax.imshow(img70, extent=[b70.left, b70.right, b70.bottom, b70.top], alpha=0.85)
    roads.plot(ax=ax, color="white", linewidth=0.4, alpha=0.5)
    gdf_mc.boundary.plot(ax=ax, color="red", linewidth=2.4, label=f"Urban Unit MC Boundary ({mc_poly.area/1e6:.2f} km2)")
    gdf_bu.boundary.plot(ax=ax, color="cyan", linewidth=1.8, linestyle="--", label=f"Built-Up Urban Core ({built_up.area/1e6:.2f} km2)")
    gdf_buf.boundary.plot(ax=ax, color="orange", linewidth=1.5, linestyle=":", label="1 km External Buffer")
    ax.set_xlim(gdf_buf.total_bounds[0] - 200, gdf_buf.total_bounds[2] + 200)
    ax.set_ylim(gdf_buf.total_bounds[1] - 200, gdf_buf.total_bounds[3] + 200)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(f"Narowal Preliminary Study Boundaries Verification (MC={mc_poly.area/1e6:.2f} km2, Built-Up={built_up.area/1e6:.2f} km2)")
    plt.tight_layout()
    ver_png = os.path.join(OUT_DIR, "boundary_verification_mc_and_builtup.png")
    plt.savefig(ver_png, dpi=150)
    plt.close(fig)
    print("Saved boundary verification plot ->", ver_png)


if __name__ == "__main__":
    main()
