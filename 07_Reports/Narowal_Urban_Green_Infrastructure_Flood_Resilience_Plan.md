# NAROWAL URBAN GREEN INFRASTRUCTURE & FLOOD RESILIENCE INITIATIVE
## Geospatial Decision-Support Technical Report for the Municipal Corporation Narowal

**Prepared For:** Worshipful Mayor & Municipal Infrastructure Authorities, Municipal Corporation Narowal, Punjab, Pakistan  
**Prepared By:** Multidisciplinary GIS, Remote Sensing, Hydrology & SuDS Planning Team  
**Date:** November 12, 2026  
**Coordinate Reference Systems:** `WGS 84 / UTM Zone 43N (EPSG:32643)` for all spatial metrics & modelling; `WGS 84 (EPSG:4326)` for Web GIS & KML exports  
**Interactive Web GIS Companion:** [`Narowal Web GIS App`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/05_Maps/Narowal_WebGIS_App/index.html)

---

## Executive Summary

Narowal City faces converging pressures from severe public green-space scarcity and recurrent monsoon pluvial waterlogging. Combining free, authoritative satellite earth observation (Copernicus Sentinel-1 RTC, Sentinel-2 L2A, DEM GLO-30), OpenStreetMap (OSM), Microsoft Global ML Building Footprints, JRC Global Surface Water, CHIRPS rainfall, GHSL population grids, and the **Urban Unit (2021) Narowal Regional Development Master Plan**, this GIS decision-support study evaluates urban park equity, surface drainage vulnerability, and multi-benefit Sustainable Urban Drainage Systems (SuDS) opportunities across Narowal Municipal Corporation (**24.905 km² preliminary boundary**).

### Headline Evidence-Based Findings

1. **Acute Formal Park Equity Deficit:** Only **1** formal public park is mapped inside the urban area (**Faiz Ahmad Faiz Park**, 3.19 ha / 7.88 acres). Within a 10-minute walk (`800 m @ 4.8 km/h`) over **184.87 km** of MC walkable streets, only **10.91%** of street length (**20.17 km**) and **5.68%** of residents (**17,170 of 302,379** GHSL 2025 population) are served—leaving **94.32% (~285,208 residents)** underserved. Formal park provision stands at **0.24 m²/person** (Urban Unit 2025 projection: 132,194) or **0.11 m²/person** (GHSL 2025: 302,379), representing a **97–99% deficit** below the **9.0 m²/person WHO benchmark**. Zero formal parks meet the >=10-acre regional standard (`0.00%` coverage). Even including the **Narowal Sports Complex** (18.34 ha; access status unverified), total coverage reaches only **6.40%** of MC population.
2. **Monsoon Pluvial & Drainage Vulnerability:** CHIRPS climatology (1981–2024) records **779.8 mm/yr** mean annual rainfall, **69.5% (542.1 mm)** concentrated in July–September, with wettest post-2014 month reaching **488.1 mm (August 2020)**. Sentinel-1 SAR change detection for the historic **August 2025** monsoon storm (`Asc-100 2025-08-27` vs `08-15`) detected **236.8 ha** of candidate inundation/saturation inside MC and **6,571.2 ha** across the surrounding floodplain AOI. Multi-indicator screening (5 available indicators renormalized over 85%, sensitivity `r = 0.874–0.968`) classifies **30.0% of the MC (7.472 km²)** as **High (4.483 km²)** or **Very High (2.989 km²)** flood/waterlogging susceptibility, alongside **12 Priority Drainage Investigation Zones** (`DRN_PRIO_01`–`12`) where DEM convergence paths lack mapped engineered drains.
3. **Dual-Benefit Vacant Urban Land & Priority Portfolio:** Screening strictly inside the **17.837 km² Built-Up Core** (excluding outer peri-urban agriculture to preserve food security and realism) identified **45 candidate unbuilt urban plots >= 0.2 ha** totaling **90.70 ha** (2 Government railway/park strips = 6.71 ha; 5 Institutional grounds = 11.01 ha; 38 unverified plots = 72.98 ha). A 5-criteria GI Suitability Model (sensitivity `r = 0.905–0.972`) shortlisted **8 catalytic Priority Intervention Sites (`GI_SITE_01`–`GI_SITE_08`, totaling 12.47 ha)** combining retention/detention parks, rain gardens, bioswales, pocket parks, and green pedestrian corridors.

