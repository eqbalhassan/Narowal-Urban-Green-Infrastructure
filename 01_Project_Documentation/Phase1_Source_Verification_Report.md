# PHASE 1: SOURCE VERIFICATION & DATA ACQUISITION REPORT
**Project:** Narowal Urban Green Infrastructure & Flood Resilience Initiative  
**Study Area:** Narowal City Municipal Area + 1 km External Buffer, Punjab, Pakistan  
**Analysis CRS:** WGS 84 / UTM Zone 43N (`EPSG:32643`) | **Export/Web CRS:** WGS 84 (`EPSG:4326`)  
**Date:** 2026-11-12  

---

## 1. Environment & Software Verification

- **Project Workspace:** `C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure\`
- **ArcGIS Pro & ArcPy:** ArcGIS Pro 3.6 Python (`C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`, Python 3.13.7) verified with `arcpy`, `geopandas 1.1.0`, `rasterio 1.4.3`, `gdal 3.11.3`, `fiona 1.10.1` (`OpenFileGDB` and `GPKG` drivers), `shapely 2.1.2`, `pyproj 3.7.2`, `networkx 3.4.2`, `openpyxl 3.1.5`, `scipy 1.14.1`, `matplotlib 3.9.4`, and `pypdf 4.3.1`.
- **QGIS Desktop & GDAL CLI:** QGIS 3.40.15 (`qgis_process-qgis-ltr.bat`, `ogr2ogr.exe`, `gdalinfo.exe`) verified installed.
- **System Python 3.13:** Installed with `python-pptx 1.0.2`, `reportlab 4.5.1`, `pandas 3.1.0`, `openpyxl 3.1.5`.
- **Note:** `osmnx` is not installed in `arcgispro-py3` (OSM network extraction and topology building will be performed cleanly in Phase 2 using `geopandas` + `shapely` + `networkx` / ArcGIS Network Analyst). ArcGIS Pro MCP Bridge was inactive (desktop session not open), so all File Geodatabase (`Narowal_Green_Infrastructure.gdb`) operations were executed directly via `arcpy` Python.

---

## 2. Authoritative Government Document Review (The Urban Unit, 2021)

**Downloaded File:** `02_Raw_Data/08_Government_Reports/Narowal_Regional_Development_Master_Plan_Water_Supply_Sewerage_Env.pdf` (222 pages, 17,827,559 bytes)  
**Source URL:** `https://urbanunit.gov.pk/Download/publications/Files/13/2021/Narowal%20Regional%20Development%20Master%20Plan%20-%20Water%20Supply%2C%20Sewerage%20%26%20Env%20Sector.pdf`

### Verified Findings Extracted from the Report
1. **Municipal Demographics & Urban Extent (p. 11, Table 5):**
   - Projected population within Municipal Committee (MC) Narowal "Existing Urban Boundary": **113,150** (2020), **132,194** (2025), and **154,443** (2030).
2. **Existing & Proposed Public Parks (pp. 46, 49–50):**
   - **Faiz Ahmed Faiz Park** (GPS: `32.0954 N, 74.8947 E`, opposite DC Office): reported as the **only proper public park** in Narowal City; area **58 kanals** (~7.25 acres / ~2.93 ha); maintained by 4 staff (short by 2).
   - **Proposed Public Park near Manak Road (Railway strip)** (GPS: `32° 5' 54.38" N, 74° 51' 51.13" E` = `32.098439, 74.864203`; Figure 26, p. 50; estimated cost PKR 23.199M): **unverified** whether constructed since 2021.
3. **Existing Sewerage & Disposal Infrastructure (pp. 20, 35–41):**
   - Existing sewerage network totals **11.3 km** (~45% area coverage), supplemented by deteriorated open tertiary drains (Condition D–F).
   - **Two Disposal Stations** (combined installed capacity **41 cusec**; actual ~10 hrs/day operation yields **9.1 MGD** vs estimated 2020 flow **12.48 MGD**, a **3.38 MGD / 27% deficit**):
     - **Rasinwal Disposal Station:** Installed 1992, 4 pump sets, 16 cusec, Condition C (Fair).
     - **Zafarwal Road Disposal Station:** Installed 1985, 7 pump sets, 25 cusec, Condition C (Fair).
   - **Wastewater Treatment Plant (WWTP):** **None exists**; all city sewage discharges untreated directly into **Nullah Daik**. A WWTP on Ghausia Road Extension (`32° 4' 35.292" N, 74° 53' 33.036" E` = `32.076470, 74.892510`) was proposed as a 6–10 year long-term project (PKR 233.44M).
