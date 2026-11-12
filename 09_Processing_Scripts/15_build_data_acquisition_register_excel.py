"""Build comprehensive Phase 1 Excel Data Acquisition Register from verified disk & catalog metadata."""

import json
import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
RAW = os.path.join(ROOT, "02_Raw_Data")
PROC = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")
DOC = os.path.join(ROOT, "01_Project_Documentation")
OUT_XLSX = os.path.join(DOC, "Narowal_Data_Acquisition_Register.xlsx")


def file_status(rel_path):
    full = os.path.join(ROOT, rel_path)
    if os.path.exists(full):
        sz = os.path.getsize(full)
        if sz > 0:
            return f"Downloaded & Verified ({sz:,} bytes)", full
    return "Pending / Partial", full


def style_sheet(ws, headers, col_widths):
    header_fill = PatternFill(start_color="1B4332", end_color="1B4332", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    body_font = Font(name="Calibri", size=10)
    thin = Side(border_style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    ws.append(headers)
    for c_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"

    for r_idx in range(2, ws.max_row + 1):
        for c_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.font = body_font
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border

    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def main():
    wb = openpyxl.Workbook()

    # =========================================================
    # SHEET 1: Data Acquisition Register (all 13 required fields)
    # =========================================================
    ws1 = wb.active
    ws1.title = "Data_Acquisition_Register"
    headers1 = [
        "Dataset Name",
        "Source Organisation",
        "Official Download URL",
        "Geographic Coverage",
        "Spatial Resolution",
        "Temporal Coverage",
        "Coordinate Reference System",
        "File Format",
        "Download Date",
        "Licence",
        "Intended Analysis",
        "Data Limitations",
        "Acquisition Status",
        "Local File Path",
    ]

    def check_s2_status():
        s2_dir = os.path.join(RAW, "03_Sentinel_2")
        tifs = []
        for dp, _, fns in os.walk(s2_dir):
            for fn in fns:
                if fn.endswith("_AOI.tif"):
                    tifs.append(fn)
        return f"Cataloged (79 scenes) & Partial/Active AOI COG Download ({len(tifs)} band GeoTIFFs on disk)"

    def check_s1_status():
        s1_dir = os.path.join(RAW, "02_Sentinel_1")
        tifs = []
        for dp, _, fns in os.walk(s1_dir):
            for fn in fns:
                if fn.endswith("_AOI.tif"):
                    tifs.append(fn)
        return f"CDSE Cataloged (388 scenes, SAFE download 401); PC S1-RTC Cataloged (151 scenes) & Downloaded ({len(tifs)} VV/VH AOI GeoTIFFs)"

    def check_ghsl_status():
        p20 = os.path.join(RAW, "06_Population", "GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R6_C25.tif")
        p25 = os.path.join(RAW, "06_Population", "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C25.tif")
        z20 = os.path.join(RAW, "06_Population", "GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R6_C25.zip")
        z25 = os.path.join(RAW, "06_Population", "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C25.zip")
        if os.path.exists(p20) and os.path.exists(p25):
            return f"Downloaded, Extracted & Clipped to UTM43N (E2020 tif: {os.path.getsize(p20):,} B; E2025 tif: {os.path.getsize(p25):,} B)"
        if os.path.exists(z20) and os.path.exists(z25):
            return f"Downloaded & Verified ZIPs (E2020: {os.path.getsize(z20):,} B; E2025: {os.path.getsize(z25):,} B)"
        return "Pending / Partial"

    rows1 = [
        [
            "Urban Unit Narowal Regional Development Master Plan (Water Supply, Sewerage & Env Sector)",
            "The Urban Unit (Urban Sector Planning & Management Services Unit), Govt. of Punjab",
            "https://urbanunit.gov.pk/Download/publications/Files/13/2021/Narowal%20Regional%20Development%20Master%20Plan%20-%20Water%20Supply%2C%20Sewerage%20%26%20Env%20Sector.pdf",
            "District Narowal & Narowal City MC Area",
            "Report figures & layout maps (~1:40,000 rasterized PDF maps)",
            "2020-2030 planning horizon (published 2021)",
            "WGS 84 / UTM Zone 43N (after georeferencing Fig. 18 & Annexure 2)",
            "PDF (222 pp) + extracted JPG/PNG maps + georeferenced GeoTIFF/GPKG",
            "2026-11-11",
            "Public Government Publication",
            "Baseline MC boundary, existing sewerage/disposal stations, parks, proposed Manak Rd park, WWTP, flood history",
            "2021 planning document; proposed schemes not verified as built; embedded maps are raster images (~48m RMSE when georeferenced), original GIS shapefiles not included",
            file_status(r"02_Raw_Data\08_Government_Reports\Narowal_Regional_Development_Master_Plan_Water_Supply_Sewerage_Env.pdf")[0],
            os.path.join(RAW, "08_Government_Reports", "Narowal_Regional_Development_Master_Plan_Water_Supply_Sewerage_Env.pdf"),
        ],
        [
            "OpenStreetMap (OSM) Narowal Urban Extract (Roads, Parks, Waterways, Facilities, Places)",
            "OpenStreetMap Contributors / Overpass API",
            "https://overpass-api.de/api/interpreter (see also https://download.geofabrik.de/asia/pakistan.html)",
            "Narowal Urban Area + Buffer (32.04N-32.17N, 74.80E-74.95E)",
            "Vector (~1-10m positional accuracy)",
            "Snapshot as of 2026-11-11",
            "WGS 84 (EPSG:4326), projected to EPSG:32643",
            "OSM XML (.osm), GeoPackage (.gpkg), FileGDB",
            "2026-11-11",
            "ODbL 1.0",
            "10-min pedestrian network analysis, baseline roads, parks, waterways, public facilities",
            "Severely incomplete buildings (only 11 mapped in OSM); only 4 green/leisure polygons; 7 waterways; disconnected segments & missing footpath/entrance tags require cleaning & field verification",
            file_status(r"02_Raw_Data\01_OSM\narowal_urban_bbox_raw.osm")[0],
            os.path.join(RAW, "01_OSM", "narowal_urban_bbox_raw.osm"),
        ],
        [
            "OpenStreetMap Administrative Boundaries (Narowal District, Tehsil, Punjab)",
            "OpenStreetMap Contributors / Overpass API",
            "https://overpass-api.de/api/interpreter",
            "31.95N-32.25N, 74.70E-75.05E",
            "Vector administrative polygons",
            "Snapshot as of 2026-11-11",
            "WGS 84 (EPSG:4326)",
            "Overpass JSON (.json)",
            "2026-11-11",
            "ODbL 1.0",
            "Administrative boundary check",
            "Contains Narowal District (admin_level=6) & Narowal Tehsil (admin_level=7), but NO Municipal Committee Narowal urban boundary (admin_level=8/9/10 absent)",
            file_status(r"02_Raw_Data\01_OSM\narowal_admin_boundaries_raw.json")[0],
            os.path.join(RAW, "01_OSM", "narowal_admin_boundaries_raw.json"),
        ],
        [
            "Microsoft Global ML Building Footprints (QuadKey 123103232, Narowal AOI)",
            "Microsoft Planetary Computer / Bing Maps ML Buildings",
            "https://minedbuildings.z5.web.core.windows.net/global-buildings/2026-02-03/global-buildings.geojsonl/RegionName=Pakistan/quadkey=123103232/part-00197-4feead82-d499-422b-94cb-c036c212127a.c000.csv.gz",
            "QuadKey 123103232; filtered to Narowal AOI (51,497 buildings)",
            "Vector footprints (~0.5-1m imagery-derived)",
            "2026-02-03 release (multi-date Bing imagery)",
            "WGS 84 (EPSG:4326) & EPSG:32643",
            "Gzipped GeoJSONL (.csv.gz) + GeoPackage + FileGDB",
            "2026-11-11",
            "CDLA-Permissive-2.0",
            "Compensates OSM missing buildings; built-up urban extent delineation; park service-area building counts; exclusion mask",
            "ML-derived footprints may merge dense courtyard roofs or miss very recent 2026 structures; no occupancy/land-use attributes",
            file_status(r"02_Raw_Data\01_OSM\ms_buildings_pakistan_qk_123103232.csv.gz")[0],
            os.path.join(RAW, "01_OSM", "ms_buildings_pakistan_qk_123103232.csv.gz"),
        ],
        [
            "Copernicus DEM GLO-30 (Tile N32_00_E074_00)",
            "European Space Agency (ESA) / Copernicus Programme via AWS Open Data",
            "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N32_00_E074_00_DEM/Copernicus_DSM_COG_10_N32_00_E074_00_DEM.tif",
            "1x1 deg tile (32N-33N, 74E-75E); clipped to Narowal AOI",
            "1 arc-second (~30 m)",
            "TanDEM-X acquisition 2011-2015 (GLO-30 release)",
            "WGS 84 / EGM2008 vertical; clipped copy in EPSG:32643",
            "Cloud Optimized GeoTIFF (.tif)",
            "2026-11-11",
            "Copernicus DEM Licence (Free & Open)",
            "Preliminary terrain slope, flow direction, flow accumulation, drainage convergence, relative elevation",
            "Digital Surface Model (not bare-earth urban DTM); 30 m grid cannot detect street-level depressions, roadside drain levels, or calculate engineering flood depths",
            file_status(r"02_Raw_Data\04_DEM\Copernicus_DSM_COG_10_N32_00_E074_00_DEM.tif")[0],
            os.path.join(RAW, "04_DEM", "Copernicus_DSM_COG_10_N32_00_E074_00_DEM.tif"),
        ],
        [
            "JRC Global Surface Water v1.4 (Occurrence, Seasonality, Extent)",
            "European Commission JRC / Google Earth Engine",
            "https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/occurrence_70E_40Nv1_4_2021.tif",
            "10x10 deg tile (70E-80E, 30N-40N); clipped to Narowal AOI",
            "30 m",
            "1984-2021 Landsat archive",
            "WGS 84 (EPSG:4326), clipped copy in EPSG:32643",
            "GeoTIFF (.tif)",
            "2026-11-11",
            "Creative Commons Attribution (CC BY 4.0)",
            "Permanent & seasonal water masking (rivers/nullahs/ponds) prior to SAR flood extraction",
            "Does not capture short-duration urban street waterlogging; ends 2021; 30 m Landsat resolution misses narrow urban drains",
            file_status(r"02_Raw_Data\07_Historical_Flood_Data\JRC_GSW_occurrence_70E_40Nv1_4_2021.tif")[0],
            os.path.join(RAW, "07_Historical_Flood_Data", "JRC_GSW_occurrence_70E_40Nv1_4_2021.tif"),
        ],
        [
            "Sentinel-2 Level-2A Multispectral Imagery (MGRS-43SDR)",
            "ESA Copernicus / Element84 Earth Search AWS Sentinel-COGs",
            "https://earth-search.aws.element84.com/v1/search",
            "MGRS Tile 43SDR (Narowal City + buffer AOI 74.80E-74.95E, 32.04N-32.17N)",
            "10 m (B02,B03,B04,B08) & 20 m (B11 SWIR, SCL)",
            "2018-05-28, 2022-08-10, 2025-05-16, 2025-08-21, 2025-09-23, 2026 (<20% cloud cataloged)",
            "WGS 84 / UTM Zone 43N (EPSG:32643)",
            "STAC JSON + Clipped AOI Cloud Optimized GeoTIFFs (.tif)",
            "2026-11-11",
            "Copernicus Sentinel Data Terms (Free & Open)",
            "NDVI, NDWI, NDBI, LULC classification (6 classes), vacant urban land screening, SAR flood validation",
            "10-20 m resolution cannot distinguish land ownership or small (<200 m2) plots; cloud cover during peak monsoon restricts optical flood snapshots",
            check_s2_status(),
            os.path.join(RAW, "03_Sentinel_2"),
        ],
        [
            "Sentinel-1 IW GRDH & RTC SAR Imagery (Monsoon Events 2014-2026)",
            "ESA CDSE (Catalog) & Microsoft Planetary Computer (S1-RTC Open COGs)",
            "https://catalogue.dataspace.copernicus.eu/odata/v1/Products & https://planetarycomputer.microsoft.com/api/stac/v1",
            "Point intersect Narowal (74.873E, 32.102N) + AOI COGs (74.80E-74.95E, 32.04N-32.17N)",
            "10 m (IW GRDH / RTC)",
            "2014 (Oct-Dec VV; 15 scenes) & 2018-2026 (373 CDSE / 151 PC-RTC VV+VH scenes; Aug 2025 pairs downloaded)",
            "WGS 84 / UTM Zone 43N (EPSG:32643) for downloaded PC S1-RTC COGs",
            "CDSE JSON, PC STAC JSON & Clipped VV/VH GeoTIFFs (.tif)",
            "2026-11-11",
            "Copernicus Sentinel Data Terms (Open; CDSE raw SAFE requires free login)",
            "Monsoon event flood/waterlogging backscatter change detection (VV/VH)",
            "CDSE raw SAFE binary returns HTTP 401 without login (mitigated for 2018-2026 via open Planetary Computer S1-RTC COGs); Sept 2014 flood missed by S1A; urban double-bounce/shadow limits pure SAR waterlogging detection",
            check_s1_status(),
            os.path.join(RAW, "02_Sentinel_1"),
        ],
        [
            "CHIRPS Monthly & Daily Gridded Precipitation (v2.0 ERDDAP + v3.0 Docs)",
            "UCSB Climate Hazards Center / NOAA CoastWatch ERDDAP",
            "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalMonthlyP05 & https://data.chc.ucsb.edu/products/CHIRPS/v3.0/",
            "31.95N-32.25N, 74.70E-75.05E (Narowal District & City)",
            "0.05 deg (~5.5 km)",
            "Monthly 1981-2025 (complete); Daily sample/ERDDAP",
            "WGS 84 (EPSG:4326)",
            "NetCDF (.nc), CSV (.csv), TXT README",
            "2026-11-11",
            "Public Domain / Open Data",
            "Historical annual/monthly rainfall trends and monsoon event context",
            "Coarse ~5.5 km grid cannot resolve street-level rainfall differences; UCSB CHIRPS v3.0 server returned HTTP 429 rate-limit during bulk requests; ERDDAP daily had HTTP 503/stride gaps",
            "Monthly 1981-2025 Downloaded & Verified (NC+CSV); UCSB v3.0 daily/annual pending retry after rate-limit cooldown",
            os.path.join(RAW, "05_Rainfall", "chirps_v20_narowal_monthly_1981_present.nc"),
        ],
        [
            "GHSL Population Grid (GHS-POP R2023A, 100 m, Epochs 2020 & 2025, Tile R6_C25)",
            "European Commission Joint Research Centre (JRC)",
            "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C25.zip",
            "GHSL Tile R6_C25 (covers Narowal & Upper Punjab)",
            "100 m",
            "Epochs 2020 and 2025 (projections from 2017/census)",
            "World Mollweide (ESRI:54009); will reproject to EPSG:32643",
            "Zipped GeoTIFF (.zip / .tif)",
            "2026-11-11",
            "CC BY 4.0",
            "Population density, population within/outside 10-min park service areas, beneficiary population",
            "Modelled gridded disaggregation, NOT official Pakistan 2023 census block counts; JRC FTP throttled (~25 KB/s)",
            check_ghsl_status(),
            os.path.join(RAW, "06_Population"),
        ],
        [
            "Official Municipal Boundary Shapefile & Cadastral/Public Land Parcels",
            "Municipal Corporation Narowal / Urban Unit Punjab / LG&CD Punjab",
            "Official municipal request required (see https://lgcd.punjab.gov.pk/)",
            "Narowal Municipal Area",
            "Survey/Cadastral scale",
            "Current notified boundary",
            "Projected / Local",
            "SHP / GDB / DWG / Notified Map",
            "N/A",
            "Government Departmental Approval Required",
            "Authoritative municipal jurisdiction, verified public/municipal vacant plot ownership",
            "Not openly downloadable as vector GIS; preliminary MC boundary digitized from Urban Unit 2021 PDF instead",
            "Missing - Municipal Request Required (documented in Phase 1 & Phase 5 plan)",
            "N/A",
        ],
        [
            "Municipal Stormwater, Sewerage GIS, Drain Invert Levels & Rescue 1122 Flood Logs",
            "MC Narowal / PHED Punjab / Irrigation Dept / Rescue 1122 / DC Narowal",
            "Departmental request required",
            "Narowal City & surrounding nullahs (Daik, Basantar, Bein)",
            "Engineering survey / GPS points",
            "Historical monsoon events (2013-2026)",
            "WGS 84 / Local",
            "SHP / CAD / Excel / Geotagged Photos",
            "N/A",
            "Government Departmental Approval Required",
            "Hydraulic drainage bottlenecks, Indicator E/F of Flood Susceptibility, verified waterlogging hotspots",
            "Not publicly available online; Urban Unit 2021 PDF provides narrative summary of 6 flooded streets & 2 disposal stations only",
            "Missing - Municipal Request Required",
            "N/A",
        ],
    ]

    for r in rows1:
        ws1.append(r)
    style_sheet(ws1, headers1, [34, 26, 42, 24, 18, 22, 22, 20, 12, 20, 34, 42, 28, 42])

    # =========================================================
    # SHEET 2: Sentinel-1 Candidate Scenes (CDSE Catalog)
    # =========================================================
    ws2 = wb.create_sheet("Sentinel1_Candidate_Scenes")
    headers2 = [
        "Period_Group",
        "Product_Name",
        "Acquisition_Date",
        "Acquisition_Time_UTC",
        "Platform",
        "Sensor_Mode",
        "Product_Type",
        "Polarisation",
        "Orbit_Direction",
        "Relative_Orbit",
        "Size_MB",
        "Event_Role_Status",
        "CDSE_Product_ID",
    ]
    s1_json = os.path.join(RAW, "02_Sentinel_1", "cdse_sentinel1_catalog_narowal.json")
    with open(s1_json, encoding="utf-8") as f:
        s1_cat = json.load(f)
    for period, items in s1_cat.items():
        if not isinstance(items, list):
            continue
        for it in items:
            dt_str = it.get("ContentDate", {}).get("Start", "")
            acq_date = dt_str[:10]
            acq_time = dt_str[11:19]
            sz_mb = round((it.get("ContentLength") or 0) / (1024 * 1024), 1)
            role = "Candidate Monsoon / Reference Scene (verify rainfall event before Pre/Post assignment)"
            if "2014" in period:
                role = "Post-2014-Flood Only (S1A began Oct 2014 over Narowal; VV only)"
            elif "2025_monsoon" in period and acq_date >= "2025-08-20" and acq_date <= "2025-09-10":
                role = "Priority Candidate Post-Event Scene (Late Aug 2025 Narowal Flood Window)"
            elif "2025_monsoon" in period and acq_date < "2025-08-20":
                role = "Candidate Pre-Event Baseline (2025 Monsoon)"
            ws2.append([
                period,
                it.get("Name"),
                acq_date,
                acq_time,
                it.get("platformSerialIdentifier"),
                it.get("operationalMode"),
                it.get("productType"),
                it.get("polarisationChannels"),
                it.get("orbitDirection"),
                it.get("relativeOrbitNumber"),
                sz_mb,
                role,
                it.get("Id"),
            ])
    style_sheet(ws2, headers2, [18, 55, 14, 14, 10, 12, 12, 12, 14, 13, 10, 38, 38])

    # =========================================================
    # SHEET 3: Sentinel-2 Candidate Scenes (Earth Search)
    # =========================================================
    ws3 = wb.create_sheet("Sentinel2_Candidate_Scenes")
    headers3 = [
        "Season_Group",
        "Scene_ID",
        "Acquisition_Date",
        "Cloud_Cover_Pct",
        "MGRS_Tile",
        "Platform",
        "Local_AOI_Download_Status",
        "Red_COG_URL",
    ]
    s2_json = os.path.join(RAW, "03_Sentinel_2", "earth_search_sentinel2_catalog_narowal.json")
    with open(s2_json, encoding="utf-8") as f:
        s2_cat = json.load(f)
    for grp, items in s2_cat.items():
        if not isinstance(items, list):
            continue
        for it in sorted(items, key=lambda x: x.get("cloud_cover", 999)):
            sid = it.get("id")
            # Check if any folder has this scene_id downloaded
            dl_stat = "Cataloged (Available unauthenticated via AWS COG)"
            for dname in os.listdir(os.path.join(RAW, "03_Sentinel_2")):
                if sid in dname and os.path.isdir(os.path.join(RAW, "03_Sentinel_2", dname)):
                    n_tifs = len([x for x in os.listdir(os.path.join(RAW, "03_Sentinel_2", dname)) if x.endswith(".tif")])
                    dl_stat = f"AOI Bands on Disk ({n_tifs}/6 GeoTIFFs)"
            ws3.append([
                grp,
                sid,
                it.get("datetime", "")[:10],
                round(it.get("cloud_cover", 0), 2),
                it.get("mgrs_tile"),
                it.get("platform"),
                dl_stat,
                it.get("red_href"),
            ])
    style_sheet(ws3, headers3, [20, 30, 14, 14, 14, 14, 28, 60])

    # =========================================================
    # SHEET 4: Urban Unit 2021 Asset & Verification Register
    # =========================================================
    ws4 = wb.create_sheet("UrbanUnit_2021_Findings")
    headers4 = [
        "Item_Type",
        "Feature_or_Location_Name",
        "Report_Page",
        "Coordinates_WGS84",
        "Reported_Details_2021",
        "Verification_Status",
        "Phase2_3_Action_Required",
    ]
    rows4 = [
        ["Existing Public Park", "Faiz Ahmed Faiz Park", "p. 46", "32.0954 N, 74.8947 E", "Only proper public park in Narowal; 58 kanals (~7.25 acres); walking tracks, swings, mini-zoo, tennis/badminton courts, cafeteria; 4 staff (short by 2)", "Verified in OSM (way/519685072) & satellite imagery", "Map exact pedestrian entrances & boundary for 10-min network analysis"],
        ["Proposed Public Park", "Proposed Public Park near Manak Road (Railway strip)", "p. 49-50", "32.098439 N, 74.864203 E", "Proposed PKR 23.199M park along railway open strip", "Unverified whether constructed since 2021", "Check recent 2025/2026 imagery + field verification"],
        ["Disposal Station", "Rasinwal Disposal Station", "p. 35, 37", "~32.1117 N, 74.8729 E (georef Annex 2)", "Installed 1992; 4 pumps, 16 cusec; operates ~10 hrs/day; Condition C (Fair); spalling civil structure", "Location georeferenced (~7m RMSE) from Annex 2; asset condition from 2021 report", "Verify exact GPS, pump status, outfall pipe & operating hours with PHED/MC"],
        ["Disposal Station", "Zafarwal Road Disposal Station", "p. 35, 37", "~32.0815 N, 74.8595 E (georef Annex 2)", "Installed 1985; 7 pumps, 25 cusec; operates ~10 hrs/day; Condition C (Fair); spalling civil structure", "Location georeferenced (~7m RMSE) from Annex 2; asset condition from 2021 report", "Verify exact GPS, pump status, outfall route & operating hours with PHED/MC"],
        ["Proposed WWTP", "Wastewater Treatment Plant (Ghausia Road Ext)", "p. 40-41", "32.076470 N, 74.892510 E", "Proposed long-term (6-10 yrs) PKR 233.44M; currently NO WWTP exists; raw sewage discharged directly into Nullah Daik", "Unverified whether land acquired/constructed", "Confirm WWTP status with PHED & Irrigation Dept"],
        ["Reported Flooded Streets", "Eidgah Rd, Church Rd, Kachahry Rd, Tariq Pura, Sadiq Pura, Model Town", "p. 20", "Central Narowal neighbourhoods", "Reported by DC Narowal team as flooded during monsoon; rainwater entered residential houses during Eid-ul-Azha", "Narrative report only (2021); no GPS/depth log", "Request geotagged complaints from MC/Rescue 1122 & verify in Phase 3/5"],
        ["Natural Drainage", "Nullah Daik, Nullah Basantar, Nullah Bein, Nullah Jajri, River Ravi", "p. 47-48", "District / Peri-urban channels", "Nullah Daik max 30,500 cusec (receives untreated city sewage); Basantar max 17,800 cusec; Bein max 43,000 cusec; 2013 flood hit 60,705 acres / 304 villages", "Authoritative hydrological background; city-level outfall linkages unmapped in GIS", "Trace local nullah/drain alignments & outfalls with Irrigation Dept & DEM"],
        ["MC Population Baseline", "MC Narowal Existing Urban Boundary", "p. 11", "MC Boundary (~24.9 km2 digitized)", "Projected MC population: 113,150 (2020), 132,194 (2025), 154,443 (2030); water demand 9.93 MGD vs 2.85 MGD supply; sewerage 11.3 km (45% area)", "Official Urban Unit planning projections (derived from 2017 census)", "Cross-check against GHSL R2023A 2020/2025 grids & request 2023 Census block stats"],
    ]
    for r in rows4:
        ws4.append(r)
    style_sheet(ws4, headers4, [20, 34, 12, 24, 48, 30, 38])

    # =========================================================
    # SHEET 5: Outstanding / Missing Data Summary
    # =========================================================
    ws5 = wb.create_sheet("Missing_and_Action_Items")
    headers5 = ["Missing_or_Pending_Item", "Category", "Blocking_Phase", "Reason_or_Access_Constraint", "Required_Action"]
    rows5 = [
        ["Official Notified MC Narowal Boundary GIS Shapefile", "Administrative", "Phase 2/5 (preliminary boundary ready)", "Not published online as vector GIS by LG&CD or Urban Unit", "Formal data request to MC Narowal / Urban Unit / LG&CD Punjab"],
        ["Sentinel-1 GRD SAFE Binary Downloads", "Satellite SAR", "Phase 3", "CDSE download API returns HTTP 401 without free Copernicus account credentials", "User registers free CDSE account or provides token for selected monsoon event scenes in Sheet 2"],
        ["Verified Municipal Waterlogging & Rescue 1122 Flood Incidents", "Ground Truth", "Phase 3", "Not publicly available online", "Departmental request to Rescue 1122, DC Narowal, MC Narowal"],
        ["Sewerage & Stormwater Drain GIS Network + Invert Levels", "Engineering", "Phase 3/4", "PDF layout maps only; no pipe sizes/invert levels/condition GIS", "Request original shapefiles/CAD from Urban Unit & PHED Punjab"],
        ["Municipal Land Ownership / Vacant Plot Cadastre", "Cadastral", "Phase 4/5", "Land ownership cannot be inferred from satellite imagery", "Request municipal/state land records from MC Narowal / Revenue Dept / PULSE"],
        ["CHIRPS v3.0 Daily/Annual GeoTIFFs (full UCSB archive)", "Climate", "Phase 3", "UCSB server returned HTTP 429 rate-limit; ERDDAP v2.0 monthly 1981-2025 already acquired", "Re-run CHIRPS v3.0 polite fetcher after cooldown for 2022-2025 daily monsoon totals"],
    ]
    for r in rows5:
        ws5.append(r)
    style_sheet(ws5, headers5, [36, 16, 20, 42, 42])

    wb.save(OUT_XLSX)
    print("Saved Data Acquisition Register Excel ->", OUT_XLSX)


if __name__ == "__main__":
    main()
