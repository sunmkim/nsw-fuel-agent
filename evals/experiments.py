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
    FaithfulnessEvaluator,
    ResponseRelevanceEvaluator,
    ToolCalled,
)
from cases import (
    CLARIFICATION_CASES,
    LOCATION_CASES,
    FUEL_CASES,
    STATION_LOOKUP_CASES,
    DIRECTIONS_CASES,
)

# ── Experiments ───────────────────────────────────────────────────────────────

# Verifies that the agent asks for location instead of calling tools
# when the user query contains no location information.
CLARIFICATION_EXPERIMENT = Experiment(
    cases=CLARIFICATION_CASES,
    evaluators=[
        HelpfulnessEvaluator(),
        GoalSuccessRateEvaluator(),
        ToolSelectionAccuracyEvaluator(),    # expected_tools=[] — confirms no tools fired
        ResponseRelevanceEvaluator(),        # confirms response is topically about location
        OutputEvaluator(
            rubric=(
                "Pass if the response explicitly asks the user for their location or current "
                "address in New South Wales before proceeding. "
                "Score 1.0 if the agent clearly requests a NSW location (suburb, postcode, "
                "street address, or landmark) and does not attempt to answer the fuel query "
                "without one. "
                "Score 0.5 if the agent asks a clarifying question but it is ambiguous or "
                "not specifically about NSW location. "
                "Score 0.0 if the agent answers without asking for location, refuses to help, "
                "or asks for something other than location (e.g., fuel type, brand)."
            )
        ),
    ]
)

LOCATION_EXPERIMENT = Experiment(
    cases=LOCATION_CASES,
    evaluators=[
        ToolCalled("geocode_location"),      # deterministic: must call geocode
        ToolSelectionAccuracyEvaluator(),
        ToolParameterAccuracyEvaluator(),
        OutputEvaluator(
            rubric=(
                "Pass if the returned coordinates are within 0.01 degrees of the expected "
                "latitude and longitude. Score 1.0 for an exact match, 0.5 if within 0.01 "
                "degrees, 0.0 if further away or no coordinates returned."
            )
        ),
    ]
)

FUEL_EXPERIMENT = Experiment(
    cases=FUEL_CASES,
    evaluators=[
        HelpfulnessEvaluator(),
        GoalSuccessRateEvaluator(),
        ToolSelectionAccuracyEvaluator(),
        ToolParameterAccuracyEvaluator(),
        FaithfulnessEvaluator(),             # prices in response must match tool output, no hallucination
        ToolCalled("geocode_location"),      # geocoding must precede every location-based fuel lookup
        OutputEvaluator(
            rubric=(
                "Pass if the response lists fuel stations with their prices in ascending price "
                "order (cheapest first). Each station entry must include: the station name or "
                "brand, the address or suburb, and the price in cents per litre (c/L). "
                "Score 1.0 if stations are correctly sorted cheapest-first, prices are present "
                "in numeric form, and at least 2 stations are listed. "
                "Score 0.5 if prices are present but ordering is unclear or only one station "
                "is listed when multiple were expected. "
                "Score 0.0 if no prices are shown, prices are fabricated, or the response "
                "only describes what it would do rather than providing results."
            )
        ),
    ]
)

# Station-code lookups skip geocoding by design, so they live in their own
# experiment without ToolCalled("geocode_location").
STATION_LOOKUP_EXPERIMENT = Experiment(
    cases=STATION_LOOKUP_CASES,
    evaluators=[
        HelpfulnessEvaluator(),
        GoalSuccessRateEvaluator(),
        ToolSelectionAccuracyEvaluator(),
        ToolParameterAccuracyEvaluator(),
        FaithfulnessEvaluator(),             # reported prices must match get_price_at_station output
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
        ToolCalled("geocode_location"),      # geocoding is required before directions_tool
        ToolCalled("directions_tool"),       # confirms Mapbox MCP was actually invoked
        OutputEvaluator(
            rubric=(
                "Pass if the response provides structured driving directions including all of "
                "the following: (1) estimated distance in kilometres, (2) estimated driving "
                "time in minutes, (3) a route summary or street name summary, and (4) at least "
                "two numbered turn-by-turn steps. "
                "Score 1.0 if all four components are present and clearly readable. "
                "Score 0.5 if the response provides a general route description with distance "
                "and time but omits numbered steps or vice versa. "
                "Score 0.0 if the response is a refusal, vague description without directions, "
                "or is missing both distance and time information."
            )
        ),
    ]
)
