# Documentation & Submission Hub
## Atlanta Urban Climate Resilience & Walkability Advisor

Welcome to the central documentation and submission repository for the **Atlanta Urban Climate Resilience & Walkability Advisor** (Agents for Impact 2026 — Challenge 1: Urban Heat Track).

All competition submission deliverables, presentation decks, video walkthrough scripts, and technical architecture specifications are consolidated here in one place.

---

## 🏆 Official Competition Submission

* **[Official Submission Document (`SUBMISSION.md`)](SUBMISSION.md)**  
  The complete, publication-ready submission writeup for the [AngelHack Submission Portal](https://portal.angelhack.com/a4i-console). Covers executive summary, target municipal persona (Dana, City Manager's Office), top 5 capabilities, placement recommendation artifact with 100% equity compliance, all recent engineering hardening (runtime isolation, telemetry spans, model contracts, Vertex AI Cloud Run deployment, Vite CORS reverse proxy), defended decisions under the 25% Rigor rubric, honest limitations, and the multi-clock roadmap.

* **[Technical Architecture & Multi-Agent Orchestration (`SUBMISSION_OVERVIEW.md`)](SUBMISSION_OVERVIEW.md)**  
  Detailed system architecture diagrams, multi-layer decoupling (presentation, cognitive agent runtime, toolset, BQML data plane), cognitive planner mechanics, and component breakdowns.

---

## 📊 Pitch Deck & Presentation Materials

* **[2-Slide Executive Pitch Deck (`Atlanta_Heat_Resilience_2_Slide_Deck.pptx`)](Atlanta_Heat_Resilience_2_Slide_Deck.pptx)**  
  Official widescreen PowerPoint presentation designed for judging review:
  - **Slide 1:** Executive Hook, Municipal Scenario, Top 5 Capabilities & Siting Placement Recommendation Table (Sweet Auburn, Peoplestown, Mechanicsville).
  - **Slide 2:** Full-Stack Architecture Tour, Defended Decisions Audit, Honest Limitations & Multi-Clock Strategic Roadmap.
  - *Direct download portal:* **[Download Deck (`download_ppt.html`)](download_ppt.html)**

* **[Interactive Web Slides & PDF Export (`pitch_deck_2_slides.html`)](pitch_deck_2_slides.html)**  
  Browser-based slide deck viewer requiring zero local software. Features keyboard navigation (`←`/`→`) and a print stylesheet allowing instant 1-click export to high-resolution vector PDF.

* **[2-Slide Deck Markdown Reference (`PITCH_DECK_2_SLIDES.md`)](PITCH_DECK_2_SLIDES.md)**  
  Full text and ASCII layout reference of the 2-slide presentation for quick review and version tracking.

---

## 🎥 Pitch Video & Demonstration

* **[3-Minute Timed Video Walkthrough Script (`DEMO_SCRIPT.md`)](DEMO_SCRIPT.md)**  
  Choreographed second-by-second screen-share script designed to hit the 3-minute hard ceiling:
  - **[0:00 – 0:20] Section 2a:** Challenge hook & Atlanta scenario (Slide 1).
  - **[0:20 – 1:05] Section 2b.1:** Top 5 live capabilities in action (GIS map, 800m isochrones, street-name queries, composite ranking, 1-click council memo).
  - **[1:05 – 1:40] Section 2b.2:** Defended engineering decisions (bias exclusion, offset modeling, 75th-percentile hardship audit).
  - **[1:40 – 2:10] Section 2b.3:** Honest limitations & model boundaries (single-day Heat Watch baseline, station sparsity, no counterfactual simulation).
  - **[2:10 – 2:40] Section 2b.4:** Architecture tour & live Cloud Run execution (<600ms latency).
  - **[2:40 – 3:00] Section 2c:** Multi-clock strategic roadmap & outro (Slide 2).

---

## 🔬 Background Research & Context

* **[Data Sources & Analytical Framework (DATA_SOURCES.md)](DATA_SOURCES.md)**  
  Comprehensive data dictionary, lineage, mathematical derivations (tree canopy, plantable ROW, marginal costs), multi-departmental cost-sharing matrix, MILP optimization formulation, and cohort equity drawdown analysis.


* **[Atlanta Heat Vulnerability Synopsis (`atlanta_heat_vulnerability_synopsis (2).md`)](atlanta_heat_vulnerability_synopsis%20(2).md)**  
  Comprehensive research synopsis documenting the empirical drivers of Atlanta's urban heat island effect, historical tree canopy deficits, and demographic transportation vulnerabilities across Fulton County census tracts.

* **[Original Pitch Deck Draft (`PITCH_DECK.md`)](PITCH_DECK.md)**  
  Initial working draft of the team's presentation notes and messaging concepts.

---

## 🛠️ Deployed Endpoints & Codebase References

| Resource | URL / Path | Description |
|---|---|---|
| **Live Deployed Agent API** | [Cloud Run Service](https://atlanta-heat-advisor-1004921377034.us-central1.run.app) | Production Cloud Run agent endpoint with Vertex AI mode |
| **Agent Core & Tools** | [`../agent/`](../agent/) | ADK runtime, cognitive tools, telemetry spans, and contracts |
| **Data Plane & BQML** | [`../data_plane/`](../data_plane/) | BigQuery datasets, feature validation, and model training pipelines |
| **GIS Frontend** | [`../frontend/`](../frontend/) | React 18 + TypeScript + Leaflet dashboard with Vite reverse proxy |
| **Live Deployed Frontend Dashboard** | [Frontend Dashboard](https://atlanta-heat-advisor-frontend-1004921377034.us-central1.run.app) | Interactive React 18 Leaflet GIS interface |