### Critical Methodological Safeguards & Caveats

- **Preliminary Boundary:** `mc_boundary_preliminary` (24.905 km²) is digitized from Urban Unit (2021) Annexure 2 & urban core distribution—**not** a gazetted LG&CD shapefile.
- **Population Discrepancy:** GHSL 2025 (**302,379** in MC) is ~2.3x higher than Urban Unit's 2025 projection (**132,194**). Both are reported side-by-side pending **PBS 2023 Census** block release.
- **Screening Hydrology:** Copernicus DEM GLO-30 (**30 m DSM**) cannot resolve street curbs or invert depths; engineering flood depths are intentionally **not** calculated.
- **Sewage Separation Gate:** Urban Unit (2021) confirms Narowal's sewerage discharges untreated via Rasinwal (16 cusec) & Zafarwal Rd (25 cusec) disposal stations toward Nullah Daik. **Raw domestic sewage must never be routed into unlined rain gardens or infiltration basins.**

---

## 1. Study Area & Authoritative Data Register

Narowal City (`32.10°N, 74.87°E`) is the administrative headquarters of Narowal District, Punjab. Consistent with project scope, analysis is confined to the **Narowal Urban / Municipal Corporation Preliminary Boundary (24.905 km² / 2,490.5 ha)**, the **Built-Up Urban Core (17.837 km²)**, and a **1 km external buffer (57.939 km²)** to capture cross-boundary park sheds and drainage outfalls (`MAP 01`).

### 1.1 Data Sources, Licensing & Known Limitations

| Dataset | Source Organization | Resolution / Coverage | Temporal Reference | Key Limitation / Handling |
| :--- | :--- | :--- | :--- | :--- |
| **Urban Unit Master Plan** | The Urban Unit Punjab | PDF (222 pp) & Annex Maps | 2021 (proj. 2017–2040) | No native SHP released; Annexure 2 georeferenced (`RMSE = 7.12 m`) |
| **OpenStreetMap Roads, Parks, Waterways** | OSM / Overpass API | Vector lines/polygons | 2026-11-12 extract | Potential omission of informal neighbourhood lawns or locked gates |
| **MS Global ML Building Footprints** | Microsoft / QuadKey `123103232` | Vector polygons (**13,087** in MC) | Feb 2026 release | Footprint roofs only; height & occupancy attributes absent |
| **Sentinel-2 L2A Multispectral** | Copernicus / Planetary Computer | 10 m / 20 m (`T43SDR`) | May 2025 (dry), Aug 2022 & Sep 2025 (monsoon) | PB 04.00+ offset `(DN - 1000)/10000` applied |
| **Sentinel-1 RTC C-Band SAR** | Copernicus / Planetary Computer | 10 m (`VV` & `VH`) | Aug 2025 (`08-05/15/23/27`) | Dense building walls/shadows masked out to prevent false floodwater |
| **Copernicus DEM GLO-30** | ESA Copernicus | 30 m DSM | Reference 2011–2015 | Preliminary screening only; cannot resolve roadside drain inverts |
| **CHIRPS v2.0 Rainfall** | UCSB / NOAA ERDDAP | `0.05°` (~5.5 km) monthly | 1981–2025 | Cannot distinguish street-to-street micro-storm differences |
| **GHSL Population Grid (`R2023A`)** | JRC European Commission | 100 m Mollweide | 2020 & 2025 epochs | ~2.3x Urban Unit projection; treated as spatial weighting grid |
| **JRC Global Surface Water v1.4** | EC-JRC | 30 m (`70E_40N`) | 1984–2021 | Misses short-duration urban pluvial ponding (<1 month) |

