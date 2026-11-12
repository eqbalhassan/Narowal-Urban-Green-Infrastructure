"""Phase 1: Create Urban Unit 2021 key infrastructure layer, clip DEM/GSW to study AOI (UTM43N), and populate FileGDB."""

import os
import arcpy
import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from shapely.geometry import Point, mapping
from pyproj import Transformer

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAW_DIR = os.path.join(ROOT, "02_Raw_Data")
BASE_DIR = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
GDB_PATH = os.path.join(ROOT, "04_Geodatabase", "Narowal_Green_Infrastructure.gdb")

arcpy.env.overwriteOutput = True


def build_urban_unit_assets_layer():
    """Create GIS point layer of key infrastructure & parks documented in Urban Unit Master Plan (2021)."""
    # Get affine transform of georeferenced Annexure 2 to extract exact positions of the 2 disposal stations
    tif_70 = os.path.join(BASE_DIR, "UrbanUnit_2021_Annexure2_Georef_UTM43N.tif")
    with rasterio.open(tif_70) as src:
        aff70 = src.transform
    tr_utm_to_wgs = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
    tr_wgs_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)

    # Pixel coords of Disposal Station icons on page_70_img_1.jpg (from gcp_grid_page_70_img_1.jpg.png)
    rasinwal_utm = aff70 * (572, 196)
    rasinwal_wgs = tr_utm_to_wgs.transform(*rasinwal_utm)
    zafarwal_utm = aff70 * (290, 792)
    zafarwal_wgs = tr_utm_to_wgs.transform(*zafarwal_utm)

    records = [
        {
            "asset_id": "UU_PARK_01",
            "name": "Faiz Ahmed Faiz Park",
            "category": "Public Park (Existing)",
            "status": "Existing - Operational (verified in OSM & Urban Unit 2021)",
            "capacity_or_size": "58 kanals (~7.25 acres / ~2.93 ha)",
            "condition": "Well-maintained (4 staff; insufficient)",
            "coord_source": "Urban Unit Master Plan p.46 GPS (32.0954, 74.8947) & OSM way/519685072",
            "lon": 74.8947,
            "lat": 32.0954,
        },
        {
            "asset_id": "UU_PARK_02",
            "name": "Proposed Public Park - Manak Road (Near Railway)",
            "category": "Public Park (Proposed 2021)",
            "status": "Proposed in 2021 Master Plan (PKR 23.199M) - Construction status unverified",
            "capacity_or_size": "TBD (verify via field survey)",
            "condition": "Not Verified",
            "coord_source": "Urban Unit Master Plan p.49 GPS (32d 5m 54.38s N, 74d 51m 51.13s E)",
            "lon": 74.864203,
            "lat": 32.098439,
        },
        {
            "asset_id": "UU_DISP_01",
            "name": "Rasinwal Disposal Station",
            "category": "Sewerage Disposal Station (Existing)",
            "status": "Existing (installed 1992; 4 pump sets, 16 cusec, 10 hrs/day)",
            "capacity_or_size": "16 cusec",
            "condition": "C (Fair) - spalling civil structure & unattended electrical",
            "coord_source": "Georeferenced from Urban Unit Annexure 2 (2021) icon (~7m RMSE); verify GPS in field",
            "lon": round(rasinwal_wgs[0], 6),
            "lat": round(rasinwal_wgs[1], 6),
        },
        {
            "asset_id": "UU_DISP_02",
            "name": "Zafarwal Road Disposal Station",
            "category": "Sewerage Disposal Station (Existing)",
            "status": "Existing (installed 1985; 7 pump sets, 25 cusec, 10 hrs/day)",
            "capacity_or_size": "25 cusec",
            "condition": "C (Fair) - spalling civil structure & unattended electrical",
            "coord_source": "Georeferenced from Urban Unit Annexure 2 (2021) icon (~7m RMSE); verify GPS in field",
            "lon": round(zafarwal_wgs[0], 6),
            "lat": round(zafarwal_wgs[1], 6),
        },
        {
            "asset_id": "UU_WWTP_01",
            "name": "Proposed Wastewater Treatment Plant (Ghausia Road Ext)",
            "category": "Wastewater Treatment Plant (Proposed 2021)",
            "status": "Proposed Long-Term (6-10 yrs, PKR 233.44M) - Status unverified",
            "capacity_or_size": "Citywide WWTP",
            "condition": "Proposed",
            "coord_source": "Urban Unit Master Plan p.41 GPS (32d 4m 35.292s N, 74d 53m 33.036s E)",
            "lon": 74.892510,
            "lat": 32.076470,
        },
        {
            "asset_id": "UU_OHR_01",
            "name": "TMA Narowal Overhead Reservoir",
            "category": "Water Supply OHR (Existing)",
            "status": "Functional for Filtration Plant (built 1985, RCC)",
            "capacity_or_size": "50,000 gallons",
            "condition": "C (Fair)",
            "coord_source": "Urban Unit Master Plan Table 9 p.15 GPS",
            "lon": 74.88136,
            "lat": 32.10270,
        },
        {
            "asset_id": "UU_OHR_02",
            "name": "Old Civil Hospital Overhead Reservoir",
            "category": "Water Supply OHR (Existing)",
            "status": "Not Functional (built 1965, Brick)",
            "capacity_or_size": "20,000 gallons",
            "condition": "C / Non-functional",
            "coord_source": "Urban Unit Master Plan Table 9 p.15 GPS",
            "lon": 74.86881,
            "lat": 32.09547,
        },
    ]

    geoms = [Point(*tr_wgs_to_utm.transform(r["lon"], r["lat"])) for r in records]
    gdf = gpd.GeoDataFrame(records, geometry=geoms, crs="EPSG:32643")
    out_gpkg = os.path.join(BASE_DIR, "Narowal_UrbanUnit_2021_Assets_UTM43N.gpkg")
    gdf.to_file(out_gpkg, layer="uu2021_key_assets_preliminary", driver="GPKG")
    print(f"Saved {len(gdf)} Urban Unit 2021 assets -> {out_gpkg}")
    return out_gpkg


