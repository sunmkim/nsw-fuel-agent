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
from strands_evals.extractors import tools_use_extractor
from tools import NSWFuelClient, geocode_location
from prompts import (
    LOCATION_ASSISTANT_PROMPT,
    FUEL_ASSISTANT_PROMPT,
    DIRECTIONS_ASSISTANT_PROMPT,
)
from experiments import (
    LOCATION_EXPERIMENT, 
    FUEL_EXPERIMENT, 
    DIRECTIONS_EXPERIMENT
)


MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"


# ── Task Functions ────────────────────────────────────────────────────────────
# Each function creates a fresh agent per case (prevents message bleed across
# cases) and returns {"output": ..., "trajectory": ...} so tool-accuracy
# evaluators have the trajectory data they need.

def run_location_case(case: Case) -> dict:
    agent = Agent(
        system_prompt=LOCATION_ASSISTANT_PROMPT,
        tools=[geocode_location],
        model=MODEL_ID,
        callback_handler=None,
    )
    response = agent(case.input)
    trajectory = tools_use_extractor.extract_agent_tools_used_from_messages(agent.messages)
    return {"output": str(response), "trajectory": trajectory}


def run_fuel_case(case: Case) -> dict:
    client = NSWFuelClient()
    agent = Agent(
        system_prompt=FUEL_ASSISTANT_PROMPT,
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
    trajectory = tools_use_extractor.extract_agent_tools_used_from_messages(agent.messages)
    return {"output": str(response), "trajectory": trajectory}

if __name__ == "__main__":
    mapbox_mcp_client = MCPClient(
        lambda: streamable_http_client(
            url="https://mcp.mapbox.com/mcp",
            http_client=httpx.AsyncClient(
                headers={"Authorization": f"Bearer {os.getenv('MAPBOX_API_KEY')}"}
            ),
        ),
        tool_filters={"allowed": ["directions_tool", "reverse_geocode_tool"]}
    )

    with mapbox_mcp_client:
        mapbox_tools = mapbox_mcp_client.list_tools_sync()

        def run_directions_case(case: Case) -> dict:
            agent = Agent(
                system_prompt=DIRECTIONS_ASSISTANT_PROMPT,
                tools=[mapbox_tools, geocode_location],
                model=MODEL_ID,
                callback_handler=None,
            )
            response = agent(case.input)
            trajectory = tools_use_extractor.extract_agent_tools_used_from_messages(agent.messages)
            return {"output": str(response), "trajectory": trajectory}

        # Run location experiment
        location_reports = LOCATION_EXPERIMENT.run_evaluations(run_location_case)
        print("=== Location Evaluation Results ===")
        location_reports[0].run_display()
        LOCATION_EXPERIMENT.to_file("location_evaluation")

        # Run fuel experiment
        fuel_reports = FUEL_EXPERIMENT.run_evaluations(run_fuel_case)
        print("=== Fuel Evaluation Results ===")
        fuel_reports[0].run_display()
        FUEL_EXPERIMENT.to_file("fuel_evaluation")

        # Run directions experiment
        directions_reports = DIRECTIONS_EXPERIMENT.run_evaluations(run_directions_case)
        print("=== Directions Evaluation Results ===")
        directions_reports[0].run_display()
        DIRECTIONS_EXPERIMENT.to_file("directions_evaluation")