*Full provenance metadata and municipal data request checklists are maintained in [`Narowal_Data_Acquisition_Register.xlsx`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/01_Project_Documentation/Narowal_Data_Acquisition_Register.xlsx) and [`Narowal_Municipal_Data_Acquisition_Plan.xlsx`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/01_Project_Documentation/Narowal_Municipal_Data_Acquisition_Plan.xlsx).*

---

## 2. Urban Baseline & Land Use / Land Cover (Phase 2A)

A supervised 6-class **Random Forest** classification on cloud-free dry-season Sentinel-2 L2A imagery (`2025-05-16`) combined with NDVI, NDBI, NDWI, and brightness bands achieved **91.17% Overall Accuracy** (`Kappa = 0.888`) across independent validation samples (`MAP 01`):

| LULC Class | MC Area (km²) | MC Area (ha) | Share of MC (%) | Planning Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **1. Built-up** | 7.5824 | 758.24 | 30.44% | Impervious roofs (3.59 km² MS footprints), roads, paved yards |
| **2. Vegetation** | 4.5810 | 458.10 | 18.39% | Trees, roadside foliage, gardens, Sports Complex grass |
| **3. Agricultural land** | 10.4611 | 1,046.11 | 42.00% | Peri-urban farmland — **strictly excluded** from vacant-land candidates |
| **4. Bare soil** | 1.1722 | 117.22 | 4.71% | Unbuilt urban infill plots & disturbed peri-urban tracts |
| **5. Water** | 0.0059 | 0.59 | 0.02% | Open channels & isolated retention ponds |
| **6. Other / Uncertain** | 1.1046 | 110.46 | 4.43% | Transitional construction, brick surfaces, shadow mixtures |
| **Total Preliminary MC** | **24.9072** | **2,490.72** | **100.00%** | — |

---

## 3. Ten-Minute Park Accessibility Assessment (Objective A — Maps 02 & 03)

Replicating and refining the Lahore network-based accessibility workflow for Narowal, we built a topologically cleaned pedestrian network (**1,909 nodes**, **2,450 edges**, **184.87 km** walkable streets inside MC) excluding access-controlled highways, and snapped explicit frontage access gates (`Narowal_Park_Entrances_Preliminary_UTM43N.gpkg`) to compute `800 m` shortest-path service sheds (`4.8 km/h` walking speed).

### 3.1 Multi-Scenario Accessibility Summary Inside Preliminary MC

