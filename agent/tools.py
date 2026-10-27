"""
Custom BigQuery & BQML tools for Atlanta Heat Resilience Planning Assistant.
Synchronized with data-lane cleaning contracts and production model serving.
"""

import os
import re
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
    WITH tract AS (
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
            "median_year_structure_built": int(row.median_year_structure_built)
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
    
    return {
        "site_1": {"name": label1, "details": site1},
        "site_2": {"name": label2, "details": site2},
        "temperature_difference_f": diff_f,
        "comparison_summary": (
            f"{label1} is predicted to be {abs(diff_f)}°F "
            f"{'hotter' if diff_f > 0 else 'cooler'} than {label2}."
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
      geo_id,
      tract_lat,
      tract_lon,
      ROUND(predicted_offset_f, 2) AS offset_f,
      ROUND(total_pop) AS total_pop,
      ROUND(poverty_rate * 100, 1) AS poverty_pct,
      ROUND(no_vehicle_rate * 100, 1) AS no_vehicle_pct,
      ROUND(median_age, 1) AS median_age,
      ROUND(
        (predicted_offset_f * 0.4) + 
        (poverty_rate * 10.0 * 0.3) + 
        (no_vehicle_rate * 10.0 * 0.3),
        2
      ) AS composite_vulnerability_score,
      top_feature_attributions
    FROM predictions
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
          geo_id,
          tract_lat,
          tract_lon,
          total_pop,
          CASE WHEN median_age BETWEEN 0 AND 120 THEN median_age ELSE 36.0 END AS median_age,
          CASE WHEN median_income >= 0 THEN median_income ELSE 65000.0 END AS median_income,
          CASE WHEN housing_units >= 0 THEN housing_units ELSE 1500.0 END AS housing_units,
          CASE
            WHEN median_year_structure_built > 1800 AND median_year_structure_built <= 2030
            THEN median_year_structure_built
            ELSE 1975.0
          END AS median_year_structure_built,
          no_cars,
          households,
          ROUND(CASE WHEN poverty_rate BETWEEN 0 AND 1 THEN poverty_rate ELSE 0.15 END * 100, 1) AS poverty_pct,
          ROUND(CASE WHEN no_vehicle_rate BETWEEN 0 AND 1 THEN no_vehicle_rate ELSE 0.10 END * 100, 1) AS no_vehicle_pct
        FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics`
        WHERE geo_id = @tract_id
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
          geo_id,
          tract_lat,
          tract_lon,
          total_pop,
          CASE WHEN median_age BETWEEN 0 AND 120 THEN median_age ELSE 36.0 END AS median_age,
          CASE WHEN median_income >= 0 THEN median_income ELSE 65000.0 END AS median_income,
          CASE WHEN housing_units >= 0 THEN housing_units ELSE 1500.0 END AS housing_units,
          CASE
            WHEN median_year_structure_built > 1800 AND median_year_structure_built <= 2030
            THEN median_year_structure_built
            ELSE 1975.0
          END AS median_year_structure_built,
          no_cars,
          households,
          ROUND(CASE WHEN poverty_rate BETWEEN 0 AND 1 THEN poverty_rate ELSE 0.15 END * 100, 1) AS poverty_pct,
          ROUND(CASE WHEN no_vehicle_rate BETWEEN 0 AND 1 THEN no_vehicle_rate ELSE 0.10 END * 100, 1) AS no_vehicle_pct
        FROM `{PROJECT_ID}.{DATASET_ID}.tract_demographics`
        ORDER BY ST_DISTANCE(ST_GEOGPOINT(@lon, @lat), ST_GEOGPOINT(tract_lon, tract_lat)), geo_id
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
        "no_vehicle_rate_pct": r.no_vehicle_pct
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
