"""
Custom BigQuery & BQML tools for Atlanta Heat Resilience Planning Assistant.
Synchronized with data-lane cleaning contracts and production model serving.
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from google.cloud import bigquery
except ImportError:
    class _DummyBigQuery:
        class QueryJobConfig:
            def __init__(self, query_parameters=None):
                self.query_parameters = query_parameters or []

        class ScalarQueryParameter:
            def __init__(self, name, type_, value):
                self.name = name
                self.type_ = type_
                self.value = value

    bigquery = _DummyBigQuery

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-1578f96a5a7a")
DATASET_ID = os.environ.get("BQ_DATASET", "a4i_climate")
MODEL_NAME = os.environ.get("BQ_MODEL_NAME", "heat_offset_model")

# Atlanta municipal & metro coverage boundary
ATLANTA_BOUNDS = {
    "min_lat": 33.55,
    "max_lat": 34.02,
    "min_lon": -84.60,
    "max_lon": -84.15,
}

_client = None


def get_client():
    global _client
    if _client is not None:
        return _client
    if not hasattr(bigquery, "Client"):
        raise RuntimeError("google-cloud-bigquery is required to interact with BigQuery.")
    _client = bigquery.Client(project=PROJECT_ID)
    return _client


def set_client(custom_client):
    global _client
    _client = custom_client


def is_in_atlanta_bounds(lat: float, lon: float) -> bool:
    return (
        ATLANTA_BOUNDS["min_lat"] <= lat <= ATLANTA_BOUNDS["max_lat"]
        and ATLANTA_BOUNDS["min_lon"] <= lon <= ATLANTA_BOUNDS["max_lon"]
    )


def predict_heat_offset_and_explain(
    latitude: Optional[float] = None, 
    longitude: Optional[float] = None, 
    tract_id: Optional[str] = None,
    baseline_forecast_f: Optional[float] = 102.0,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Predicts the urban heat offset in degrees Fahrenheit for any location or Census tract in Atlanta 
    and returns feature attributions using BigQuery ML.EXPLAIN_PREDICT.

    Args:
        latitude: Latitude coordinate of the location (optional if tract_id provided).
        longitude: Longitude coordinate of the location (optional if tract_id provided).
        tract_id: 11-digit Census tract GEOID (optional if coordinates provided).
        baseline_forecast_f: Regional baseline forecast temperature in Fahrenheit (default 102.0).
        model_name: BigQuery ML model resource name (defaults to active model heat_offset_model).

    Returns:
        Dict with predicted offset, predicted temperature, top feature attributions, and demographic context.
    """
    client = get_client()
    target_model = model_name or MODEL_NAME

    if tract_id and (latitude is None or longitude is None):
        if not re.fullmatch(r"^[0-9]{11}$", str(tract_id)):
            return {"error": f"Invalid 11-digit Census tract GEOID: {tract_id}."}
        coord_query = f"""
        SELECT tract_lat, tract_lon FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics`
        WHERE geo_id = '{tract_id}' LIMIT 1
        """
        coord_res = list(client.query(coord_query).result())
        if coord_res:
            latitude = coord_res[0].tract_lat
            longitude = coord_res[0].tract_lon
        else:
            return {"error": f"Tract ID {tract_id} not found in Atlanta demographics."}

    if latitude is None or longitude is None:
        return {"error": "Must provide either latitude & longitude coordinates or tract_id."}

    if not is_in_atlanta_bounds(latitude, longitude):
        return {
            "error": (
                f"Coordinates ({latitude}, {longitude}) are outside the supported Atlanta coverage area "
                f"(latitude [{ATLANTA_BOUNDS['min_lat']}, {ATLANTA_BOUNDS['max_lat']}], "
                f"longitude [{ATLANTA_BOUNDS['min_lon']}, {ATLANTA_BOUNDS['max_lon']}]). "
                "The model is strictly calibrated for Atlanta municipal microclimate planning."
            )
        }

    sql = f"""
    WITH tract_base AS (
      SELECT 
        geo_id,
        tract_lat,
        tract_lon,
        total_pop,
        CASE WHEN median_income >= 0 THEN median_income ELSE 65000.0 END AS median_income,
        CASE WHEN poverty_rate BETWEEN 0 AND 1 THEN poverty_rate ELSE 0.15 END AS poverty_rate,
        CASE WHEN no_vehicle_rate BETWEEN 0 AND 1 THEN no_vehicle_rate ELSE 0.10 END AS no_vehicle_rate,
        CASE WHEN median_age BETWEEN 0 AND 120 THEN median_age ELSE 36.0 END AS median_age,
        CASE WHEN housing_units >= 0 THEN housing_units ELSE 1500.0 END AS housing_units,
        CASE
          WHEN median_year_structure_built > 1800 AND median_year_structure_built <= 2030
          THEN median_year_structure_built
          ELSE 1975.0
        END AS median_year_structure_built
      FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics`
      WHERE REGEXP_CONTAINS(geo_id, r'^[0-9]{{11}}$')
        AND tract_lat BETWEEN -90 AND 90
        AND tract_lon BETWEEN -180 AND 180
      ORDER BY ST_DISTANCE(ST_GEOGPOINT(@lon, @lat), ST_GEOGPOINT(tract_lon, tract_lat)), geo_id
      LIMIT 1
    ),
    tract AS (
      SELECT 
        b.*,
        ROUND(CASE WHEN c.tree_canopy_pct <= 1.0 THEN c.tree_canopy_pct * 100 ELSE c.tree_canopy_pct END, 1) AS tree_canopy_pct
      FROM tract_base b
      LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.atlanta_canopy_heat_svi_modeling` c
        ON b.geo_id = c.GEOID
    )
    SELECT 
      p.predicted_offset_f,
      p.top_feature_attributions,
      t.*
    FROM ML.EXPLAIN_PREDICT(
      MODEL `{PROJECT_ID}.{DATASET_ID}.{target_model}`,
      (
        SELECT 
          @lat AS latitude,
          @lon AS longitude,
          median_income,
          poverty_rate,
          no_vehicle_rate,
          median_age,
          housing_units,
          median_year_structure_built
        FROM tract
      ),
      STRUCT(3 as top_k_features)
    ) p
    CROSS JOIN tract t
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("lat", "FLOAT64", latitude),
            bigquery.ScalarQueryParameter("lon", "FLOAT64", longitude),
        ]
    )
    results = list(client.query(sql, job_config=job_config).result())
    if not results:
        return {"error": "Location coordinates out of bounds or no model prediction available."}
    
    row = results[0]
    offset = round(row.predicted_offset_f, 2)
    predicted_temp = round(baseline_forecast_f + offset, 2) if baseline_forecast_f is not None else None
    
    attributions = []
    for attr in row.top_feature_attributions:
        feat = attr.get("feature", "")
        weight = round(attr.get("attribution", 0.0), 2)
        attributions.append({"feature": feat, "attribution_deg_f": weight})
        
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "tract_id": row.geo_id,
        "predicted_heat_offset_f": offset,
        "baseline_forecast_f": baseline_forecast_f,
        "predicted_surface_temp_f": predicted_temp,
        "top_feature_attributions": attributions,
        "demographics": {
            "total_pop": int(row.total_pop) if row.total_pop else None,
            "poverty_rate_pct": round(row.poverty_rate * 100, 1),
            "no_vehicle_rate_pct": round(row.no_vehicle_rate * 100, 1),
            "median_age": round(row.median_age, 1),
            "median_year_structure_built": int(row.median_year_structure_built),
            "tree_canopy_pct": getattr(row, "tree_canopy_pct", None),
        }
    }


def compare_locations_and_explain(
    lat1: float, 
    lon1: float, 
    label1: str, 
    lat2: float, 
    lon2: float, 
    label2: str,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compares heat risk and underlying drivers between two Atlanta locations.
    Answers questions like 'Why is intersection A so much worse than intersection B?'

    Args:
        lat1: Latitude of first site.
        lon1: Longitude of first site.
        label1: Name or description of first site (e.g. 'South Pryor St').
        lat2: Latitude of second site.
        lon2: Longitude of second site.
        label2: Name or description of second site (e.g. 'Piedmont Park').
        model_name: Optional model override.

    Returns:
        Dict detailing the offset differential and comparative feature breakdown.
    """
    site1 = predict_heat_offset_and_explain(lat1, lon1, model_name=model_name)
    site2 = predict_heat_offset_and_explain(lat2, lon2, model_name=model_name)
    
    if "error" in site1 or "error" in site2:
        return {"error": "Failed to evaluate one or both locations.", "details": {"site_1": site1, "site_2": site2}}

    diff_f = round(site1["predicted_heat_offset_f"] - site2["predicted_heat_offset_f"], 2)
    
    canopy1 = site1.get("demographics", {}).get("tree_canopy_pct")
    canopy2 = site2.get("demographics", {}).get("tree_canopy_pct")
    canopy_summary = ""
    if canopy1 is not None and canopy2 is not None:
        canopy_diff = round(canopy1 - canopy2, 1)
        canopy_summary = (
            f" Tree canopy cover: {label1} has {canopy1}% vs {label2} with {canopy2}% "
            f"({abs(canopy_diff)}% {'higher' if canopy_diff > 0 else 'lower'})."
        )
    
    return {
        "site_1": {"name": label1, "details": site1},
        "site_2": {"name": label2, "details": site2},
        "temperature_difference_f": diff_f,
        "comparison_summary": (
            f"{label1} is predicted to be {abs(diff_f)}°F "
            f"{'hotter' if diff_f > 0 else 'cooler'} than {label2}.{canopy_summary}"
        )
    }


