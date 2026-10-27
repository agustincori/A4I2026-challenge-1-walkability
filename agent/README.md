# Urban Heat Resilience ADK Agent (`agent/`)

Production-grade **Google ADK (Agent Development Kit)** implementation for **A4I 2026 — Challenge 1: Community Climate Resilience (Urban Heat)**.

---

## Architecture & Custom ADK Function Tools

The agent combines **Gemini**, **BigQuery ML (`ML.EXPLAIN_PREDICT`)**, and an optional **Managed MCP Server (MCP Toolbox for Databases)** with four purpose-built Python ADK Function Tools in [`agent/tools.py`](./tools.py):

| Tool | Purpose & Planner Question Answered | BigQuery / BQML Backing |
|---|---|---|
| [`predict_and_explain_location(latitude, longitude)`](./tools.py) | **Required BQML Tool (Q2 & Q4):** Verifies that `(latitude, longitude)` falls inside the loaded city's campaign bounding box in `heat_observations` (returning an explicit `OUT_OF_BOUNDS` refusal otherwise), interpolates nearby Census tract features via inverse-distance weighting, executes `ML.EXPLAIN_PREDICT`, and formats nested `top_feature_attributions` into human-readable drivers (e.g., `"+3.82°F from older building stock & urban form"`). | `ML.EXPLAIN_PREDICT` on `a4i_climate.heat_offset_model` + `tract_demographics` + `heat_observations` |
| [`rank_cooling_sites(top_n, mode)`](./tools.py) | **Placement Recommendation & Trade-off Tool (Q1, Q5, Q6):** Crosses `ML.EXPLAIN_PREDICT` predictions and attributions with `tract_demographics` (`no_vehicle_rate`, `poverty_rate`, `median_age`, `total_pop`) to rank candidate sites for `"today"` (Emergency Management), `"budget_cycle"` (Permanent Cooling Centers), or `"decade"` (Urban Forestry & Cool Pavement). | `ML.EXPLAIN_PREDICT` + `a4i_climate.tract_demographics` |
| [`audit_recommendations_equity(tract_ids)`](./tools.py) | **Post-Hoc Equity Audit Tool (Q7 — 25% Rigor & Judgment):** Normalizes 11-digit Census Tract IDs (`LPAD(geo_id, 11, '0')`) and compares recommended tracts against the citywide baseline (`poverty_rate`, `no_vehicle_rate`, `median_age`, `median_income`), implementing the *"Strip the variable, audit the outcome"* methodology. | `a4i_climate.tract_demographics` |
| [`get_station_heat_frequency(threshold_f)`](./tools.py) | **Temporal Frequency & Trend Tool (Q3):** Aggregates 7 years of NOAA GHCN-Daily regional weather station data per calendar day to compute annual days exceeding `threshold_f` (default `95.0°F`), multi-year averages, and linear warming trends across complete years. | `a4i_climate.station_daily_temps` |

---

## Quick Start (Cloud Shell)

```bash
# 1. Install dependencies
pip install -r agent/requirements.txt

# 2. (Optional) Train the BQML model explicitly, or let the agent auto-bootstrap it on first call
bq query --use_legacy_sql=false < agent/sql/bqml_model.sql

# 3. Launch ADK Web UI from the repository root
adk web .
```

---

## Deploying to Cloud Run (Pinning 1 Warm Instance for Demo Reliability)

```bash
gcloud run deploy urban-heat-agent \
  --source . \
  --dockerfile agent/Dockerfile \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project),BQ_DATASET=a4i_climate,BQ_LOCATION=US,BQML_MODEL=heat_offset_model"
```

---

## Running Unit Tests

```bash
python3 -m unittest discover -s agent/tests -v
```
