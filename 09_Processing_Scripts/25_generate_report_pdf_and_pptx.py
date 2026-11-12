"""Step 6: Compile Formatted Technical Report PDF (ReportLab) & 14-Slide Mayoral Briefing Deck (python-pptx)."""

import json
import os
import pandas as pd

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
STATS_DIR = os.path.join(ROOT, "08_Tables_and_Statistics")
REP_DIR = os.path.join(ROOT, "07_Reports")
PPT_DIR = os.path.join(ROOT, "10_Presentation")
os.makedirs(REP_DIR, exist_ok=True)
os.makedirs(PPT_DIR, exist_ok=True)

MAPS = {
    "MAP01": os.path.join(ROOT, "05_Maps", "01_Urban_Baseline", "MAP_01_Narowal_Urban_Baseline.png"),
    "MAP02": os.path.join(ROOT, "05_Maps", "02_Park_Accessibility", "MAP_02_Ten_Minute_Park_Accessibility.png"),
    "MAP03": os.path.join(ROOT, "05_Maps", "02_Park_Accessibility", "MAP_03_Population_Based_Park_Accessibility.png"),
    "MAP04": os.path.join(ROOT, "05_Maps", "03_Flood_Assessment", "MAP_04_Historical_Flood_Evidence.png"),
    "MAP05": os.path.join(ROOT, "05_Maps", "03_Flood_Assessment", "MAP_05_Terrain_Surface_Drainage.png"),
    "MAP06": os.path.join(ROOT, "05_Maps", "03_Flood_Assessment", "MAP_06_Preliminary_Flood_Susceptibility.png"),
    "MAP07": os.path.join(ROOT, "05_Maps", "04_Drainage", "MAP_07_Existing_Drainage_Sewerage.png"),
    "MAP08": os.path.join(ROOT, "05_Maps", "04_Drainage", "MAP_08_Drainage_Investigation_Priorities.png"),
    "MAP09": os.path.join(ROOT, "05_Maps", "05_Green_Infrastructure", "MAP_09_Vacant_Underutilised_Land.png"),
    "MAP10": os.path.join(ROOT, "05_Maps", "05_Green_Infrastructure", "MAP_10_Green_Infrastructure_Suitability.png"),
    "MAP11": os.path.join(ROOT, "05_Maps", "06_Intervention_Plan", "MAP_11_Proposed_GI_Intervention_Plan.png"),
}

# Load verified quantitative summaries
with open(os.path.join(STATS_DIR, "phase2_urban_baseline_summary.json"), encoding="utf-8") as f:
    BASE = json.load(f)
with open(os.path.join(STATS_DIR, "lulc_accuracy_and_areas.json"), encoding="utf-8") as f:
    LULC = json.load(f)
with open(os.path.join(STATS_DIR, "chirps_rainfall_summary.json"), encoding="utf-8") as f:
    RAIN = json.load(f)
ACC_DF = pd.read_csv(os.path.join(STATS_DIR, "phase2_park_accessibility_summary.csv"))
SUS_DF = pd.read_csv(os.path.join(STATS_DIR, "phase3_flood_susceptibility_areas.csv"))
SENS_P3 = pd.read_csv(os.path.join(STATS_DIR, "phase3_flood_sensitivity_analysis.csv"))
SENS_P4 = pd.read_csv(os.path.join(STATS_DIR, "phase4_suitability_sensitivity.csv"))
SITES_DF = pd.read_excel(os.path.join(STATS_DIR, "Narowal_Priority_Intervention_Sites.xlsx"))