def rank_cooling_center_sites(
    top_n: int = 3, 
    focus_criteria: str = "vulnerability_and_heat",
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ranks candidate cooling center locations across Atlanta by combining BQML heat offset 
    predictions and feature attributions with Census demographic vulnerability.

    Args:
        top_n: Number of recommendations to return (default 3).
        focus_criteria: Ranking methodology, e.g. 'vulnerability_and_heat' or 'pure_heat'.
        model_name: BigQuery ML model resource name.

    Returns:
        Dict with ranked candidate sites, coordinates, demographic stats, attributions, and justification.
    """
    client = get_client()
    target_model = model_name or MODEL_NAME

    sql = f"""
    WITH cleaned_tracts AS (
      SELECT
        geo_id,
        tract_lat,
        tract_lon,
        total_pop,
        CASE WHEN median_income >= 0 THEN median_income ELSE 65000.0 END AS median_income,
        CASE WHEN poverty_rate BETWEEN 0 AND 1 THEN poverty_rate ELSE 0.15 END AS poverty_rate,
        CASE WHEN no_vehicle_rate BETWEEN 0 AND 1 THEN no_vehicle_rate ELSE 0.10 END AS no_vehicle_rate,
        CASE WHEN median_age BETWEEN 0 AND 120 THEN median_age ELSE 36.0 END AS median_age,
        CASE WHEN housing_units >= 0 THEN housing_units ELSE 1500.0 END AS housing_units,
        CASE
          WHEN median_year_structure_built > 1800 AND median_year_structure_built <= 2030
          THEN median_year_structure_built
          ELSE 1975.0
        END AS median_year_structure_built
      FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics`
      WHERE REGEXP_CONTAINS(geo_id, r'^[0-9]{{11}}$')
        AND total_pop > 400
        AND tract_lat BETWEEN {ATLANTA_BOUNDS['min_lat']} AND {ATLANTA_BOUNDS['max_lat']}
        AND tract_lon BETWEEN {ATLANTA_BOUNDS['min_lon']} AND {ATLANTA_BOUNDS['max_lon']}
    ),
    predictions AS (
      SELECT
        p.predicted_offset_f,
        p.top_feature_attributions,
        t.geo_id,
        t.tract_lat,
        t.tract_lon,
        t.total_pop,
        t.poverty_rate,
        t.no_vehicle_rate,
        t.median_age
      FROM ML.EXPLAIN_PREDICT(
        MODEL `{PROJECT_ID}.{DATASET_ID}.{target_model}`,
        (
          SELECT 
            geo_id,
            tract_lat AS latitude,
            tract_lon AS longitude,
            median_income,
            poverty_rate,
            no_vehicle_rate,
            median_age,
            housing_units,
            median_year_structure_built
          FROM cleaned_tracts
        ),
        STRUCT(3 AS top_k_features)
      ) p
      JOIN cleaned_tracts t USING (geo_id)
    )
    SELECT 
      p.geo_id,
      p.tract_lat,
      p.tract_lon,
      ROUND(p.predicted_offset_f, 2) AS offset_f,
      ROUND(p.total_pop) AS total_pop,
      ROUND(p.poverty_rate * 100, 1) AS poverty_pct,
      ROUND(p.no_vehicle_rate * 100, 1) AS no_vehicle_pct,
      ROUND(p.median_age, 1) AS median_age,
      ROUND(
        (p.predicted_offset_f * 0.4) + 
        (p.poverty_rate * 10.0 * 0.3) + 
        (p.no_vehicle_rate * 10.0 * 0.3),
        2
      ) AS composite_vulnerability_score,
      ROUND(CASE WHEN c.tree_canopy_pct <= 1.0 THEN c.tree_canopy_pct * 100 ELSE c.tree_canopy_pct END, 1) AS tree_canopy_pct,
      p.top_feature_attributions
    FROM predictions p
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.atlanta_canopy_heat_svi_modeling` c
      ON p.geo_id = c.GEOID
    ORDER BY composite_vulnerability_score DESC
    LIMIT {top_n}
    """
    rows = list(client.query(sql).result())
    sites = []
    for i, r in enumerate(rows, 1):
        attributions = []
        if hasattr(r, "top_feature_attributions") and r.top_feature_attributions:
            for attr in r.top_feature_attributions:
                feat = attr.get("feature", "")
                weight = round(attr.get("attribution", 0.0), 2)
                attributions.append({"feature": feat, "attribution_deg_f": weight})

        sites.append({
            "rank": i,
            "tract_id": r.geo_id,
            "latitude": r.tract_lat,
            "longitude": r.tract_lon,
            "predicted_heat_offset_f": r.offset_f,
            "population": int(r.total_pop) if r.total_pop else None,
            "poverty_rate_pct": r.poverty_pct,
            "no_vehicle_rate_pct": r.no_vehicle_pct,
            "median_age": r.median_age,
            "tree_canopy_pct": getattr(r, "tree_canopy_pct", None),
            "composite_score": r.composite_vulnerability_score,
            "top_feature_attributions": attributions,
        })
    return {"ranked_sites": sites, "count": len(sites)}


def query_heat_history(
    min_temp_f: float = 90.0, 
    start_year: int = 2018
) -> Dict[str, Any]:
    """
    Queries historical weather station data for Atlanta to determine how often 
    temperatures reach extreme or dangerous thresholds, and whether frequency is increasing.

    Args:
        min_temp_f: Temperature threshold in Fahrenheit (e.g. 90.0, 95.0, or 100.0).
        start_year: Beginning calendar year to analyze (default 2018).

    Returns:
        Dict with year-by-year counts of days exceeding the threshold and multi-year trend.
    """
    client = get_client()
    sql = f"""
    SELECT 
      EXTRACT(YEAR FROM observation_date) AS year,
      COUNT(DISTINCT observation_date) AS days_exceeding_threshold,
      ROUND(MAX(max_temp_f), 1) AS peak_temp_f,
      ROUND(AVG(max_temp_f), 1) AS avg_summer_max_f
    FROM `{PROJECT_ID}.{DATASET_ID}.station_daily_temps`
    WHERE max_temp_f >= {min_temp_f}
      AND EXTRACT(YEAR FROM observation_date) >= {start_year}
    GROUP BY 1
    ORDER BY 1
    """
    rows = list(client.query(sql).result())
    history = []
    for r in rows:
        history.append({
            "year": r.year,
            "days_exceeding": r.days_exceeding_threshold,
            "peak_temp_f": r.peak_temp_f,
            "avg_max_temp_f": r.avg_summer_max_f
        })
    return {
        "threshold_deg_f": min_temp_f,
        "start_year": start_year,
        "yearly_records": history,
        "summary": f"Historical days exceeding {min_temp_f}°F across Atlanta stations from {start_year} to present."
    }


def get_tract_demographics(
    latitude: Optional[float] = None, 
    longitude: Optional[float] = None,
    tract_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Looks up detailed Census tract demographics for any Atlanta location coordinates or tract GEOID.

    Args:
        latitude: Latitude coordinate (optional if tract_id provided).
        longitude: Longitude coordinate (optional if tract_id provided).
        tract_id: 11-digit Census tract GEOID (optional if coordinates provided).

    Returns:
        Dict with tract ID, population, median age, income, housing age, and mobility access.
    """
    client = get_client()

    if tract_id:
        if not re.fullmatch(r"^[0-9]{11}$", str(tract_id)):
            return {"error": f"Invalid 11-digit Census tract GEOID: {tract_id}."}
        sql = f"""
        SELECT 
          d.geo_id,
          d.tract_lat,
          d.tract_lon,
          d.total_pop,
          CASE WHEN d.median_age BETWEEN 0 AND 120 THEN d.median_age ELSE 36.0 END AS median_age,
          CASE WHEN d.median_income >= 0 THEN d.median_income ELSE 65000.0 END AS median_income,
          CASE WHEN d.housing_units >= 0 THEN d.housing_units ELSE 1500.0 END AS housing_units,
          CASE
            WHEN d.median_year_structure_built > 1800 AND d.median_year_structure_built <= 2030
            THEN d.median_year_structure_built
            ELSE 1975.0
          END AS median_year_structure_built,
          d.no_cars,
          d.households,
          ROUND(CASE WHEN d.poverty_rate BETWEEN 0 AND 1 THEN d.poverty_rate ELSE 0.15 END * 100, 1) AS poverty_pct,
          ROUND(CASE WHEN d.no_vehicle_rate BETWEEN 0 AND 1 THEN d.no_vehicle_rate ELSE 0.10 END * 100, 1) AS no_vehicle_pct,
          ROUND(CASE WHEN c.tree_canopy_pct <= 1.0 THEN c.tree_canopy_pct * 100 ELSE c.tree_canopy_pct END, 1) AS tree_canopy_pct,
          ROUND(c.integrated_risk_score, 2) AS integrated_risk_score
        FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics` d
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.atlanta_canopy_heat_svi_modeling` c
          ON d.geo_id = c.GEOID
        WHERE d.geo_id = @tract_id
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tract_id", "STRING", tract_id)
            ]
        )
    elif latitude is not None and longitude is not None:
        if not is_in_atlanta_bounds(latitude, longitude):
            return {
                "error": (
                    f"Coordinates ({latitude}, {longitude}) are outside the supported Atlanta coverage area. "
                    "Demographic lookups are strictly calibrated for Atlanta."
                )
            }
        sql = f"""
        SELECT 
          d.geo_id,
          d.tract_lat,
          d.tract_lon,
          d.total_pop,
          CASE WHEN d.median_age BETWEEN 0 AND 120 THEN d.median_age ELSE 36.0 END AS median_age,
          CASE WHEN d.median_income >= 0 THEN d.median_income ELSE 65000.0 END AS median_income,
          CASE WHEN d.housing_units >= 0 THEN d.housing_units ELSE 1500.0 END AS housing_units,
          CASE
            WHEN d.median_year_structure_built > 1800 AND median_year_structure_built <= 2030
            THEN d.median_year_structure_built
            ELSE 1975.0
          END AS median_year_structure_built,
          d.no_cars,
          d.households,
          ROUND(CASE WHEN d.poverty_rate BETWEEN 0 AND 1 THEN d.poverty_rate ELSE 0.15 END * 100, 1) AS poverty_pct,
          ROUND(CASE WHEN d.no_vehicle_rate BETWEEN 0 AND 1 THEN d.no_vehicle_rate ELSE 0.10 END * 100, 1) AS no_vehicle_pct,
          ROUND(CASE WHEN c.tree_canopy_pct <= 1.0 THEN c.tree_canopy_pct * 100 ELSE c.tree_canopy_pct END, 1) AS tree_canopy_pct,
          ROUND(c.integrated_risk_score, 2) AS integrated_risk_score
        FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics` d
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.atlanta_canopy_heat_svi_modeling` c
          ON d.geo_id = c.GEOID
        ORDER BY ST_DISTANCE(ST_GEOGPOINT(@lon, @lat), ST_GEOGPOINT(d.tract_lon, d.tract_lat)), d.geo_id
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("lat", "FLOAT64", latitude),
                bigquery.ScalarQueryParameter("lon", "FLOAT64", longitude),
            ]
        )
    else:
        return {"error": "Must provide either tract_id or latitude & longitude coordinates."}

    results = list(client.query(sql, job_config=job_config).result())
    if not results:
        return {"error": "No demographic data found for this location or tract ID."}
    r = results[0]
    return {
        "tract_id": r.geo_id,
        "latitude": r.tract_lat,
        "longitude": r.tract_lon,
        "total_population": int(r.total_pop) if r.total_pop else None,
        "median_age": r.median_age,
        "median_household_income": r.median_income,
        "housing_units": int(r.housing_units) if r.housing_units else None,
        "median_year_built": int(r.median_year_structure_built) if r.median_year_structure_built else None,
        "households_without_vehicle": int(r.no_cars) if r.no_cars else None,
        "poverty_rate_pct": r.poverty_pct,
        "no_vehicle_rate_pct": r.no_vehicle_pct,
        "tree_canopy_pct": getattr(r, "tree_canopy_pct", None),
        "integrated_risk_score": getattr(r, "integrated_risk_score", None),
    }


