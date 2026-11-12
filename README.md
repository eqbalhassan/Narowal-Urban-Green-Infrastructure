# Narowal Urban Green Infrastructure & Flood Resilience Initiative

**Study Area:** Narowal City (Municipal Committee Urban Area + 1 km External Buffer), Punjab, Pakistan  
**Primary Analysis CRS:** WGS 84 / UTM Zone 43N (`EPSG:32643`)  
**Web Mapping / Export CRS:** WGS 84 (`EPSG:4326`)  
**Project Status:** Phases 1–5 Complete (Maps 01–11 PDF/PNG, FileGDB, Technical Report PDF, Mayoral Briefing PPTX, Municipal & Field Workbooks, Interactive Web GIS App)  

---

## 1. Project Overview

This GIS decision-support project evaluates **Narowal City, Punjab, Pakistan** across three interconnected planning objectives:
1. **Ten-Minute Park Accessibility:** Pedestrian network service-area analysis (`4.8 km/h`, `800 m` threshold) identifying underserved neighbourhoods and population.
2. **Urban Flooding & Waterlogging Assessment:** Multi-indicator susceptibility screening integrating historical monsoon inundation evidence, terrain convergence, imperviousness, rainfall, drainage deficiencies, and verified flood complaints.
3. **Urban Green Infrastructure (SuDS) Interventions:** Prioritising dual-purpose sites (retention/detention parks, bioswales, rain gardens, pocket parks, green corridors, and drainage rehabilitation) that simultaneously reduce urban waterlogging and close park accessibility deficits.

---

## 2. Directory Structure

```text
Narowal_Urban_Green_Infrastructure/
├── README.md                              # Project documentation, CRS, workflow & data status
├── 01_Project_Documentation/              # Data acquisition register (Excel), source verification, logs
├── 02_Raw_Data/                           # Untouched authoritative raw inputs (preserved read-only)
│   ├── 01_OSM/                            # Raw Overpass OSM XML, admin JSON, MS Building Footprints
│   ├── 02_Sentinel_1/                     # CDSE Sentinel-1 IW GRDH catalog & access verification
│   ├── 03_Sentinel_2/                     # Earth Search STAC catalog & clipped L2A AOI COG bands
│   ├── 04_DEM/                            # Copernicus DEM GLO-30 tile (N32_00_E074_00)
│   ├── 05_Rainfall/                       # CHIRPS precipitation (ERDDAP monthly/daily + v3.0 docs)
│   ├── 06_Population/                     # GHSL GHS-POP R2023A 100 m (Tile R6_C25, 2020 & 2025)
│   ├── 07_Historical_Flood_Data/          # JRC Global Surface Water v1.4 (occurrence, seasonality, extent)
│   └── 08_Government_Reports/             # Urban Unit Narowal Regional Development Master Plan (2021)
├── 03_Processed_Data/                     # Derived analysis-ready layers (UTM 43N & WGS 84)
│   ├── 01_Base_Mapping/                   # Preliminary MC/built-up boundaries, parsed OSM, MS buildings, clipped DEM/GSW
│   ├── 02_Land_Use_Land_Cover/            # Sentinel-2 6-class RF LULC (OA=91.17%), NDVI/NDBI/NDWI
│   ├── 03_Hydrological_Analysis/          # GLO-30 Priority-Flood DEM, Slope, HAND, TWI, Flow Acc
│   ├── 04_Historical_Flood_Mapping/       # Sentinel-1 RTC Aug 2025 flood pairs, S2 MNDWI, 5-class susceptibility
│   ├── 05_Park_Accessibility/             # Clean walkable network, entrances, 10-min service areas, deficit grid
│   ├── 06_Drainage_Mapping/               # DEM-inferred convergence & 12 drainage investigation priority zones
│   └── 07_Suitability_Analysis/           # 45 vacant candidates, 5-class GI suitability, 8 priority sites
├── 04_Geodatabase/
│   └── Narowal_Green_Infrastructure.gdb   # Master Esri File Geodatabase (EPSG:32643)
├── 05_Maps/                               # Cartographic exports (MAP 01-11 PDF & 300 DPI PNG)
│   └── Narowal_WebGIS_App/                # Interactive Leaflet Web GIS Portal (index.html + EPSG:4326 GeoJSONs)
├── 06_Field_Verification/                 # Survey123/QField XLSForm & Field Verification Protocol
├── 07_Reports/                            # Final Technical Report (Markdown + Formatted PDF)
├── 08_Tables_and_Statistics/              # Traceable summary CSV/JSON/Excel statistics
├── 09_Processing_Scripts/                 # Reproducible Python & ArcPy/GDAL processing scripts (01..25)
└── 10_Presentation/                       # 14-slide Mayoral briefing presentation (PPTX)
```

