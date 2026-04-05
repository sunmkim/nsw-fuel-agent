import os
import sys
import httpx

# Add agents/ directory to path (agents/ uses flat imports, not a package)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))

# Strands imports
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamable_http_client

# Strands Evals imports
from strands_evals import Case
from strands_evals.telemetry.config import StrandsEvalsTelemetry
from strands_evals.mappers import StrandsInMemorySessionMapper
from tools import NSWFuelClient, geocode_location
from prompts import SYSTEM_PROMPT
from experiments import (
    CLARIFICATION_EXPERIMENT,
    LOCATION_EXPERIMENT,
    FUEL_EXPERIMENT,
    STATION_LOOKUP_EXPERIMENT,
    DIRECTIONS_EXPERIMENT,
)


MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"

# ── Telemetry ─────────────────────────────────────────────────────────────────
# Configure a single in-memory exporter shared across all runs.
# Spans are cleared before each case so results don't bleed across runs.
telemetry = StrandsEvalsTelemetry().setup_in_memory_exporter()
mapper = StrandsInMemorySessionMapper()


def _build_session(case_name: str):
    """Collect finished spans and map them to a Session object."""
    spans = list(telemetry.in_memory_exporter.get_finished_spans())
    return mapper.map_to_session(spans, session_id=case_name)


# ── Task Functions ────────────────────────────────────────────────────────────
# Each function creates a fresh agent per case (prevents message bleed across
# cases) and returns {"output": ..., "trajectory": Session} so tool-accuracy
# evaluators have the Session they require.


def run_standard_case(case: Case) -> dict:
    """
    Task function for CLARIFICATION, LOCATION, FUEL, and STATION_LOOKUP experiments.
    Builds an agent without Mapbox tools — these experiments never call directions_tool.
    Keeping directions_tool out of the tool list ensures ToolSelectionAccuracyEvaluator
    results are not polluted by an extra available-but-unused tool (especially important
    for CLARIFICATION cases where expected_tools=[]).
    """
    telemetry.in_memory_exporter.clear()
    client = NSWFuelClient()
    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[
            geocode_location,
            client.get_prices_for_location,
            client.get_nearby_prices,
            client.get_price_at_station,
        ],
        model=MODEL_ID,
        callback_handler=None,
    )
    response = agent(case.input)
    return {"output": str(response), "trajectory": _build_session(case.name)}


if __name__ == "__main__":

    # ── Experiments that do NOT need Mapbox MCP ────────────────────────────
    clarification_reports = CLARIFICATION_EXPERIMENT.run_evaluations(run_standard_case)
    print("=== Clarification Evaluation Results ===")
    clarification_reports[0].run_display()
    CLARIFICATION_EXPERIMENT.to_file("clarification_evaluation")

    location_reports = LOCATION_EXPERIMENT.run_evaluations(run_standard_case)
    print("=== Location Evaluation Results ===")
    location_reports[0].run_display()
    LOCATION_EXPERIMENT.to_file("location_evaluation")

    fuel_reports = FUEL_EXPERIMENT.run_evaluations(run_standard_case)
    print("=== Fuel Evaluation Results ===")
    fuel_reports[0].run_display()
    FUEL_EXPERIMENT.to_file("fuel_evaluation")

    station_reports = STATION_LOOKUP_EXPERIMENT.run_evaluations(run_standard_case)
    print("=== Station Lookup Evaluation Results ===")
    station_reports[0].run_display()
    STATION_LOOKUP_EXPERIMENT.to_file("station_lookup_evaluation")

    # ── Experiments that require Mapbox MCP ───────────────────────────────
    mapbox_mcp_client = MCPClient(
        lambda: streamable_http_client(
            url="https://mcp.mapbox.com/mcp",
            http_client=httpx.AsyncClient(
                headers={"Authorization": f"Bearer {os.getenv('MAPBOX_API_KEY')}"}
            ),
        ),
        tool_filters={"allowed": ["directions_tool"]}
    )

    with mapbox_mcp_client:
        mapbox_tools = mapbox_mcp_client.list_tools_sync()
        fuel_tools = NSWFuelClient()

        def run_mapbox_case(case: Case) -> dict:
            """
            Task function for DIRECTIONS experiment.
            Includes directions_tool from Mapbox MCP alongside all fuel tools.
            """
            telemetry.in_memory_exporter.clear()
            agent = Agent(
                system_prompt=SYSTEM_PROMPT,
                tools=[
                    mapbox_tools,
                    geocode_location,
                    fuel_tools.get_prices_for_location,
                    fuel_tools.get_nearby_prices,
                    fuel_tools.get_price_at_station,
                ],
                model=MODEL_ID,
                callback_handler=None,
            )
            response = agent(case.input)
            return {"output": str(response), "trajectory": _build_session(case.name)}

        directions_reports = DIRECTIONS_EXPERIMENT.run_evaluations(run_mapbox_case)
        print("=== Directions Evaluation Results ===")
        directions_reports[0].run_display()
        DIRECTIONS_EXPERIMENT.to_file("directions_evaluation")