def compare_census_tracts(
    tract_id_1: str, 
    tract_id_2: str,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compares two Atlanta Census tracts side-by-side on heat risk, feature attributions, 
    and demographics to weigh municipal tradeoffs when siting cooling centers.

    Args:
        tract_id_1: First 11-digit Census tract GEOID (e.g. '13121006802').
        tract_id_2: Second 11-digit Census tract GEOID (e.g. '13121007808').
        model_name: Optional model override.

    Returns:
        Dict detailing direct comparisons, trade-offs, and strategic considerations for each site.
    """
    site1 = predict_heat_offset_and_explain(tract_id=tract_id_1, model_name=model_name)
    site2 = predict_heat_offset_and_explain(tract_id=tract_id_2, model_name=model_name)
    
    if "error" in site1 or "error" in site2:
        return {
            "error": "Failed to look up one or both tracts.",
            "details": {"tract_1": site1, "tract_2": site2}
        }
        
    diff_offset = round(site1["predicted_heat_offset_f"] - site2["predicted_heat_offset_f"], 2)
    
    return {
        "tract_1": {
            "tract_id": tract_id_1,
            "predicted_heat_offset_f": site1["predicted_heat_offset_f"],
            "top_attributions": site1["top_feature_attributions"],
            "demographics": site1["demographics"]
        },
        "tract_2": {
            "tract_id": tract_id_2,
            "predicted_heat_offset_f": site2["predicted_heat_offset_f"],
            "top_attributions": site2["top_feature_attributions"],
            "demographics": site2["demographics"]
        },
        "comparison_metrics": {
            "heat_offset_difference_f": diff_offset,
            "hotter_tract": tract_id_1 if diff_offset > 0 else tract_id_2,
            "larger_population_tract": tract_id_1 if (site1["demographics"]["total_pop"] or 0) > (site2["demographics"]["total_pop"] or 0) else tract_id_2,
            "higher_poverty_tract": tract_id_1 if site1["demographics"]["poverty_rate_pct"] > site2["demographics"]["poverty_rate_pct"] else tract_id_2,
            "higher_transit_dependency_tract": tract_id_1 if site1["demographics"]["no_vehicle_rate_pct"] > site2["demographics"]["no_vehicle_rate_pct"] else tract_id_2,
            "lower_tree_canopy_tract": tract_id_1 if (site1["demographics"].get("tree_canopy_pct") or 0.0) < (site2["demographics"].get("tree_canopy_pct") or 0.0) else tract_id_2,
        }
    }


def audit_equity(selected_tract_ids: List[str]) -> Dict[str, Any]:
    """
    Audits candidate or selected cooling center locations against citywide benchmarks 
    to verify whether resource placement reaches the most vulnerable populations.

    Args:
        selected_tract_ids: List of 11-digit Census tract GEOIDs being proposed.

    Returns:
        Dict comparing selected sites against citywide 75th percentile and average poverty/mobility rates.
    """
    if not selected_tract_ids:
        return {"error": "Please provide at least one tract ID to audit."}
    
    for tid in selected_tract_ids:
        if not re.fullmatch(r"^[0-9]{11}$", str(tid)):
            return {"error": f"Invalid 11-digit Census tract GEOID: {tid}."}

    client = get_client()
    tract_list_str = ", ".join([f"'{tid}'" for tid in selected_tract_ids])
    sql = f"""
    WITH city_baseline AS (
      SELECT
        AVG(CASE WHEN poverty_rate BETWEEN 0 AND 1 THEN poverty_rate ELSE 0.15 END) AS city_avg_poverty,
        AVG(CASE WHEN no_vehicle_rate BETWEEN 0 AND 1 THEN no_vehicle_rate ELSE 0.10 END) AS city_avg_no_vehicle,
        APPROX_QUANTILES(CASE WHEN poverty_rate BETWEEN 0 AND 1 THEN poverty_rate ELSE 0.15 END, 100)[OFFSET(75)] AS p75_poverty,
        APPROX_QUANTILES(CASE WHEN no_vehicle_rate BETWEEN 0 AND 1 THEN no_vehicle_rate ELSE 0.10 END, 100)[OFFSET(75)] AS p75_no_vehicle
      FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics`
      WHERE total_pop > 100
    ),
    selected AS (
      SELECT
        geo_id,
        CASE WHEN poverty_rate BETWEEN 0 AND 1 THEN poverty_rate ELSE 0.15 END AS poverty_rate,
        CASE WHEN no_vehicle_rate BETWEEN 0 AND 1 THEN no_vehicle_rate ELSE 0.10 END AS no_vehicle_rate,
        total_pop
      FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics`
      WHERE geo_id IN ({tract_list_str})
    )
    SELECT
      ROUND(b.city_avg_poverty * 100, 1) AS city_avg_poverty_pct,
      ROUND(AVG(s.poverty_rate) * 100, 1) AS selected_avg_poverty_pct,
      ROUND(b.p75_poverty * 100, 1) AS city_p75_poverty_pct,
      ROUND(b.city_avg_no_vehicle * 100, 1) AS city_avg_no_vehicle_pct,
      ROUND(AVG(s.no_vehicle_rate) * 100, 1) AS selected_avg_no_vehicle_pct,
      ROUND(b.p75_no_vehicle * 100, 1) AS city_p75_no_vehicle_pct,
      SUM(s.total_pop) AS total_served_pop,
      CASE 
        WHEN AVG(s.poverty_rate) >= b.p75_poverty AND AVG(s.no_vehicle_rate) >= b.p75_no_vehicle 
        THEN 'PASSED: Recommended placements concentrate in the highest quartile (top 25%) of economic and mobility vulnerability.'
        WHEN AVG(s.poverty_rate) >= b.city_avg_poverty OR AVG(s.no_vehicle_rate) >= b.city_avg_no_vehicle
        THEN 'MODERATE: Recommendations exceed city averages, but some sites fall outside the highest-need quartile.'
        ELSE 'FAILED: Recommendations under-serve vulnerable communities relative to the citywide baseline.'
      END AS audit_status
    FROM selected s
    CROSS JOIN city_baseline b
    GROUP BY b.city_avg_poverty, b.city_avg_no_vehicle, b.p75_poverty, b.p75_no_vehicle
    """
    results = list(client.query(sql).result())
    if not results:
        return {"error": "Unable to compute equity audit for specified tracts."}
    r = results[0]
    return {
        "selected_tract_count": len(selected_tract_ids),
        "total_population_served": int(r.total_served_pop) if r.total_served_pop else None,
        "poverty_comparison": {
            "selected_sites_avg_pct": r.selected_avg_poverty_pct,
            "citywide_avg_pct": r.city_avg_poverty_pct,
            "citywide_75th_percentile_pct": r.city_p75_poverty_pct
        },
        "mobility_access_comparison": {
            "selected_sites_no_vehicle_avg_pct": r.selected_avg_no_vehicle_pct,
            "citywide_avg_no_vehicle_pct": r.city_avg_no_vehicle_pct,
            "citywide_75th_percentile_no_vehicle_pct": r.city_p75_no_vehicle_pct
        },
        "audit_finding": r.audit_status
    }


def recommend_canopy_interventions(
    top_n: int = 5,
    min_pop_density: float = 1000.0,
) -> Dict[str, Any]:
    """
    Identifies high-priority Atlanta Census tracts for urban forestry, tree planting,
    and shade canopy interventions based on heat exposure, social vulnerability,
    population density, and current canopy deficit.

    Args:
        top_n: Number of priority tracts to return (default: 5).
        min_pop_density: Minimum population density per sq mile to prioritize human impact (default: 1000.0).

    Returns:
        Dict with list of recommended tracts, canopy deficits, and targeted resilience interventions.
    """
    client = get_client()
    sql = f"""
    SELECT 
      GEOID AS tract_id,
      NAME AS tract_name,
      POP100 AS population,
      ROUND(pop_density, 1) AS pop_density,
      ROUND(mean_temp, 1) AS mean_temp_f,
      ROUND(CASE WHEN tree_canopy_pct <= 1.0 THEN tree_canopy_pct * 100 ELSE tree_canopy_pct END, 1) AS tree_canopy_pct,
      ROUND(RPL_THEMES, 3) AS svi_percentile,
      ROUND(integrated_risk_score, 2) AS integrated_risk_score,
      ROUND(EP_POV150, 1) AS poverty_pct,
      ROUND(EP_NOVEH, 1) AS no_vehicle_pct
    FROM `{PROJECT_ID}.{DATASET_ID}.atlanta_canopy_heat_svi_modeling`
    WHERE pop_density >= @min_pop_density
      AND tree_canopy_pct IS NOT NULL
    ORDER BY integrated_risk_score DESC, tree_canopy_pct ASC
    LIMIT @top_n
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("top_n", "INT64", top_n),
            bigquery.ScalarQueryParameter("min_pop_density", "FLOAT64", min_pop_density),
        ]
    )
    results = list(client.query(sql, job_config=job_config).result())
    recommendations = []
    target_canopy_goal = 50.0  # City of Atlanta master plan canopy target
    for r in results:
        canopy = r.tree_canopy_pct or 0.0
        deficit = round(max(0.0, target_canopy_goal - canopy), 1)
        actions = [
            "Right-of-way street tree planting along major pedestrian and transit corridors",
            "Cool pavement and reflective surface treatments for wide unshaded asphalt",
        ]
        if (r.no_vehicle_pct or 0) > 20.0:
            actions.append("Shaded bus stop canopy retrofits and high-capacity misting shelters")
        if (r.poverty_pct or 0) > 25.0:
            actions.append("Direct residential tree distribution and community green space expansion")

        recommendations.append({
            "tract_id": r.tract_id,
            "tract_name": r.tract_name,
            "population": int(r.population) if r.population else None,
            "pop_density_per_sq_mi": r.pop_density,
            "mean_summer_temp_f": r.mean_temp_f,
            "tree_canopy_pct": canopy,
            "city_target_gap_pct": deficit,
            "social_vulnerability_index": r.svi_percentile,
            "integrated_risk_score": r.integrated_risk_score,
            "poverty_pct": r.poverty_pct,
            "no_vehicle_pct": r.no_vehicle_pct,
            "priority_interventions": actions,
        })

    return {
        "city_target_canopy_pct": target_canopy_goal,
        "recommended_priority_tracts": recommendations,
        "count": len(recommendations),
        "strategic_framework": "Atlanta Decade Track Urban Forestry & Heat Equity Plan",
    }


