import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))

from strands_evals import Experiment
from strands_evals.evaluators import (
    OutputEvaluator,
    HelpfulnessEvaluator,
    GoalSuccessRateEvaluator,
    ToolSelectionAccuracyEvaluator,
    ToolParameterAccuracyEvaluator,
)
from cases import CLARIFICATION_CASES, LOCATION_CASES, FUEL_CASES, DIRECTIONS_CASES

# ── Experiments ───────────────────────────────────────────────────────────────

# Verifies that the agent asks for location instead of calling tools
# when the user query contains no location information.
CLARIFICATION_EXPERIMENT = Experiment(
    cases=CLARIFICATION_CASES,
    evaluators=[
        HelpfulnessEvaluator(),
        GoalSuccessRateEvaluator(),
        ToolSelectionAccuracyEvaluator(),  # expected_tools is [] — confirms no tools fired
    ]
)

LOCATION_EXPERIMENT = Experiment(
    cases=LOCATION_CASES,
    evaluators=[
        OutputEvaluator(
            rubric=(
                "Pass if the returned coordinates are within 0.01 degrees of the expected "
                "latitude and longitude. Score 1.0 for an exact match, 0.5 if within 0.01 "
                "degrees, 0.0 if further away or no coordinates returned."
            )
        ),
        ToolSelectionAccuracyEvaluator(),
        ToolParameterAccuracyEvaluator(),
    ]
)

FUEL_EXPERIMENT = Experiment(
    cases=FUEL_CASES,
    evaluators=[
        HelpfulnessEvaluator(),
        GoalSuccessRateEvaluator(),
        ToolSelectionAccuracyEvaluator(),
        ToolParameterAccuracyEvaluator(),
    ]
)

# directions_tool is called with geocoded coordinates, so ToolParameterAccuracyEvaluator
# validates that geocode_location was invoked with the right addresses before directions_tool.
DIRECTIONS_EXPERIMENT = Experiment(
    cases=DIRECTIONS_CASES,
    evaluators=[
        HelpfulnessEvaluator(),
        GoalSuccessRateEvaluator(),
        ToolSelectionAccuracyEvaluator(),
        ToolParameterAccuracyEvaluator(),
    ]
)
