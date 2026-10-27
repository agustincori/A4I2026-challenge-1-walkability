"""Custom ADK Function Tools for the Urban Heat Resilience Planning Agent.

Implements four purpose-built BigQuery & BigQuery ML tools:
1. `predict_and_explain_location`: Runs `ML.EXPLAIN_PREDICT` for any (lat, lon) inside the
   city campaign bounding box, returning predicted heat offset (°F above city mean) and
   human-readable feature attributions. Refuses out-of-bounds coordinates explicitly.
2. `rank_cooling_sites`: Crosses `ML.EXPLAIN_PREDICT` predictions and attributions with
   `tract_demographics` to produce ranked Placement Recommendations tailored to the active
   decision track (`today`, `budget_cycle`, or `decade`).
3. `audit_recommendations_equity`: Audits recommended Census tract IDs against the citywide
   baseline in `tract_demographics` (`poverty_rate`, `no_vehicle_rate`, `median_age`,
   `median_income`) to answer whether interventions reach the most vulnerable residents.
4. `get_station_heat_frequency`: Analyzes 7 years of NOAA GHCN-Daily station history in
   `station_daily_temps` to quantify how often the city exceeds a dangerous heat threshold
   and whether extreme heat frequency is trending upward.
"""

from __future__ import annotations

import logging
import math
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

try:
    import google.auth
    from google.api_core.exceptions import GoogleAPICallError, NotFound
    from google.cloud import bigquery
except ImportError:  # pragma: no cover - lightweight shims for offline local testing
    google = None  # type: ignore[assignment]

    class GoogleAPICallError(Exception):  # type: ignore[no-redef]
        """Fallback exception when google-api-core is not installed locally."""

    class NotFound(GoogleAPICallError):  # type: ignore[no-redef]
        """Fallback NotFound exception when google-api-core is not installed locally."""

    class _BigQueryShim:
        """Minimal shim for QueryJobConfig and QueryParameters in offline test environments."""

        class ScalarQueryParameter:
            def __init__(self, name: str, type_: str, value: Any):
                self.name = name
                self.type_ = type_
                self.value = value

        class ArrayQueryParameter:
            def __init__(self, name: str, array_type: str, values: list[Any]):
                self.name = name
                self.array_type = array_type
                self.values = values

        class QueryJobConfig:
            def __init__(self, query_parameters: list[Any] | None = None, **kwargs: Any):
                self.query_parameters = query_parameters or []
                self.extra = kwargs

        Client = Any

    bigquery = _BigQueryShim()  # type: ignore[assignment]

if TYPE_CHECKING:
    from google.cloud.bigquery import Client as BigQueryClient
else:
    BigQueryClient = Any

