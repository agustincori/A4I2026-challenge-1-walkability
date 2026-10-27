# Atlanta Heat Resilience Advisor (ADK Agent)

**Track:** Challenge 1 - Urban Climate Resilience & Walkability  
**Target City:** Atlanta, GA  
**Powered by:** Google Agent Development Kit (ADK), Gemini 2.5 Flash on Vertex AI, BigQuery ML (`LINEAR_REG` with `ML.EXPLAIN_PREDICT`).

---

## 1. Overview & Architecture

The **Atlanta Heat Resilience Advisor** assists municipal decision-makers (city planners, emergency managers, City Council) in siting cooling centers, prioritizing climate investments, explaining heat disparities, and conducting climate equity audits.

### Core Architecture
- **Reasoning Engine:** Gemini 2.5 Flash via Google ADK (`google-genai-adk`) configured on Vertex AI.
- **Predictive Engine:** BigQuery ML Model `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_offset_model` trained on NOAA Heat Watch traverse data fused with Census tract socioeconomic metrics.
- **Explainability:** Employs `ML.EXPLAIN_PREDICT` to extract feature attributions (structure age, latitude, transit dependency, poverty rates) rather than black-box estimates.
- **Scope & Safety:** Calibrated strictly for Atlanta; refuses inquiries outside municipal bounds.

---

## 2. Tools & Capabilities

The agent exposes 7 specialized Python tools addressing the core planner workflows:

1. `predict_heat_offset_and_explain(latitude, longitude, tract_id, baseline_forecast_f)`
   - Predicts localized microclimate heat offset (°F) and computes localized temperatures against any forecast.
   - Extracts top-3 feature attributions explaining *why* the microclimate is warmer.

2. `compare_locations_and_explain(lat1, lon1, label1, lat2, lon2, label2)`
   - Computes spatial temperature differentials between two coordinates (e.g. South Pryor St vs. Piedmont Park).
   - Breaks down the comparative structural drivers.

3. `compare_census_tracts(tract_id_1, tract_id_2)`
   - Provides side-by-side trade-off evaluations between two Census tracts.
   - Contrasts acute vulnerability (poverty & vehicle deprivation) against aggregate population scale.

4. `rank_cooling_center_sites(top_n, focus_criteria)`
   - Calculates a multi-factor composite vulnerability score:
     $$\text{Composite Score} = 0.4 \times \text{Offset (°F)} + 0.3 \times \text{Poverty Rate (scaled)} + 0.3 \times \text{Transit Deprivation (scaled)}$$
   - Returns top recommended Census tracts across Atlanta.

5. `query_heat_history(min_temp_f, start_year)`
   - Analyzes multi-year GHCN daily weather station observations from 2018 to present.
   - Counts extreme heat days (e.g. $\ge 95^\circ\text{F}$) and computes summer peak temperatures.

6. `get_tract_demographics(latitude, longitude, tract_id)`
   - Retrieves population, median age, median income, housing units, housing vintage, and transit access by coordinate or GEOID.

7. `audit_equity(selected_tract_ids)`
   - Benchmarks recommended sites against the Atlanta citywide 75th percentile (top quartile) for poverty and no-vehicle rates.
   - Validates that public investments counteract historic climate inequities.

---

## 3. Local Development & Testing

### Running Queries via CLI
```bash
# Siting recommendations
adk run agent "We have funding for 3 cooling centers. Where should they go?"

# Disparities and Explainability
adk run agent "Why is South Pryor St hotter than Piedmont Park?"

# Historical station trends
adk run agent "How often does Atlanta hit 95°F? Is it getting worse?"

# Tradeoff comparison
adk run agent "Compare Census Tract 13121006802 versus Tract 13121007808."

# Equity audit
adk run agent "Audit the equity of cooling centers in tracts 13121006802, 13121007808, and 13121007603."
```

### Launching the Web UI & API Server
```bash
adk web --port 8080 .
```

---

## 4. Integration with Front-End Lane

The ADK server exposes standard REST and streaming endpoints:
- `POST /run`: Execute a query and receive assistant responses.
- `GET /apps/agent/sessions`: Manage interactive conversation sessions.
- Interactive Web UI: Available at the root path of the deployed service.
