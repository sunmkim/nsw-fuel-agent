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
    DIRECTIONS_EXPERIMENT,
)


MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"

# ── Telemetry ─────────────────────────────────────────────────────────────────
# Configure a single in-memory exporter shared across all runs.
# Spans are cleared before each case so results don't bleed across runs.
telemetry = StrandsEvalsTelemetry().setup_in_memory_exporter()
mapper = StrandsInMemorySessionMapper()

fuel_tools = NSWFuelClient()


def _build_session(case_name: str):
    """Collect finished spans and map them to a Session object."""
    spans = list(telemetry.in_memory_exporter.get_finished_spans())
    return mapper.map_to_session(spans, session_id=case_name)


# ── Task Functions ────────────────────────────────────────────────────────────
# Each function creates a fresh agent per case (prevents message bleed across
# cases) and returns {"output": ..., "trajectory": Session} so tool-accuracy
# evaluators have the Session they require.


def run_fuel_case(case: Case) -> dict:
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

        def run_cases(case: Case) -> dict:
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

        # Run clarification experiment
        # clarification_reports = CLARIFICATION_EXPERIMENT.run_evaluations(run_cases)
        # print("=== Clarification Evaluation Results ===")
        # clarification_reports[0].run_display()
        # CLARIFICATION_EXPERIMENT.to_file("clarification_evaluation")

        # Run location experiment
        # location_reports = LOCATION_EXPERIMENT.run_evaluations(run_cases)
        # print("=== Location Evaluation Results ===")
        # location_reports[0].run_display()
        # LOCATION_EXPERIMENT.to_file("location_evaluation")

        # Run fuel experiment
        # fuel_reports = FUEL_EXPERIMENT.run_evaluations(run_cases)
        # print("=== Fuel Evaluation Results ===")
        # fuel_reports[0].run_display()
        # FUEL_EXPERIMENT.to_file("fuel_evaluation")

        # Run directions experiment
        directions_reports = DIRECTIONS_EXPERIMENT.run_evaluations(run_cases)
        print("=== Directions Evaluation Results ===")
        directions_reports[0].run_display()
        DIRECTIONS_EXPERIMENT.to_file("directions_evaluation")
