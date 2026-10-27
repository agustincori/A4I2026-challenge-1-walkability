# Atlanta Urban Climate & Heat Resilience Dashboard (Frontend Lane)

**Challenge:** Challenge 1 - Urban Climate Resilience & Walkability  
**Target City:** Atlanta, GA  
**Track:** Frontend Lane  
**Integration:** Connected directly to deployed Cloud Run ADK Agent ([https://atlanta-heat-advisor-hxywpvumaq-uc.a.run.app](https://atlanta-heat-advisor-hxywpvumaq-uc.a.run.app))  
**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, Leaflet

---

## 1. Executive Summary & Purpose

The **Atlanta Heat Resilience Dashboard** translates complex spatial temperature offset predictions and Census vulnerability indicators into actionable municipal decisions for city planners, emergency management staff, and the Atlanta City Council.

As outlined in the challenge guidelines:
> *"Option Custom web UI: Full control. A map a council member could actually read beats a chat log."*  
> *"Strip the variable. Audit the outcome. Say you did both."*

This frontend connects directly to the live Cloud Run agent to deliver:
1. **Interactive Heat & Walkability Map**: Visualizes Atlanta census tract microclimate heat offsets (°F) alongside 10-minute pedestrian walking buffers around cooling center sites.
2. **Cooling Center Siting Optimization**: Ranks candidate public facilities by multi-objective composite score:
   $$\text{Composite Score} = 0.4 \times \text{Offset (°F)} + 0.3 \times \text{Poverty Rate} + 0.3 \times \text{Transit Deprivation}$$
3. **Algorithmic Climate Equity Audit**: Benchmarks recommended public investments against the City of Atlanta 75th percentile thresholds (Poverty: 24.5%, Carless Households: 14.8%) to verify that interventions counteract historical redlining and disinvestment.
4. **Historical Extreme Heat Trends (2018–2024)**: Visualizes multi-year GHCN weather station observations, demonstrating a 177% increase in days $\ge 95^\circ\text{F}$.
5. **Direct AI Advisor Chat**: Interactive natural language interface communicating directly with the deployed Cloud Run agent (`/run`), with preset action chips for all 7 Core Planner Questions and visual tool call inspection.

---

## 2. Integration with Deployed Cloud Run Agent

The dashboard communicates directly with the deployed ADK service at:
`https://atlanta-heat-advisor-hxywpvumaq-uc.a.run.app`

### Endpoints Used:
- `GET /health` – Live connection indicator and real-time latency ping.
- `POST /apps/agent/users/{userId}/sessions` – Session lifecycle management.
- `POST /run` – Multi-turn conversation and tool invocation dispatch.

### Dual Engine Capability: Live Agent API + TypeScript Mock Data
The two modes are explicit, not automatic failover:
- **Live Agent API Mode (Default):** Dispatches prompts to the Cloud Run agent and renders the completed `/run` event response. Session, HTTP and model errors surface to the user; they never become simulated recommendations.
- **Mock Data Layer Mode:** Provides a complete TypeScript simulation matching the BigQuery schemas (`heat_offset_model`, `tract_demographics`, `station_daily_temps`), allowing offline evaluation while backend SQL databases are provisioned.

### Grounded recommendation cards

The advisor renders cards only from successful (`status: OK`) ranking tool
payloads, never from numbers extracted from model prose. The Atlanta and planning
schemas are validated separately; failed, legacy status-less or malformed
rankings do not create cards. Unknown demographics are shown as unavailable,
not zero. Repeated/parallel tool responses are paired by their ADK call ID.

Cards show campaign-relative offsets, tract population and vulnerability,
model provenance when returned, and a coordinate link to OpenStreetMap in a new
tab. These links do not route through the dashboard's mock tract map or claim
verified facilities/walking routes. The audit action sends the exact displayed
tract IDs back to the live agent; it does not display a mock audit or change the
ranking. Actions from messages generated in a different data mode are disabled.

Model-generated interpretation remains available under a disclosure, separate
from tool evidence. Both model families are supported for display compatibility,
but their scores and offsets are not merged. No generated HTML, dynamic code
execution, or sandbox is needed. The map, siting and equity dashboard tabs still
use their existing demonstration datasets; these cards do not make those tabs live.

Run `npm test` for event/evidence parsing and live-error regression tests, then
`npm run build` for strict TypeScript checking and production bundling.

---

## 3. Key Components & Architecture

- `src/components/HeatMap.tsx`: High-performance Leaflet mapping engine plotting 109 Atlanta census tracts with dynamic heat offset color ramps (Green $\le 0^\circ\text{F}$ to Red $\ge +4^\circ\text{F}$), 800-meter walk buffers, landmark/tract search, and real-time mobile dispatched asset markers.
- `src/components/DecisionsAndDispatch.tsx`: Synthesized Planner Action Deck featuring:
  - **Decisions Needed Triage**: Prioritized municipal actions (FY25 Council Siting Memo, Bankhead Hydration Surge, Thomasville Senior Outreach, Campbellton Cooling Bus Relay).
  - **Resource Mover (Municipal Asset Allocator)**: Real-time inventory (Potable Hydration Trailers, Mobile Wellness Vans, MARTA Climate Shelter Buses) with instant field dispatch onto the Leaflet map and live protected population counters.
- `src/components/HeatAlertBanner.tsx`: High-visibility National Weather Service Stage 3 Heat Advisory ticker and modal with emergency directives and hotspot telemetry.
- `src/components/CoolingCenterRankings.tsx`: Siting optimizer table with interactive citywide baseline forecast slider (85°F to 105°F), automatically computing localized microclimate temperatures.
- `src/components/EquityAuditDashboard.tsx`: Compliance audit module proving 100% of top recommendations land in tracts exceeding top-quartile vulnerability, with 1-click export of City Council Legislative Resolution Memoranda.
- `src/components/HistoricalTrends.tsx`: Multi-year station temperature bar chart tracking severe heat trends from 2018 to 2024.
- `src/components/AdvisorChat.tsx`: Conversational AI advisor with one-click chips for the 7 Planner Questions and tool trace inspection.
- `src/components/ExplainabilityModal.tsx`: Visual breakdown of BigQuery ML `ML.EXPLAIN_PREDICT` feature attributions (canopy loss, structural vintage, transit deprivation).

---

## 4. Local Development & Deployment

### Standalone Interactive HTML Application (Zero-Dependency)
For immediate evaluation, offline demos, and council meetings without requiring Node.js or build steps:
- Open `index.html` or `atlanta_heat_resilience_dashboard.html` in any modern web browser.
- Includes complete interactive cartography, animated dispatch routes, decisions needed triage board, active emergency heat alerts, live resource mover simulator, BigQuery historical trends, and Cloud Run ADK agent chatbot integration.

### Quick Start:
```bash
# Enter frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite local development server
npm run dev
```
The application will launch on `http://localhost:3000`.

### Building for Production:
```bash
npm run build
```
Build output is generated in `frontend/dist/`.

### Previewing Production Build:
```bash
npm run preview
```