def styled_table(data, col_widths=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2537")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FA")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def build_report_pdf():
    out_pdf = os.path.join(REP_DIR, "Narowal_Urban_Green_Infrastructure_Flood_Resilience_Plan.pdf")

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#555555"))
        if doc.page > 1:
            canvas.drawString(1.8 * cm, A4[1] - 1.2 * cm, "Narowal Urban Green Infrastructure & Flood Resilience Initiative  |  Geospatial Decision-Support Plan")
            canvas.line(1.8 * cm, A4[1] - 1.35 * cm, A4[0] - 1.8 * cm, A4[1] - 1.35 * cm)
            canvas.drawString(1.8 * cm, 1.1 * cm, "Preliminary Screening Study (EPSG:32643 / EPSG:4326) — Subject to Municipal Boundary, Cadastre & Field Verification")
            canvas.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        out_pdf, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.7 * cm,
        title="Narowal Urban Green Infrastructure & Flood Resilience Plan"
    )
    styles = getSampleStyleSheet()
    st_title = ParagraphStyle("T", parent=styles["Title"], fontSize=22, leading=27, textColor=colors.HexColor("#0F2537"), spaceAfter=12)
    st_sub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=12, leading=16, textColor=colors.HexColor("#1B5E20"), spaceAfter=18)
    st_h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14, leading=18, textColor=colors.HexColor("#0F2537"), spaceBefore=14, spaceAfter=6)
    st_h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, leading=14, textColor=colors.HexColor("#00695C"), spaceBefore=10, spaceAfter=4)
    st_body = ParagraphStyle("B", parent=styles["Normal"], fontSize=9.3, leading=13.2, textColor=colors.HexColor("#1E293B"), spaceAfter=6)
    st_note = ParagraphStyle("N", parent=styles["Normal"], fontSize=8.5, leading=12, textColor=colors.HexColor("#5D4037"),
                             backColor=colors.HexColor("#FFF8E1"), borderColor=colors.HexColor("#FFE082"),
                             borderWidth=0.6, borderPadding=7, spaceAfter=8)
    st_cap = ParagraphStyle("C", parent=styles["Italic"], fontSize=8, leading=11, textColor=colors.HexColor("#475569"), alignment=1, spaceAfter=10)

    story = []

    # Cover Page
    story.append(Spacer(1, 1.1 * inch))
    story.append(Paragraph("NAROWAL URBAN GREEN INFRASTRUCTURE &amp; FLOOD RESILIENCE INITIATIVE", st_title))
    story.append(Paragraph("Geospatial Decision-Support Plan for Public Park Accessibility, Pluvial Flood Mitigation &amp; Multi-Benefit SuDS Investments", st_sub))
    story.append(Spacer(1, 0.25 * inch))
    meta_rows = [
        ["Prepared For", "Worshipful Mayor & Municipal Infrastructure Authorities, Municipal Corporation Narowal"],
        ["Location", "Narowal City, Punjab, Pakistan (Preliminary MC Area: 24.905 km²; Core: 17.837 km²)"],
        ["Spatial Reference", "WGS 84 / UTM Zone 43N (EPSG:32643) for Metrics & Modelling; WGS 84 (EPSG:4326) for Web/KML"],
        ["Lead Baseline Sources", "Urban Unit Master Plan (2021), OSM (2026), MS Buildings (2026-02), Copernicus S1/S2/GLO-30, CHIRPS, GHSL 2025"],
        ["Report Date & Status", "November 12, 2026 — Decision-Support Screening Complete (Phase 5 Field & Cadastre Validation Next)"],
    ]
    story.append(styled_table(meta_rows, col_widths=[4.2 * cm, 13.0 * cm]))
    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph(
        "<b>METHODOLOGICAL DISCLOSURE:</b> Preliminary MC boundaries digitized from Urban Unit (2021) Annexure 2 and urban core distribution are clearly labeled preliminary pending LG&CD/MC notification. "
        "Satellite flood and DEM screening (Copernicus GLO-30) cannot replace surveyed 0.2 m invert levels or Rescue 1122 street flood logs. Domestic sewage separation must be field-verified prior to constructing any infiltration SuDS.",
        st_note
    ))
    story.append(PageBreak())

    # TOC & List of Maps
    story.append(Paragraph("Table of Contents &amp; Cartographic Atlas Index", st_h1))
    toc_rows = [
        ["Section", "Chapter Title"],
        ["Exec. Summary", "Headline Evidence-Based Findings & Core Safeguards"],
        ["Section 1", "Study Area, Boundary Definition & Authoritative Data Register"],
        ["Section 2", "Urban Baseline & Sentinel-2 Land Use / Land Cover Classification (MAP 01)"],
        ["Section 3", "Objective A: 10-Minute Park Network Accessibility & Population Equity (MAPS 02–03)"],
        ["Section 4", "Objective B: Rainfall, Monsoon SAR Flood Evidence, Hydrology & Drainage (MAPS 04–08)"],
        ["Section 5", "Objective C: Vacant Urban Land, GI Suitability & 8 Priority Interventions (MAPS 09–11)"],
        ["Section 6", "Municipal Data Request Register, Field Verification Protocol & Phased Roadmap"],
    ]
    story.append(styled_table(toc_rows, col_widths=[3.2 * cm, 14.0 * cm]))
    story.append(Spacer(1, 0.2 * inch))

    map_idx_rows = [
        ["Map ID", "Title", "Primary Planning Decision Question"],
        ["MAP 01", "Urban Baseline & 6-Class LULC", "Where are built-up roofs, agriculture & urban assets inside MC?"],
        ["MAP 02", "10-Minute Park Walk Accessibility", "Which streets fall within an 800 m (10-min) walk of parks?"],
        ["MAP 03", "Population-Based Park Equity", "How many residents live in underserved high-density cells?"],
        ["MAP 04", "Historical Monsoon Flood Evidence", "Where did Aug 2025 S1 SAR & S2 MNDWI detect flood/wetness?"],
        ["MAP 05", "Terrain & Surface Drainage Screening", "Where do GLO-30 HAND & D8 flow paths converge?"],
        ["MAP 06", "Preliminary Flood Susceptibility", "Which 30% of MC faces High/Very High pluvial susceptibility?"],
        ["MAP 07", "Existing Drainage & Sewerage Assets", "What is observed (OS/UU) vs. unverified DEM flow paths?"],
        ["MAP 08", "Drainage Investigation Priorities", "Which 12 unserved hotspots need immediate drain inspection?"],
        ["MAP 09", "Vacant & Underutilised Open Land", "Where are the 45 open plots (>=0.2 ha) inside the built-up core?"],
        ["MAP 10", "GI Multi-Criteria Suitability Model", "Where do flood need, park deficit & open space align?"],
        ["MAP 11", "Proposed 8-Site Intervention Plan", "Which 8 catalytic SuDS/park investments deliver maximum impact?"],
    ]
    story.append(styled_table(map_idx_rows, col_widths=[2.0 * cm, 6.2 * cm, 9.0 * cm]))
    story.append(PageBreak())

    # Executive Summary
    story.append(Paragraph("Executive Summary: Closing Park Equity &amp; Flood Gaps Simultaneously", st_h1))
    story.append(Paragraph(
        f"Narowal City is experiencing rapid spatial growth over flat Ravi-Nullah Daik alluvial plains while relying on severely constrained drainage and park infrastructure. "
        f"Across our preliminary <b>{BASE['mc_area_km2']} km²</b> MC study area (containing <b>{BASE['ms_buildings_count_mc']:,}</b> mapped MS Buildings and <b>{BASE['walkable_street_length_mc_km']} km</b> of walkable streets), "
        f"integrated analysis across Phases 1–4 establishes three core decision findings:",
        st_body
    ))
    kpi_summary = [
        ["Strategic Domain", "Verified Quantitative Metric", "Decision Implication"],
        ["Formal Park Equity", f"1 formal park (Faiz Park, {BASE['formal_park_area_ha']} ha); 5.68% GHSL pop served (94.32% unserved)", "Urgent need for distributed 0.4–3.0 ha pocket parks west of rail/central core"],
        ["Per-Capita Green Space", f"{BASE['formal_park_m2_per_capita_uu2025']} m²/cap (UU 2025) / {BASE['formal_park_m2_per_capita_ghsl2025']} m²/cap (GHSL) vs WHO 9.0 m²", "97–99% green-space deficit; zero formal parks >=10 acres (0.00%)"],
        ["Monsoon Rainfall & SAR", f"{RAIN['mean_annual_1981_2024_mm']} mm/yr mean ({RAIN['mean_jas_monsoon_mm']} mm JAS); Aug 2025 S1 MC flood = 236.8 ha", "Dense monsoon storms overwhelm unmapped urban drainage outlets"],
        ["Flood Susceptibility", "7.472 km² (30.0% of MC) High or Very High (Sens. r = 0.874–0.968)", "Combine SuDS retention with Rasinwal (16 cusec) & Zafarwal (25 cusec) drainage"],
        ["Candidate Open Land", "45 unbuilt urban plots >=0.2 ha (90.70 ha inside 17.84 km² core)", "Outer farmland strictly protected; 8 priority GI sites (12.47 ha) shortlisted"],
    ]
    story.append(styled_table(kpi_summary, col_widths=[3.7 * cm, 7.2 * cm, 6.3 * cm]))
    story.append(Spacer(1, 0.15 * inch))

    def add_map_figure(map_key, caption):
        if os.path.exists(MAPS[map_key]):
            story.append(Image(MAPS[map_key], width=16.8 * cm, height=12.9 * cm, kind="proportional"))
            story.append(Paragraph(caption, st_cap))

    # Section 1 & 2
    story.append(Paragraph("1. Study Area &amp; 2. Urban Baseline Land Cover (MAP 01)", st_h1))
    story.append(Paragraph(
        f"The 6-class Sentinel-2 Random Forest classification (`2025-05-16` dry season) achieved <b>{LULC['overall_accuracy']*100:.2f}%</b> Overall Accuracy (`Kappa = {LULC['kappa']}`). "
        f"Noticeably, <b>42.00%</b> (10.461 km²) inside the preliminary MC perimeter remains peri-urban agriculture, which is explicitly barred from urban vacant-land targeting.",
        st_body
    ))
    lulc_rows = [["LULC Class", "MC Area (km²)", "Area (ha)", "Share (%)"]]
    for cname, info in LULC["mc_boundary_lulc_area"].items():
        lulc_rows.append([cname, f"{info['area_km2']:.4f}", f"{info['area_ha']:.2f}", f"{info['pct']:.2f}%"])
    story.append(styled_table(lulc_rows, col_widths=[5.5 * cm, 3.8 * cm, 3.8 * cm, 4.1 * cm]))
    story.append(Spacer(1, 0.12 * inch))
    add_map_figure("MAP01", "Figure 1 (MAP 01): Narowal Preliminary Study Boundaries, Sentinel-2 LULC & Key Municipal Assets.")
    story.append(PageBreak())

    # Section 3: Park Accessibility
    story.append(Paragraph("3. Ten-Minute Park Accessibility Assessment (MAPS 02 &amp; 03)", st_h1))
    story.append(Paragraph(
        "Pedestrian shortest-path routing (`800 m` threshold at `4.8 km/h`) from explicit park frontage gates confirms stark spatial inequity. "
        "Note the ~2.3x population discrepancy between GHSL 2025 (`302,379` inside MC) and Urban Unit's 2025 projection (`132,194`), which does not alter the percentage equity share (~94% unserved) and will be reconciled once PBS 2023 block tables are released.",
        st_body
    ))
    acc_rows = [["Scenario", "Walkable Streets", "Street %", "GHSL Pop <=10m", "Pop %", "Bldgs %"]]
    for _, r in ACC_DF.iterrows():
        acc_rows.append([
            str(r["category"]).replace("_", " "),
            f"{r['accessible_street_km']} km",
            f"{r['pct_street_accessible']}%",
            f"{int(r['pop_within_10min']):,}",
            f"{r['pct_pop_accessible']}%",
            f"{r['pct_buildings_accessible']}%"
        ])
    story.append(styled_table(acc_rows, col_widths=[6.4 * cm, 2.4 * cm, 2.0 * cm, 2.6 * cm, 1.9 * cm, 1.9 * cm]))
    story.append(Spacer(1, 0.1 * inch))
    add_map_figure("MAP02", "Figure 2 (MAP 02): 10-Minute Walk Street Network Accessibility from Mapped Parks & Sports Grounds.")
    story.append(PageBreak())
    add_map_figure("MAP03", "Figure 3 (MAP 03): Population-Weighted 10-Minute Formal Park Equity & Highest-Deficit 300 m Grid Cells.")
    story.append(PageBreak())

    # Section 4: Flood & Drainage
    story.append(Paragraph("4. Rainfall, Flood Screening &amp; Drainage Investigation Priorities (MAPS 04–08)", st_h1))
    story.append(Paragraph(
        "Sentinel-1 RTC August 2025 flood pairs, Copernicus DEM GLO-30 (`HAND` + `TWI` + `D8 Flow Accumulation`), Urban Unit (2021) sewerage assets, and impervious footprints were integrated via renormalized 5-indicator weighted overlay (`Pearson r = 0.874–0.968` across equal, terrain-heavy, and urban-pluvial sensitivity schemes).",
        st_body
    ))
    sus_rows = [["Susceptibility Class", "MC Area (km²)", "Share (%)"]]
    for _, r in SUS_DF.iterrows():
        sus_rows.append([f"{int(r['class_id'])} - {r['class_name']}", f"{r['area_km2']:.3f}", f"{r['pct_mc']:.1f}%"])
    story.append(styled_table(sus_rows, col_widths=[6.5 * cm, 5.2 * cm, 5.5 * cm]))
    story.append(Spacer(1, 0.1 * inch))
    add_map_figure("MAP04", "Figure 4 (MAP 04): Historical Monsoon Flood & Wetness Evidence (Sentinel-1 Aug 2025 SAR & Sentinel-2 MNDWI).")
    story.append(PageBreak())
    add_map_figure("MAP05", "Figure 5 (MAP 05): Copernicus GLO-30 Relative Elevation (HAND) & DEM-Inferred Flow Convergence Screening.")
    story.append(PageBreak())
    add_map_figure("MAP06", "Figure 6 (MAP 06): Provisional 5-Class Urban Flood & Waterlogging Susceptibility inside Narowal MC.")
    story.append(PageBreak())
    add_map_figure("MAP07", "Figure 7 (MAP 07): Observed OSM Waterways & Urban Unit Sewerage Assets vs. Unverified DEM Convergence.")
    story.append(PageBreak())
    add_map_figure("MAP08", "Figure 8 (MAP 08): Twelve Drainage Investigation Priority Zones (DRN_PRIO_01–12) Requiring Field Survey.")
    story.append(PageBreak())

    # Section 5: Suitability & 8 Priority Sites
    story.append(Paragraph("5. Vacant Land Screening, GI Suitability &amp; 8 Priority Interventions (MAPS 09–11)", st_h1))
    story.append(Paragraph(
        "Suitability weighting (Flood 30%, Park Deficit 25%, Open Land 20%, GHSL 500 m Pop 15%, Drainage Connectivity 10%; sensitivity r = 0.905–0.972) identified <b>5.200 km²</b> of High/Very High GI suitability and shortlisted <b>8 catalytic multi-benefit interventions</b> totaling <b>12.47 ha</b>.",
        st_body
    ))
    site_tbl = [["Site ID", "Location & Typology", "Area (ha)", "Park Dist", "Pop (500m)", "GI Score", "Tier"]]
    for _, r in SITES_DF.iterrows():
        site_tbl.append([
            r["Site_ID"],
            f"{str(r['Location']).split('(')[0].strip()}\n({r['Recommended_Intervention']})",
            f"{r['Est_Area_ha']}",
            f"{int(r['Dist_Formal_Park_m'])} m",
            f"{int(r['Nearby_Pop_500m_GHSL2025']):,}",
            f"{r['GI_Suitability_Score']}/5",
            str(r["Implementation_Priority"]).split("(")[0].strip()
        ])
    story.append(styled_table(site_tbl, col_widths=[1.9 * cm, 6.7 * cm, 1.5 * cm, 1.8 * cm, 2.0 * cm, 1.5 * cm, 1.8 * cm]))
    story.append(PageBreak())
    add_map_figure("MAP09", "Figure 9 (MAP 09): 45 Candidate Vacant & Underutilised Open Urban Plots (>=0.2 ha) Inside Built-Up Core.")
    story.append(PageBreak())
    add_map_figure("MAP10", "Figure 10 (MAP 10): Urban Green Infrastructure Multi-Criteria Suitability Index with Exclusion Masks.")
    story.append(PageBreak())
    add_map_figure("MAP11", "Figure 11 (MAP 11): Proposed Narowal Urban Green Infrastructure Intervention Plan (Sites GI_SITE_01–08).")
    story.append(PageBreak())

    # Section 6: Roadmap & Closing
    story.append(Paragraph("6. Governance, Field Verification Gate &amp; Phased Roadmap", st_h1))
    road_rows = [
        ["Phase / Horizon", "Key Actions & Institutional Leads", "Mandatory Gate Before Construction"],
        ["Phase A (0–6 Mos)", "Request MDR-01..09 (MC, Rescue 1122, PHED, BOR); execute 2-week Survey123/QField audit; initiate GI_SITE_01/03/07", "Pakistan Railways NOC (GI_SITE_01) & dry-weather raw sewage check"],
        ["Phase B (6–18 Mos)", "Commission 0.2 m DGPS survey, ASTM soil Ksat tests, PMD IDF 1D/2D hydraulic modelling; advance GI_SITE_02/04/05/06", "Khasra cadastre clearance & separate sanitary trunk interceptor"],
        ["Phase C (18–36 Mos)", "Deliver GI_SITE_08 university greenbelt, protect Nullah Daik buffers, track KPI progress in WebGIS Portal", "Annual monsoon inspection & community maintenance MoUs"],
    ]
    story.append(styled_table(road_rows, col_widths=[3.2 * cm, 8.2 * cm, 5.8 * cm]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "<b>Important Engineering Safeguard:</b> In line with Urban Unit (2021) findings that municipal sewerage currently empties untreated toward Nullah Daik, no unlined rain garden or bioswale may accept sanitary greywater or combined sewage overflow. Every infiltration site must pass dry-weather separation verification and double-ring soil testing prior to detailed civil design.",
        st_note
    ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Saved {out_pdf}")


def build_mayoral_pptx():
    out_pptx = os.path.join(PPT_DIR, "Narowal_Mayoral_Briefing_UGI_Plan.pptx")
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    NAVY = RGBColor(15, 37, 55)
    GREEN = RGBColor(27, 94, 32)
    CRIMSON = RGBColor(142, 0, 28)
    BLUE = RGBColor(21, 101, 192)
    SLATE = RGBColor(51, 65, 85)
    BG_LIGHT = RGBColor(244, 247, 250)
    WHITE = RGBColor(255, 255, 255)

    def add_header(slide, title, subtitle):
        bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(1.05))
        bar.fill.solid()
        bar.fill.fore_color.rgb = NAVY
        bar.line.fill.background()

        tb = slide.shapes.add_textbox(Inches(0.45), Inches(0.12), Inches(12.4), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.color.rgb = WHITE
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(12)
        p2.font.color.rgb = RGBColor(186, 214, 232)

    def add_footer(slide, page_no):
        tb = slide.shapes.add_textbox(Inches(0.45), Inches(7.12), Inches(12.4), Inches(0.3))
        p = tb.text_frame.paragraphs[0]
        p.text = f"Narowal Urban Green Infrastructure & Flood Resilience Initiative  |  Mayoral Decision-Support Briefing  |  Slide {page_no} of 14"
        p.font.size = Pt(9.5)
        p.font.color.rgb = RGBColor(100, 116, 139)

    def add_bullets(slide, x, y, w, h, items, title=None, accent=GREEN):
        box = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
        box.fill.solid()
        box.fill.fore_color.rgb = BG_LIGHT
        box.line.color.rgb = RGBColor(203, 213, 225)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.18)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.15)
        first = True
        if title:
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = accent
            p.space_after = Pt(8)
            first = False
        for it in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.text = f"• {it}"
            p.font.size = Pt(11.5)
            p.font.color.rgb = SLATE
            p.space_after = Pt(6)

    # Slide 1: Cover
    s1 = prs.slides.add_slide(blank)
    bg1 = s1.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY
    bg1.line.fill.background()
    acc_bar = s1.shapes.add_shape(1, Inches(0), Inches(6.25), Inches(13.333), Inches(0.15))
    acc_bar.fill.solid()
    acc_bar.fill.fore_color.rgb = RGBColor(46, 125, 50)
    acc_bar.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(0.9), Inches(1.5), Inches(11.5), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "NAROWAL URBAN GREEN INFRASTRUCTURE\n& FLOOD RESILIENCE INITIATIVE"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p2 = tf1.add_paragraph()
    p2.text = "\nEvidence-Based Geospatial Decision-Support Briefing for the Mayor & Municipal Corporation Narowal"
    p2.font.size = Pt(18)
    p2.font.color.rgb = RGBColor(165, 214, 167)
    p3 = tf1.add_paragraph()
    p3.text = "\nIntegrating 10-Minute Park Equity, Urban Hydrology, Drainage Resilience & 8 Catalytic SuDS Investments\nDate: November 12, 2026  |  CRS: EPSG:32643 / EPSG:4326"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(203, 213, 225)

    # Slide 2: Executive KPIs
    s2 = prs.slides.add_slide(blank)
    add_header(s2, "1. Why Act Now? Twin Crises of Green Deficit & Pluvial Waterlogging",
               "Headline GIS & Earth Observation Metrics for Preliminary MC Boundary (24.91 km²)")
    cards = [
        ("94.3%", "Residents Outside 10-Min Formal Park Walk (285,208 of 302,379 GHSL)", CRIMSON),
        ("0.11–0.24 m²", "Formal Park Area / Person vs. 9.0 m² WHO Minimum Benchmark", CRIMSON),
        ("30.0% (7.47 km²)", "MC Area in High or Very High Flood Susceptibility Class", BLUE),
        ("779.8 mm/yr", "Mean CHIRPS Rainfall (69.5% concentrated in JAS Monsoon)", BLUE),
        ("90.70 ha", "45 Candidate Open Urban Plots (>=0.2 ha) Inside Built-Up Core", GREEN),
        ("8 Priority Sites", "Dual-Benefit SuDS & Park Investments Identified (12.47 ha)", GREEN),
    ]
    for idx, (val, desc, col) in enumerate(cards):
        cx = 0.55 + (idx % 3) * 4.15
        cy = 1.45 + (idx // 3) * 2.65
        sh = s2.shapes.add_shape(1, Inches(cx), Inches(cy), Inches(3.85), Inches(2.25))
        sh.fill.solid()
        sh.fill.fore_color.rgb = BG_LIGHT
        sh.line.color.rgb = col
        sh.line.width = Pt(2.2)
        tf = sh.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.2)
        tf.margin_top = Inches(0.35)
        pv = tf.paragraphs[0]
        pv.text = val
        pv.font.size = Pt(28)
        pv.font.bold = True
        pv.font.color.rgb = col
        pd_p = tf.add_paragraph()
        pd_p.text = "\n" + desc
        pd_p.font.size = Pt(12.5)
        pd_p.font.color.rgb = SLATE
    add_footer(s2, 2)

    # Helper for Map + Insight Slides
    def map_slide(slide_no, title, subtitle, map_key, bullets_title, bullets, accent=GREEN):
        s = prs.slides.add_slide(blank)
        add_header(s, title, subtitle)
        if os.path.exists(MAPS[map_key]):
            s.shapes.add_picture(MAPS[map_key], Inches(0.45), Inches(1.25), width=Inches(7.65))
        add_bullets(s, 8.3, 1.25, 4.6, 5.7, bullets, title=bullets_title, accent=accent)
        add_footer(s, slide_no)

    map_slide(3, "2. Study Area & Land Cover Baseline (MAP 01)",
              "Preliminary MC Boundary (24.91 km²), MS Buildings (13,087) & Sentinel-2 LULC (OA = 91.17%)",
              "MAP01", "Key Baseline Insights", [
                  "MC Perimeter is preliminary (Urban Unit 2021 Annexure 2 + core buildings); await official gazette shapefile.",
                  "Built-up urban land covers 7.58 km² (30.4%) with 13,087 MS ML buildings inside MC.",
                  "Agriculture covers 10.46 km² (42.0%) inside MC fringe — excluded from vacant land screening.",
                  "Bare soil (1.17 km²) & open urban green (4.58 km²) inside 17.84 km² core form infill candidates."
              ], NAVY)

    map_slide(4, "3. Ten-Minute Walk Park Accessibility (MAP 02)",
              "184.87 km Walkable MC Streets Routed to Explicit Frontage Entrances (800 m @ 4.8 km/h)",
              "MAP02", "Network Routing Findings", [
                  "Only 1 formal public park mapped: Faiz Ahmad Faiz Park (3.19 ha / 7.88 acres) in the eastern sector.",
                  "Formal park serves just 10.91% of MC street length (20.17 km out of 184.87 km).",
                  "Zero formal parks >=10 acres exist inside MC (0.00% coverage).",
                  "Adding Narowal Sports Complex (18.34 ha; verify open access) raises street access to 20.43%."
              ], GREEN)

    map_slide(5, "4. Population Equity & Severely Underserved Neighbourhoods (MAP 03)",
              "Linking Street Accessibility to 300 m GHSL Population Grids & Urban Unit Projections",
              "MAP03", "Equity Gap & Data Note", [
                  "285,208 of 302,379 GHSL 2025 residents (94.32%) live >10-min walk from any formal park.",
                  "Highest-deficit core wards (Eidgah Rd, Model Town, Tariq Pura, Manak Rd) are 1.8–3.3 km away.",
                  "Urban Unit 2025 pop (132,194) vs GHSL (302,379): both yield 0.11–0.24 m²/cap vs 9.0 m² WHO norm.",
                  "PBS 2023 Census block data requested to reconcile exact municipal headcount."
              ], CRIMSON)

    map_slide(6, "5. Rainfall Climatology & Monsoon Flood Evidence (MAP 04)",
              "CHIRPS 1981–2024 Series & August 2025 Sentinel-1 SAR / Sentinel-2 MNDWI Cross-Check",
              "MAP04", "Historical & SAR Signals", [
                  "CHIRPS mean rainfall: 779.8 mm/yr (JAS Monsoon = 542.1 mm; wettest year 1990 = 1,102 mm).",
                  "Aug 27, 2025 Sentinel-1 Asc-100 detects 236.8 ha candidate inundation inside MC fringe.",
                  "MS Building footprints masked to prevent SAR radar-shadow false positives on streets.",
                  "Urban Unit (2021 p.20) confirms chronic ponding along Eidgah, Church, Kachahry, Tariq & Sadiq Pura."
              ], BLUE)

    map_slide(7, "6. Preliminary Flood Susceptibility & Drainage Screen (MAP 06)",
              "Renormalized 5-Indicator Overlay Supported by GLO-30 Topography (Sensitivity r = 0.87–0.97)",
              "MAP06", "Where Waterlogging Concentrates", [
                  "30.0% of MC (7.472 km²) falls in High (18.0%) or Very High (12.0%) susceptibility.",
                  "Copernicus GLO-30 (30 m DSM) screens macro flow convergence & low HAND pockets cleanly.",
                  "Limitation: GLO-30 cannot resolve street curbs — engineering survey required prior to design.",
                  "Rescue 1122 / MC dewatering logs requested to replace proxy validation."
              ], CRIMSON)

    map_slide(8, "7. Observed vs. Inferred Drainage & 12 Survey Hotspots (MAP 08)",
              "Urban Unit Disposal Stations (Rasinwal 16 cusec, Zafarwal Rd 25 cusec) & Nullah Outfalls",
              "MAP08", "Drainage Deficiencies", [
                  "Detailed municipal pipe GIS & invert levels are missing from public records.",
                  "Observed waterways & disposal stations overlaid with GLO-30 flow lines locate 12 hotspots.",
                  "Top hotspots (DRN_PRIO_01..03 >100 ha each) coincide with northern & western expansion.",
                  "Untreated Rasinwal & Zafarwal sewage toward Nullah Daik demands strict stormwater separation."
              ], BLUE)

    map_slide(9, "8. Vacant Urban Land & GI Suitability Model (MAP 09 & MAP 10)",
              "45 Open Urban Parcels >=0.2 ha (90.70 ha) Strictly Inside 17.84 km² Built-Up Core",
              "MAP10", "Where Land & Need Align", [
                  "7.58 km² built-up roofs/roads & outer farmlands excluded to protect livelihoods & realism.",
                  "2 Government corridor sites (6.71 ha, incl. Manak Rd Railway Strip) + 5 Institutional grounds (11.01 ha).",
                  "38 unverified urban infill plots (72.98 ha) flagged for Revenue Khasra ownership verification.",
                  "5.20 km² inside MC scores High/Very High GI Suitability (Sensitivity r = 0.905–0.972)."
              ], GREEN)

    map_slide(10, "9. Proposed 8-Site Green Infrastructure Plan (MAP 11)",
              "Catalytic Multi-Benefit Portfolio Totaling 12.47 ha Across Narowal's Underserved Wards",
              "MAP11", "Dual-Benefit Strategy", [
                  "4 Priority 1 Flagship / Quick-Win Pilots (GI_SITE_01, 02, 03, 07) target immediate core deficits.",
                  "3 Priority 2 Catchment Relief Sites (GI_SITE_04, 05, 06) buffer high-density & disposal zones.",
                  "1 Priority 3 Institutional Greenway (GI_SITE_08, University of Narowal eastern sector).",
                  "Each intervention combines safe pedestrian green space with targeted SuDS storage."
              ], CRIMSON)

    # Slide 11: Summary Table of 8 Priority Sites
    s11 = prs.slides.add_slide(blank)
    add_header(s11, "10. Detailed Schedule of 8 Shortlisted Priority Intervention Sites",
               "Verified Spatial Metrics (EPSG:32643) & Pre-Construction Verification Requirements")
    cols_s = ["Site ID", "Location", "Area (ha)", "Park Dist", "500m Pop", "Score", "Recommended SuDS / GI", "Priority Tier"]
    tshape = s11.shapes.add_table(9, 8, Inches(0.4), Inches(1.25), Inches(12.53), Inches(5.6))
    tbl = tshape.table
    widths = [1.1, 2.75, 0.85, 0.95, 1.0, 0.75, 3.03, 2.1]
    for ci, w in enumerate(widths):
        tbl.columns[ci].width = Inches(w)
    for ci, htxt in enumerate(cols_s):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = htxt
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE
    for ri, (_, row) in enumerate(SITES_DF.iterrows(), 1):
        vals = [
            row["Site_ID"],
            str(row["Location"]).split("(")[0].strip(),
            f"{row['Est_Area_ha']}",
            f"{int(row['Dist_Formal_Park_m'])} m",
            f"{int(row['Nearby_Pop_500m_GHSL2025']):,}",
            f"{row['GI_Suitability_Score']}/5",
            str(row["Recommended_Intervention"]),
            str(row["Implementation_Priority"]),
        ]
        for ci, v in enumerate(vals):
            cell = tbl.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = BG_LIGHT if ri % 2 == 0 else WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = v
            p.font.size = Pt(9.2)
            p.font.color.rgb = SLATE
    add_footer(s11, 11)

    # Slide 12: Flagship Quick Wins
    s12 = prs.slides.add_slide(blank)
    add_header(s12, "11. Priority 1 Catalytic Flagship Investments (Immediate 0–12 Month Focus)",
               "High-Impact Corridors Ready for Inter-Departmental Coordination & Quick-Win Delivery")
    add_bullets(s12, 0.5, 1.35, 6.0, 2.65, [
        "Area: ~2.85 ha railway corridor; 30,080 GHSL pop within 500 m; 2,803 m from Faiz Park.",
        "Already identified in Urban Unit (2021) Master Plan — highest GIS Suitability (4.14/5).",
        "Action: Execute Pakistan Railways lease/NOC, 0.2 m topo & soil percolation survey."
    ], "GI_SITE_01: Manak Rd Retention / Detention Park", CRIMSON)
    add_bullets(s12, 6.8, 1.35, 6.0, 2.65, [
        "Area: ~0.95 ha in chronic waterlogged residential wards (Urban Unit p.20); 28,388 pop.",
        "GIS Score: 3.36/5; relieves flood storage while eliminating a 2.1 km walk gap.",
        "Mandatory Gate: Verify Khasra title & isolate domestic sewage inflow before infiltration."
    ], "GI_SITE_02: Tariq Pura / Sadiq Pura Pocket Park", CRIMSON)
    add_bullets(s12, 0.5, 4.25, 6.0, 2.65, [
        "Area: ~0.72 ha institutional courtyard retrofit in waterlogged Model Town / Kachahry Rd.",
        "Serves 34,770 residents within 500 m; minimal land-acquisition hurdle if MoU signed.",
        "Action: Install rain gardens, permeable paving & drain invert relief."
    ], "GI_SITE_03: Model Town / Kachahry Rd Pilot", GREEN)
    add_bullets(s12, 6.8, 4.25, 6.0, 2.65, [
        "2.1 km shaded green corridor & roadside bioswales along Circular Rd -> Faiz Park.",
        "Low land cost inside municipal ROW; immediately connects 20,730 residents safely.",
        "Action: Audit sidewalks, encroachments, lighting & culvert cross-drainage."
    ], "GI_SITE_07: Circular Rd – Faiz Park Greenway", GREEN)
    add_footer(s12, 12)

    # Slide 13: Engineering & Governance Safeguards
    s13 = prs.slides.add_slide(blank)
    add_header(s13, "12. Municipal Data Handover & Mandatory Pre-Design Engineering Gates",
               "Transparent Risk Controls Before Issuing Detailed Engineering Tenders")
    add_bullets(s13, 0.55, 1.35, 5.9, 5.4, [
        "MDR-01 Official MC & Ward Boundaries (MC / LG&CD)",
        "MDR-02 Park Inventory & Gate Access Hours (MC Parks Wing)",
        "MDR-03 Sewerage & Storm Drain Drawings (MC / PHED)",
        "MDR-04 Historical Street Flood Logs 2018–2026 (Rescue 1122)",
        "MDR-05 Khasra / Mauza Revenue Title Records (BOR / AC)",
        "MDR-07 PBS 2023 Census Block Counts (Reconcile GHSL)",
        "MDR-08 PMD Daily/Hourly Rainfall Records (IDF Sizing)"
    ], "Municipal Data Requests (Workbooks Provided)", NAVY)
    add_bullets(s13, 6.85, 1.35, 5.9, 5.4, [
        "SEWAGE SEPARATION GATE: Never route untreated sanitary sewage into open rain gardens or detention basins.",
        "SOIL & WATERTABLE CHECK: Conduct ASTM double-ring infiltration & augered watertable depth before choosing unlined vs. lined SuDS.",
        "MICRO-TOPOGRAPHY GATE: Commission 0.2 m DGPS survey — GLO-30 DEM cannot replace pipe invert levels.",
        "INTERACTIVE PORTAL READY: All 15 GIS layers delivered in FileGDB + offline-capable Leaflet Web GIS App."
    ], "Technical Safeguards & Field Verification", CRIMSON)
    add_footer(s13, 13)

    # Slide 14: Phased Action Plan
    s14 = prs.slides.add_slide(blank)
    add_header(s14, "13. Immediate Decisions Requested from the Mayor of Narowal",
               "Phased 36-Month Implementation Roadmap & Week 1 Action Items")
    phases = [
        ("PHASE A: 0–6 Months\nValidation & Quick Wins", [
            "Designate MC Focal Person & issue data directive (MDR-01..09).",
            "Launch 2-week Survey123/QField field check across 8 sites & 12 hotspots.",
            "Initiate Pakistan Railways NOC (GI_SITE_01) & Model Town MoU (GI_SITE_03).",
            "Begin Circular Rd sidewalk/bioswale greenway pilot (GI_SITE_07)."
        ], CRIMSON),
        ("PHASE B: 6–18 Months\nEngineering Design", [
            "Procure 0.2 m DGPS topo survey & soil percolation pits for confirmed sites.",
            "Run 1D/2D storm hydraulic model tied to Rasinwal & Zafarwal disposal.",
            "Enforce PHED sanitary sewer separation ahead of WWTP commissioning.",
            "Tender GI_SITE_02, GI_SITE_04, GI_SITE_05 & GI_SITE_06 works."
        ], BLUE),
        ("PHASE C: 18–36 Months\nScale-Up & Resilience", [
            "Execute University of Narowal eastern greenbelt partnership (GI_SITE_08).",
            "Enforce Nullah Daik & tributary buffer protection in MC zoning.",
            "Expand pocket-park network using verified remaining VAC_XX parcels.",
            "Update Narowal Web GIS KPIs annually post-monsoon."
        ], GREEN),
    ]
    for idx, (ptit, pitems, pcol) in enumerate(phases):
        add_bullets(s14, 0.5 + idx * 4.2, 1.4, 3.9, 5.4, pitems, ptit, pcol)
    add_footer(s14, 14)

    prs.save(out_pptx)
    print(f"Saved {out_pptx}")


if __name__ == "__main__":
    build_report_pdf()
    build_mayoral_pptx()
