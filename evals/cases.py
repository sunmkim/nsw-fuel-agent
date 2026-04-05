import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
from typing import List
from strands_evals import Case
from models import Coordinates

# ── Clarification Cases ───────────────────────────────────────────────────────
# Cases where the agent must ask the user for their location before calling tools.
# Per the system prompt: "Assistant will always ask user for their location
# when location is not given in user query."

CLARIFICATION_CASES: List[Case] = [
    Case(
        name="clarification-missing-location-01",
        input="Get prices for Unleaded 91 fuel near me",
        metadata={
            "category": "clarification",
            "subcategory": "missing-location",
            "difficulty": "easy",
            "tags": ["u91", "missing-location"],
            "goal": "Agent must ask the user for their location — no tools should be called",
            "expected_tools": [],
        }
    ),
    Case(
        name="clarification-missing-location-02",
        input="Find me the cheapest fuel",
        metadata={
            "category": "clarification",
            "subcategory": "missing-location",
            "difficulty": "easy",
            "tags": ["missing-location", "generic-query"],
            "goal": "Agent must ask the user for their location — no tools should be called",
            "expected_tools": [],
        }
    ),
    Case(
        name="clarification-missing-location-03",
        input="Are there any LPG stations nearby?",
        metadata={
            "category": "clarification",
            "subcategory": "missing-location",
            "difficulty": "easy",
            "tags": ["lpg", "missing-location"],
            "goal": "Agent must ask the user for their location — no tools should be called",
            "expected_tools": [],
        }
    ),
]

# ── Location Cases ────────────────────────────────────────────────────────────

LOCATION_CASES: List[Case] = [
    Case(
        name="location-geocode-01",
        input="Nearest fuel station to 125 Denison St, Hamilton NSW 2303",
        expected_output=Coordinates(
            latitude=-32.9251,
            longitude=151.7469,
        ),
        metadata={
            "category": "location",
            "subcategory": "geocode",
            "difficulty": "easy",
            "tags": ["street-address", "newcastle"],
            "goal": "Geocode a full street address to latitude/longitude coordinates",
            "expected_tools": ["geocode_location"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "125 Denison St, Hamilton NSW 2303"
                }
            }
        }
    ),
    Case(
        name="location-geocode-02",
        input="Nearest fuel to Newtown, Sydney",
        expected_output=Coordinates(
            latitude=-33.8976,
            longitude=151.1787,
        ),
        metadata={
            "category": "location",
            "subcategory": "geocode",
            "difficulty": "easy",
            "tags": ["suburb", "sydney"],
            "goal": "Geocode a suburb name to latitude/longitude coordinates",
            "expected_tools": ["geocode_location"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "Newtown, Sydney NSW"
                }
            }
        }
    ),
    Case(
        name="location-geocode-03",
        input="Find fuel near postcode 2000",
        expected_output=Coordinates(
            latitude=-33.8688,
            longitude=151.2093,
        ),
        metadata={
            "category": "location",
            "subcategory": "geocode",
            "difficulty": "easy",
            "tags": ["postcode", "sydney-cbd"],
            "goal": "Geocode a NSW postcode to latitude/longitude coordinates",
            "expected_tools": ["geocode_location"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "2000 NSW"
                }
            }
        }
    ),
    Case(
        name="location-geocode-04",
        input="Where is the Sydney Opera House?",
        expected_output=Coordinates(
            latitude=-33.8568,
            longitude=151.2153,
        ),
        metadata={
            "category": "location",
            "subcategory": "geocode",
            "difficulty": "easy",
            "tags": ["landmark", "sydney"],
            "goal": "Geocode a well-known Sydney landmark to latitude/longitude coordinates",
            "expected_tools": ["geocode_location"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "Sydney Opera House NSW"
                }
            }
        }
    ),
]

# ── Fuel Cases ────────────────────────────────────────────────────────────────