from .config import (
    FEATURE_EXPLANATION_LABELS,
    FEATURE_INTERVENTION_GUIDANCE,
    AgentConfig,
    get_config,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CityCampaignMetadata:
    """Cached spatial and thermal baseline metadata for the loaded city campaign."""

    city: str
    total_observations: int
    city_avg_temp_f: float
    city_min_temp_f: float
    city_max_temp_f: float
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    @property
    def center_lat(self) -> float:
        return (self.min_lat + self.max_lat) / 2.0

    @property
    def center_lon(self) -> float:
        return (self.min_lon + self.max_lon) / 2.0

    @property
    def spread_f(self) -> float:
        return self.city_max_temp_f - self.city_min_temp_f


class HeatResilienceRuntime:
    """Thread-safe runtime managing BigQuery, city bounds, and the planning model."""

    def __init__(self, config: AgentConfig | None = None, client: bigquery.Client | None = None):
        self.config = config or get_config()
        self._client = client
        self._project_id: str | None = self.config.project_id
        self._city_meta: CityCampaignMetadata | None = None
        self._resolved_model_fqn: str | None = None
        self._lock = threading.RLock()

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    if not self._project_id:
                        _, default_project = google.auth.default()
                        self._project_id = default_project
                    self._client = bigquery.Client(
                        project=self._project_id,
                        location=self.config.location,
                    )
                    if not self._project_id:
                        self._project_id = self._client.project
        return self._client

    @property
    def project_id(self) -> str:
        if not self._project_id:
            _ = self.client
        if not self._project_id:
            raise RuntimeError(
                "Could not determine Google Cloud project ID. "
                "Set GOOGLE_CLOUD_PROJECT or authenticate via `gcloud auth application-default login`."
            )
        return self._project_id

    @property
    def dataset_fqn(self) -> str:
        return f"{self.project_id}.{self.config.dataset_id}"

    def reset_cache(self) -> None:
        """Clear cached metadata (useful for tests or after reloading a new city)."""
        with self._lock:
            self._city_meta = None
            self._resolved_model_fqn = None

    def query_rows(
        self, sql: str, job_config: bigquery.QueryJobConfig | None = None
    ) -> list[Any]:
        """Execute with shared cost/deadline limits and no application-level retries."""
        job_config = job_config or bigquery.QueryJobConfig()
        job_config.maximum_bytes_billed = self.config.maximum_bytes_billed
        job_config.job_timeout_ms = self.config.query_timeout_seconds * 1000
        job = None
        try:
            job = self.client.query(
                sql, job_config=job_config, timeout=self.config.query_timeout_seconds
            )
            rows = list(job.result(timeout=self.config.query_timeout_seconds))
            logger.info(
                "BigQuery query completed job_id=%s bytes_billed=%s rows=%s",
                job.job_id, job.total_bytes_billed, len(rows),
            )
            return rows
        except TimeoutError:
            logger.exception("BigQuery query exceeded its deadline")
            if job is not None:
                try:
                    job.cancel()
                except GoogleAPICallError:
                    logger.exception("Failed to cancel timed-out BigQuery job")
            raise
        except GoogleAPICallError:
            logger.exception("BigQuery query failed")
            raise

    def get_city_metadata(self) -> CityCampaignMetadata:
        """Fetch and cache the bounding box and baseline temperature for the loaded city."""
        if self._city_meta is not None:
            return self._city_meta

        with self._lock:
            if self._city_meta is not None:
                return self._city_meta

            sql = f"""
            SELECT
              ANY_VALUE(city) AS city,
              COUNT(*) AS total_observations,
              AVG(temp_f) AS city_avg_temp_f,
              MIN(temp_f) AS city_min_temp_f,
              MAX(temp_f) AS city_max_temp_f,
              MIN(latitude) AS min_lat,
              MAX(latitude) AS max_lat,
              MIN(longitude) AS min_lon,
              MAX(longitude) AS max_lon
            FROM `{self.dataset_fqn}.heat_observations`
            WHERE temp_f IS NOT NULL
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
            """
            rows = self.query_rows(sql)
            if not rows or not rows[0]["total_observations"]:
                raise RuntimeError(
                    f"Table `{self.dataset_fqn}.heat_observations` is empty or missing. "
                    "Run `bash scripts/load.sh <city>` or the load notebook first."
                )
            row = rows[0]
            self._city_meta = CityCampaignMetadata(
                city=str(row["city"] or "Unknown City"),
                total_observations=int(row["total_observations"]),
                city_avg_temp_f=float(row["city_avg_temp_f"]),
                city_min_temp_f=float(row["city_min_temp_f"]),
                city_max_temp_f=float(row["city_max_temp_f"]),
                min_lat=float(row["min_lat"]),
                max_lat=float(row["max_lat"]),
                min_lon=float(row["min_lon"]),
                max_lon=float(row["max_lon"]),
            )
            return self._city_meta

    def resolve_or_bootstrap_model(self) -> str:
        """Resolve the configured planning model, bootstrapping it if enabled."""
        if self._resolved_model_fqn is not None:
            return self._resolved_model_fqn

        with self._lock:
            if self._resolved_model_fqn is not None:
                return self._resolved_model_fqn

            if self.config.planning_bqml_model_name == self.config.bqml_model_name:
                raise ValueError(
                    "PLANNING_BQML_MODEL must differ from BQML_MODEL: "
                    "the planning and Atlanta tools require different model schemas."
                )
            preferred_fqn = f"{self.dataset_fqn}.{self.config.planning_bqml_model_name}"
            try:
                self.client.get_model(preferred_fqn)
                self._resolved_model_fqn = preferred_fqn
                return preferred_fqn
            except NotFound:
                logger.info("Planning BQML model %s not found.", preferred_fqn)

            if not self.config.auto_bootstrap_bqml:
                raise RuntimeError(
                    f"No BigQuery ML model found in `{self.dataset_fqn}`. "
                    f"Expected `{preferred_fqn}`. Ask the Data Lane to train the model or "
                    "enable AUTO_BOOTSTRAP_BQML=true."
                )

            # Auto-bootstrap a baseline LINEAR_REG offset model so Agent & Frontend lanes
            # are never blocked waiting on the Data Lane.
            logger.info("Bootstrapping baseline BQML model `%s`...", preferred_fqn)
            train_sql = build_bqml_training_sql(
                self.dataset_fqn, self.config.planning_bqml_model_name
            )
            self.query_rows(train_sql)
            self._resolved_model_fqn = preferred_fqn
            return preferred_fqn


# Default module-level runtime singleton
_RUNTIME = HeatResilienceRuntime()


def get_runtime() -> HeatResilienceRuntime:
    """Return the active HeatResilienceRuntime singleton."""
    return _RUNTIME


def set_runtime(runtime: HeatResilienceRuntime) -> None:
    """Override the module-level runtime (used in unit and integration tests)."""
    global _RUNTIME
    _RUNTIME = runtime


def build_bqml_training_sql(dataset_fqn: str, model_name: str = "heat_planning_model") -> str:
    """Return the SQL statement to train the baseline BigQuery ML heat offset model.

    Predicts `heat_offset_f` (degrees Fahrenheit above the city's campaign average),
    joining street-level NOAA Heat Watch traverses to their nearest Census tract
    in `tract_demographics`. Race is intentionally excluded from model inputs.
    """
    return f"""
    CREATE MODEL IF NOT EXISTS `{dataset_fqn}.{model_name}`
    OPTIONS(
      model_type = 'LINEAR_REG',
      input_label_cols = ['heat_offset_f'],
      optimize_strategy = 'NORMAL_EQUATION'
    ) AS
    WITH city_stats AS (
      SELECT
        AVG(temp_f) AS avg_temp_f,
        AVG(latitude) AS center_lat,
        AVG(longitude) AS center_lon
      FROM `{dataset_fqn}.heat_observations`
      WHERE temp_f IS NOT NULL
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
    ),
    grid_observations AS (
      -- Aggregate ~100m spatial cells to reduce GPS traverse oversampling at stop lights
      SELECT
        ROUND(latitude, 3) AS latitude,
        ROUND(longitude, 3) AS longitude,
        AVG(temp_f) AS local_temp_f,
        AVG(humidity_pct) AS humidity_pct
      FROM `{dataset_fqn}.heat_observations`
      WHERE temp_f IS NOT NULL
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
      GROUP BY 1, 2
    ),
    matched_tracts AS (
      SELECT
        g.latitude,
        g.longitude,
        g.local_temp_f - c.avg_temp_f AS heat_offset_f,
        ST_DISTANCE(
          ST_GEOGPOINT(g.longitude, g.latitude),
          ST_GEOGPOINT(c.center_lon, c.center_lat)
        ) / 1000.0 AS dist_from_center_km,
        ARRAY_AGG(
          STRUCT(
            t.total_pop AS total_pop,
            NULLIF(t.median_age, -666666666.0) AS median_age,
            NULLIF(t.median_income, -666666666.0) AS median_income,
            t.housing_units AS housing_units,
            NULLIF(t.median_year_structure_built, -666666666.0) AS median_year_structure_built,
            t.no_cars AS no_cars,
            t.households AS households,
            t.poverty_rate AS poverty_rate,
            t.no_vehicle_rate AS no_vehicle_rate
          )
          ORDER BY ST_DISTANCE(
            ST_GEOGPOINT(g.longitude, g.latitude),
            ST_GEOGPOINT(t.tract_lon, t.tract_lat)
          ) ASC
          LIMIT 1
        )[OFFSET(0)] AS nearest_tract
      FROM grid_observations AS g
      CROSS JOIN city_stats AS c
      CROSS JOIN `{dataset_fqn}.tract_demographics` AS t
      WHERE t.tract_lat IS NOT NULL AND t.tract_lon IS NOT NULL
      GROUP BY g.latitude, g.longitude, g.local_temp_f, c.avg_temp_f, c.center_lon, c.center_lat
    )
    SELECT
      heat_offset_f,
      latitude,
      longitude,
      dist_from_center_km,
      COALESCE(nearest_tract.total_pop, 3500.0) AS total_pop,
      COALESCE(nearest_tract.median_age, 36.0) AS median_age,
      COALESCE(nearest_tract.median_income, 55000.0) AS median_income,
      COALESCE(nearest_tract.housing_units, 1500.0) AS housing_units,
      COALESCE(nearest_tract.median_year_structure_built, 1978.0) AS median_year_structure_built,
      GREATEST(0.0, 2026.0 - COALESCE(nearest_tract.median_year_structure_built, 1978.0)) AS structure_age_years,
      SAFE_DIVIDE(
        COALESCE(nearest_tract.housing_units, 1500.0),
        GREATEST(COALESCE(nearest_tract.total_pop, 3500.0), 100.0)
      ) AS housing_density_proxy,
      COALESCE(nearest_tract.no_cars, 120.0) AS no_cars,
      COALESCE(nearest_tract.households, 1300.0) AS households,
      COALESCE(nearest_tract.poverty_rate, 0.15) AS poverty_rate,
      COALESCE(nearest_tract.no_vehicle_rate, 0.08) AS no_vehicle_rate
    FROM matched_tracts
    """


def format_feature_attributions(
    raw_attributions: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], str]:
    """Convert raw BigQuery `top_feature_attributions` into structured items and clean prose.

    Args:
        raw_attributions: List of dicts with `'feature'` and `'attribution'` keys
            returned by `ML.EXPLAIN_PREDICT`.

    Returns:
        A tuple of `(structured_list, formatted_summary_sentence)`.
    """
    if not raw_attributions:
        return [], "No individual feature attributions returned by model."

    cleaned: list[dict[str, Any]] = []
    for item in raw_attributions:
        if not isinstance(item, dict):
            # Support Row / namedtuple objects if returned by BigQuery client
            feature = str(getattr(item, "feature", None) or item.get("feature", "unknown"))
            attribution = float(getattr(item, "attribution", 0.0) or item.get("attribution", 0.0))
        else:
            feature = str(item.get("feature", "unknown"))
            attribution = float(item.get("attribution") or 0.0)

        human_label = FEATURE_EXPLANATION_LABELS.get(
            feature, f"{feature.replace('_', ' ')} ({feature})"
        )
        sign = "+" if attribution >= 0 else "\u2212"
        abs_val = abs(attribution)
        direction = "warming_driver" if attribution >= 0 else "cooling_mitigator"
        formatted_item = f"{sign}{abs_val:.2f}\u00b0F from {human_label}"

        cleaned.append(
            {
                "feature": feature,
                "human_label": human_label,
                "attribution_f": round(attribution, 2),
                "direction": direction,
                "formatted": formatted_item,
            }
        )

    cleaned.sort(key=lambda x: abs(x["attribution_f"]), reverse=True)
    summary_parts = [item["formatted"] for item in cleaned if abs(item["attribution_f"]) >= 0.01]
    if not summary_parts:
        summary_parts = [item["formatted"] for item in cleaned[:3]]

    narrative = "; ".join(summary_parts)
    return cleaned, narrative


def _extract_predicted_offset(row_dict: dict[str, Any]) -> float:
    """Extract the predicted offset column from an `ML.EXPLAIN_PREDICT` row regardless of label name."""
    for candidate in (
        "predicted_heat_offset_f",
        "predicted_degrees_above_city_average",
        "predicted_offset_f",
        "predicted_offset",
        "predicted_temp_offset_f",
    ):
        if candidate in row_dict and row_dict[candidate] is not None:
            return float(row_dict[candidate])

    for key, val in row_dict.items():
        if key.startswith("predicted_") and val is not None:
            return float(val)

    raise KeyError(
        f"Could not find `predicted_*` column in ML.EXPLAIN_PREDICT output. Columns: {list(row_dict.keys())}"
    )


