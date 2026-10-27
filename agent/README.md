# Atlanta Heat Resilience Advisor (ADK Agent)

**Track:** Challenge 1 - Urban Climate Resilience & Walkability  
**Target City:** Atlanta, GA  
**Powered by:** Google Agent Development Kit (ADK), Gemini 2.5 Flash on Vertex AI, BigQuery ML (`LINEAR_REG` with `ML.EXPLAIN_PREDICT`).

---

## 1. Overview & Architecture

The **Atlanta Heat Resilience Advisor** assists municipal decision-makers (city planners, emergency managers, City Council) in siting cooling centers, prioritizing climate investments, explaining heat disparities, and conducting climate equity audits.

### Core Architecture
- **Reasoning Engine:** Gemini 2.5 Flash via Google ADK (`google-adk`) configured on Vertex AI.
- **Predictive Engine:** The planning tools use BigQuery ML model `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_planning_model`, trained from the Atlanta Heat Watch campaign and Census tract features. Station tables provide temporal context separately; they are not training examples for the spatial offset model.
- **Explainability:** Employs `ML.EXPLAIN_PREDICT` to extract feature attributions (structure age, latitude, transit dependency, poverty rates) rather than black-box estimates.
- **Scope & Safety:** Calibrated strictly for Atlanta; refuses inquiries outside municipal bounds.

---

## 2. Tools & Capabilities

The agent preserves the 7 Atlanta tools and adds 4 planning tools from `feat/agent`:

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

### Extended Planning Tools

- `predict_and_explain_location(latitude, longitude)`: campaign-bound prediction,
  interpolated tract features, feature attributions, and nearby measured readings.
- `rank_cooling_sites(top_n, mode)`: explained rankings and interventions for
  `today`, `budget_cycle`, and `decade` planning.
- `audit_recommendations_equity(tract_ids)`: selected-versus-citywide differences
  in poverty, vehicle access, age, and income (complements the quartile audit).
- `get_station_heat_frequency(threshold_f)`: annual regional extreme-heat
  frequency and trend summaries.

The original Atlanta implementations remain in [`tools.py`](./tools.py).
The extended implementations live in [`planning_tools.py`](./planning_tools.py)
and are also re-exported by `tools.py`. Both sets are registered on the same
`atlanta_heat_resilience_advisor` agent.

### Configuration and Model Compatibility

Both toolsets share a lazily created BigQuery client configured by
[`config.py`](./config.py). Importing the agent does not query BigQuery.

| Environment variable | Default | Purpose |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` / `GCP_PROJECT` | `qwiklabs-gcp-03-1578f96a5a7a` | BigQuery project |
| `BQ_DATASET` | `a4i_climate` | Input tables and models |
| `BQ_LOCATION` | `US` | BigQuery job location |
| `BQML_MODEL` | `heat_offset_model` | Existing Atlanta model; label `offset_f` |
| `PLANNING_BQML_MODEL` | `heat_planning_model` | Extended planning model; label `heat_offset_f` |
| `GEMINI_MODEL` | `gemini-2.5-flash` | ADK reasoning model |
| `AUTO_BOOTSTRAP_BQML` | `true` | Train the planning model on first use if absent |
| `BBOX_PAD_DEGREES` | `0.03` | Planning prediction bounds padding |
| `EXPLAIN_TOP_K` | `4` | Planning attribution count |
| `MCP_TOOLBOX_URL` | unset | Optional MCP Toolbox endpoint |

**Keep the two model names distinct.** Their labels and input features differ.
Planning tools only resolve their configured model; they never discover an
arbitrary dataset model or replace the Atlanta model. The optional training
reference [`sql/bqml_model.sql`](./sql/bqml_model.sql) creates only
`qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_planning_model`; adjust its identifiers for other projects or datasets.
Do not treat outputs from the two model families as interchangeable.

Setting `MCP_TOOLBOX_URL` adds Toolbox tools to the agent. Connection or tool
loading errors propagate rather than silently disabling a configured integration.

---

## 3. Local Development & Testing

From the repository root:

```bash
python -m pip install -r agent/requirements.txt
python -m unittest discover -s agent/tests -p 'test_*.py'
```

For Vertex AI, set `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`,
and `GOOGLE_CLOUD_LOCATION`, and configure Application Default Credentials.
For local container testing:

```bash
docker build -f agent/Dockerfile -t atlanta-heat-advisor .
```

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

## 4. Live Cloud Run Deployment & Front-End Integration

### Live Endpoints
- **Web UI:** [https://atlanta-heat-advisor-hxywpvumaq-uc.a.run.app](https://atlanta-heat-advisor-hxywpvumaq-uc.a.run.app)
- **Health Check:** `GET /health` -> `{"status":"ok"}`
- **List Agents:** `GET /list-apps` -> `["agent"]`
- **Agent Run API:** `POST /run` (JSON body with user query)
- **Streaming API:** `POST /run_sse` (Server-sent events for streaming UI)

### Local Dev Alternative
```bash
adk web --port 8080 .
```
