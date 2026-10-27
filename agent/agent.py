"""Google ADK Agent definition for Challenge 1: Urban Heat Resilience."""

from __future__ import annotations

import logging
from typing import Any

from .config import AgentConfig, get_config
from .prompts import SYSTEM_INSTRUCTION
from .tools import (
    CUSTOM_HEAT_TOOLS,
    audit_recommendations_equity,
    get_station_heat_frequency,
    predict_and_explain_location,
    rank_cooling_sites,
)

logger = logging.getLogger(__name__)


def _load_optional_mcp_tools(config: AgentConfig) -> list[Any]:
    """Attach managed MCP Toolbox / MCP server tools when `MCP_TOOLBOX_URL` is configured."""
    if not config.mcp_toolbox_url:
        return []

    # Support Google MCP Toolbox for Databases or standard ADK MCPToolset
    try:
        from toolbox_core import ToolboxSyncClient  # type: ignore[import-not-found]

        client = ToolboxSyncClient(config.mcp_toolbox_url)
        tools = list(client.load_toolset())
        logger.info("Loaded %d tools from MCP Toolbox at %s", len(tools), config.mcp_toolbox_url)
        return tools
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Could not load MCP Toolbox from %s (%s); continuing with custom Python ADK tools.",
            config.mcp_toolbox_url,
            exc,
        )
        return []


def build_agent(config: AgentConfig | None = None) -> Any:
    """Instantiate the Urban Heat Resilience ADK Agent with custom BQML tools and optional MCP."""
    active_config = config or get_config()
    tools: list[Any] = list(CUSTOM_HEAT_TOOLS) + _load_optional_mcp_tools(active_config)

    try:
        from google.adk.agents import Agent  # type: ignore[import-not-found]

        return Agent(
            name="urban_heat_resilience_agent",
            model=active_config.gemini_model,
            description=(
                "Decision-support planning agent for municipal urban heat resilience. "
                "Predicts street-level heat offsets and feature attributions via BigQuery ML "
                "(ML.EXPLAIN_PREDICT), ranks cooling interventions across Census tracts, "
                "analyzes 7-year NOAA GHCN extreme heat frequency, and audits demographic equity."
            ),
            instruction=SYSTEM_INSTRUCTION,
            tools=tools,
        )
    except ImportError:
        logger.warning(
            "`google-adk` is not installed in the current Python environment; "
            "returning a lightweight agent specification."
        )
        return {
            "name": "urban_heat_resilience_agent",
            "model": active_config.gemini_model,
            "instruction": SYSTEM_INSTRUCTION,
            "tools": tools,
        }


root_agent = build_agent()

__all__ = [
    "root_agent",
    "build_agent",
    "predict_and_explain_location",
    "rank_cooling_sites",
    "audit_recommendations_equity",
    "get_station_heat_frequency",
    "CUSTOM_HEAT_TOOLS",
]

