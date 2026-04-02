import boto3

# Strands imports
from strands import Agent, tool

# Strands Evals imports
from strands_evals import Experiment, Case
from strands_evals.extractors import tools_use_extractor
from strands_evals.evaluators import (
    OutputEvaluator,
    HelpfulnessEvaluator,
    GoalSuccessRateEvaluator,
    ToolSelectionAccuracyEvaluator,
    ToolParameterAccuracyEvaluator,
    TrajectoryEvaluator
)
from agents.tools import NSWFuelClient, geocode_location
from agents.models import Coordinates
from agents.prompts import (
    LOCATION_ASSISTANT_PROMPT,
    FUEL_ASSISTANT_PROMPT,
    DIRECTIONS_ASSISTANT_PROMPT,
)


MODEL_ID = "gpt-5.4-mini"


# Create a test agent instance
test_agent = Agent(
    system_prompt=LOCATION_ASSISTANT_PROMPT,
    tools=[geocode_location],
    model=MODEL_ID
)


# Create test cases for evaluation
test_cases = [
    Case(
        name="Geoencoding - Address Search",
        input="Nearest fuel station to 125 Denison St, Hamilton NSW 2303",
        expected_output=Coordinates(
            latitude=-32.925096699345, 
            longitude=151.74690855951,
        ),
        metadata={
            "goal": "Find recipes using specified ingredients",
            "expected_tools": ["geocode_location"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "125 Denison St, Hamilton NSW 2303"
                }
            }
        }
    )
]