FUEL_CASES: List[Case] = [
    Case(
        name="fuel-location-p95-01",
        input="Find cheapest P95 near 125 Denison St, Hamilton NSW 2303",
        metadata={
            "category": "fuel",
            "subcategory": "location-prices",
            "difficulty": "medium",
            "tags": ["p95", "newcastle", "location-search"],
            "goal": "Return a list of stations with P95 prices sorted cheapest-first for the given postcode",
            "expected_tools": ["geocode_location", "get_prices_for_location"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "125 Denison St, Hamilton NSW 2303"
                },
                "get_prices_for_location": {
                    "postcode": "2303",
                    "fueltype": "P95"
                }
            }
        }
    ),
    Case(
        name="fuel-location-diesel-01",
        input="What's the cheapest diesel in Parramatta 2150?",
        metadata={
            "category": "fuel",
            "subcategory": "location-prices",
            "difficulty": "easy",
            "tags": ["diesel", "parramatta", "location-search"],
            "goal": "Return diesel (DL) prices sorted cheapest-first for Parramatta postcode 2150",
            "expected_tools": ["geocode_location", "get_prices_for_location"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "Parramatta NSW 2150"
                },
                "get_prices_for_location": {
                    "postcode": "2150",
                    "fueltype": "DL"
                }
            }
        }
    ),
    Case(
        name="fuel-location-u91-01",
        input="Show me the cheapest unleaded 91 near Circular Quay 2000",
        metadata={
            "category": "fuel",
            "subcategory": "location-prices",
            "difficulty": "easy",
            "tags": ["u91", "sydney-cbd", "location-search"],
            "goal": "Return U91 prices sorted cheapest-first for Sydney CBD postcode 2000",
            "expected_tools": ["geocode_location", "get_prices_for_location"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "Circular Quay NSW 2000"
                },
                "get_prices_for_location": {
                    "postcode": "2000",
                    "fueltype": "U91"
                }
            }
        }
    ),
    Case(
        name="fuel-nearby-e10-01",
        input="Find E10 stations within 3km of Chatswood 2067",
        metadata={
            "category": "fuel",
            "subcategory": "nearby-prices",
            "difficulty": "medium",
            "tags": ["e10", "chatswood", "radius-search"],
            "goal": "Return E10 stations within a 3km radius of Chatswood, sorted by price",
            "expected_tools": ["geocode_location", "get_nearby_prices"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "Chatswood NSW 2067"
                },
                "get_nearby_prices": {
                    "postcode": "2067",
                    "fueltype": "E10",
                    "radius": 3
                }
            }
        }
    ),
    Case(
        name="fuel-nearby-p98-01",
        input="Find Premium 98 stations within 5km of Bondi Beach",
        metadata={
            "category": "fuel",
            "subcategory": "nearby-prices",
            "difficulty": "medium",
            "tags": ["p98", "bondi", "radius-search"],
            "goal": "Return P98 stations within a 5km radius of Bondi Beach, sorted by price",
            "expected_tools": ["geocode_location", "get_nearby_prices"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "Bondi Beach NSW 2026"
                },
                "get_nearby_prices": {
                    "postcode": "2026",
                    "fueltype": "P98",
                    "radius": 5
                }
            }
        }
    ),
    Case(
        name="fuel-station-01",
        input="What fuel prices are available at station 20594?",
        metadata={
            "category": "fuel",
            "subcategory": "station-price",
            "difficulty": "easy",
            "tags": ["station-lookup", "direct-lookup"],
            "goal": "Return all current fuel prices for station code 20594",
            "expected_tools": ["get_price_at_station"],
            "expected_tool_params": {
                "get_price_at_station": {
                    "station_code": "20594"
                }
            }
        }
    ),
]

# ── Directions Cases ──────────────────────────────────────────────────────────

DIRECTIONS_CASES: list[Case] = [
    Case(
        name="directions-route-01",
        input="How do I drive from Sydney CBD to Parramatta?",
        metadata={
            "category": "directions",
            "subcategory": "route",
            "difficulty": "easy",
            "tags": ["driving", "sydney", "parramatta"],
            "goal": "Geocode both locations then provide turn-by-turn driving directions from Sydney CBD to Parramatta",
            # Per system prompt Example 2: geocode_location is called for each address
            # before passing coordinates to directions_tool.
            "expected_tools": ["geocode_location", "directions_tool"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "Sydney CBD NSW"
                },
                "directions_tool": {
                    "origin": "Sydney CBD NSW",
                    "destination": "Parramatta NSW"
                }
            }
        }
    ),
    Case(
        name="directions-route-02",
        input="How do I drive from Newcastle to Sydney Airport?",
        metadata={
            "category": "directions",
            "subcategory": "route",
            "difficulty": "medium",
            "tags": ["driving", "newcastle", "airport"],
            "goal": "Geocode both locations then provide turn-by-turn driving directions from Newcastle to Sydney Airport",
            # Per system prompt Example 2: geocode_location is called for each address
            # before passing coordinates to directions_tool.
            "expected_tools": ["geocode_location", "directions_tool"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "Newcastle NSW"
                },
                "directions_tool": {
                    "origin": "Newcastle NSW",
                    "destination": "Sydney Airport NSW"
                }
            }
        }
    ),
    Case(
        name="directions-route-03",
        input="Give me driving directions from 351 Windsor Rd, Baulkham Hills NSW 2153 to 64 North Rocks Rd, North Rocks NSW 2151",
        metadata={
            "category": "directions",
            "subcategory": "route",
            "difficulty": "medium",
            "tags": ["driving", "baulkham-hills", "north-rocks", "street-address"],
            "goal": "Geocode both street addresses then provide turn-by-turn driving directions",
            "expected_tools": ["geocode_location", "directions_tool"],
            "expected_tool_params": {
                "geocode_location": {
                    "address": "351 Windsor Rd, Baulkham Hills NSW 2153"
                },
                "directions_tool": {
                    "origin": "351 Windsor Rd, Baulkham Hills NSW 2153",
                    "destination": "64 North Rocks Rd, North Rocks NSW 2151"
                }
            }
        }
    ),
]
