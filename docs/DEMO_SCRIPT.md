# Challenge 1: Video Walkthrough & Presentation Script
## 3 to 4-Minute Screen Recording Guide

---

### Timing Breakdown (Total: 3m 30s)
- **0:00 – 0:30 (30s):** The Problem & The Redlining / Heat Disparity Hook
- **0:30 – 1:15 (45s):** The BigQuery ML Model & Thermal Heat Offsets
- **1:15 – 2:00 (45s):** Interactive Walkability Map & Landmark Search Demo
- **2:00 – 2:45 (45s):** Centerpiece: The Outcome Equity Audit & City Council Memo
- **2:45 – 3:30 (45s):** Live AI Advisor Tool Execution & Final Takeaway

---

### [0:00 - 0:30] Hook & Problem Statement
*(Screen: Show the Atlanta Heat Resilience Dashboard overview)*

> **Speaker:**
> "Welcome. When a heat advisory hits Atlanta, news reports quote a single number from Hartsfield-Jackson Airport. But urban heat doesn't strike Atlanta equally.
> In neighborhoods like Sweet Auburn and Peoplestown, asphalt density and canopy deficits create microclimates that run **up to 4.7 degrees hotter** than the airport. Worse, nearly half of those households have no personal vehicle. If a city relies solely on raw regional forecasts, the most vulnerable citizens are left without reachable shelter.
> We built the **Atlanta Urban Climate Resilience & Walkability Advisor** to solve this using BigQuery ML, spatial walkability buffers, and an equity-first outcome audit."

---

### [0:30 - 1:15] The Data & BigQuery ML Microclimate Offsets
*(Screen: Switch to the Map view, click on Tract 44 Sweet Auburn or South Pryor)*

> **Speaker:**
> "To power this, we trained custom BigQuery ML linear regression models on historical NOAA weather stations and fused all 109 Atlanta census tracts with CDC Social Vulnerability Indices and urban tree canopy data.
> Rather than raw temperatures, our model predicts **spatial heat offsets**.
> As you can see when clicking on Sweet Auburn, this tract runs **+4.61°F hotter** than city baseline. With only 33% tree canopy and a 57% poverty rate, a 95°F afternoon at the airport translates to an extreme 99.6°F on the street."

---

### [1:15 - 2:00] Landmark Search & 10-Minute Walk Buffers ("Talk in Street Names")
*(Screen: In the map search bar, type "Peoplestown" or "Midtown", and toggle 10-minute walk buffers)*

> **Speaker:**
> "Judges know that city planners don't talk in GEOIDs or raw coordinates—they talk in neighborhood and street names.
> We built real-time autocomplete search into our map. We can type 'Peoplestown' or 'Sweet Auburn', and the map flies directly to the neighborhood.
> Notice the blue dashed circles: these are **10-minute pedestrian walking buffers (800 meters)** around candidate cooling centers. In an emergency, a resident without a car cannot walk 3 miles in 100-degree heat. Our tool tests whether real pedestrian access exists where heat stress is highest."

---

### [2:00 - 2:45] The Centerpiece: Siting Optimization & Outcome Equity Audit
*(Screen: Click the 'Siting Optimization' tab, then the 'Outcome Equity Audit' tab)*

> **Speaker:**
> "Next, our multi-objective siting algorithm balances heat exposure, poverty, and carlessness to recommend the top 3 resilience hubs.
> But we didn't stop at an algorithm. As the Challenge 1 guidance emphasizes, **we made the equity audit our centerpiece**.
> In this dashboard, we rigorously benchmark our candidate sites against Atlanta's 75th percentile hardship thresholds—24.5% poverty and 14.8% zero-vehicle households.
> 100% of our recommended sites clear these thresholds, preventing equity drift.
> And with one click, a planner can generate and print this formal **City Council Resolution Memo**, pre-populated with statutory justifications and BigQuery ML citations ready for legislative adoption."

---

### [2:45 - 3:30] Live Agent API Execution & Wrap Up
*(Screen: Switch to 'AI Advisor Chat' tab, click one of the preset chips like 'Rank top 3 cooling centers')*

> **Speaker:**
> "Finally, all of this is accessible through our conversational AI agent deployed live on Google Cloud Run.
> When we ask the advisor to rank sites or explain thermal attribution, it executes real BigQuery tools in real-time under 600ms latency, returning citations and explainable ML feature attributions.
> By connecting cutting-edge BigQuery ML with street-level pedestrian walkability and an uncompromising equity audit, we give Atlanta leaders the tool they need to protect every neighborhood this summer. Thank you."

---

### Visual Checklist Before Recording:
- [x] Dashboard running on port 8080 or Cloud Run
- [x] Mode toggled to "Live Agent API" or verified local data
- [x] Map markers and 10-minute walk rings clearly visible
- [x] Search bar tested with "Sweet Auburn", "Peoplestown", "Midtown"
- [x] Council resolution memo previewed