---

## 3. Coordinate Reference Systems (CRS)

- **Analysis & Metric Operations:** `WGS 84 / UTM Zone 43N` (`EPSG:32643`) — all distance, area, buffering (`1 km` external buffer, `800 m` walking thresholds), and raster hydrological workflows.
- **Web Mapping / KML / Catalog Queries:** `WGS 84` (`EPSG:4326`).

---

## 4. Phase 1 Key Data Sources & Boundary Methodology

- **Preliminary Municipal Boundary:** Because no official vector GIS boundary for Municipal Committee Narowal is openly available in OSM (`admin_level=8/9` absent) or LG&CD web portals, a preliminary boundary (`~24.91 km²`) was digitized and georeferenced from the **Urban Unit Narowal Regional Development Master Plan (2021, Fig. 18 & Annexure 2)** and paired with a **Preliminary Built-Up Urban Extent (`~17.84 km²`)** derived from **51,497 Microsoft Global ML Building Footprints** plus a **1 km external buffer**. These are explicitly labelled preliminary and must not be represented as officially notified cadastral boundaries.
- **Government Report:** *Narowal Regional Development Master Plan – Water Supply, Sewerage & Environment Sector* (The Urban Unit, 2021).
- **Open Geospatial Datasets:** OpenStreetMap (Overpass API), Microsoft Global ML Building Footprints (2026-02 release), Copernicus DEM GLO-30 (AWS Open Data), JRC Global Surface Water v1.4, Sentinel-2 L2A (Element84 Earth Search COGs), Sentinel-1 IW GRDH metadata (Copernicus Data Space Ecosystem), CHIRPS precipitation (NOAA ERDDAP & UCSB CHC), and GHSL `GHS_POP_GLOBE_R2023A` (Tile `R6_C25`).

---

## 5. Processing Workflow (Phased)

- **Phase 1 (Complete):** Environment audit, Urban Unit Master Plan extraction, preliminary MC (`24.905 km²`) & built-up (`17.837 km²`) boundaries + 1 km buffer, open dataset acquisition, Excel Data Acquisition Register, Source Verification Report, and base File Geodatabase (`Narowal_Green_Infrastructure.gdb`).
- **Phase 2 (Complete):** Sentinel-2 6-class RF LULC (`OA=91.17%`), OSM pedestrian network topology cleaning (`184.87 km` inside MC), explicit park frontage entrances, 10-min (`800 m` @ `4.8 km/h`) network accessibility, GHSL population equity (`5.68%` formal park coverage; `94.32%` underserved), **Maps 01–03**.
- **Phase 3 (Complete):** Sentinel-1 RTC Aug 2025 flood pairs & Sentinel-2 MNDWI, GLO-30 Priority-Flood hydrological conditioning (HAND, TWI, Flow Acc), CHIRPS climatology (`779.8 mm/yr`), drainage gap analysis (12 hotspots), renormalized 5-indicator flood susceptibility (`30.0%` High/Very High; sensitivity `r=0.874–0.968`), **Maps 04–08**.
- **Phase 4 (Complete):** Vacant urban land screening inside built-up core (`45` plots, `90.70 ha`), weighted GI Suitability Model (sensitivity `r=0.905–0.972`), 8 shortlisted dual-benefit Priority Intervention Sites (`GI_SITE_01`–`08`, `12.47 ha`), **Maps 09–11**.
- **Phase 5 & Web GIS (Complete):** 5-sheet Municipal Data Acquisition Plan, Survey123/QField XLSForm + Protocol, Interactive Leaflet Web GIS App (`05_Maps/Narowal_WebGIS_App/index.html`) + `EPSG:4326` GeoJSONs, Final Technical Report (`.md` & `.pdf`), and 14-slide Mayoral PowerPoint Briefing.

---

## 6. Outstanding Municipal & Engineering Requirements (Phase 5 Gates)

1. Official notified MC Narowal vector boundary and Khasra/Mauza land parcel ownership registers (MC Narowal / BOR / Pakistan Railways).
2. Sewerage/stormwater GIS layers, drain invert levels, and Rasinwal/Zafarwal pump specs (PHED / MC Narowal / Irrigation Dept).
3. Geotagged municipal waterlogging complaints and Rescue 1122 monsoon incident records (2018–2026) + PBS 2023 Census block counts.
4. Field verification deployment (Survey123/QField XLSForm) checking raw sewage separation, active encroachment, and park gate hours prior to 0.2 m DGPS surveying and soil percolation testing.