def _select_intervention(
    mode: str,
    attributions: list[dict[str, Any]],
    no_vehicle_rate: float,
    poverty_rate: float,
) -> str:
    """Choose a specific, defensible intervention based on track mode and dominant warming driver."""
    mode_map = FEATURE_INTERVENTION_GUIDANCE.get(mode, FEATURE_INTERVENTION_GUIDANCE["budget_cycle"])

    # Pick the strongest positive (warming) attribution first
    warming_drivers = [a for a in attributions if a["attribution_f"] > 0]
    dominant_feature = (
        warming_drivers[0]["feature"]
        if warming_drivers
        else (attributions[0]["feature"] if attributions else "default")
    )

    if dominant_feature in mode_map:
        base_recommendation = mode_map[dominant_feature]
    elif no_vehicle_rate >= 0.15 and "no_vehicle_rate" in mode_map:
        base_recommendation = mode_map["no_vehicle_rate"]
    else:
        base_recommendation = mode_map["default"]

    return base_recommendation


# ==============================================================================
# ADK Function Tool 1: predict_and_explain_location (REQUIRED)
# ==============================================================================


def predict_and_explain_location(latitude: float, longitude: float) -> dict[str, Any]:
    """Predict the urban heat offset (°F above city average) and feature attributions for a specific coordinate.

    Executes BigQuery ML's `ML.EXPLAIN_PREDICT` at the requested `(latitude, longitude)` by
    interpolating built-environment and demographic features from the nearest Census tracts
    in `tract_demographics`. Also checks `heat_observations` to report whether volunteers
    directly measured streets near this point or if it is an unmeasured location.

    IMPORTANT FOR THE AGENT:
    - First verifies whether `(latitude, longitude)` falls inside the loaded city's campaign
      bounding box in `heat_observations`. If out of bounds, returns `{"status": "OUT_OF_BOUNDS", ...}`.
      When `status == "OUT_OF_BOUNDS"`, you MUST refuse to predict and state which city and
      bounding box are loaded.
    - The model predicts a **heat offset** (`predicted_heat_offset_f`, i.e., degrees Fahrenheit
      hotter or cooler than the citywide average on a hot afternoon), NOT an absolute daily
      weather forecast temperature.

    Args:
        latitude: Decimal latitude in WGS84 (e.g., 32.7485 for Oak Cliff in Dallas).
        longitude: Decimal longitude in WGS84 (e.g., -96.8183 for Oak Cliff in Dallas).

    Returns:
        A dictionary containing:
        - `status`: `"OK"`, `"OUT_OF_BOUNDS"`, or `"ERROR"`.
        - `city`: Name of the city loaded in BigQuery.
        - `coordinates`: Requested `{"latitude": float, "longitude": float}`.
        - `predicted_heat_offset_f`: Predicted temperature offset (°F relative to city average).
        - `formatted_offset`: Signed string representation (e.g., `"+6.4°F above city average"`).
        - `city_campaign_avg_temp_f`: Citywide mean temperature during the Heat Watch campaign.
        - `explanation_summary`: Clean human-readable summary of `ML.EXPLAIN_PREDICT` attributions.
        - `top_feature_attributions`: List of per-feature attribution objects.
        - `nearest_tract_context`: Census tract ID (`geo_id`) and demographics of the surrounding area.
        - `nearby_observed_readings`: Summary of any empirical street traverse points within 500m.
    """
    if (
        type(latitude) not in (int, float)
        or type(longitude) not in (int, float)
        or math.isnan(latitude)
        or math.isnan(longitude)
        or not (-90.0 <= float(latitude) <= 90.0)
        or not (-180.0 <= float(longitude) <= 180.0)
    ):
        logger.warning("predict_and_explain_location rejected invalid coordinates")
        return {
            "status": "INVALID_INPUT",
            "error_code": "INVALID_COORDINATES",
            "message": (
                f"Coordinates latitude={latitude}, longitude={longitude} are not valid "
                "WGS84 decimal degrees (latitude must be in [-90, 90], longitude in [-180, 180])."
            ),
        }

    lat = float(latitude)
    lon = float(longitude)
    runtime = get_runtime()

    try:
        city_meta = runtime.get_city_metadata()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load city campaign metadata")
        return {
            "status": "ERROR",
            "error_code": "METADATA_UNAVAILABLE",
            "message": str(exc),
        }

    pad = runtime.config.bbox_pad_degrees
    in_lat_bounds = (city_meta.min_lat - pad) <= lat <= (city_meta.max_lat + pad)
    in_lon_bounds = (city_meta.min_lon - pad) <= lon <= (city_meta.max_lon + pad)

    if not (in_lat_bounds and in_lon_bounds):
        return {
            "status": "OUT_OF_BOUNDS",
            "error_code": "LOCATION_OUTSIDE_CAMPAIGN_BOUNDS",
            "loaded_city": city_meta.city,
            "requested_coordinates": {"latitude": round(lat, 5), "longitude": round(lon, 5)},
            "valid_bounding_box": {
                "min_latitude": round(city_meta.min_lat, 4),
                "max_latitude": round(city_meta.max_lat, 4),
                "min_longitude": round(city_meta.min_lon, 4),
                "max_longitude": round(city_meta.max_lon, 4),
                "padding_degrees": pad,
            },
            "refusal_instruction": (
                f"REFUSE PREDICTION: Coordinates ({lat:.4f}, {lon:.4f}) lie outside the loaded "
                f"NOAA Heat Watch campaign footprint for {city_meta.city} "
                f"(lat {city_meta.min_lat:.3f}..{city_meta.max_lat:.3f}, "
                f"lon {city_meta.min_lon:.3f}..{city_meta.max_lon:.3f}). "
                f"State clearly that you only have verified model coverage for {city_meta.city} "
                "and cannot fabricate predictions for out-of-bounds locations or unloaded cities."
            ),
        }

    try:
        model_fqn = runtime.resolve_or_bootstrap_model()
        top_k = runtime.config.explain_top_k

        sql = f"""
        WITH target_point AS (
          SELECT
            @lat AS latitude,
            @lon AS longitude,
            ST_GEOGPOINT(@lon, @lat) AS pt,
            ST_DISTANCE(
              ST_GEOGPOINT(@lon, @lat),
              ST_GEOGPOINT(@center_lon, @center_lat)
            ) / 1000.0 AS dist_from_center_km
        ),
        nearest_tracts AS (
          SELECT
            LPAD(t.geo_id, 11, '0') AS geo_id,
            t.tract_lat,
            t.tract_lon,
            t.total_pop,
            NULLIF(t.median_age, -666666666.0) AS median_age,
            NULLIF(t.median_income, -666666666.0) AS median_income,
            t.housing_units,
            NULLIF(t.median_year_structure_built, -666666666.0) AS median_year_structure_built,
            t.no_cars,
            t.households,
            t.poverty_rate,
            t.no_vehicle_rate,
            ST_DISTANCE(
              (SELECT pt FROM target_point),
              ST_GEOGPOINT(t.tract_lon, t.tract_lat)
            ) AS dist_m,
            1.0 / POW(
              GREATEST(
                ST_DISTANCE(
                  (SELECT pt FROM target_point),
                  ST_GEOGPOINT(t.tract_lon, t.tract_lat)
                ),
                50.0
              ),
              2
            ) AS idw_weight
          FROM `{runtime.dataset_fqn}.tract_demographics` AS t
          WHERE t.tract_lat IS NOT NULL AND t.tract_lon IS NOT NULL
          ORDER BY dist_m ASC
          LIMIT 3
        ),
        primary_tract AS (
          SELECT * FROM nearest_tracts ORDER BY dist_m ASC LIMIT 1
        ),
        interpolated_features AS (
          SELECT
            (SELECT latitude FROM target_point) AS latitude,
            (SELECT longitude FROM target_point) AS longitude,
            (SELECT dist_from_center_km FROM target_point) AS dist_from_center_km,
            (SELECT geo_id FROM primary_tract) AS primary_geo_id,
            (SELECT dist_m FROM primary_tract) AS primary_tract_dist_m,
            (SELECT tract_lat FROM primary_tract) AS tract_lat,
            (SELECT tract_lon FROM primary_tract) AS tract_lon,
            COALESCE(SUM(total_pop * idw_weight) / NULLIF(SUM(idw_weight), 0), 3500.0) AS total_pop,
            COALESCE(SUM(median_age * idw_weight) / NULLIF(SUM(idw_weight), 0), 36.0) AS median_age,
            COALESCE(SUM(median_income * idw_weight) / NULLIF(SUM(idw_weight), 0), 55000.0) AS median_income,
            COALESCE(SUM(housing_units * idw_weight) / NULLIF(SUM(idw_weight), 0), 1500.0) AS housing_units,
            COALESCE(
              SUM(median_year_structure_built * idw_weight) / NULLIF(SUM(idw_weight), 0),
              1978.0
            ) AS median_year_structure_built,
            GREATEST(
              0.0,
              2026.0 - COALESCE(
                SUM(median_year_structure_built * idw_weight) / NULLIF(SUM(idw_weight), 0),
                1978.0
              )
            ) AS structure_age_years,
            SAFE_DIVIDE(
              COALESCE(SUM(housing_units * idw_weight) / NULLIF(SUM(idw_weight), 0), 1500.0),
              GREATEST(COALESCE(SUM(total_pop * idw_weight) / NULLIF(SUM(idw_weight), 0), 3500.0), 100.0)
            ) AS housing_density_proxy,
            COALESCE(SUM(no_cars * idw_weight) / NULLIF(SUM(idw_weight), 0), 120.0) AS no_cars,
            COALESCE(SUM(households * idw_weight) / NULLIF(SUM(idw_weight), 0), 1300.0) AS households,
            COALESCE(SUM(poverty_rate * idw_weight) / NULLIF(SUM(idw_weight), 0), 0.15) AS poverty_rate,
            COALESCE(SUM(no_vehicle_rate * idw_weight) / NULLIF(SUM(idw_weight), 0), 0.08) AS no_vehicle_rate,
            50.0 AS humidity_pct
          FROM nearest_tracts
        ),
        nearby_observations AS (
          SELECT
            COUNTIF(dist_m <= 500.0) AS readings_within_500m,
            MIN(dist_m) AS nearest_reading_dist_m,
            AVG(IF(dist_m <= 500.0, temp_f, NULL)) AS avg_temp_within_500m_f
          FROM (
            SELECT
              temp_f,
              ST_DISTANCE(
                ST_GEOGPOINT(@lon, @lat),
                ST_GEOGPOINT(longitude, latitude)
              ) AS dist_m
            FROM `{runtime.dataset_fqn}.heat_observations`
            WHERE temp_f IS NOT NULL
          )
        )
        SELECT
          pred.*,
          obs.readings_within_500m,
          obs.nearest_reading_dist_m,
          obs.avg_temp_within_500m_f
        FROM ML.EXPLAIN_PREDICT(
          MODEL `{model_fqn}`,
          (SELECT * FROM interpolated_features),
          STRUCT({int(top_k)} AS top_k_features)
        ) AS pred
        CROSS JOIN nearby_observations AS obs
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("lat", "FLOAT64", lat),
                bigquery.ScalarQueryParameter("lon", "FLOAT64", lon),
                bigquery.ScalarQueryParameter("center_lat", "FLOAT64", city_meta.center_lat),
                bigquery.ScalarQueryParameter("center_lon", "FLOAT64", city_meta.center_lon),
            ]
        )

        rows = runtime.query_rows(sql, job_config)
        if not rows:
            return {
                "status": "NO_PREDICTION",
                "error_code": "EMPTY_MODEL_RESULT",
                "loaded_city": city_meta.city,
                "requested_coordinates": {"latitude": lat, "longitude": lon},
                "message": "The BigQuery ML model returned no prediction rows for this coordinate.",
            }

        row_dict = dict(rows[0].items())
        predicted_offset = _extract_predicted_offset(row_dict)
        raw_attributions = row_dict.get("top_feature_attributions") or []
        structured_attrs, narrative_summary = format_feature_attributions(raw_attributions)

        sign = "+" if predicted_offset >= 0 else "\u2212"
        formatted_offset = f"{sign}{abs(predicted_offset):.2f}\u00b0F vs. {city_meta.city} campaign average"

        readings_500m = int(row_dict.get("readings_within_500m") or 0)
        nearest_obs_m = (
            round(float(row_dict["nearest_reading_dist_m"]), 1)
            if row_dict.get("nearest_reading_dist_m") is not None
            else None
        )
        avg_obs_500m = row_dict.get("avg_temp_within_500m_f")
        observed_offset_500m = (
            round(float(avg_obs_500m) - city_meta.city_avg_temp_f, 2)
            if avg_obs_500m is not None
            else None
        )

        return {
            "status": "OK",
            "city": city_meta.city,
            "model_used": model_fqn,
            "coordinates": {"latitude": round(lat, 5), "longitude": round(lon, 5)},
            "predicted_heat_offset_f": round(predicted_offset, 2),
            "formatted_offset": formatted_offset,
            "baseline_value_f": (
                round(float(row_dict["baseline_value"]), 2)
                if row_dict.get("baseline_value") is not None
                else 0.0
            ),
            "city_campaign_avg_temp_f": round(city_meta.city_avg_temp_f, 1),
            "estimated_temp_on_campaign_day_f": round(
                city_meta.city_avg_temp_f + predicted_offset, 1
            ),
            "explanation_summary": narrative_summary,
            "top_feature_attributions": structured_attrs,
            "nearest_tract_context": {
                "tract_geo_id": str(row_dict.get("primary_geo_id") or ""),
                "distance_to_tract_centroid_m": round(
                    float(row_dict.get("primary_tract_dist_m") or 0.0), 1
                ),
                "total_population": int(round(float(row_dict.get("total_pop") or 0.0))),
                "median_age": round(float(row_dict.get("median_age") or 0.0), 1),
                "median_income_usd": int(round(float(row_dict.get("median_income") or 0.0))),
                "poverty_rate_pct": round(float(row_dict.get("poverty_rate") or 0.0) * 100.0, 1),
                "no_vehicle_rate_pct": round(
                    float(row_dict.get("no_vehicle_rate") or 0.0) * 100.0, 1
                ),
                "median_year_structure_built": int(
                    round(float(row_dict.get("median_year_structure_built") or 1978.0))
                ),
            },
            "nearby_observed_readings": {
                "was_directly_measured_within_500m": readings_500m > 0,
                "traverse_points_within_500m": readings_500m,
                "nearest_volunteer_reading_distance_m": nearest_obs_m,
                "empirical_offset_within_500m_f": observed_offset_500m,
                "note": (
                    "This location was not directly traversed within 500m; heat offset is "
                    "predicted entirely by the BigQuery ML model."
                    if readings_500m == 0
                    else f"BigQuery ML prediction supplemented by {readings_500m} nearby empirical traverse points within 500m."
                ),
            },
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error in predict_and_explain_location(%s, %s)", lat, lon)
        return {
            "status": "ERROR",
            "error_code": "BQML_PREDICTION_FAILED",
            "loaded_city": city_meta.city,
            "requested_coordinates": {"latitude": lat, "longitude": lon},
            "message": f"BigQuery ML prediction query failed: {exc}",
        }


# ==============================================================================
# ADK Function Tool 2: rank_cooling_sites
# ==============================================================================


def rank_cooling_sites(top_n: int = 5, mode: str = "budget_cycle") -> dict[str, Any]:
    """Rank the highest-priority intervention locations by crossing `ML.EXPLAIN_PREDICT` with Census demographics.

    Runs `ML.EXPLAIN_PREDICT` across candidate Census tracts inside the city's Heat Watch
    campaign footprint and combines the predicted microclimate heat offset (`predicted_heat_offset_f`)
    with tract-level vulnerability indicators from `tract_demographics` (`no_vehicle_rate`,
    `poverty_rate`, `median_age`, `total_pop`) to build the **Placement Recommendation** artifact.

    Supports three decision tracks via `mode`:
    - `"today"` (Emergency Management / Tomorrow's Heat Wave): Prioritizes extreme heat offset +
      car-free households (`no_vehicle_rate`) + older residents (`median_age`) for mobile hydration
      trucks, transit shuttles, and wellness checks.
    - `"budget_cycle"` (City Planning / Council Budget Proposal): Prioritizes extreme heat offset +
      `poverty_rate` + `no_vehicle_rate` + `total_pop` for siting permanent cooling centers.
    - `"decade"` (Sustainability / Urban Forestry & Cool Pavement): Prioritizes extreme heat offset +
      built-environment structure density/age + `poverty_rate` for tree canopy and cool pavement
      investments, using `ML.EXPLAIN_PREDICT` attributions to recommend the specific physical fix.

    Args:
        top_n: Number of top candidate sites to return (between 1 and 20; defaults to 5).
        mode: Planning track — one of `"today"`, `"budget_cycle"`, or `"decade"`.

    Returns:
        A dictionary containing:
        - `status`: `"OK"` or `"ERROR"`.
        - `city`: Loaded city name.
        - `mode`: Normalized decision track (`"today"`, `"budget_cycle"`, or `"decade"`).
        - `recommended_tract_ids`: List of 11-digit Census tract `geo_id` strings (pass directly
          to `audit_recommendations_equity(tract_ids=...)` to audit equity).
        - `sites`: Ranked list of candidate sites with coordinates, `predicted_heat_offset_f`,
          formatted `ML.EXPLAIN_PREDICT` attributions, demographics, and recommended intervention.
    """
    if type(top_n) is not int or not 1 <= top_n <= 20:
        logger.warning("rank_cooling_sites rejected invalid top_n")
        return {
            "status": "INVALID_INPUT",
            "error_code": "INVALID_LIMIT",
            "message": "top_n must be an integer between 1 and 20.",
        }
    if not isinstance(mode, str):
        logger.warning("rank_cooling_sites rejected invalid mode")
        return {
            "status": "INVALID_INPUT",
            "error_code": "INVALID_MODE",
            "message": "mode must be today, budget_cycle, or decade.",
        }
    raw_mode = mode.strip().lower()
    if raw_mode in {"today", "emergency", "dispatch", "hydration", "tomorrow"}:
        normalized_mode = "today"
    elif raw_mode in {"decade", "forestry", "trees", "canopy", "sustainability", "pavement"}:
        normalized_mode = "decade"
    elif raw_mode == "budget_cycle":
        normalized_mode = "budget_cycle"
    else:
        logger.warning("rank_cooling_sites rejected unsupported mode")
        return {
            "status": "INVALID_INPUT",
            "error_code": "INVALID_MODE",
            "message": "mode must be today, budget_cycle, or decade (documented aliases are accepted).",
        }

    runtime = get_runtime()

    try:
        city_meta = runtime.get_city_metadata()
        model_fqn = runtime.resolve_or_bootstrap_model()
        top_k = runtime.config.explain_top_k
        pad = runtime.config.bbox_pad_degrees

        # Track-specific weighting expression in SQL (normalized 0..100 priority score)
        if normalized_mode == "today":
            score_expr = (
                "0.45 * norm_offset + 0.30 * norm_no_vehicle "
                "+ 0.15 * norm_median_age + 0.10 * norm_pop"
            )
            track_description = (
                "Emergency Response (Today Track): Weights predicted heat offset (45%), "
                "car-free households (30%), median age (15%), and population (10%)."
            )
        elif normalized_mode == "decade":
            score_expr = (
                "0.50 * norm_offset + 0.25 * norm_structure_age + 0.25 * norm_poverty"
            )
            track_description = (
                "Long-Term Urban Forestry & Cool Surfaces (Decade Track): Weights predicted "
                "heat offset (50%), built-structure age/density (25%), and poverty rate (25%)."
            )
        else:
            score_expr = (
                "0.40 * norm_offset + 0.25 * norm_poverty "
                "+ 0.20 * norm_no_vehicle + 0.15 * norm_pop"
            )
            track_description = (
                "Capital Siting for Permanent Cooling Centers (Budget Cycle Track): Weights "
                "predicted heat offset (40%), poverty rate (25%), car-free rate (20%), and population (15%)."
            )

        sql = f"""
        WITH candidate_tracts AS (
          SELECT
            LPAD(t.geo_id, 11, '0') AS geo_id,
            t.tract_lat AS latitude,
            t.tract_lon AS longitude,
            t.tract_lat,
            t.tract_lon,
            ST_DISTANCE(
              ST_GEOGPOINT(t.tract_lon, t.tract_lat),
              ST_GEOGPOINT(@center_lon, @center_lat)
            ) / 1000.0 AS dist_from_center_km,
            COALESCE(t.total_pop, 0.0) AS total_pop,
            COALESCE(NULLIF(t.median_age, -666666666.0), 35.0) AS median_age,
            COALESCE(NULLIF(t.median_income, -666666666.0), 55000.0) AS median_income,
            COALESCE(t.housing_units, 1200.0) AS housing_units,
            COALESCE(
              NULLIF(t.median_year_structure_built, -666666666.0),
              1978.0
            ) AS median_year_structure_built,
            GREATEST(
              0.0,
              2026.0 - COALESCE(NULLIF(t.median_year_structure_built, -666666666.0), 1978.0)
            ) AS structure_age_years,
            SAFE_DIVIDE(
              COALESCE(t.housing_units, 1200.0),
              GREATEST(COALESCE(t.total_pop, 1000.0), 100.0)
            ) AS housing_density_proxy,
            COALESCE(t.no_cars, 0.0) AS no_cars,
            COALESCE(t.households, 1000.0) AS households,
            COALESCE(t.poverty_rate, 0.0) AS poverty_rate,
            COALESCE(t.no_vehicle_rate, 0.0) AS no_vehicle_rate,
            50.0 AS humidity_pct
          FROM `{runtime.dataset_fqn}.tract_demographics` AS t
          WHERE t.tract_lat BETWEEN @min_lat AND @max_lat
            AND t.tract_lon BETWEEN @min_lon AND @max_lon
            AND COALESCE(t.total_pop, 0) >= 250
        ),
        explained AS (
          SELECT
            *
          FROM ML.EXPLAIN_PREDICT(
            MODEL `{model_fqn}`,
            (SELECT * FROM candidate_tracts),
            STRUCT({int(top_k)} AS top_k_features)
          )
        ),
        normalized AS (
          SELECT
            e.*,
            SAFE_DIVIDE(
              e.predicted_heat_offset_f - MIN(e.predicted_heat_offset_f) OVER (),
              NULLIF(MAX(e.predicted_heat_offset_f) OVER () - MIN(e.predicted_heat_offset_f) OVER (), 0)
            ) AS norm_offset,
            SAFE_DIVIDE(
              e.no_vehicle_rate - MIN(e.no_vehicle_rate) OVER (),
              NULLIF(MAX(e.no_vehicle_rate) OVER () - MIN(e.no_vehicle_rate) OVER (), 0)
            ) AS norm_no_vehicle,
            SAFE_DIVIDE(
              e.poverty_rate - MIN(e.poverty_rate) OVER (),
              NULLIF(MAX(e.poverty_rate) OVER () - MIN(e.poverty_rate) OVER (), 0)
            ) AS norm_poverty,
            SAFE_DIVIDE(
              e.median_age - MIN(e.median_age) OVER (),
              NULLIF(MAX(e.median_age) OVER () - MIN(e.median_age) OVER (), 0)
            ) AS norm_median_age,
            SAFE_DIVIDE(
              e.total_pop - MIN(e.total_pop) OVER (),
              NULLIF(MAX(e.total_pop) OVER () - MIN(e.total_pop) OVER (), 0)
            ) AS norm_pop,
            SAFE_DIVIDE(
              e.structure_age_years - MIN(e.structure_age_years) OVER (),
              NULLIF(MAX(e.structure_age_years) OVER () - MIN(e.structure_age_years) OVER (), 0)
            ) AS norm_structure_age
          FROM explained AS e
        )
        SELECT
          *,
          ROUND(100.0 * ({score_expr}), 1) AS composite_priority_score
        FROM normalized
        ORDER BY composite_priority_score DESC, predicted_heat_offset_f DESC
        LIMIT @top_n
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("min_lat", "FLOAT64", city_meta.min_lat - pad),
                bigquery.ScalarQueryParameter("max_lat", "FLOAT64", city_meta.max_lat + pad),
                bigquery.ScalarQueryParameter("min_lon", "FLOAT64", city_meta.min_lon - pad),
                bigquery.ScalarQueryParameter("max_lon", "FLOAT64", city_meta.max_lon + pad),
                bigquery.ScalarQueryParameter("center_lat", "FLOAT64", city_meta.center_lat),
                bigquery.ScalarQueryParameter("center_lon", "FLOAT64", city_meta.center_lon),
                bigquery.ScalarQueryParameter("top_n", "INT64", top_n),
            ]
        )

        rows = runtime.query_rows(sql, job_config)
        sites: list[dict[str, Any]] = []
        tract_ids: list[str] = []

        for idx, row in enumerate(rows, start=1):
            row_dict = dict(row.items())
            geo_id = str(row_dict.get("geo_id") or "").zfill(11)
            tract_ids.append(geo_id)

            pred_offset = _extract_predicted_offset(row_dict)
            raw_attrs = row_dict.get("top_feature_attributions") or []
            structured_attrs, narrative_summary = format_feature_attributions(raw_attrs)

            no_veh_rate = float(row_dict.get("no_vehicle_rate") or 0.0)
            pov_rate = float(row_dict.get("poverty_rate") or 0.0)
            intervention = _select_intervention(
                normalized_mode, structured_attrs, no_veh_rate, pov_rate
            )

            sign = "+" if pred_offset >= 0 else "\u2212"
            sites.append(
                {
                    "rank": idx,
                    "tract_geo_id": geo_id,
                    "coordinates": {
                        "latitude": round(float(row_dict["latitude"]), 5),
                        "longitude": round(float(row_dict["longitude"]), 5),
                    },
                    "composite_priority_score": float(
                        row_dict.get("composite_priority_score") or 0.0
                    ),
                    "predicted_heat_offset_f": round(pred_offset, 2),
                    "formatted_offset": f"{sign}{abs(pred_offset):.2f}\u00b0F vs. city average",
                    "estimated_temp_on_campaign_day_f": round(
                        city_meta.city_avg_temp_f + pred_offset, 1
                    ),
                    "why_it_is_hot": narrative_summary,
                    "top_feature_attributions": structured_attrs,
                    "demographics": {
                        "total_population": int(round(float(row_dict.get("total_pop") or 0.0))),
                        "poverty_rate_pct": round(pov_rate * 100.0, 1),
                        "no_vehicle_rate_pct": round(no_veh_rate * 100.0, 1),
                        "households_without_car": int(round(float(row_dict.get("no_cars") or 0.0))),
                        "median_age": round(float(row_dict.get("median_age") or 0.0), 1),
                        "median_income_usd": int(
                            round(float(row_dict.get("median_income") or 0.0))
                        ),
                        "median_year_structure_built": int(
                            round(float(row_dict.get("median_year_structure_built") or 1978.0))
                        ),
                    },
                    "recommended_intervention": intervention,
                }
            )

        return {
            "status": "OK",
            "city": city_meta.city,
            "mode": normalized_mode,
            "scoring_methodology": track_description,
            "model_used": model_fqn,
            "city_campaign_avg_temp_f": round(city_meta.city_avg_temp_f, 1),
            "top_n_returned": len(sites),
            "recommended_tract_ids": tract_ids,
            "sites": sites,
            "next_step_hint": (
                "Call `audit_recommendations_equity(tract_ids=recommended_tract_ids)` to verify "
                "whether these recommended tracts reach the city's most vulnerable residents."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error in rank_cooling_sites(top_n=%s, mode=%s)", top_n, mode)
        return {
            "status": "ERROR",
            "error_code": "SITE_RANKING_FAILED",
            "message": f"Failed to rank cooling sites: {exc}",
        }


# ==============================================================================
# ADK Function Tool 3: audit_recommendations_equity
# ==============================================================================


def audit_recommendations_equity(tract_ids: list[str]) -> dict[str, Any]:
    """Audit whether recommended Census tracts equitably reach the city's most vulnerable neighborhoods.

    Compares the average `poverty_rate`, `no_vehicle_rate`, `median_age`, and `median_income`
    of the selected `tract_ids` against the citywide baseline across all tracts in
    `tract_demographics`.

    Why this tool matters (Rigor & Judgment):
    Race was deliberately excluded from the BigQuery ML model inputs (`tract_demographics`)
    because physical built-environment features cause urban heat islands directly. However,
    "fairness through unawareness" is insufficient—we must audit the model's recommended
    output tracts post-hoc against socioeconomic vulnerability metrics.

    Args:
        tract_ids: List of Census tract `geo_id` strings (e.g., `["48113008900", "48113004900"]`)
            returned by `rank_cooling_sites` or selected by the planner.

    Returns:
        A dictionary containing:
        - `status`: `"OK"` or `"ERROR"`.
        - `city`: Loaded city name.
        - `audited_tract_ids`: Normalized 11-digit Census tract IDs matched in BigQuery.
        - `recommended_tracts_summary`: Aggregated demographics of the recommended sites.
        - `citywide_baseline_summary`: Aggregated demographics across all city tracts.
        - `equity_deltas_vs_city_average`: Exact differences in poverty rate, car-free rate,
          median age, and median income between recommended sites and the city as a whole.
        - `equity_verdict`: Classification and transparent narrative explaining whether the
          recommendations landed in high-need neighborhoods or missed them.
    """
    if not tract_ids or not isinstance(tract_ids, list) or len(tract_ids) > 100:
        logger.warning("audit_recommendations_equity rejected invalid tract list")
        return {
            "status": "INVALID_INPUT",
            "error_code": "EMPTY_TRACT_LIST",
            "message": (
                "Provide between 1 and 100 Census tract `geo_id` strings to audit "
                "(e.g., from `rank_cooling_sites`)."
            ),
        }

    if any(
        not isinstance(tid, str)
        or not tid.strip().isascii()
        or not tid.strip().isdigit()
        or not 1 <= len(tid.strip()) <= 11
        for tid in tract_ids
    ):
        logger.warning("audit_recommendations_equity rejected invalid GEOID")
        return {
            "status": "INVALID_INPUT",
            "error_code": "INVALID_TRACT_ID",
            "message": "Tract IDs must contain 1 to 11 ASCII digits; leading zeros may be omitted.",
        }

    # Preserve the existing leading-zero normalization for Census GEOIDs.
    normalized_ids = list(
        dict.fromkeys(str(tid).strip().zfill(11) for tid in tract_ids if str(tid).strip())
    )
    if not normalized_ids:
        return {
            "status": "INVALID_INPUT",
            "error_code": "EMPTY_TRACT_LIST",
            "message": "No valid Census tract IDs were provided.",
        }

    runtime = get_runtime()

    try:
        city_meta = runtime.get_city_metadata()

        sql = f"""
        WITH normalized_tracts AS (
          SELECT
            LPAD(geo_id, 11, '0') AS geo_id,
            total_pop,
            NULLIF(median_age, -666666666.0) AS median_age,
            NULLIF(median_income, -666666666.0) AS median_income,
            poverty_rate,
            no_vehicle_rate,
            no_cars,
            households,
            LPAD(geo_id, 11, '0') IN UNNEST(@tract_ids) AS is_recommended
          FROM `{runtime.dataset_fqn}.tract_demographics`
          WHERE total_pop IS NOT NULL AND total_pop > 0
        )
        SELECT
          -- Recommended tracts aggregation
          COUNTIF(is_recommended) AS rec_tract_count,
          ARRAY_AGG(IF(is_recommended, geo_id, NULL) IGNORE NULLS) AS matched_tract_ids,
          SUM(IF(is_recommended, total_pop, 0)) AS rec_total_pop,
          AVG(IF(is_recommended, poverty_rate, NULL)) AS rec_avg_poverty_rate,
          AVG(IF(is_recommended, no_vehicle_rate, NULL)) AS rec_avg_no_vehicle_rate,
          AVG(IF(is_recommended, median_age, NULL)) AS rec_avg_median_age,
          AVG(IF(is_recommended, median_income, NULL)) AS rec_avg_median_income,
          SUM(IF(is_recommended, no_cars, 0)) AS rec_total_no_car_households,

          -- Citywide baseline aggregation
          COUNT(*) AS city_tract_count,
          SUM(total_pop) AS city_total_pop,
          AVG(poverty_rate) AS city_avg_poverty_rate,
          AVG(no_vehicle_rate) AS city_avg_no_vehicle_rate,
          AVG(median_age) AS city_avg_median_age,
          AVG(median_income) AS city_avg_median_income
        FROM normalized_tracts
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("tract_ids", "STRING", normalized_ids),
            ]
        )

        rows = runtime.query_rows(sql, job_config)
        if not rows:
            return {
                "status": "ERROR",
                "error_code": "DEMOGRAPHICS_TABLE_EMPTY",
                "message": f"Table `{runtime.dataset_fqn}.tract_demographics` returned no rows.",
            }

        r = dict(rows[0].items())
        rec_count = int(r.get("rec_tract_count") or 0)
        matched_ids = list(r.get("matched_tract_ids") or [])
        missing_ids = [tid for tid in normalized_ids if tid not in set(matched_ids)]

        if rec_count == 0:
            return {
                "status": "NOT_FOUND",
                "error_code": "NO_MATCHING_TRACTS",
                "loaded_city": city_meta.city,
                "requested_tract_ids": normalized_ids,
                "message": (
                    f"None of the provided Census tract IDs ({normalized_ids}) matched tracts in "
                    f"`{runtime.dataset_fqn}.tract_demographics` for {city_meta.city}."
                ),
            }

        rec_pov_pct = float(r.get("rec_avg_poverty_rate") or 0.0) * 100.0
        city_pov_pct = float(r.get("city_avg_poverty_rate") or 0.0) * 100.0
        pov_delta_pts = rec_pov_pct - city_pov_pct

        rec_noveh_pct = float(r.get("rec_avg_no_vehicle_rate") or 0.0) * 100.0
        city_noveh_pct = float(r.get("city_avg_no_vehicle_rate") or 0.0) * 100.0
        noveh_delta_pts = rec_noveh_pct - city_noveh_pct

        rec_age = float(r.get("rec_avg_median_age") or 0.0)
        city_age = float(r.get("city_avg_median_age") or 0.0)
        age_delta = rec_age - city_age

        rec_inc = float(r.get("rec_avg_median_income") or 0.0)
        city_inc = float(r.get("city_avg_median_income") or 0.0)
        inc_delta = rec_inc - city_inc
        inc_ratio_pct = (rec_inc / city_inc * 100.0) if city_inc > 0 else 100.0

        # Evaluate alignment with high-need populations
        reaches_higher_poverty = pov_delta_pts >= 2.0
        reaches_lower_vehicle_access = noveh_delta_pts >= 1.5
        reaches_lower_income = inc_delta < 0

        if (reaches_higher_poverty and reaches_lower_vehicle_access) or (
            reaches_higher_poverty and reaches_lower_income
        ):
            verdict_code = "STRONG_VULNERABILITY_ALIGNMENT"
            verdict_summary = (
                f"PASS (High Equity Alignment): Recommended sites in {city_meta.city} "
                f"serve neighborhoods with a {rec_pov_pct:.1f}% poverty rate "
                f"({pov_delta_pts:+.1f} percentage points vs. the {city_pov_pct:.1f}% city average), "
                f"{rec_noveh_pct:.1f}% households without vehicles "
                f"({noveh_delta_pts:+.1f} percentage points vs. the {city_noveh_pct:.1f}% city average), "
                f"and median income of ${rec_inc:,.0f} ({inc_ratio_pct:.0f}% of the ${city_inc:,.0f} citywide average)."
            )
        elif reaches_higher_poverty or reaches_lower_vehicle_access or reaches_lower_income:
            verdict_code = "PARTIAL_VULNERABILITY_ALIGNMENT"
            verdict_summary = (
                f"MIXED (Partial Equity Alignment): Recommended sites capture above-average need on "
                f"some dimensions (poverty rate {rec_pov_pct:.1f}% vs. {city_pov_pct:.1f}% citywide; "
                f"car-free households {rec_noveh_pct:.1f}% vs. {city_noveh_pct:.1f}% citywide), "
                "but planners should verify whether pockets of isolated seniors or extreme poverty were missed."
            )
        else:
            verdict_code = "VULNERABILITY_GAP_DETECTED"
            verdict_summary = (
                f"WARNING (Equity Gap Detected): The selected sites skew wealthier and higher-mobility "
                f"than the {city_meta.city} average (poverty rate {rec_pov_pct:.1f}% vs. {city_pov_pct:.1f}% citywide; "
                f"car-free households {rec_noveh_pct:.1f}% vs. {city_noveh_pct:.1f}% citywide; "
                f"median income ${rec_inc:,.0f} vs. ${city_inc:,.0f} citywide). "
                "Pure thermal features are capturing commercial/industrial pavement heat rather than "
                "residential vulnerability—re-weight siting toward high-no-vehicle and high-poverty tracts."
            )

        return {
            "status": "OK",
            "city": city_meta.city,
            "audited_tract_ids": matched_ids,
            "missing_tract_ids": missing_ids,
            "recommended_tracts_summary": {
                "tract_count": rec_count,
                "total_population_covered": int(round(float(r.get("rec_total_pop") or 0.0))),
                "total_car_free_households_covered": int(
                    round(float(r.get("rec_total_no_car_households") or 0.0))
                ),
                "avg_poverty_rate_pct": round(rec_pov_pct, 1),
                "avg_no_vehicle_rate_pct": round(rec_noveh_pct, 1),
                "avg_median_age_years": round(rec_age, 1),
                "avg_median_income_usd": int(round(rec_inc)),
            },
            "citywide_baseline_summary": {
                "total_city_tracts": int(r.get("city_tract_count") or 0),
                "total_city_population": int(round(float(r.get("city_total_pop") or 0.0))),
                "avg_poverty_rate_pct": round(city_pov_pct, 1),
                "avg_no_vehicle_rate_pct": round(city_noveh_pct, 1),
                "avg_median_age_years": round(city_age, 1),
                "avg_median_income_usd": int(round(city_inc)),
            },
            "equity_deltas_vs_city_average": {
                "poverty_rate_delta_pct_points": round(pov_delta_pts, 1),
                "no_vehicle_rate_delta_pct_points": round(noveh_delta_pts, 1),
                "median_age_delta_years": round(age_delta, 1),
                "median_income_delta_usd": int(round(inc_delta)),
                "recommended_to_city_income_ratio_pct": round(inc_ratio_pct, 1),
            },
            "equity_verdict": {
                "classification": verdict_code,
                "summary": verdict_summary,
                "methodology_note": (
                    "Strip the variable, audit the outcome: Race and ethnicity columns were "
                    "deliberately excluded from model training inputs so public resources are not "
                    "allocated by demographic proxies for concrete/canopy. This post-hoc audit verifies "
                    "whether physical & socioeconomic siting actually reaches vulnerable residents."
                ),
            },
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error in audit_recommendations_equity(%s)", tract_ids)
        return {
            "status": "ERROR",
            "error_code": "EQUITY_AUDIT_FAILED",
            "message": f"Failed to run equity audit: {exc}",
        }


# ==============================================================================
# ADK Function Tool 4: get_station_heat_frequency
# ==============================================================================


def get_station_heat_frequency(threshold_f: float = 95.0) -> dict[str, Any]:
    """Analyze 7 years of NOAA GHCN-Daily weather station history to quantify extreme heat frequency and trends.

    Queries `station_daily_temps` (multi-year daily maximum temperatures from regional NOAA GHCN
    stations around the city) to answer:
    - How many days per year does the city reach or exceed `threshold_f` (default 95°F)?
    - Is dangerous heat frequency increasing over the 7-year observation record?
    - How does regional station history combine with local microclimate offsets (e.g., a site
      with a +7°F offset experiences 102°F+ conditions every time the regional station hits 95°F)?

    Args:
        threshold_f: Daily maximum temperature threshold in degrees Fahrenheit (default 95.0).

    Returns:
        A dictionary containing:
        - `status`: `"OK"` or `"ERROR"`.
        - `city`: Loaded city name.
        - `threshold_f`: Evaluated temperature threshold in °F.
        - `station_coverage`: Number of distinct GHCN stations and date range covered.
        - `multi_year_summary`: Average annual days >= `threshold_f`, 90°F, 95°F, and 100°F across
          complete observation years, plus all-time peak station temperature.
        - `trend_analysis`: Comparison of early vs. recent complete years and annual trend slope.
        - `yearly_breakdown`: Year-by-year table of hot days and summer peak temperatures.
    """
    if (
        type(threshold_f) not in (int, float)
        or math.isnan(threshold_f)
        or not (40.0 <= float(threshold_f) <= 135.0)
    ):
        logger.warning("get_station_heat_frequency rejected invalid threshold")
        return {
            "status": "INVALID_INPUT",
            "error_code": "INVALID_THRESHOLD",
            "message": f"threshold_f={threshold_f} must be a plausible temperature between 40°F and 135°F.",
        }

    thresh = float(threshold_f)
    runtime = get_runtime()

    try:
        city_meta = runtime.get_city_metadata()

        sql = f"""
        WITH daily_city_temps AS (
          -- Aggregate across regional stations per day so multi-station cities do not double-count days
          SELECT
            observation_date,
            EXTRACT(YEAR FROM observation_date) AS obs_year,
            EXTRACT(MONTH FROM observation_date) AS obs_month,
            AVG(max_temp_f) AS city_station_avg_max_f,
            MAX(max_temp_f) AS city_station_peak_max_f,
            COUNT(DISTINCT station_id) AS reporting_stations
          FROM `{runtime.dataset_fqn}.station_daily_temps`
          WHERE max_temp_f IS NOT NULL
          GROUP BY observation_date
        ),
        station_meta AS (
          SELECT
            COUNT(DISTINCT station_id) AS total_stations,
            ARRAY_AGG(DISTINCT station_name IGNORE NULLS LIMIT 10) AS station_names,
            MIN(observation_date) AS first_date,
            MAX(observation_date) AS last_date
          FROM `{runtime.dataset_fqn}.station_daily_temps`
          WHERE max_temp_f IS NOT NULL
        ),
        yearly AS (
          SELECT
            obs_year,
            COUNT(*) AS observed_days,
            COUNTIF(city_station_avg_max_f >= @threshold_f) AS days_avg_ge_threshold,
            COUNTIF(city_station_peak_max_f >= @threshold_f) AS days_peak_ge_threshold,
            COUNTIF(city_station_avg_max_f >= 90.0) AS days_ge_90f,
            COUNTIF(city_station_avg_max_f >= 95.0) AS days_ge_95f,
            COUNTIF(city_station_avg_max_f >= 100.0) AS days_ge_100f,
            ROUND(AVG(IF(obs_month IN (6, 7, 8), city_station_avg_max_f, NULL)), 1) AS summer_mean_max_f,
            ROUND(MAX(city_station_peak_max_f), 1) AS annual_peak_temp_f
          FROM daily_city_temps
          GROUP BY obs_year
          ORDER BY obs_year ASC
        )
        SELECT
          y.*,
          m.total_stations,
          m.station_names,
          m.first_date,
          m.last_date
        FROM yearly AS y
        CROSS JOIN station_meta AS m
        ORDER BY y.obs_year ASC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("threshold_f", "FLOAT64", thresh),
            ]
        )

        rows = runtime.query_rows(sql, job_config)
        if not rows:
            return {
                "status": "ERROR",
                "error_code": "STATION_HISTORY_EMPTY",
                "loaded_city": city_meta.city,
                "message": f"Table `{runtime.dataset_fqn}.station_daily_temps` returned no observations.",
            }

        first_row = dict(rows[0].items())
        total_stations = int(first_row.get("total_stations") or 0)
        station_names = list(first_row.get("station_names") or [])
        first_date = str(first_row.get("first_date") or "")
        last_date = str(first_row.get("last_date") or "")

        yearly_breakdown: list[dict[str, Any]] = []
        complete_years: list[dict[str, Any]] = []

        for row in rows:
            r = dict(row.items())
            obs_days = int(r.get("observed_days") or 0)
            is_complete_year = obs_days >= 240  # Guard against partial final calendar year
            item = {
                "year": int(r["obs_year"]),
                "observed_days": obs_days,
                "is_complete_year": is_complete_year,
                "days_at_or_above_threshold": int(r.get("days_avg_ge_threshold") or 0),
                "days_any_station_at_or_above_threshold": int(
                    r.get("days_peak_ge_threshold") or 0
                ),
                "days_90f_plus": int(r.get("days_ge_90f") or 0),
                "days_95f_plus": int(r.get("days_ge_95f") or 0),
                "days_100f_plus": int(r.get("days_ge_100f") or 0),
                "summer_jja_mean_max_f": (
                    float(r["summer_mean_max_f"])
                    if r.get("summer_mean_max_f") is not None
                    else None
                ),
                "annual_peak_temp_f": float(r.get("annual_peak_temp_f") or 0.0),
            }
            yearly_breakdown.append(item)
            if is_complete_year:
                complete_years.append(item)

        # Fallback to all years if none have >= 240 days
        eval_years = complete_years if complete_years else yearly_breakdown
        n_years = len(eval_years)

        avg_days_ge_thresh = (
            sum(y["days_at_or_above_threshold"] for y in eval_years) / n_years if n_years else 0.0
        )
        avg_days_90 = sum(y["days_90f_plus"] for y in eval_years) / n_years if n_years else 0.0
        avg_days_95 = sum(y["days_95f_plus"] for y in eval_years) / n_years if n_years else 0.0
        avg_days_100 = sum(y["days_100f_plus"] for y in eval_years) / n_years if n_years else 0.0
        all_time_peak_f = max(y["annual_peak_temp_f"] for y in yearly_breakdown)

        # Compute trend across complete years (ordinary least squares slope + early vs late split)
        if n_years >= 2:
            xs = [float(y["year"]) for y in eval_years]
            ys = [float(y["days_at_or_above_threshold"]) for y in eval_years]
            x_mean = sum(xs) / n_years
            y_mean = sum(ys) / n_years
            denom = sum((x - x_mean) ** 2 for x in xs)
            slope_days_per_year = (
                sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
                if denom > 0
                else 0.0
            )

            mid = n_years // 2
            early_slice = eval_years[:mid]
            late_slice = eval_years[mid:]
            early_avg = sum(y["days_at_or_above_threshold"] for y in early_slice) / len(early_slice)
            late_avg = sum(y["days_at_or_above_threshold"] for y in late_slice) / len(late_slice)
            delta_early_to_late = late_avg - early_avg
        else:
            slope_days_per_year = 0.0
            early_avg = avg_days_ge_thresh
            late_avg = avg_days_ge_thresh
            delta_early_to_late = 0.0

        if slope_days_per_year >= 0.75 or delta_early_to_late >= 3.0:
            trend_direction = "INCREASING"
        elif slope_days_per_year <= -0.75 or delta_early_to_late <= -3.0:
            trend_direction = "DECREASING"
        else:
            trend_direction = "STABLE_HIGH_VARIABILITY"

        return {
            "status": "OK",
            "city": city_meta.city,
            "threshold_f": thresh,
            "station_coverage": {
                "distinct_stations": total_stations,
                "sample_station_names": station_names,
                "first_observation_date": first_date,
                "last_observation_date": last_date,
                "complete_years_analyzed": n_years,
            },
            "multi_year_summary": {
                "avg_annual_days_at_or_above_threshold": round(avg_days_ge_thresh, 1),
                "avg_annual_days_90f_plus": round(avg_days_90, 1),
                "avg_annual_days_95f_plus": round(avg_days_95, 1),
                "avg_annual_days_100f_plus": round(avg_days_100, 1),
                "all_time_record_max_f_in_window": round(all_time_peak_f, 1),
            },
            "trend_analysis": {
                "direction": trend_direction,
                "slope_hot_days_per_year": round(slope_days_per_year, 2),
                "early_period_avg_days_ge_threshold": round(early_avg, 1),
                "recent_period_avg_days_ge_threshold": round(late_avg, 1),
                "change_recent_vs_early_days": round(delta_early_to_late, 1),
                "microclimate_compounding_note": (
                    f"Regional stations measure background air mass ({avg_days_ge_thresh:.1f} days/yr >= {thresh:.0f}°F). "
                    f"However, a street corner with a +6°F microclimate offset crosses {thresh:.0f}°F "
                    f"whenever the regional airport station reaches {thresh - 6.0:.0f}°F—dramatically "
                    "multiplying how often residents experience dangerous heat stress."
                ),
            },
            "yearly_breakdown": yearly_breakdown,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error in get_station_heat_frequency(threshold_f=%s)", threshold_f)
        return {
            "status": "ERROR",
            "error_code": "STATION_FREQUENCY_QUERY_FAILED",
            "message": f"Failed to compute station heat frequency: {exc}",
        }


CUSTOM_HEAT_TOOLS = [
    predict_and_explain_location,
    rank_cooling_sites,
    audit_recommendations_equity,
    get_station_heat_frequency,
]
