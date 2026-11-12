"""Georeference Urban Unit Annexure 2 (page_70) and Figure 18 (page_53) to EPSG:32643 and extract MC Boundary."""

import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import Affine
from shapely.geometry import Polygon
from PIL import Image
import matplotlib.pyplot as plt
from pyproj import Transformer

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
MAPS_DIR = os.path.join(ROOT, "02_Raw_Data", "08_Government_Reports", "extracted_maps")
OUT_DIR = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
GPKG_UTM = os.path.join(OUT_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg")


def fit_affine_gcps(gcps_px, gcps_utm):
    """Fit 6-parameter affine transform: X = a*col + b*row + c, Y = d*col + e*row + f."""
    A = np.column_stack([gcps_px[:, 0], gcps_px[:, 1], np.ones(len(gcps_px))])
    cx, _, _, _ = np.linalg.lstsq(A, gcps_utm[:, 0], rcond=None)
    cy, _, _, _ = np.linalg.lstsq(A, gcps_utm[:, 1], rcond=None)
    pred_x = A @ cx
    pred_y = A @ cy
    errs = np.sqrt((pred_x - gcps_utm[:, 0]) ** 2 + (pred_y - gcps_utm[:, 1]) ** 2)
    rmse = float(np.sqrt(np.mean(errs ** 2)))
    transform = Affine(cx[0], cx[1], cx[2], cy[0], cy[1], cy[2])
    return transform, errs, rmse


def write_geotiff(img_path, out_tif, transform, crs="EPSG:32643"):
    arr = np.array(Image.open(img_path).convert("RGB"))
    h, w, _ = arr.shape
    with rasterio.open(
        out_tif,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=3,
        dtype=arr.dtype,
        crs=crs,
        transform=transform,
        compress="DEFLATE",
    ) as dst:
        for b in range(3):
            dst.write(arr[:, :, b], b + 1)
    return out_tif


def main():
    tr = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)

    # First check exact coordinates of University of Narowal / District Jail / Circular Rd junctions from OSM
    roads = gpd.read_file(GPKG_UTM, layer="osm_roads_raw")
    fac = gpd.read_file(GPKG_UTM, layer="osm_facilities_poly_raw")
    parks = gpd.read_file(GPKG_UTM, layer="osm_parks_green_poly_raw")

    # Initial GCPs on page_70_img_1.jpg (col, row) -> WGS84 -> UTM43N
    # 1. elementry college centroid (74.873543, 32.108222) -> ~(583, 312)
    # 2. Govt Girls College centroid (74.873360, 32.106092) -> ~(580, 354)
    # 3. District Headquarters Hospital (74.884819, 32.099358) -> ~(812, 484)
    # 4. Faiz Ahmad Faiz Park (74.895464, 32.095265) -> ~(1025, 563)
    # 5. Proposed WWTP (74.892510, 32.076470) -> ~(967, 958)
    gcps_wgs = [
        ("elementry_college", (583, 312), (74.873543, 32.108222)),
        ("govt_girls_college", (580, 354), (74.873360, 32.106092)),
        ("dhq_hospital", (812, 484), (74.884819, 32.099358)),
        ("faiz_park", (1025, 563), (74.895464, 32.095265)),
        ("proposed_wwtp", (967, 958), (74.892510, 32.076470)),
    ]
    px = np.array([g[1] for g in gcps_wgs], dtype=float)
    utm = np.array([tr.transform(g[2][0], g[2][1]) for g in gcps_wgs], dtype=float)

    affine_70, errs, rmse = fit_affine_gcps(px, utm)
    print(f"Page 70 initial affine RMSE: {rmse:.2f} m")
    for (name, _, _), e in zip(gcps_wgs, errs):
        print(f"  {name}: residual = {e:.2f} m")

    tif_70 = os.path.join(OUT_DIR, "UrbanUnit_2021_Annexure2_Georef_UTM43N.tif")
    write_geotiff(os.path.join(MAPS_DIR, "page_70_img_1.jpg"), tif_70, affine_70)

    # Render overlay verification check: georeferenced page_70 + OSM roads + parks + facilities
    with rasterio.open(tif_70) as src:
        img = np.moveaxis(src.read(), 0, -1)
        b = src.bounds
    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
    ax.imshow(img, extent=[b.left, b.right, b.bottom, b.top])
    roads.plot(ax=ax, color="cyan", linewidth=0.6, alpha=0.8)
    parks.boundary.plot(ax=ax, color="yellow", linewidth=1.5)
    fac.boundary.plot(ax=ax, color="magenta", linewidth=1.2)
    ax.set_xlim(b.left, b.right)
    ax.set_ylim(b.bottom, b.top)
    ax.set_title(f"Georeferencing Verification: Urban Unit Annexure 2 vs OSM (RMSE={rmse:.1f}m)")
    plt.tight_layout()
    ver_png = os.path.join(OUT_DIR, "georef_verification_page70_vs_osm.png")
    plt.savefig(ver_png, dpi=150)
    plt.close(fig)
    print("Saved verification overlay ->", ver_png)


if __name__ == "__main__":
    main()
