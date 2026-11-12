"""Phase 5A: Generate Municipal Data Acquisition Plan Workbook (5 sheets) & Survey123/QField XLSForm."""

import os
import pandas as pd

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
DOC_DIR = os.path.join(ROOT, "01_Project_Documentation")
FIELD_DIR = os.path.join(ROOT, "06_Field_Verification")
os.makedirs(DOC_DIR, exist_ok=True)
os.makedirs(FIELD_DIR, exist_ok=True)


def build_municipal_acquisition_workbook():
    out_xlsx = os.path.join(DOC_DIR, "Narowal_Municipal_Data_Acquisition_Plan.xlsx")

    # Sheet 1: Data Request Register
    s1 = pd.DataFrame([
        {
            "Request_ID": "MDR-01",
            "Dataset_Requested": "Official Notified Municipal Corporation Narowal Boundary & Ward Boundaries",
            "Custodian_Agency": "Municipal Corporation Narowal / LG&CD Punjab",
            "Preferred_Format": "Shapefile / FileGDB / GeoJSON (EPSG:32643 or EPSG:4326)",
            "Required_Attributes": "MC_Name, Notification_No, Gazette_Date, Ward_No, Ward_Name",
            "Target_Study_Objective": "Study Area, Park Deficit Equity, Ward-Level Budget Allocation",
            "Priority": "Critical (Gate 1)",
            "Status": "Pending Official Release",
            "Workaround_Used_Currently": "Preliminary MC boundary (24.91 km2) digitized from Urban Unit (2021) Annexure 2 & OSM/MS Buildings",
            "Action_Required_From_Authority": "Issue signed/stamped notification map or GIS polygon shapefile via Mayor's Office",
        },
        {
            "Request_ID": "MDR-02",
            "Dataset_Requested": "Official Public Park Inventory, Lease Boundaries & Park Entrance Gates",
            "Custodian_Agency": "Municipal Corporation Narowal (Parks & Horticulture Wing)",
            "Preferred_Format": "GIS Polygon/Point + Tabular Register (Excel)",
            "Required_Attributes": "Park_ID, Name, Area_Kanals, Gate_Access_Hours, Ownership_Status, Maintenance_Status",
            "Target_Study_Objective": "Objective A: 10-Minute Park Accessibility & Per-Capita Green Space",
            "Priority": "High",
            "Status": "Pending Official Release",
            "Workaround_Used_Currently": "OSM mapped parks + Sports Complex + Urban Unit (2021) Proposed Manak Rd Park",
            "Action_Required_From_Authority": "Confirm all neighbourhood parks, fenced/restricted grounds, and actual open pedestrian gates",
        },
        {
            "Request_ID": "MDR-03",
            "Dataset_Requested": "Urban Sewerage & Stormwater Drain Network Map (Pipes, Open Drains, Invert Levels, Catchments)",
            "Custodian_Agency": "Municipal Corporation Narowal / PHED Punjab",
            "Preferred_Format": "CAD/DXF, Shapefile, or As-Built Engineering Drawings + Asset Register",
            "Required_Attributes": "Pipe_Diam_mm, Material, Invert_Elev_m, Flow_Dir, Combined_vs_Storm, Outfall_ID",
            "Target_Study_Objective": "Objective B & C: Drainage Deficiency & Sewage-Stormwater Separation",
            "Priority": "Critical (Engineering Gate)",
            "Status": "Missing in Open Data",
            "Workaround_Used_Currently": "Urban Unit (2021) disposal station coords (Rasinwal 16 cusec, Zafarwal Rd 25 cusec) + GLO-30 convergence lines",
            "Action_Required_From_Authority": "Provide sewerage/drainage network drawings and clarify combined vs. separate storm drains",
        },
        {
            "Request_ID": "MDR-04",
            "Dataset_Requested": "Historical Urban Waterlogging & Flood Incident Log (2018-2026)",
            "Custodian_Agency": "Rescue 1122 Narowal / PDMA Punjab / MC Dewatering Cell",
            "Preferred_Format": "CSV/Excel with Street Names, Dates, Ponding Depth & Duration",
            "Required_Attributes": "Incident_Date, Street_Mohalla, Lat_Lon, Dewatering_Hours, Max_Depth_cm, Cause",
            "Target_Study_Objective": "Objective B: Flood Model Calibration & Street-Level Validation",
            "Priority": "Critical (Validation Gate)",
            "Status": "Partial Narrative Only",
            "Workaround_Used_Currently": "Urban Unit (2021) p.20 named streets + Sentinel-1 Aug 2025 SAR & Sentinel-2 MNDWI screening",
            "Action_Required_From_Authority": "Share monsoon emergency dewatering logs and street complaints from 2022-2025 monsoons",
        },
        {
            "Request_ID": "MDR-05",
            "Dataset_Requested": "Land Ownership & Revenue Cadastre (Khasra / Mauza / State & Railway Land) for Priority Sites",
            "Custodian_Agency": "Assistant Commissioner / Revenue Dept (BOR Punjab) / Pakistan Railways",
            "Preferred_Format": "Digitized Mauza Sheets / Khasra Parcel Shapefiles + Title Status Table",
            "Required_Attributes": "Mauza_Name, Khasra_No, Owner_Category (State/MC/Railway/Evacuee/Private), Encroachment_Flag",
            "Target_Study_Objective": "Objective C: Land Acquisition Feasibility for GI Sites GI_SITE_01 to GI_SITE_08",
            "Priority": "Critical (Implementation Gate)",
            "Status": "Not Available Publicly",
            "Workaround_Used_Currently": "Vacant open parcels mapped from Sentinel-2 & MS Buildings labeled 'Ownership Unknown'",
            "Action_Required_From_Authority": "Verify public title / NOC feasibility for shortlisted vacant parcels before design tender",
        },
        {
            "Request_ID": "MDR-06",
            "Dataset_Requested": "High-Resolution Urban Topographic Survey / LiDAR / UAV Ortho + Sub-Meter Spot Levels",
            "Custodian_Agency": "Urban Unit Punjab / C&W Dept / Survey Contractor",
            "Preferred_Format": "DEM GeoTIFF (<=0.5 m) or Surveyed Spot Levels + 0.2 m Contours",
            "Required_Attributes": "Elevation_m_MSL, Curb_Level_m, Drain_Bed_m, Benchmark_Control",
            "Target_Study_Objective": "Objective B & C: Engineering SuDS Sizing, Cut/Fill, Hydraulic Invert Design",
            "Priority": "High (Design Phase)",
            "Status": "Not Available",
            "Workaround_Used_Currently": "Copernicus DEM GLO-30 (30 m DSM - preliminary screening only)",
            "Action_Required_From_Authority": "Commission UAV photogrammetry or DGPS total-station survey across Priority Sites 1-8",
        },
        {
            "Request_ID": "MDR-07",
            "Dataset_Requested": "Official 2023 Census Block/Ward Population & Housing Counts",
            "Custodian_Agency": "Pakistan Bureau of Statistics (PBS) / District Administration",
            "Preferred_Format": "Excel / Shapefile of Census Circles & Blocks",
            "Required_Attributes": "Block_Code, Pop_2017, Pop_2023, Households, Growth_Rate",
            "Target_Study_Objective": "Objective A & C: Reconcile GHSL (302k) vs Urban Unit Projection (132k)",
            "Priority": "High",
            "Status": "Discrepancy Flagged",
            "Workaround_Used_Currently": "GHSL 2025 (100 m) & Urban Unit (2021) Table 2-1 reported side-by-side",
            "Action_Required_From_Authority": "Provide PBS 2023 final block-level population inside Narowal MC boundary",
        },
        {
            "Request_ID": "MDR-08",
            "Dataset_Requested": "Daily Rain Gauge Measurements (PMD Narowal Station, 2014-2026)",
            "Custodian_Agency": "Pakistan Meteorological Department (PMD) / Irrigation Dept",
            "Preferred_Format": "CSV/Excel Daily Rainfall Series (mm/day)",
            "Required_Attributes": "Date, Daily_Rainfall_mm, Storm_Intensity_mm_hr (if tipping bucket available)",
            "Target_Study_Objective": "Objective B & C: Design Storm IDF Curve for SuDS Volume Sizing",
            "Priority": "Medium-High",
            "Status": "Pending Official Request",
            "Workaround_Used_Currently": "CHIRPS v2.0 (0.05 deg monthly climatology 1981-2025; mean 779.8 mm/yr)",
            "Action_Required_From_Authority": "Obtain PMD station daily/hourly storm maxima for 2-, 5-, 10-, and 25-year IDF calculation",
        },
        {
            "Request_ID": "MDR-09",
            "Dataset_Requested": "Shallow Groundwater Depth & Soil Geotechnical / Percolation Logs",
            "Custodian_Agency": "PHED / Punjab Irrigation Dept (SCARP/DLR)",
            "Preferred_Format": "Borehole Log Table + Seasonal Depth-to-Watertable (m bgl)",
            "Required_Attributes": "Location, Pre_Post_Monsoon_WT_m, Soil_Class, Infiltration_K_mm_hr",
            "Target_Study_Objective": "Objective C: Select Infiltration (Rain Garden/Bioswale) vs. Lined Detention",
            "Priority": "High (Pre-Design)",
            "Status": "Missing",
            "Workaround_Used_Currently": "Flagged as mandatory pre-design geotechnical test on all 8 GI sites",
            "Action_Required_From_Authority": "Conduct double-ring infiltrometer & auger tests at GI_SITE_01 to GI_SITE_08",
        },
    ])

    # Sheet 2: Department Contact - Responsibility (ZERO fabricated contacts!)
    s2 = pd.DataFrame([
        {
            "Agency_Department": "Municipal Corporation Narowal (Mayor Office & Municipal Officer Infrastructure)",
            "Role_in_Project": "Project Owner, Park Maintenance, Drain Desilting, Municipal Land Allocation, ROW Permits",
            "Datasets_Held": "MC Boundary, Park Register, Municipal Open Plots, Street Dewatering Logs",
            "Named_Contact_Person": "Not Verified in Public Documents - Municipal Liaison Required",
            "Phone_Email_Official": "Not Verified in Public Documents - Confirm via Mayor's Secretariat",
            "Verification_Note": "Do not assume officer names; establish focal person during Phase 5 Inception Briefing.",
        },
        {
            "Agency_Department": "The Urban Unit (Urban Sector Planning & Management Services Unit), Lahore",
            "Role_in_Project": "Regional Master Plan Custodian, Technical Advisor on Urban Water & GIS Standards",
            "Datasets_Held": "Narowal Regional Master Plan GIS layers (Disposal Stations, Proposed WWTP, Land Use)",
            "Named_Contact_Person": "Not Verified in Public Documents - Technical Request Required",
            "Phone_Email_Official": "Not Verified in Public Documents - Official portal urbanunit.gov.pk",
            "Verification_Note": "2021 Master Plan PDF downloaded and cited; request original vector shapefiles formally.",
        },
        {
            "Agency_Department": "Public Health Engineering Department (PHED) Punjab - Narowal Division",
            "Role_in_Project": "Sewerage Trunk Design, Disposal Station Operations, WWTP Execution Authority",
            "Datasets_Held": "Rasinwal (16 cusec) & Zafarwal Rd (25 cusec) pump curves, trunk sewer profiles",
            "Named_Contact_Person": "Not Verified in Public Documents - Official Liaison Required",
            "Phone_Email_Official": "Not Verified in Public Documents",
            "Verification_Note": "Essential partner to enforce raw sewage separation prior to SuDS construction.",
        },
        {
            "Agency_Department": "Rescue 1122 & District Disaster Management Authority (DDMA) Narowal",
            "Role_in_Project": "Monsoon Flood Emergency Response & Historical Waterlogging Incident Validation",
            "Datasets_Held": "Monsoon street flood dispatch coordinates, pumping records (2018-2026)",
            "Named_Contact_Person": "Not Verified in Public Documents - Official Liaison Required",
            "Phone_Email_Official": "Not Verified in Public Documents",
            "Verification_Note": "Provides independent ground truth for validating Sentinel-1/DEM flood hotspots.",
        },
        {
            "Agency_Department": "Board of Revenue (BOR) / Assistant Commissioner Office Narowal",
            "Role_in_Project": "Land Title Verification, State Land Identification, Cadastral Clearance",
            "Datasets_Held": "Mauza Revenue Records, Khasra Ownership, Evacuee Trust / State Land Registers",
            "Named_Contact_Person": "Not Verified in Public Documents - Official Liaison Required",
            "Phone_Email_Official": "Not Verified in Public Documents",
            "Verification_Note": "Mandatory clearance step before committing municipal funds to GI_SITE_02/04/05/06.",
        },
        {
            "Agency_Department": "Pakistan Railways (Lahore/Narowal Division) & C&W Highway Dept",
            "Role_in_Project": "Inter-Departmental NOC for Manak Rd Railway Strip & Arterial Road Bioswales",
            "Datasets_Held": "Railway ROW Maps (GI_SITE_01), Circular/Zafarwal Road ROW Drawings (GI_SITE_06/07)",
            "Named_Contact_Person": "Not Verified in Public Documents - Official Liaison Required",
            "Phone_Email_Official": "Not Verified in Public Documents",
            "Verification_Note": "Required for Urban Unit Proposed Manak Rd Park (GI_SITE_01) & Circular Rd Corridor (GI_SITE_07).",
        },
        {
            "Agency_Department": "Punjab Irrigation Department & PMD / PBS",
            "Role_in_Project": "Nullah Daik Outfall Hydraulic Constraints, Rainfall Gauges, Census Block Figures",
            "Datasets_Held": "Nullah flows, PMD daily station rain records, PBS 2023 Census block tables",
            "Named_Contact_Person": "Not Verified in Public Documents - Official Liaison Required",
            "Phone_Email_Official": "Not Verified in Public Documents",
            "Verification_Note": "Request via District Coordination Committee.",
        },
    ])

    # Sheet 3: Data Availability Status
    s3 = pd.DataFrame([
        {
            "Data_Domain": "Municipal & Built-Up Boundaries",
            "Current_Open_Proxy_Available": "Preliminary MC boundary (24.91 km2) from Urban Unit 2021 Fig/Annexure + Built-up core (17.84 km2)",
            "Missing_Municipal_Dataset": "Notified Gazette Municipal & Ward Shapefiles",
            "Impact_on_Current_Analysis": "Boundary uncertainty along peri-urban fringe (+/- 100-300 m)",
            "Confidence_Level_Current": "Moderate (Clearly labeled Preliminary)",
            "Next_Step": "Obtain official MC GIS polygon",
        },
        {
            "Data_Domain": "Parks & Pedestrian Street Network",
            "Current_Open_Proxy_Available": "OSM walkable streets (184.87 km in MC), Faiz Park, Sports Complex, explicit frontage entrances",
            "Missing_Municipal_Dataset": "Complete MC park inventory, informal neighbourhood lawns, school open-hour policies",
            "Impact_on_Current_Analysis": "Unmapped small municipal parks (<0.2 ha) could slightly understate current coverage",
            "Confidence_Level_Current": "High for major mapped parks; field check needed",
            "Next_Step": "Audit unmapped green parcels via Survey123/QField",
        },
        {
            "Data_Domain": "Population Distribution",
            "Current_Open_Proxy_Available": "GHSL 2025 100 m grid (302,379 in MC) & Urban Unit projection (132,194 in 2025)",
            "Missing_Municipal_Dataset": "PBS 2023 Census Block Counts",
            "Impact_on_Current_Analysis": "Absolute underserved headcount differs by ~2.3x depending on source; % share (94.3% unserved) is consistent",
            "Confidence_Level_Current": "Moderate-High (Relative) / Moderate (Absolute)",
            "Next_Step": "Reconcile with PBS 2023 block data",
        },
        {
            "Data_Domain": "Stormwater & Sewerage Infrastructure",
            "Current_Open_Proxy_Available": "Rasinwal & Zafarwal Rd disposal coords, Proposed WWTP, OSM waterways, GLO-30 convergence paths",
            "Missing_Municipal_Dataset": "Pipe network GIS, invert depths, drain cross-sections, blockage locations",
            "Impact_on_Current_Analysis": "Cannot compute hydraulic surcharge or pipe capacity; screening hotspots only",
            "Confidence_Level_Current": "Low-Moderate (Inferred topology)",
            "Next_Step": "Conduct Drainage Walkover & Total-Station Survey",
        },
        {
            "Data_Domain": "Flood & Waterlogging Calibration",
            "Current_Open_Proxy_Available": "S1 RTC Aug 2025 pairs, S2 MNDWI, Urban Unit 2021 p.20 street list",
            "Missing_Municipal_Dataset": "Geo-tagged Rescue 1122 logs & high-water marks inside narrow old-city lanes",
            "Impact_on_Current_Analysis": "10m SAR cannot resolve shallow (<0.2 m) alley ponding under dense roofs",
            "Confidence_Level_Current": "Moderate (Macro screening)",
            "Next_Step": "Interview residents & validate 12 Priority Drainage Zones",
        },
        {
            "Data_Domain": "Cadastral Ownership & Soil Mechanics",
            "Current_Open_Proxy_Available": "Sentinel-2 open plots >=0.2 ha + OSM institutional overlays",
            "Missing_Municipal_Dataset": "Khasra titles, soil Ksat percolation rates, seasonal groundwater table",
            "Impact_on_Current_Analysis": "Shortlisted sites may be private or contaminated with sewage/high water table",
            "Confidence_Level_Current": "Low (Cadastre unverified)",
            "Next_Step": "Revenue title check & geotechnical pit tests",
        },
    ])

    # Sheet 4: Field Verification Requirements
    s4 = pd.DataFrame([
        {
            "Verification_Topic": "1. Park Accessibility & Gate Audit",
            "Target_Locations": "Faiz Ahmad Faiz Park, Sports Complex, Manak Rd Strip, Institutional Playgrounds",
            "Sampling_Protocol": "Walk all perimeter edges; log open vs locked gates, ticketing/fee rules, lighting & women/family safety",
            "Equipment_Method": "QField / Survey123 mobile app, GPS (<5m), timestamped photos",
            "XLSForm_Module": "Pedestrian_Access_Constraints, Safety_Lighting_Status",
            "Required_By_Phase": "Week 1-2 of Phase 5",
        },
        {
            "Verification_Topic": "2. Flooded Street & Drainage Hotspot Ground-Truthing",
            "Target_Locations": "DRN_PRIO_01..12 + Eidgah Rd, Church Rd, Kachahry Rd, Tariq Pura, Sadiq Pura, Model Town",
            "Sampling_Protocol": "Structured resident/shopkeeper interviews (3 per hotspot); mark high-water marks; check drain silt/solid-waste blockage",
            "Equipment_Method": "Survey123 form + measuring tape + geotagged photos",
            "XLSForm_Module": "Observed_Waterlogging_History, Drain_Condition",
            "Required_By_Phase": "Week 1-3 of Phase 5",
        },
        {
            "Verification_Topic": "3. Sewage vs. Stormwater Separation Audit",
            "Target_Locations": "All 8 Priority GI Sites + upstream catch-basins feeding proposed rain gardens/bioswales",
            "Sampling_Protocol": "Visual & odor inspection + dry-weather flow check; NEVER route dry-weather greywater/sewage into unlined infiltration basins",
            "Equipment_Method": "Field checklist + grab sample if questionable",
            "XLSForm_Module": "Sewage_Contamination_Suspected",
            "Required_By_Phase": "Pre-Design Mandatory Gate",
        },
        {
            "Verification_Topic": "4. Candidate Open Parcel Verification",
            "Target_Locations": "GI_SITE_01 to GI_SITE_08 + top 15 VAC_XX vacant parcels from MAP 09",
            "Sampling_Protocol": "Confirm active vs abandoned use, squatting/encroachment, boundary walls, solid waste dumping, utility poles/transformers",
            "Equipment_Method": "Survey123 geopoint + 4-directional photos",
            "XLSForm_Module": "Current_Land_Use_Verified, Encroachment_Observed",
            "Required_By_Phase": "Week 2-4 of Phase 5",
        },
    ])

    # Sheet 5: Engineering Investigation Requirements
    s5 = pd.DataFrame([
        {
            "Investigation_Type": "DGPS / Total-Station Micro-Topographic & Invert Survey",
            "Priority_Sites_Covered": "GI_SITE_01 to GI_SITE_08 + DRN_PRIO_01..12 corridors",
            "Technical_Standard_Scope": "0.2 m contour interval, road crown elevations, drain bed/invert & soffit elevations tied to Survey of Pakistan / GNSS benchmark",
            "Governing_Constraint": "Copernicus GLO-30 (30m DSM) cannot size pipe grades or detention storage volumes",
            "Lead_Discipline": "Licensed Land Surveyor & Urban Hydrologist",
            "Gate_Before_Tender": "Yes - Mandatory for Detailed Engineering Design (DED)",
        },
        {
            "Investigation_Type": "Soil Permeability (Double-Ring Infiltrometer) & Borehole Water Table",
            "Priority_Sites_Covered": "GI_SITE_01, 02, 03, 04, 05, 06, 08",
            "Technical_Standard_Scope": "ASTM D3385 infiltration test (mm/hr), particle size & clay fraction, augered groundwater depth (pre & post monsoon)",
            "Governing_Constraint": "Low-permeability alluvial clays or high water table (<1.5 m) require underdrained bioretention or lined detention instead of infiltration",
            "Lead_Discipline": "Geotechnical Engineer / SuDS Designer",
            "Gate_Before_Tender": "Yes - Determines SuDS cross-section",
        },
        {
            "Investigation_Type": "Sub-Catchment 1D/2D Storm Drainage & Disposal Pump Hydraulic Modelling",
            "Priority_Sites_Covered": "Rasinwal & Zafarwal Rd drainage catchments + Nullah Daik outfall reach",
            "Technical_Standard_Scope": "SWMM / InfoWorks / HEC-RAS 2D coupled street-drain model driven by PMD 2-, 5-, 10-, 25-year IDF design storms",
            "Governing_Constraint": "Assess backwater tailwater effect from Nullah Daik & pump capacity bottlenecks (16 / 25 cusec)",
            "Lead_Discipline": "Urban Hydraulic Engineer",
            "Gate_Before_Tender": "Yes - Validates detention storage volume & overflow weir safety",
        },
        {
            "Investigation_Type": "Environmental & Sewerage Interceptor Pre-Treatment Check",
            "Priority_Sites_Covered": "GI_SITE_02 (Tariq/Sadiq Pura), GI_SITE_05 (Rasinwal), GI_SITE_06 (Zafarwal Rd)",
            "Technical_Standard_Scope": "Identify illicit sanitary connections; design trash racks, sediment forebays & bypass weirs for first-flush isolation",
            "Governing_Constraint": "Zero untreated sanitary sewage permitted inside public park detention basins",
            "Lead_Discipline": "Environmental / Wastewater Engineer",
            "Gate_Before_Tender": "Yes - Public health safeguard",
        },
    ])

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        s1.to_excel(writer, sheet_name="Data Request Register", index=False)
        s2.to_excel(writer, sheet_name="Department Contact - Resp", index=False)
        s3.to_excel(writer, sheet_name="Data Availability Status", index=False)
        s4.to_excel(writer, sheet_name="Field Verification Reqs", index=False)
        s5.to_excel(writer, sheet_name="Engineering Investigation Reqs", index=False)

        # Auto-fit readable column widths
        for sname, df_s in [
            ("Data Request Register", s1),
            ("Department Contact - Resp", s2),
            ("Data Availability Status", s3),
            ("Field Verification Reqs", s4),
            ("Engineering Investigation Reqs", s5),
        ]:
            ws = writer.sheets[sname]
            for idx, col in enumerate(df_s.columns, 1):
                max_len = max(df_s[col].astype(str).map(len).max(), len(col))
                ws.column_dimensions[ws.cell(1, idx).column_letter].width = min(max_len + 4, 48)
    print(f"Saved {out_xlsx}")