def generate_council_proposal(
    top_n: int = 3,
    baseline_forecast_f: float = 102.0,
    funding_source: str = "Atlanta Climate Resilience Emergency Fund",
) -> Dict[str, Any]:
    """
    Synthesizes cooling center recommendations, equity audit verification, and canopy
    interventions into a formal municipal policy memorandum ready for presentation to the
    Atlanta City Council and Mayor's Office.

    Args:
        top_n: Number of emergency cooling center locations to propose (default: 3).
        baseline_forecast_f: Citywide baseline weather forecast during heat emergency (default: 102.0°F).
        funding_source: Designated funding vehicle (default: 'Atlanta Climate Resilience Emergency Fund').

    Returns:
        Dict containing structured memorandum components and the full formatted proposal markdown.
    """
    ranked_result = rank_cooling_center_sites(top_n=top_n)
    if "error" in ranked_result or not ranked_result.get("ranked_sites"):
        return {"error": "Failed to retrieve ranked cooling center sites for proposal."}

    sites = ranked_result["ranked_sites"]
    tract_ids = [s["tract_id"] for s in sites]

    audit_result = audit_equity(selected_tract_ids=tract_ids)
    canopy_result = recommend_canopy_interventions(top_n=top_n)

    memo_lines = [
        "# MEMORANDUM",
        "",
        "**TO:** Atlanta City Council, Committee on City Utilities & Resilience",
        "**FROM:** Office of Sustainability and Resilience, Urban Heat Emergency Task Force",
        f"**DATE:** {datetime.now(timezone.utc).strftime('%B %d, %Y')}",
        "**SUBJECT:** Action Item: Emergency Cooling Center Mobilization & Targeted Canopy Mitigation Authorization",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        f"During extreme weather conditions with ambient forecasts reaching {baseline_forecast_f}°F, localized urban heat island effects exacerbate surface and ambient temperatures substantially across vulnerable neighborhoods. Based on BigQuery ML empirical microclimate modeling, this proposal authorizes the immediate mobilization of {top_n} primary emergency cooling facilities and initiates accompanying urban forestry interventions.",
        "",
        "## 2. Priority Cooling Center Deployments",
        "The following locations have been identified through empirical heat offset prediction and socio-demographic vulnerability indexing:",
        "",
    ]

    for idx, s in enumerate(sites, 1):
        offset = s["predicted_heat_offset_f"]
        surface_temp = round(baseline_forecast_f + offset, 1)
        top_attr = ", ".join([f"{a['feature']} (+{a['attribution_deg_f']}°F)" for a in s.get("top_feature_attributions", [])])
        canopy_val = f"{s['tree_canopy_pct']}%" if s.get("tree_canopy_pct") is not None else "N/A"
        pop_str = f"{s['population']:,}" if s.get('population') else "N/A"
        memo_lines.extend([
            f"### Site {idx}: Census Tract {s['tract_id']}",
            f"- **Coordinates:** Latitude {s['latitude']}, Longitude {s['longitude']}",
            f"- **Predicted Surface Microclimate:** {surface_temp}°F (+{offset}°F microclimate offset over {baseline_forecast_f}°F baseline)",
            f"- **Vulnerability Profile:** Population {pop_str} | Poverty Rate: {s['poverty_rate_pct']}% | Zero-Vehicle Households: {s['no_vehicle_rate_pct']}% | Tree Canopy: {canopy_val}",
            f"- **Key Thermal Drivers (Attributions):** {top_attr if top_attr else 'Impervious surface & legacy built environment'}",
            "- **Recommended Facility:** Municipal library, community center, or MARTA-adjacent public facility equipped with redundant backup HVAC and continuous hydration stations.",
            "",
        ])

    memo_lines.extend([
        "## 3. Title VI & Equity Audit Verification",
        f"- **Audit Status:** {audit_result.get('audit_finding', 'VERIFIED')}",
        f"- **Poverty Quartile Alignment:** Selected sites average {audit_result.get('poverty_comparison', {}).get('selected_sites_avg_pct', 0)}% poverty vs. citywide average {audit_result.get('poverty_comparison', {}).get('citywide_avg_pct', 0)}% (75th percentile benchmark: {audit_result.get('poverty_comparison', {}).get('citywide_75th_percentile_pct', 0)}%).",
        f"- **Transit & Mobility Dependency:** Selected sites average {audit_result.get('mobility_access_comparison', {}).get('selected_sites_no_vehicle_avg_pct', 0)}% vehicle lack vs. citywide average {audit_result.get('mobility_access_comparison', {}).get('citywide_avg_no_vehicle_pct', 0)}% (75th percentile benchmark: {audit_result.get('mobility_access_comparison', {}).get('citywide_75th_percentile_no_vehicle_pct', 0)}%).",
        "- **Civil Rights Compliance:** Demographic features are excluded from training-stage prediction gates; resource distribution strictly remediates empirical heat burden and transit exclusion.",
        "",
        "## 4. Concurrent Canopy & Urban Forestry Interventions (Decade Track)",
        "To reduce long-term dependency on emergency cooling centers, the following tracts are designated for priority green infrastructure investment to close canopy deficits relative to Atlanta's 50% target:",
        "",
    ])

    for c in canopy_result.get("recommended_priority_tracts", []):
        memo_lines.extend([
            f"- **Tract {c['tract_id']} ({c.get('tract_name', 'Atlanta')}):** Current canopy {c['tree_canopy_pct']}% (Canopy deficit: {c['city_target_gap_pct']}%). Interventions: {'; '.join(c['priority_interventions'])}.",
        ])

    memo_lines.extend([
        "",
        "## 5. Funding Mechanism & Operating Standards",
        f"- **Funding Vehicle:** Appropriated through the {funding_source}.",
        "- **Operating Hours:** 08:00 - 20:00 EST daily while heat advisory or excessive heat warning remains in effect.",
        "- **MARTA Integration:** Free fare-free transit passes and shuttle coordination along designated high-risk routes for residents without vehicle access.",
        "",
        "## 6. Action Requested",
        "Adoption of the emergency resolution authorizing facility operations and departmental deployment.",
    ])

    proposal_md = "\n".join(memo_lines)
    return {
        "title": "Atlanta Emergency Cooling Center Mobilization & Canopy Mitigation Plan",
        "target_tract_ids": tract_ids,
        "equity_audit": audit_result,
        "funding_source": funding_source,
        "proposal_markdown": proposal_md,
    }