4. **Historical Flooding & Natural Nullahs (pp. 20, 47–48):**
   - DC Narowal consultation documented monsoon rainwater flooding along **Eidgah Road, Church Road, Kachahry Road, Tariq Pura, Sadiq Pura, and Model Town** (water entered houses).
   - Major regional flood tributaries: **River Ravi (Jassar)**, **Nullah Jajri**, **Nullah Bein** (up to 43,000 cusec), **Nullah Basantar** (up to 17,800 cusec), and **Nullah Daik/Dake** (up to 30,500 cusec; 1,000-cusec siphon bottleneck near Baddomalhi).

---

## 3. Study Area Boundary Establishment & Verification

1. **Official Boundary Search:**
   - OpenStreetMap administrative relations (`narowal_admin_boundaries_raw.json`) contain `Narowal District` (`admin_level=6`, rel/16117668) and `Narowal Tehsil` (`admin_level=7`, rel/16108415), **but no Municipal Committee Narowal urban boundary polygon**.
   - LG&CD Punjab and Urban Unit web portals document the constituent mouzas of MC Narowal (*Narowal, Chandowal, Ghaziwal, Narowal Rural, Saran, Kotli Boota Singh, Jaman, Dogar Hindu*) and publish rasterized layout maps, but **no open vector GIS shapefile** is downloadable without formal departmental request.
2. **Preliminary Boundary Extraction (Verified Methodology):**
   - Embedded high-resolution maps were extracted from the 2021 Urban Unit Master Plan: **Annexure 2** (`page_70_img_1.jpg`, 1430×1011 px) was georeferenced to `EPSG:32643` using 5 verified OSM/GPS control points (**RMSE = 7.12 m**).
   - **Figure 18** (`page_53_img_5.jpg`, 1431×1105 px), which depicts the complete unclipped `Narowal City` (`MC Boundary`) outline, was georeferenced to `EPSG:32643` using 6 shared road-junction and corner control points (**RMSE = 47.90 m**) and vectorized via sealed morphological contour extraction.
   - A **Preliminary Built-Up Urban Extent** was independently derived from **51,497 Microsoft Global ML Building Footprints** (`2026-02-03` release) via 75 m cluster aggregation.
   - A **1,000 m external buffer** was generated around the preliminary MC boundary in `EPSG:32643`.
3. **Resulting Preliminary Areas (`EPSG:32643`):**
   - `mc_boundary_preliminary` (Urban Unit 2021 Fig. 18 digitized): **24.905 km²** (2,490.5 ha) — *clearly labelled Preliminary; pending official MC Narowal / Urban Unit GIS shapefile.*
   - `builtup_urban_boundary_preliminary` (MS Buildings core): **17.837 km²** (1,783.7 ha).
   - `study_buffer_1km`: **57.939 km²** (5,793.9 ha).

---

## 4. Dataset Verification & Data Quality Concerns