def build_survey123_qfield_xlsform():
    out_xls = os.path.join(FIELD_DIR, "Narowal_GI_Field_Survey123_QField_Form.xlsx")

    survey_rows = [
        {"type": "start", "name": "survey_start", "label": "Start Time", "hint": "", "required": "", "constraint": "", "appearance": ""},
        {"type": "today", "name": "Survey_Date", "label": "1. Inspection Date", "hint": "Auto-recorded date", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "text", "name": "Inspector_Name", "label": "Inspector Full Name & Role", "hint": "GIS / Municipal Engineering Team Member", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "select_one site_list", "name": "Site_ID", "label": "2. Target Site / Priority Hotspot ID", "hint": "Select GI_SITE_01..08, DRN_PRIO, or Other", "required": "yes", "constraint": "", "appearance": "autocomplete"},
        {"type": "text", "name": "Site_ID_Other", "label": "Specify Other Site/Street Name", "hint": "Only if Other selected", "required": "no", "constraint": "", "appearance": ""},
        {"type": "geopoint", "name": "GPS_Location", "label": "3. Field GPS Coordinate (WGS 84)", "hint": "Stand at site center or representative drain point; target accuracy < 5 m", "required": "yes", "constraint": "", "appearance": "maps"},
        {"type": "select_one land_use_cat", "name": "Current_Land_Use_Verified", "label": "4. Verified Current Land Use", "hint": "Ground observation overriding satellite LULC", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "select_one ownership_cat", "name": "Land_Ownership_Category", "label": "5a. Preliminary Land Ownership Category", "hint": "Confirm with local patwari / MC inspector", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "text", "name": "Ownership_Source_Evidence", "label": "5b. Ownership Evidence / Signboard / Informant", "hint": "Record Khasra No. or authority signboard if visible", "required": "no", "constraint": "", "appearance": ""},
        {"type": "select_one yes_no", "name": "Encroachment_Observed", "label": "6a. Any Encroachment or Informal Occupation Observed?", "hint": "Temporary stalls, boundary extensions, solid waste dumping, parked trucks", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "text", "name": "Encroachment_Details", "label": "6b. Describe Encroachment Type & Approx % Area Affected", "hint": "Leave blank if None", "required": "no", "constraint": "", "appearance": "multiline"},
        {"type": "select_one waterlog_freq", "name": "Observed_Waterlogging_History", "label": "7a. Observed / Reported Waterlogging History", "hint": "Cross-check with 2+ nearby residents or shopkeepers", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "integer", "name": "Max_Ponding_Depth_cm", "label": "7b. Reported Max Monsoon Ponding Depth (cm)", "hint": "Typical ankle=15, knee=45; enter 0 if none", "required": "yes", "constraint": ". >= 0 and . <= 300", "appearance": ""},
        {"type": "select_one drain_cond_cat", "name": "Drain_Condition", "label": "8a. Adjacent Drain / Outfall Physical Condition", "hint": "Inspect nearest roadside drain or nullah edge", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "text", "name": "Drain_Dimensions_m", "label": "8b. Approx Drain Width x Depth (m) & Flow Direction", "hint": "e.g., 0.6m x 0.4m flowing South", "required": "no", "constraint": "", "appearance": ""},
        {"type": "select_one yes_no_unsure", "name": "Sewage_Contamination_Suspected", "label": "9. Dry-Weather Raw Sewage Contamination Suspected?", "hint": "CRITICAL GATE: Septic odor, black/grey stagnant flow, household latrine pipes emptying into open plot/drain. If YES, unlined infiltration/rain garden CANNOT proceed without diversion.", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "select_one soil_cat", "name": "Soil_Type_Infiltration_Note", "label": "10a. Surface Soil / Cover Permeability Appearance", "hint": "Visual surface texture check", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "select_one yes_no", "name": "Percolation_Test_Required", "label": "10b. Detailed Soil Percolation & Groundwater Test Needed?", "hint": "Recommended Yes for all SuDS basins", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "select_multiple access_barrier_cat", "name": "Pedestrian_Access_Constraints", "label": "11. Pedestrian Access & Connectivity Barriers", "hint": "Check barriers along walking routes within 200 m", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "select_one safety_cat", "name": "Safety_Lighting_Status", "label": "12. Night Lighting, Sightlines & Family Safety Rating", "hint": "Suitability for women, children & elderly", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "image", "name": "Photo_Overview", "label": "13a. Geotagged Photo — Site Overview", "hint": "Capture wide view of open plot or corridor", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "image", "name": "Photo_Drain_Access", "label": "13b. Geotagged Photo — Adjacent Drain / Street Edge", "hint": "Capture drainage condition / invert / bottleneck", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "select_one verdict_cat", "name": "Field_Feasibility_Verdict", "label": "14a. Field Team Feasibility Verdict", "hint": "Overall on-site confirmation", "required": "yes", "constraint": "", "appearance": ""},
        {"type": "text", "name": "Recommendation_and_Notes", "label": "14b. Field Recommendations, Utilities Conflicts & Notes", "hint": "Overhead lines, transformers, school timing, community feedback", "required": "no", "constraint": "", "appearance": "multiline"},
    ]

    choices_rows = [
        ("site_list", "GI_SITE_01", "GI_SITE_01: Manak Road Railway Strip"),
        ("site_list", "GI_SITE_02", "GI_SITE_02: Tariq Pura / Sadiq Pura"),
        ("site_list", "GI_SITE_03", "GI_SITE_03: Model Town / Kachahry Rd"),
        ("site_list", "GI_SITE_04", "GI_SITE_04: Eidgah Rd / Old City"),
        ("site_list", "GI_SITE_05", "GI_SITE_05: Rasinwal Circular Rd Zone"),
        ("site_list", "GI_SITE_06", "GI_SITE_06: Zafarwal Rd SW Corridor"),
        ("site_list", "GI_SITE_07", "GI_SITE_07: Circular Rd - Faiz Park Greenway"),
        ("site_list", "GI_SITE_08", "GI_SITE_08: University of Narowal Greenway"),
        ("site_list", "DRN_PRIO", "Drainage Priority Zone (DRN_PRIO_XX)"),
        ("site_list", "EXISTING_PARK", "Existing Park Entrance / Perimeter Audit"),
        ("site_list", "OTHER", "Other Unmapped Parcel / Flooded Street"),
        ("land_use_cat", "vacant_open", "Vacant Unbuilt Open Plot"),
        ("land_use_cat", "informal_play", "Informal Neighbourhood Playground / Open Ground"),
        ("land_use_cat", "institutional_yard", "School / College / Public Office Yard"),
        ("land_use_cat", "road_verge_row", "Wide Road Right-of-Way / Green Verge"),
        ("land_use_cat", "waste_dump", "Open Dumping / Waterlogged Pit"),
        ("land_use_cat", "newly_built", "Recently Constructed Building (No Longer Vacant)"),
        ("land_use_cat", "agricultural", "Active Peri-Urban Agriculture"),
        ("ownership_cat", "municipal_mc", "Municipal Corporation / District Council"),
        ("ownership_cat", "provincial_govt", "Provincial Govt / Railway / Highway ROW"),
        ("ownership_cat", "institutional", "Public Educational / Health Institution"),
        ("ownership_cat", "private", "Private Ownership"),
        ("ownership_cat", "disputed_unknown", "Disputed / Ownership Unknown"),
        ("yes_no", "yes", "Yes"),
        ("yes_no", "no", "No"),
        ("yes_no_unsure", "yes", "Yes - Raw Sewage Present (Infiltration Prohibited Without Diversion)"),
        ("yes_no_unsure", "no", "No - Clean Surface Runoff / Dry Drain Only"),
        ("yes_no_unsure", "unsure", "Unsure - Lab / Tracer Testing Required"),
        ("waterlog_freq", "chronic_every_monsoon", "Chronic (Floods Every Monsoon)"),
        ("waterlog_freq", "severe_storms_only", "Extreme Storms Only (e.g., Aug 2025)"),
        ("waterlog_freq", "drainage_backflow", "Drainage / Sewage Backflow Only"),
        ("waterlog_freq", "none_reported", "None Reported by Residents"),
        ("drain_cond_cat", "open_clear", "Open & Flowing Freely"),
        ("drain_cond_cat", "silted_blocked", "Partially Silted / Solid Waste Choked"),
        ("drain_cond_cat", "collapsed_undersized", "Collapsed Lining / Severely Undersized"),
        ("drain_cond_cat", "no_drain_present", "No Engineered Drain Present"),
        ("drain_cond_cat", "combined_sewer_overflow", "Combined Sewer (Overflows in Rain)"),
        ("soil_cat", "sandy_loam", "Sandy / Silty Loam (Promising Infiltration)"),
        ("soil_cat", "compacted_clay", "Hard Compacted Clay / Low Permeability"),
        ("soil_cat", "brick_rubble_fill", "Brick Rubble / Construction Fill"),
        ("soil_cat", "paved_impervious", "Asphalt / Concrete (Depaving Needed)"),
        ("access_barrier_cat", "none", "None - Safe Direct Pedestrian Access"),
        ("access_barrier_cat", "missing_sidewalk", "No Sidewalk / High Traffic Speed"),
        ("access_barrier_cat", "locked_gate", "Boundary Wall / Locked Gate"),
        ("access_barrier_cat", "encroached_verge", "Sidewalk Blocked by Vending/Parking"),
        ("access_barrier_cat", "open_drain_hazard", "Uncovered Drain Hazard at Entrance"),
        ("access_barrier_cat", "railway_highway_barrier", "Major Road or Railway Crossing Barrier"),
        ("safety_cat", "good", "Good (Lit, Visible Homes/Shops, Safe for Families)"),
        ("safety_cat", "moderate", "Moderate (Daytime OK; Needs Solar Lighting)"),
        ("safety_cat", "poor", "Poor (Isolated / Blind Walls / Unlit at Dusk)"),
        ("verdict_cat", "confirm_proceed", "Confirmed Suitable - Proceed to Topographic & Soil Design"),
        ("verdict_cat", "conditional_sewage_or_title", "Conditional - Requires Title Clearance or Sewage Diversion First"),
        ("verdict_cat", "reject_built_or_unsuitable", "Reject - Site Built-Over / Active Conflict / Unsuitable"),
    ]
    choices_df = pd.DataFrame(choices_rows, columns=["list_name", "name", "label"])
    settings_df = pd.DataFrame([
        {
            "form_title": "Narowal Urban Green Infrastructure & Flood Verification Form",
            "form_id": "narowal_gi_field_v1",
            "version": "2026111201",
            "default_language": "English",
            "instance_name": "concat(${Site_ID}, '_', ${Survey_Date})",
        }
    ])

    with pd.ExcelWriter(out_xls, engine="openpyxl") as writer:
        pd.DataFrame(survey_rows).to_excel(writer, sheet_name="survey", index=False)
        choices_df.to_excel(writer, sheet_name="choices", index=False)
        settings_df.to_excel(writer, sheet_name="settings", index=False)
    print(f"Saved {out_xls}")


if __name__ == "__main__":
    build_municipal_acquisition_workbook()
    build_survey123_qfield_xlsform()
