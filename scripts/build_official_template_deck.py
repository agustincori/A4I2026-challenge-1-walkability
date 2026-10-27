import os
import shutil
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def build_deck():
    template_path = r"C:\Users\tshug\AppData\Local\Programs\antigravity\downloaded_template.pptx"
    if not os.path.exists(template_path):
        template_path = r"downloaded_template.pptx"
    
    prs = Presentation(template_path)
    
    # Theme colors
    COLOR_DARK = RGBColor(32, 33, 36)
    COLOR_PRIMARY = RGBColor(26, 115, 232)
    COLOR_MUTED = RGBColor(95, 99, 104)
    COLOR_RED = RGBColor(217, 48, 37)
    COLOR_GREEN = RGBColor(30, 142, 62)

    # -------------------------------------------------------------
    # SLIDE 1: Instructions (Keep template layout, add speaker notes)
    # -------------------------------------------------------------
    slide1 = prs.slides[0]
    if slide1.has_notes_slide:
        n1 = slide1.notes_slide.notes_text_frame
        n1.text = (
            "=== SUBMISSION INSTRUCTIONS & COMPETITION CHECKLIST ===\n\n"
            "Official Template: ATL-6 - Google Slides\n"
            "Team ID: ATL-6\n"
            "Challenge 1: Community Climate Resilience (Urban Heat Track)\n"
            "Track: This Budget Cycle (Cooling Center Siting & Infrastructure Investment)\n\n"
            "Submission Checklist:\n"
            "1. Squad Environment Link: Deployed Cloud Run Agent API & React 18 GIS Dashboard\n"
            "2. Live App / Demo Link: https://atlanta-heat-advisor-frontend-1004921377034.us-central1.run.app\n"
            "3. GitHub Repository: https://github.com/agustincori/A4I2026-challenge-1-walkability\n"
            "4. Recorded Pitch Video: Exactly 3 minutes (0:20 intro, 2:20 demo, 0:20 outro)\n"
            "5. Pitch Deck: 6 required submission slides (Slides 2-7 completely filled out)"
        )

    # -------------------------------------------------------------
    # SLIDE 2: Title & Team Name
    # -------------------------------------------------------------
    slide2 = prs.slides[1]
    # Shape 0 is the text box with "Team name here"
    # Shape 1 is the A4I logo
    s2_shp0 = slide2.shapes[0]
    tf2 = s2_shp0.text_frame
    tf2.clear()
    
    p = tf2.paragraphs[0]
    p.text = "ATL-6"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.name = "Google Sans Flex Medium"
    p.font.color.rgb = COLOR_DARK
    
    p_sub = tf2.add_paragraph()
    p_sub.text = "Atlanta Urban Climate Resilience Advisor"
    p_sub.font.size = Pt(13)
    p_sub.font.bold = True
    p_sub.font.name = "Google Sans Flex"
    p_sub.font.color.rgb = COLOR_PRIMARY
    
    p_track = tf2.add_paragraph()
    p_track.text = "Challenge 1: Urban Heat • Track: This Budget Cycle"
    p_track.font.size = Pt(10)
    p_track.font.name = "Google Sans Flex"
    p_track.font.color.rgb = COLOR_MUTED

    # Add details box on Slide 2 for links & credentials
    tb2 = slide2.shapes.add_textbox(Inches(3.92), Inches(3.95), Inches(5.6), Inches(1.2))
    tf_tb2 = tb2.text_frame
    tf_tb2.word_wrap = True
    
    p_l1 = tf_tb2.paragraphs[0]
    p_l1.text = "• Live Dashboard: atlanta-heat-advisor-frontend-1004921377034.us-central1.run.app"
    p_l1.font.size = Pt(9)
    p_l1.font.color.rgb = COLOR_DARK
    
    p_l2 = tf_tb2.add_paragraph()
    p_l2.text = "• Agent API (Cloud Run): atlanta-heat-advisor-1004921377034.us-central1.run.app"
    p_l2.font.size = Pt(9)
    p_l2.font.color.rgb = COLOR_DARK

    p_l3 = tf_tb2.add_paragraph()
    p_l3.text = "• GitHub: github.com/agustincori/A4I2026-challenge-1-walkability"
    p_l3.font.size = Pt(9)
    p_l3.font.color.rgb = COLOR_DARK

    if slide2.has_notes_slide:
        n2 = slide2.notes_slide.notes_text_frame
        n2.text = (
            "=== SLIDE 2: TITLE & TEAM IDENTIFICATION ===\n\n"
            "Team: ATL-6\n"
            "Solution: Atlanta Urban Climate Resilience & Walkability Advisor\n"
            "Challenge 1: Urban Heat Track (Target Municipality: Atlanta, GA)\n"
            "Live Deployed Dashboard: https://atlanta-heat-advisor-frontend-1004921377034.us-central1.run.app\n"
            "Cloud Run Agent API: https://atlanta-heat-advisor-1004921377034.us-central1.run.app\n"
            "GitHub Repository: https://github.com/agustincori/A4I2026-challenge-1-walkability\n\n"
            "--- VIDEO WALKTHROUGH INTRO (0:00 - 0:20) ---\n"
            "\"Good afternoon, judges. When a heat advisory hits Atlanta, news reports quote KATL Airport: 95°F. But in dense neighborhoods like Sweet Auburn and Peoplestown, microclimates run up to 4.8 degrees hotter. Over 47% of households there have no car, and tree canopy drops below 33%. For Challenge 1's budget track, Dana in the City Manager's office must site 3 permanent cooling centers before tomorrow's 9 AM City Council session. We built the Atlanta Urban Climate Resilience Advisor to solve this with BigQuery ML, pedestrian walk buffers, and an equity audit. Let's see the live tool in action.\""
        )

    # -------------------------------------------------------------
    # SLIDE 3: Our Team
    # -------------------------------------------------------------
    slide3 = prs.slides[2]
    # Shape 0 is the Table
    tbl = slide3.shapes[0].table
    # Row 0: Header
    # Row 1: Agustin Corigliano
    # Row 2: tshuggler
    team_data = [
        ["Agustin Corigliano", "pagustincorigliano@gmail.com", "[On File / Discord]", "Yes (1:00-4:00 PM on 10/29)", "Yes", "team@agentsforimpact.org"],
        ["tshuggler", "tshuggler@gmail.com", "[On File / Discord]", "Yes (1:00-4:00 PM on 10/29)", "Yes", "team@agentsforimpact.org"]
    ]
    for row_idx, member in enumerate(team_data, start=1):
        for col_idx, val in enumerate(member):
            cell = tbl.cell(row_idx, col_idx)
            cell.text = val
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(8.5)
                p.font.name = "Google Sans Flex"

    if slide3.has_notes_slide:
        n3 = slide3.notes_slide.notes_text_frame
        n3.text = (
            "=== SLIDE 3: TEAM & FILMING AVAILABILITY ===\n\n"
            "Team ID: ATL-6\n"
            "Members: Agustin Corigliano (pagustincorigliano@gmail.com), tshuggler (tshuggler@gmail.com)\n"
            "Filming Availability: Both team members confirm availability to return to Coca-Cola Roxy between 1:00-4:00 PM on Thursday 10/29.\n"
            "Project Sharing: YES - Authorized to share with employer and community partners."
        )

    # -------------------------------------------------------------
    # SLIDE 4: Real-world challenge (Challenge Overview)
    # -------------------------------------------------------------
    slide4 = prs.slides[3]
    # Shape 3 is the text box
    s4_txt = slide4.shapes[3]
    tf4 = s4_txt.text_frame
    tf4.clear()

    # Expand text frame coordinates to fit cleanly
    s4_txt.left = Inches(1.2)
    s4_txt.top = Inches(1.5)
    s4_txt.width = Inches(7.6)
    s4_txt.height = Inches(3.6)

    def add_section_header(tf, text, color=COLOR_RED):
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = text
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.name = "Google Sans Flex Medium"
        p.font.color.rgb = color
        p.space_after = Pt(3)
        return p

    def add_bullet(tf, bold_prefix, text, size=9.5):
        p = tf.add_paragraph()
        p.space_after = Pt(3)
        r1 = p.add_run()
        r1.text = "• " + bold_prefix
        r1.font.bold = True
        r1.font.size = Pt(size)
        r1.font.name = "Google Sans Flex"
        r1.font.color.rgb = COLOR_DARK
        r2 = p.add_run()
        r2.text = text
        r2.font.size = Pt(size)
        r2.font.name = "Google Sans Flex"
        r2.font.color.rgb = COLOR_DARK
        return p

    add_section_header(tf4, "⚠️ Real-World Challenge: Atlanta's Urban Heat Disparity", COLOR_RED)
    add_bullet(tf4, "The Airport Forecast Fallacy: ", "Regional forecasts quote KATL Airport (95°F), hiding lethal street-level microclimates running up to +4.77°F hotter in dense asphalt corridors like Sweet Auburn.")
    add_bullet(tf4, "Severe Transit & Canopy Deprivation: ", "In the hottest census tracts, >47% of households have no vehicle and tree canopy drops below 33%. Residents cannot walk or drive miles across town to regional cooling centers.")

    add_section_header(tf4, "🏛️ Details: The Municipal Decision Crisis", COLOR_PRIMARY)
    add_bullet(tf4, "The Persona (Dana, City Manager's Office): ", "Must site 3 permanent cooling centers / resilience hubs ahead of a 102°F heatwave for City Council authorization tomorrow at 9:00 AM.")
    add_bullet(tf4, "Why It Matters on a Societal Scale: ", "Heat is America's deadliest climate hazard. Grounding siting in empirical microclimates and pedestrian walk networks prevents heat mortality and eliminates political bias.")

    if slide4.has_notes_slide:
        n4 = slide4.notes_slide.notes_text_frame
        n4.text = (
            "=== SLIDE 4: REAL-WORLD CHALLENGE & SOCIETAL IMPACT ===\n\n"
            "Key Talking Points:\n"
            "1. Airport vs. Street Disparity: Airport readings (95°F) fail to warn residents in asphalt corridors experiencing 99.8°F.\n"
            "2. Transit Dependence: Over 47% of families in Sweet Auburn and Peoplestown do not own cars. Traditional 3-mile regional facilities leave them stranded.\n"
            "3. The Decision Scenario: Dana in the City Manager's Office has $1.2M capital funding and must deliver an unimpeachable council memo by 9:00 AM tomorrow.\n"
            "4. Societal Benefit: Grounding decisions in street-level data ensures public investments flow to historically disinvested, high-vulnerability neighborhoods."
        )

    # -------------------------------------------------------------
    # SLIDE 5: Our Agent (Impact)
    # -------------------------------------------------------------
    slide5 = prs.slides[4]
    s5_txt = slide5.shapes[1]
    tf5 = s5_txt.text_frame
    tf5.clear()

    s5_txt.left = Inches(1.2)
    s5_txt.top = Inches(1.4)
    s5_txt.width = Inches(7.6)
    s5_txt.height = Inches(3.8)

    add_section_header(tf5, "🤖 Our Custom Agent: Creating Meaningful Change", COLOR_PRIMARY)
    add_bullet(tf5, "Autonomous Municipal Advisor: ", "Powered by Gemini 2.5 Flash on Vertex AI via Google ADK with 7 specialized Python domain tools connecting directly to BigQuery ML.")
    add_bullet(tf5, "Conversational Landmark Search: ", "Planners query natural street names ('Sweet Auburn', 'Peoplestown'). The agent resolves Census GEOIDs automatically, eliminating technical friction.")
    add_bullet(tf5, "10-Minute Pedestrian Isochrones: ", "Replaces circular Euclidean radii with 800m street-network walk buffers, accounting for physical highway, rail, and transit access barriers.")

    add_section_header(tf5, "📈 Details: Concrete, Defensible Outcomes", COLOR_GREEN)
    add_bullet(tf5, "Top 3 Recommended Sites: ", "Sweet Auburn (Tract 27, Score 0.864, +4.61°F offset), South Pryor (Tract 55.02, Score 0.838, +3.94°F), and Mechanicsville (Tract 56, Score 0.811, +3.78°F), sheltering 19,850 high-risk residents.")
    add_bullet(tf5, "100% Outcome Equity Audit: ", "All selected sites clear Atlanta's 75th-percentile hardship thresholds (poverty ≥24.5%, carlessness ≥14.8%), guaranteeing zero equity drift.")
    add_bullet(tf5, "1-Click Council Resolution Memo: ", "Generates pre-populated legislative resolution with statutory citations, model justifications, and funding allocations ready for immediate Council vote.")

    if slide5.has_notes_slide:
        n5 = slide5.notes_slide.notes_text_frame
        n5.text = (
            "=== SLIDE 5: OUR AGENT & TANGIBLE OUTCOMES ===\n\n"
            "Live Demo Talking Points (0:20 - 1:40):\n"
            "1. Natural Language Interface: Planners talk in street names; the cognitive planner handles geocoding, BQML tool execution, and equity auditing.\n"
            "2. Pedestrian Isochrones: Blue 800-meter walk rings model true sidewalk accessibility rather than naive radial buffers.\n"
            "3. 100% Equity Compliance: Sweet Auburn, South Pryor, and Mechanicsville all exceed the 75th percentile city hardship cutoffs.\n"
            "4. Immediate Policy Adoption: 1-click Council Memo generator eliminates hours of administrative drafting ahead of tomorrow's 9 AM vote."
        )

    # -------------------------------------------------------------
    # SLIDE 6: Sources / Data Ecosystem
    # -------------------------------------------------------------
    slide6 = prs.slides[5]
    s6_txt = slide6.shapes[0]
    tf6 = s6_txt.text_frame
    tf6.clear()

    s6_txt.left = Inches(0.8)
    s6_txt.top = Inches(1.35)
    s6_txt.width = Inches(8.4)
    s6_txt.height = Inches(3.9)

    add_section_header(tf6, "🗄️ Curated Data Ecosystem Powering the Agent", COLOR_PRIMARY)
    add_bullet(tf6, "NOAA Heat Watch Vehicle Traverses: ", "High-resolution temperature traverses across 131 Fulton County census tracts on an extreme summer day, capturing afternoon peak heating.")
    add_bullet(tf6, "BigQuery ML (heat_offset_model): ", "LINEAR_REG model predicting microclimate thermal offset (ΔT ∈ [-1.2°F, +4.77°F]) relative to city baseline—isolating physical infrastructure from weather noise.")
    add_bullet(tf6, "CDC Social Vulnerability Index (SVI 2022) & Census ACS: ", "Tract-level poverty rates (≥24.5% hardship threshold), vehicle availability (≥14.8% carless), pre-1970 housing age, and elderly populations.")
    add_bullet(tf6, "NOAA GHCN Station Max (2018–2025): ", "7-year historical weather station records providing longitudinal context and spatial interpolation calibration.")

    add_section_header(tf6, "🔍 Details: Explainability & Bias Handling", COLOR_RED)
    add_bullet(tf6, "ML.EXPLAIN_PREDICT Decomposition: ", "Decomposes heat drivers per block: canopy deficit (+2.4°F), impervious surface density (+1.8°F), and pre-1970 housing vintage.")
    add_bullet(tf6, "Proactive Bias Handling by Design: ", "Race and ethnicity variables were strictly EXCLUDED from model training to prevent self-fulfilling redlining proxies; equity is enforced post-hoc on outcomes.")

    if slide6.has_notes_slide:
        n6 = slide6.notes_slide.notes_text_frame
        n6.text = (
            "=== SLIDE 6: DATA ECOSYSTEM & ETHICAL RIGOR ===\n\n"
            "Technical Rigor & Limitations (1:40 - 2:10):\n"
            "1. Offset vs Raw Temp: Predicting thermal offset isolates permanent urban fabric from day-to-day weather fluctuations.\n"
            "2. Bias Exclusion: Strict exclusion of race/ethnicity in training features prevents machine learning from codifying historical segregation.\n"
            "3. Honest Constraints: NOAA Heat Watch captures one representative summer day; multi-year variance requires longitudinal satellite calibration. We diagnose root causes (+2.4°F canopy deficit), but do not claim to simulate future tree growth without biological models."
        )

    # -------------------------------------------------------------
    # SLIDE 7: Prototype Architecture (Technical Blueprint)
    # -------------------------------------------------------------
    slide7 = prs.slides[6]
    s7_txt = slide7.shapes[0]
    tf7 = s7_txt.text_frame
    tf7.clear()

    s7_txt.left = Inches(0.8)
    s7_txt.top = Inches(1.35)
    s7_txt.width = Inches(8.4)
    s7_txt.height = Inches(3.9)

    add_section_header(tf7, "🏗️ Technical Build & Multi-Agent Architecture Blueprint", COLOR_PRIMARY)
    add_bullet(tf7, "Presentation Plane (React 18 + TS + Leaflet): ", "Municipal executive dashboard with real-time temperature slider (85°–105°F), interactive 800m isochrone walk overlays, and zero-key OSM map tiles.")
    add_bullet(tf7, "Agent Runtime (Gemini 2.5 Flash on Vertex AI): ", "Google ADK orchestration runtime with isolated planning sessions, bounded spatial guardrails ([-84.55, 33.64] to [-84.28, 33.89]), and correlated telemetry spans.")
    add_bullet(tf7, "Domain Toolset (7 Python Bindings): ", "predict_heat_offset, rank_cooling_centers, audit_equity, compare_tracts, query_history, generate_council_memo with standardized error contracts.")
    add_bullet(tf7, "Serverless Infrastructure (Cloud Run Gen2): ", "Production Python service hosting /run endpoint (<600ms latency), Application Default Credentials (zero API key exposure), and reverse-proxied /api/agent via Vite.")

    add_section_header(tf7, "🗺️ Multi-Clock Strategic Roadmap", COLOR_GREEN)
    add_bullet(tf7, "⚡ Today (Emergency): ", "Dispatch mobile hydration vans and cooling buses to Sweet Auburn during Heat Advisories (≥95°F).")
    add_bullet(tf7, "🏛️ This Budget Cycle: ", "Fund solar-reflective shade-sails at 42 unshaded MARTA stops inside 10-minute walk buffers.")
    add_bullet(tf7, "🌳 This Decade: ", "Urban forestry program targeted at the bottom 20% canopy tracts to reverse microclimate disparity.")

    if slide7.has_notes_slide:
        n7 = slide7.notes_slide.notes_text_frame
        n7.text = (
            "=== SLIDE 7: ARCHITECTURE TOUR & 3-CLOCK OUTRO ===\n\n"
            "Architecture Tour (2:10 - 2:40):\n"
            "• Gemini 2.5 Flash on Vertex AI via Google ADK runtime.\n"
            "• BigQuery ML heat_offset_model running in Google Cloud data plane.\n"
            "• Serverless Cloud Run endpoint live at atlanta-heat-advisor-1004921377034.us-central1.run.app.\n"
            "• React 18 + Leaflet GIS dashboard with zero CORS errors via Vite proxy.\n\n"
            "20-Second Outro (2:40 - 3:00):\n"
            "\"To wrap up: our advisor gives Atlanta leaders an actionable, defensible path across all three clocks. Tomorrow, emergency hydration vans to Sweet Auburn. This budget cycle, 42 MARTA transit shade structures. And this decade, urban canopy planting at the bottom 20% tracts. By connecting BigQuery ML with street-level walkability and an uncompromising equity audit, we ensure no neighborhood is left behind. Thank you.\""
        )

    # Save to all target locations
    repo_root = r"C:\Users\tshug\.gemini\antigravity\scratch\A4I2026-challenge-1-walkability"
    artifact_dir = r"C:\Users\tshug\.gemini\antigravity\brain\18c7ad46-c91f-408a-a59a-912c804c2ced"
    
    output_paths = [
        os.path.join(repo_root, "docs", "ATL-6_Atlanta_Heat_Resilience_Official_Deck.pptx"),
        os.path.join(repo_root, "docs", "Atlanta_Heat_Resilience_2_Slide_Deck.pptx"),
        os.path.join(repo_root, "docs", "Atlanta_Heat_Resilience_2_Slide_Deck.ppt"),
        os.path.join(repo_root, "frontend", "public", "Atlanta_Heat_Resilience_2_Slide_Deck.pptx"),
        os.path.join(repo_root, "frontend", "public", "Atlanta_Heat_Resilience_2_Slide_Deck.ppt"),
        os.path.join(repo_root, "frontend", "public", "ATL-6_Atlanta_Heat_Resilience_Official_Deck.pptx"),
        os.path.join(artifact_dir, "ATL-6_Atlanta_Heat_Resilience_Official_Deck.pptx"),
        os.path.join(artifact_dir, "Atlanta_Heat_Resilience_2_Slide_Deck.pptx"),
        os.path.join(artifact_dir, "Atlanta_Heat_Resilience_2_Slide_Deck.ppt"),
    ]

    primary_out = output_paths[0]
    prs.save(primary_out)
    for p in output_paths[1:]:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copyfile(primary_out, p)
        except Exception as e:
            print(f"Error copying to {p}: {e}")

    print(f"Successfully generated official template deck at: {primary_out}")

if __name__ == "__main__":
    build_deck()