| Accessibility Scenario | Walkable Streets <=10 min | Streets Share (%) | GHSL 2025 Pop Served | Pop Share (%) | Underserved GHSL Pop | MS Buildings Served (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **All Mapped Parks & Sports Grounds** | 37.76 km | 20.43% | 19,340 | 6.40% | 283,039 | 10.93% (1,430 / 13,087) |
| **Formal Public Parks Only (Faiz Park)** | **20.17 km** | **10.91%** | **17,170** | **5.68%** | **285,208 (94.32%)** | **8.82% (1,154 / 13,087)** |
| **Sites >=10 Acres (Sports Complex)** | 17.59 km | 9.51% | 2,169 | 0.72% | 300,210 | 2.11% (276 / 13,087) |
| **Formal Parks >=10 Acres (None Exist)** | 0.00 km | 0.00% | 0 | 0.00% | 302,379 | 0.00% |
| **Small Neighbourhood Areas (<10 Acres)** | 34.50 km | 18.66% | 18,726 | 6.19% | 283,653 | 10.48% (1,372 / 13,087) |

### 3.2 Spatial Equity & Per-Capita Deficit (`MAP 03`)

- **Severe Spatial Skew:** Existing formal park supply (**Faiz Ahmad Faiz Park**, 3.19 ha at `32.0954°N, 74.8947°E`) is anchored on Narowal's eastern half, leaving the dense old-city core (*Eidgah Road, Tariq Pura, Sadiq Pura, Model Town, Manak Road, Zafarwal Road*) **1,200–3,300 m** from any formal park.
- **Highest-Deficit Grid Cells:** Thirty-eight 300 m hexagonal/square population cells across the central and western wards experience **100% population outside the 10-minute formal park shed**, led by Cell 122 (`6,079` GHSL pop), Cell 123 (`5,996`), Cell 138 (`5,821`), Cell 155 (`5,741`), and Cell 125 (`5,400`).
- **WHO Benchmark Gap:** Formal green provision is **0.11–0.24 m²/person** versus **9.0 m²/person WHO standard**, demonstrating that relying solely on large peripheral parks cannot solve Narowal's neighbourhood deficit—distributed **0.4–3.0 ha pocket and detention parks** inside the urban core are essential.

---

## 4. Urban Flood, Rainfall & Drainage Assessment (Objective B — Maps 04 to 08)

### 4.1 Rainfall Climatology & Monsoon Flood Evidence (`MAP 04`)

- **CHIRPS v2.0 (1981–2024):** Mean annual precipitation over Narowal (`32.125°N, 74.875°E`, `0.05°` cell) is **779.8 mm/yr**, with **542.1 mm (69.5%)** falling during July–September. Extreme years include `1990` (**1,102.0 mm**), `2013` (**1,091.8 mm**), `2020` (**1,050.3 mm**), and `2021` (**1,049.0 mm**).
- **Sentinel-1 SAR & Sentinel-2 Optical Cross-Check:** Post-vs-pre event RTC change detection across the **August 2025 Punjab Monsoon** identified **657,121 AOI pixels (6,571.2 ha)** on `2025-08-27` (`Asc-100`, including **236.8 ha inside preliminary MC** concentrated along eastern/southern peri-urban fringes and unbuilt depressions) and **18,656 AOI pixels (186.6 ha)** on `2025-08-23` (`Desc-34`). Dense building footprints (`MS Buildings + 3 m buffer`) were explicitly excluded to avoid radar shadow misclassification.

### 4.2 Topographic Screening & Drainage Gap (`MAP 05`, `MAP 07`, `MAP 08`)

Using Priority-Flood epsilon conditioning on **Copernicus DEM GLO-30 (30 m)** (`230.0–258.8 m` elevation range), we derived **Height Above Nearest Drainage (HAND)**, **Topographic Wetness Index (TWI)**, and **D8 Flow Accumulation** lines (`>= 120` cells convergence, clearly labeled *inferred*—never conflated with observed municipal drains).

Overlaying **Observed Waterways** and **Urban Unit (2021) Sewerage Assets** (*Rasinwal 16 cusec*, *Zafarwal Rd 25 cusec*, *Proposed WWTP* toward Nullah Daik) reveals acute drainage gaps across central and northern urban catchments where high surface convergence meets dense impervious surfaces without mapped storm outlets (`MAP 08`: 12 Drainage Investigation Priority Zones `DRN_PRIO_01`–`12`, led by `DRN_PRIO_01` = **141.27 ha**, `DRN_PRIO_02` = **106.46 ha**, `DRN_PRIO_03` = **106.15 ha**).

### 4.3 Provisional Multi-Indicator Flood Susceptibility & Sensitivity (`MAP 06`)

Because historical street-level municipal dewatering logs (Rescue 1122/MC) are pending, weights were renormalized proportionally over the **5 available indicators** (`Historical Inundation 29.41%`, `Flow Acc/TWI 23.53%`, `HAND Relative Elevation 17.65%`, `Imperviousness 17.65%`, `Drainage Deficiency 11.76%`):

| Susceptibility Class | MC Area (km²) | MC Share (%) | Sensitivity Range Across 3 Alternative Weight Schemes |
| :--- | :---: | :---: | :--- |
| **1 - Very Low** | 4.981 | 20.0% | Model correlation vs. Primary (`Pearson r`): |
| **2 - Low** | 6.227 | 25.0% | - Equal Weights (20% each): **r = 0.9677** (78.77% class match) |
| **3 - Moderate** | 6.227 | 25.0% | - Terrain-Dominant (60% Facc+HAND): **r = 0.9326** (65.96% class match) |
| **4 - High** | 4.483 | 18.0% | - Urban Pluvial-Dominant (35% Imperviousness): **r = 0.8742** |
| **5 - Very High** | **2.989** | **12.0%** | Combined High + Very High Area: **7.472 km² (30.0%)** |

---

## 5. Green Infrastructure Suitability & Priority Intervention Plan (Objective C — Maps 09 to 11)

### 5.1 Vacant & Underutilised Land Screening (`MAP 09`)

Restricting selection strictly inside the **Built-Up Urban Core** (`17.837 km²`) and masking out all MS Buildings (+3 m), Roads (+6 m), Waterways (+15 m), existing parks, JRC permanent water, and restricted prison land yields **45 open urban parcels >= 0.2 ha** totaling **90.70 ha**:
- **Government / Proposed Park Corridor (`2` parcels, 6.71 ha):** Includes the Urban Unit (2021) **Manak Road Railway Strip** (`GI_SITE_01`).
- **Institutional Open Grounds (`5` parcels, 11.01 ha):** Schools, colleges, and university open margins suitable for shared-use courtyard retrofits.
- **Unverified Urban Plots (`38` parcels, 72.98 ha):** Strictly tagged `Ownership Unknown — Cadastre Verification Required`.

### 5.2 Green Infrastructure Suitability Model (`MAP 10`)

Integrating Flood Susceptibility (**30%**), Park Deficit Distance (**25%**), Open/Buildable Land (**20%**), GHSL 500 m Population Pressure (**15%**), and Drainage Connectivity (**10%**) with hard exclusion masks identifies **5.200 km²** of High/Very High GI suitability inside MC (`sensitivity r = 0.9048–0.9723`).

### 5.3 Shortlist of 8 Priority Intervention Sites (`MAP 11`)

| Site ID | Location | Est. Area (ha) | Park Dist (m) | 500m Pop (GHSL) | GI Score | Flood Class (Site Pixel) | Recommended Intervention | Tier & Pre-Design Gate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **`GI_SITE_01`** | **Manak Road Railway Open Strip** (Urban Unit Proposed Park) | 2.85 | 2,803 | 30,080 | **4.14** | Low (2.47/5) | Retention / Detention Park | **Priority 1** (Railway NOC, 0.2m topo, soil Ksat) |
| **`GI_SITE_02`** | **Tariq Pura / Sadiq Pura** Underserved Cluster | 0.95 | 2,121 | 28,388 | **3.36** | Moderate (2.56/5) | Detention Pocket Park & Rain Gardens | **Priority 1** (Cadastre check + **sewage separation gate**) |
| **`GI_SITE_03`** | **Model Town / Kachahry Rd** Central Neighbourhood | 0.72 | 1,873 | 34,770 | **3.95** | Moderate (2.53/5) | Rain Gardens & Permeable Courtyard Retrofit | **Priority 1** (Institutional MoU + drain invert check) |
| **`GI_SITE_07`** | **Circular Rd – Faiz Park** East-West Walking Corridor | 1.40 | 772 | 20,730 | **2.33** | Low (2.32/5) | Green Walking Corridor & Roadside Bioswales | **Priority 1** (Municipal ROW; quick-win safe walk link) |
| **`GI_SITE_04`** | **Eidgah Rd / Old City** High-Density Core | 0.45 | 2,367 | 43,856 | **3.13** | Very Low (2.18/5) | Neighbourhood Pocket Park & Street Rain Gardens | **Priority 2** (Cadastre + utility conflict check) |
| **`GI_SITE_05`** | **Rasinwal / N. Circular Rd** Convergence Zone | 1.60 | 2,767 | 21,416 | **3.33** | Low (2.25/5) | Bioswale & Detention Basin + Drain Rehab | **Priority 2** (**Strict Rasinwal sewage isolation**) |
| **`GI_SITE_06`** | **Zafarwal Rd / SW Bypass** Drainage Corridor | 2.10 | 3,288 | 8,560 | **2.91** | Moderate (2.59/5) | Retention Park & Road-Corridor Bioswale | **Priority 2** (Hydraulic tie-in above disposal station) |
| **`GI_SITE_08`** | **University of Narowal** Eastern Sector Greenway | 2.40 | 1,294 | 4,610 | **2.24** | Very Low (2.06/5) | Detention Greenbelt & Public Campus Park | **Priority 3** (University MoU for public walking hours) |

---

## 6. Governance, Phased Implementation Roadmap & Immediate Next Actions

### Phase A: 0–6 Months (Validation, Governance & Quick Wins)
1. **Municipal Data Handover:** Worshipful Mayor issues directive via MC Narowal Focal Person for datasets `MDR-01` to `MDR-09` (Official MC shapefile, Rescue 1122 dewatering log, PHED sewer drawings, BOR Khasra records).
2. **Two-Week Field Verification Campaign:** Deploy [`Narowal_GI_Field_Survey123_QField_Form.xlsx`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/06_Field_Verification/Narowal_GI_Field_Survey123_QField_Form.xlsx) to audit park gates, `DRN_PRIO_01`–`12`, sewage dry-weather flows, and `GI_SITE_01`–`08`.
3. **Initiate Priority 1 Pilots (`GI_SITE_01`, `GI_SITE_03`, `GI_SITE_07`):** Negotiate Pakistan Railways NOC for **Manak Rd Strip**, retrofit institutional courtyards in **Model Town**, and establish shaded pedestrian + bioswale linkages along **Circular Road**.

### Phase B: 6–18 Months (Detailed Engineering Design & Sewage Separation)
- Commission **0.2 m DGPS topographic surveys**, **ASTM double-ring soil infiltration testing**, and **1D/2D SWMM/HEC-RAS hydraulic modelling** fed by **PMD daily/hourly rainfall IDF curves**.
- Coordinate **PHED sanitary interceptor sewers** with proposed **WWTP (Ghausia Rd Ext)** so unlined SuDS treat **clean surface runoff only**.

### Phase C: 18–36 Months (Citywide Green Network & Monitoring)
- Construct **Priority 2 & 3** detention parks (`GI_SITE_02`, `04`, `05`, `06`, `08`), protect Nullah Daik & tributary buffers via municipal zoning, and track 10-minute park accessibility progress inside the **Narowal File Geodatabase** and **Interactive Web GIS Portal**.

---

## 7. Complete Project Deliverables Index

- **Geodatabase:** [`Narowal_Green_Infrastructure.gdb`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/04_Geodatabase/Narowal_Green_Infrastructure.gdb)
- **Cartographic Atlas (`MAP 01`–`MAP 11`, PDF + 300 DPI PNG):** `05_Maps/01_Urban_Baseline/` through `05_Maps/06_Intervention_Plan/`
- **Interactive Web GIS Decision App + EPSG:4326 GeoJSONs:** [`05_Maps/Narowal_WebGIS_App/index.html`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/05_Maps/Narowal_WebGIS_App/index.html)
- **Municipal Request Register (5 Sheets):** [`Narowal_Municipal_Data_Acquisition_Plan.xlsx`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/01_Project_Documentation/Narowal_Municipal_Data_Acquisition_Plan.xlsx)
- **Field Survey XLSForm & Plan:** [`Narowal_GI_Field_Survey123_QField_Form.xlsx`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/06_Field_Verification/Narowal_GI_Field_Survey123_QField_Form.xlsx) & [`Narowal_Field_Verification_Plan.md`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/06_Field_Verification/Narowal_Field_Verification_Plan.md)
- **Mayoral Briefing Deck:** [`Narowal_Mayoral_Briefing_UGI_Plan.pptx`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/10_Presentation/Narowal_Mayoral_Briefing_UGI_Plan.pptx)
