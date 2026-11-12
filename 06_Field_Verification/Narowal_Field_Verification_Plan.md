# Narowal Urban Green Infrastructure & Flood Resilience Initiative
## Phase 5 Field Verification Protocol & Survey123 / QField Deployment Guide

**Location:** Narowal Municipal Corporation (MC) Preliminary Study Area (`EPSG:32643` / `EPSG:4326`)  
**Prepared:** 2026-11-12  
**Companion Form:** [`Narowal_GI_Field_Survey123_QField_Form.xlsx`](file:///C:/Users/LENOVO/.gemini/antigravity/scratch/Narowal_Urban_Green_Infrastructure/06_Field_Verification/Narowal_GI_Field_Survey123_QField_Form.xlsx)  
**Priority Target Layers:** `p4_priority_intervention_sites` (`GI_SITE_01`–`GI_SITE_08`), `p4_vacant_candidate_sites`, `p3_drainage_investigation_priorities` (`DRN_PRIO_01`–`12`), and existing parks/sports complexes.

---

## 1. Purpose of Field Verification

Remote sensing, OpenStreetMap (OSM), Global Human Settlement Layer (GHSL), and the Urban Unit (2021) Master Plan establish a **screening-level spatial decision framework** for Narowal. However, desktop GIS cannot substitute for municipal engineering due diligence. Field verification is **mandatory before land allocation, detailed engineering design (DED), or civil contracting** to resolve five critical unknowns:

1. **Public Park Access & Gates:** Confirm actual pedestrian entrance gates, opening hours, entry fees, boundary wall closures, and women/family safety at Faiz Ahmad Faiz Park, Narowal Sports Complex, and any unmapped neighbourhood parks omitted from OSM.
2. **Historical Flood & Waterlogging Calibration:** Ground-truth the 12 DEM/drainage hotspots (`DRN_PRIO_01`–`12`) and Urban Unit (2021, p. 20) reported flood streets (*Eidgah Road, Church Road, Kachahry Road, Tariq Pura, Sadiq Pura, Model Town*) where dense multi-storey urban streets attenuate C-band Sentinel-1 radar and 30 m Copernicus DEM cannot resolve street curbs.
3. **Raw Sewage vs. Clean Stormwater Separation (CRITICAL GATE):** Inspect dry-weather drain flow at all candidate SuDS sites. **Never route domestic sewage or greywater into unlined rain gardens, bioswales, or infiltration basins.**
4. **Land Ownership, Encroachment & Active Use:** Verify Khasra/Mauza title and active informal uses on the 8 shortlisted priority intervention locations (`GI_SITE_01`–`GI_SITE_08`) and candidate `VAC_XX` parcels before committing municipal budgets.
5. **Micro-Topography & Soil Permeability:** Identify drainage invert bottlenecks and commission ASTM double-ring infiltrometer tests plus groundwater depth borings where infiltration SuDS are proposed.

---

## 2. Field Team Modules & Target Locations

| Module | Geographic Targets | Field Protocol | Key XLSForm Fields |
| :--- | :--- | :--- | :--- |
| **A. Park & Pedestrian Access Audit** | Faiz Ahmad Faiz Park (`way/519685072`), Narowal Sports Complex (`way/860471284`), Circular Rd Corridor (`GI_SITE_07`), institutional grounds (`GI_SITE_08`) | Walk complete perimeter; log unlocked vs. locked gates; measure sidewalk gaps, railway/highway crossing hazards, dusk lighting, and women/elderly accessibility. | `Pedestrian_Access_Constraints`, `Safety_Lighting_Status` |
| **B. Flood & Drainage Walkover** | `DRN_PRIO_01`–`12`, Eidgah Rd, Church Rd, Kachahry Rd, Tariq Pura, Sadiq Pura, Model Town, Rasinwal & Zafarwal Rd disposal catchments | Interview >=3 residents/shopkeepers per hotspot regarding 2022–2025 monsoon ponding depth (cm) and hours to drain; check silt/solid-waste choking and damaged culverts. | `Observed_Waterlogging_History`, `Max_Ponding_Depth_cm`, `Drain_Condition`, `Drain_Dimensions_m` |
| **C. Sewage Separation Gate Check** | Upstream catch-basins feeding `GI_SITE_01`–`GI_SITE_08` (especially `GI_SITE_02`, `GI_SITE_05`, `GI_SITE_06`) | Conduct dry-weather manhole/drain inspection for septic odor, black/grey sullage, or latrine pipe outfalls. Flag `Yes` as conditional pending sanitary diversion/WWTP interceptor. | `Sewage_Contamination_Suspected` |
| **D. Candidate Parcel & Title Check** | `GI_SITE_01`–`GI_SITE_08` + top candidate `VAC_XX` open urban parcels | Confirm whether parcel remains unbuilt vs. newly constructed; log squatting, brick kilns, utility transformers, boundary walls; take 4 directional geotagged photos. | `Current_Land_Use_Verified`, `Land_Ownership_Category`, `Encroachment_Observed` |
| **E. Geotechnical & Micro-Survey Prep** | Sites passing Modules C & D (`confirm_proceed` or `conditional`) | Mark exact stake-out locations for licensed Total-Station/DGPS survey (0.2 m contours) and double-ring infiltrometer / auger water-table pit. | `Soil_Type_Infiltration_Note`, `Percolation_Test_Required` |

---

## 3. Recommended 2-Week Deployment Schedule

- **Days 1–2 (Orientation & Calibration):** Upload `Narowal_GI_Field_Survey123_QField_Form.xlsx` into ArcGIS Survey123 Connect (or convert for QField/QGIS). Load offline basemaps + geopackages (`mc_boundary_preliminary`, `p4_priority_intervention_sites`, `p3_drainage_investigation_priorities`) onto tablets. Meet MC Narowal Focal Person and Rescue 1122 to obtain historical dewatering logbook entries.
- **Days 3–5 (Existing Parks & Priority 1 Sites):** Complete perimeter park gate audits + field verification of `GI_SITE_01` (Manak Rd Strip), `GI_SITE_02` (Tariq Pura / Sadiq Pura), `GI_SITE_03` (Model Town / Kachahry Rd), and `GI_SITE_07` (Circular Rd Corridor).
- **Days 6–9 (Drainage Hotspots & Priority 2/3 Sites):** Inspect `GI_SITE_04`, `GI_SITE_05`, `GI_SITE_06`, `GI_SITE_08` and walk all 12 `DRN_PRIO` zones + Urban Unit named flooded streets during dry weather to confirm raw-sewage isolation.
- **Days 10–12 (Cadastre Cross-Check & QA):** Match verified `VAC_XX` / `GI_SITE_XX` GPS polygons against BOR/Assistant Commissioner Mauza sheets and Pakistan Railways ROW registers (for `GI_SITE_01`). Synchronize CSV + geotagged photos back into `Narowal_Green_Infrastructure.gdb`.

---

## 4. Decision Rules After Field Sync

- **Reject Site:** Parcel already built over, private residential dispute with high acquisition cost, or immovable industrial contamination. Replace from next-highest `VAC_XX` parcel in the same park-deficit neighbourhood.
- **Conditional (Engineering Diversion First):** `Sewage_Contamination_Suspected == Yes` -> Redesign as stormwater-only closed conveyance + landscaped dry park, OR complete sanitary sewer diversion prior to constructing bioretention.
- **Confirmed Proceed:** Unbuilt public/institutional parcel + clean stormwater catchment + verified waterlogging/deficit -> Issue work order for **0.2 m DGPS topographic survey** and **soil percolation testing**.