| Dataset | Status on Disk | Key Quality Findings & Limitations |
|---|---|---|
| **OpenStreetMap (Overpass)** | Downloaded (`22.7 MB` XML; parsed to GPKG & GDB) | **1,167** road segments, **4** green/leisure polygons (`Faiz Ahmad Faiz Park`, `Narowal Sports Complex`, 2 unnamed pitches), **7** waterways, **12** facility polygons, **15** facility points. **CRITICAL GAP:** Only **11** buildings mapped in OSM; road topology & park entrances unverified. |
| **Microsoft ML Buildings** | Downloaded (`42.8 MB` gz; **51,497** buildings in AOI) | Compensates OSM's building gap cleanly; ML footprints lack occupancy/land-use attributes and may merge dense courtyard structures. |
| **Copernicus DEM GLO-30** | Downloaded (`40.6 MB` raw; clipped `487×400` UTM 43N) | Elevation in Narowal AOI ranges **230.00 m – 258.78 m**. DSM (includes buildings/trees), not bare-earth urban DTM; **cannot** resolve street-level depressions or engineering flood depths. |
| **JRC Global Surface Water v1.4** | Downloaded (`occurrence`, `seasonality`, `extent`; clipped UTM 43N) | Occurrence 0–33%, seasonality 0–9 months in AOI; captures persistent/seasonal channels up to 2021 only, missing short-duration urban street waterlogging. |
| **Sentinel-2 L2A (PC & Element84)** | Cataloged (79 scenes); **4 full 6-band PC scenes** + **2018-05-28** partial downloaded | 0.00%–0.19% cloud scenes acquired for `2022-08-10`, `2025-05-16`, `2025-09-23`, `2026-10-28` (`10m` RGB/NIR + `20m` SWIR1/SCL). Cannot resolve ownership or tiny plots. |
| **Sentinel-1 SAR (CDSE & PC S1-RTC)** | CDSE cataloged (388 scenes, SAFE download HTTP `401`); PC S1-RTC cataloged (151 scenes) & **8 Aug-2025 VV/VH GeoTIFFs** downloaded | S1A began over Narowal in **Oct 2014** (VV only), missing Sept 2014 monsoon; 2018–2026 have dense VV+VH coverage. Aug 2025 flood pairs (`2025-08-15` vs `2025-08-27` Asc-100; `2025-08-05` vs `2025-08-23` Desc-34) acquired locally via open PC S1-RTC. |
| **CHIRPS Precipitation** | Monthly 1981–2025 (`1.4 MB` CSV + `129 KB` NC) via ERDDAP; UCSB v3.0 Docs | Coarse `0.05°` (~5.5 km) grid cannot distinguish street-level rainfall. UCSB CHIRPS v3.0 returned `HTTP 429` during bulk TIFF requests; ERDDAP daily had `HTTP 503`/stride gaps (needs polite v3.0 retry in Phase 3). |
| **GHSL GHS-POP R2023A (`R6_C25`)** | Downloaded (`E2020`: `58.0 MB`, `E2025`: `62.4 MB` TIFs), clipped to UTM 43N & loaded in GDB | **CRITICAL DISCREPANCY:** Native Mollweide (`ESRI:54009`) pixel sum inside preliminary MC boundary is **290,812** (2020) and **304,324** (2025), ~2.3×–2.6× higher than Urban Unit's MC population (**113,150** in 2020; **132,194** in 2025). Gridded disaggregation must **never** be presented as official census counts. |
| **Municipal / Departmental GIS** | **Missing (Official Request Required)** | Official MC boundary SHP, cadastral/public land ownership, drain invert levels, sewerage GIS, and Rescue 1122 geotagged waterlogging logs are not publicly downloadable. |

---

## 5. Exact Next Steps for Phase 2 (Baseline & Ten-Minute Park Accessibility)

1. Audit and clean `osm_roads_raw` topology in `EPSG:32643` (remove non-walkable/disconnected islands, snap dangling endpoints within tolerance, verify pedestrian walkability tags).
2. Verify existing and candidate public green spaces (cross-check `Faiz Ahmad Faiz Park`, `Narowal Sports Complex`, and `Proposed Manak Road Park` against 2025/2026 Sentinel-2 imagery) and define explicit park entrance nodes (`uu2021_key_assets` + OSM road junctions) flagged for field verification.
3. Build the pedestrian walking network (`4.8 km/h`, `800 m` = 10-minute threshold) and generate network service-area isochrones separately for (A) all mapped publicly accessible parks, (B) parks >= 10 acres (note: Faiz Park is ~7.25 acres, testing whether ANY >=10-acre public park exists!), and (C) small neighbourhood parks/playgrounds.
4. Calculate street-length accessibility vs. GHSL population-based and MS-building-based accessibility (explicitly distinguishing street coverage from population coverage), and produce **MAP 01**, **MAP 02**, and **MAP 03**.