def clip_and_reproject_rasters():
    """Clip Copernicus DEM GLO-30 and JRC GSW rasters to Study Buffer + 2km in EPSG:32643 via GDAL Warp."""
    from osgeo import gdal
    gdal.UseExceptions()

    bnd = gpd.read_file(os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg"), layer="study_buffer_1km")
    clip_geom_utm = bnd.geometry.buffer(2000.0).union_all()
    minx, miny, maxx, maxy = clip_geom_utm.bounds

    raster_jobs = [
        (
            os.path.join(RAW_DIR, "04_DEM", "Copernicus_DSM_COG_10_N32_00_E074_00_DEM.tif"),
            os.path.join(BASE_DIR, "Copernicus_DEM_GLO30_Narowal_AOI_UTM43N.tif"),
            "bilinear",
            30.0,
            -9999.0,
        ),
        (
            os.path.join(RAW_DIR, "07_Historical_Flood_Data", "JRC_GSW_occurrence_70E_40Nv1_4_2021.tif"),
            os.path.join(BASE_DIR, "JRC_GSW_occurrence_Narowal_AOI_UTM43N.tif"),
            "near",
            30.0,
            255,
        ),
        (
            os.path.join(RAW_DIR, "07_Historical_Flood_Data", "JRC_GSW_seasonality_70E_40Nv1_4_2021.tif"),
            os.path.join(BASE_DIR, "JRC_GSW_seasonality_Narowal_AOI_UTM43N.tif"),
            "near",
            30.0,
            255,
        ),
        (
            os.path.join(RAW_DIR, "07_Historical_Flood_Data", "JRC_GSW_extent_70E_40Nv1_4_2021.tif"),
            os.path.join(BASE_DIR, "JRC_GSW_extent_Narowal_AOI_UTM43N.tif"),
            "near",
            30.0,
            255,
        ),
    ]

    out_rasters = []
    for src_path, dst_path, resamp, res_m, nd in raster_jobs:
        if not os.path.exists(src_path):
            print("Missing raw raster:", src_path)
            continue
        opts = gdal.WarpOptions(
            dstSRS="EPSG:32643",
            outputBounds=[minx, miny, maxx, maxy],
            xRes=res_m,
            yRes=res_m,
            resampleAlg=resamp,
            dstNodata=nd,
            creationOptions=["COMPRESS=DEFLATE"],
        )
        ds = gdal.Warp(dst_path, src_path, options=opts)
        ds = None
        with rasterio.open(dst_path) as check:
            arr = check.read(1)
            valid = arr[arr != nd]
            print(f"Clipped & projected -> {os.path.basename(dst_path)} ({check.width}x{check.height} px, min={valid.min():.2f}, max={valid.max():.2f})")
        out_rasters.append(dst_path)
    return out_rasters


def load_into_file_gdb(uu_gpkg, out_rasters):
    """Export all Phase 1 UTM43N vector & raster layers into Narowal_Green_Infrastructure.gdb."""
    if not arcpy.Exists(GDB_PATH):
        arcpy.management.CreateFileGDB(os.path.dirname(GDB_PATH), os.path.basename(GDB_PATH))

    # Helper to load GPKG layer via temporary Shapefile (arcpy Conversion works natively on GPKG in Pro 3.6, let's verify!)
    bnd_gpkg = os.path.join(BASE_DIR, "Narowal_Study_Boundaries_UTM43N.gpkg")
    osm_gpkg = os.path.join(BASE_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg")
    ms_gpkg = os.path.join(BASE_DIR, "Narowal_MS_Buildings_AOI.gpkg")

    vector_loads = [
        (bnd_gpkg, "mc_boundary_preliminary", "bnd_mc_narowal_preliminary"),
        (bnd_gpkg, "builtup_urban_boundary_preliminary", "bnd_builtup_urban_preliminary"),
        (bnd_gpkg, "study_buffer_1km", "bnd_study_buffer_1km"),
        (osm_gpkg, "osm_roads_raw", "osm_roads_raw"),
        (osm_gpkg, "osm_buildings_raw", "osm_buildings_raw"),
        (osm_gpkg, "osm_parks_green_poly_raw", "osm_parks_green_poly_raw"),
        (osm_gpkg, "osm_waterways_raw", "osm_waterways_raw"),
        (osm_gpkg, "osm_waterbodies_raw", "osm_waterbodies_raw"),
        (osm_gpkg, "osm_facilities_poly_raw", "osm_facilities_poly_raw"),
        (osm_gpkg, "osm_facilities_pts_raw", "osm_facilities_pts_raw"),
        (osm_gpkg, "osm_places_pts_raw", "osm_places_pts_raw"),
        (ms_gpkg, "ms_buildings_utm43n", "ms_buildings_aoi"),
        (uu_gpkg, "uu2021_key_assets_preliminary", "uu2021_key_assets_preliminary"),
    ]

    for gpkg_path, lyr, fc_name in vector_loads:
        src_fc = os.path.join(gpkg_path, lyr)
        dst_fc = os.path.join(GDB_PATH, fc_name)
        try:
            arcpy.conversion.ExportFeatures(src_fc, dst_fc)
            cnt = int(arcpy.management.GetCount(dst_fc)[0])
            print(f"  GDB vector loaded: {fc_name} ({cnt:,} features)")
        except Exception as e:
            print(f"  GDB vector fallback via SHP for {fc_name} ({e})")
            tmp_shp = os.path.join(BASE_DIR, f"_tmp_{fc_name}.shp")
            gdf = gpd.read_file(gpkg_path, layer=lyr)
            gdf.to_file(tmp_shp)
            arcpy.conversion.ExportFeatures(tmp_shp, dst_fc)
            cnt = int(arcpy.management.GetCount(dst_fc)[0])
            print(f"  GDB vector loaded via SHP: {fc_name} ({cnt:,} features)")

    for rpath in out_rasters:
        rname = os.path.splitext(os.path.basename(rpath))[0]
        dst_r = os.path.join(GDB_PATH, rname)
        arcpy.management.CopyRaster(rpath, dst_r)
        print(f"  GDB raster loaded: {rname}")


if __name__ == "__main__":
    uu_gpkg = build_urban_unit_assets_layer()
    rasters = clip_and_reproject_rasters()
    load_into_file_gdb(uu_gpkg, rasters)
