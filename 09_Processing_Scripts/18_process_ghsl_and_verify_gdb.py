"""Extract GHSL E2020 & E2025 R6_C25 GeoTIFFs, clip/reproject to Narowal AOI (EPSG:32643), verify stats vs Urban Unit, and load into FileGDB."""

import os
import zipfile
import arcpy
import geopandas as gpd
import numpy as np
import rasterio
from osgeo import gdal

gdal.UseExceptions()
arcpy.env.overwriteOutput = True

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
POP_DIR = os.path.join(ROOT, "02_Raw_Data", "06_Population")
BASE_DIR = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
GDB_PATH = os.path.join(ROOT, "04_Geodatabase", "Narowal_Green_Infrastructure.gdb")


def main():
    # Clean stale .part file if present
    stale = os.path.join(POP_DIR, "GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R6_C25.zip.part")
    if os.path.exists(stale):
        os.remove(stale)

    # Extract zips
    tifs = {}
    for epoch in ["2020", "2025"]:
        zpath = os.path.join(POP_DIR, f"GHS_POP_E{epoch}_GLOBE_R2023A_54009_100_V1_0_R6_C25.zip")
        tif_name = f"GHS_POP_E{epoch}_GLOBE_R2023A_54009_100_V1_0_R6_C25.tif"
        tpath = os.path.join(POP_DIR, tif_name)
        if not os.path.exists(tpath):
            print(f"Extracting {zpath}...")
            with zipfile.ZipFile(zpath, "r") as zf:
                zf.extractall(POP_DIR)
        tifs[epoch] = tpath
        print(f"Verified raw GHSL {epoch}: {tpath} ({os.path.getsize(tpath):,} B)")

    # Clip & warp to Study Buffer + 2km in EPSG:32643 (100 m pixel)
    mc = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="mc_boundary_preliminary")
    buf = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="study_buffer_1km")
    minx, miny, maxx, maxy = buf.geometry.buffer(2000.0).union_all().bounds

    for epoch, raw_tif in tifs.items():
        out_tif = os.path.join(BASE_DIR, f"GHSL_POP_E{epoch}_Narowal_AOI_UTM43N.tif")
        opts = gdal.WarpOptions(
            dstSRS="EPSG:32643",
            outputBounds=[minx, miny, maxx, maxy],
            xRes=100.0,
            yRes=100.0,
            resampleAlg="bilinear",
            dstNodata=-200.0,
            creationOptions=["COMPRESS=DEFLATE"],
        )
        ds = gdal.Warp(out_tif, raw_tif, options=opts)
        ds = None

        # Also clip directly to MC boundary in native 54009 (so pixel sums are exact people counts!)
        mc_54009 = mc.to_crs("ESRI:54009")
        from rasterio.mask import mask
        with rasterio.open(raw_tif) as src:
            out_arr, _ = mask(src, mc_54009.geometry, crop=True, filled=True, nodata=0)
            pop_mc = float(np.sum(out_arr[out_arr > 0]))
        with rasterio.open(out_tif) as chk:
            arr_utm = chk.read(1)
            print(f"GHSL {epoch} UTM43N: {chk.width}x{chk.height} px | Exact MC-Boundary sum (native 54009): {pop_mc:,.0f} people")

        dst_r = os.path.join(GDB_PATH, f"GHSL_POP_E{epoch}_Narowal_AOI_UTM43N")
        arcpy.management.CopyRaster(out_tif, dst_r)
        print(f"  GDB raster loaded: GHSL_POP_E{epoch}_Narowal_AOI_UTM43N")


if __name__ == "__main__":
    main()
