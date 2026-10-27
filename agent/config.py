"""Configuration and feature metadata for the Urban Heat Resilience ADK Agent."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# Human-readable descriptions for BigQuery ML feature attributions returned by
# ML.EXPLAIN_PREDICT. Translates raw table column names into domain language
# suitable for city council proposals and urban planning explanations.
FEATURE_EXPLANATION_LABELS: dict[str, str] = {
    "median_year_structure_built": "building stock age & thermal mass (median_year_structure_built)",
    "structure_age_years": "older building stock & urban form (structure_age_years)",
    "housing_units": "built-environment housing density (housing_units)",
    "housing_density_proxy": "residential structure density (housing_density_proxy)",
    "total_pop": "neighborhood population concentration (total_pop)",
    "no_vehicle_rate": "household transit/walking dependency (no_vehicle_rate)",
    "no_cars": "households without vehicle access (no_cars)",
    "poverty_rate": "socioeconomic heat-exposure vulnerability proxy (poverty_rate)",
    "median_income": "neighborhood investment & canopy proxy (median_income)",
    "median_age": "resident age profile (median_age)",
    "households": "household density (households)",
    "humidity_pct": "local relative humidity (humidity_pct)",
    "latitude": "north-south spatial microclimate gradient (latitude)",
    "longitude": "east-west spatial microclimate gradient (longitude)",
    "tract_lat": "tract north-south spatial position (tract_lat)",
    "tract_lon": "tract east-west spatial position (tract_lon)",
    "dist_from_center_km": "urban core proximity (dist_from_center_km)",
}

# Recommended physical or operational interventions mapped to dominant feature drivers
FEATURE_INTERVENTION_GUIDANCE: dict[str, dict[str, str]] = {
    "today": {
        "no_vehicle_rate": "Deploy mobile hydration unit & door-to-door wellness checks (high share of car-free households unable to drive to distant cooling centers).",
        "median_age": "Prioritize senior wellness checks and paratransit shuttle routing to extended-hour cooling shelters.",
        "poverty_rate": "Open immediate walk-in cooling shelter with free water, electrolytes, and transit vouchers.",
        "default": "Position mobile cooling & hydration unit at high-foot-traffic intersection and extend nearest public facility hours.",
    },
    "budget_cycle": {
        "no_vehicle_rate": "Fund a permanent neighborhood cooling center within a 10-minute walk; high car-free rate means regional centers do not serve this tract.",
        "median_year_structure_built": "Site a permanent community resilience hub and pair with weatherization/HVAC retrofit grants for older housing stock.",
        "structure_age_years": "Site a permanent community resilience hub and pair with weatherization/HVAC retrofit grants for older housing stock.",
        "housing_units": "Establish a high-capacity permanent cooling facility (library/rec center expansion) to serve dense residential demand.",
        "default": "Fund a permanent multi-use cooling center co-located with existing civic infrastructure along transit corridors.",
    },
    "decade": {
        "median_year_structure_built": "Prioritize cool-roof retrofits, high-albedo pavement resurfacing, and street-tree canopy corridors in older built-out blocks.",
        "structure_age_years": "Prioritize cool-roof retrofits, high-albedo pavement resurfacing, and street-tree canopy corridors in older built-out blocks.",
        "housing_units": "Target impervious-surface depaving, cool pavement coatings, and pocket-park canopy expansion in dense residential blocks.",
        "housing_density_proxy": "Target impervious-surface depaving, cool pavement coatings, and pocket-park canopy expansion in dense residential blocks.",
        "median_income": "Direct long-term urban forestry capital to reverse historic canopy disinvestment along residential sidewalks.",
        "default": "Invest in street-tree canopy planting and cool-pavement resurfacing along primary pedestrian corridors.",
    },
}


@dataclass(frozen=True)
class AgentConfig:
    """Immutable runtime configuration for BigQuery, BQML, ADK, and MCP."""

    project_id: str | None = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT")
    )
    dataset_id: str = field(
        default_factory=lambda: os.environ.get("BQ_DATASET", "a4i_climate")
    )
    location: str = field(
        default_factory=lambda: os.environ.get("BQ_LOCATION", "US")
    )
    bqml_model_name: str = field(
        default_factory=lambda: os.environ.get("BQML_MODEL", "heat_offset_model")
    )
    gemini_model: str = field(
        default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
    )
    bbox_pad_degrees: float = field(
        default_factory=lambda: float(os.environ.get("BBOX_PAD_DEGREES", "0.03"))
    )
    explain_top_k: int = field(
        default_factory=lambda: int(os.environ.get("EXPLAIN_TOP_K", "4"))
    )
    auto_bootstrap_bqml: bool = field(
        default_factory=lambda: os.environ.get("AUTO_BOOTSTRAP_BQML", "true").lower()
        in {"1", "true", "yes"}
    )
    mcp_toolbox_url: str | None = field(
        default_factory=lambda: os.environ.get("MCP_TOOLBOX_URL")
    )


def get_config() -> AgentConfig:
    """Return the active agent configuration."""
    return AgentConfig()

