import os
import requests
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from models import Station, Coordinates, Price
from prompts import FUEL_ASSISTANT_PROMPT, DIRECTIONS_ASSISTANT_PROMPT
from dotenv import load_dotenv 
load_dotenv()

logger = logging.getLogger(__name__)


@tool
def geocode_location(address: str, mapbox_access_token: str = os.getenv("MAPBOX_API_KEY")) -> Tuple[str, List[float]]:
    """
    Helper function to convert a location into its latitute and longitude

    :param address: NSW address
    :return: Pydantic model called Coordinates, a named tuple of postcode and latitude and longitude of the input address
    """

    url = f"https://api.mapbox.com/search/geocode/v6/forward?q={address}&country=AU&limit=1&access_token={mapbox_access_token}"
    
    try:
        response = requests.get(url)
        resp_obj = json.loads(response.text)
    except Exception as err:
        raise err

    if response.status_code == 200:
        postcode = resp_obj["features"][0]["properties"]["context"]["postcode"]["name"]
        coordinates =  resp_obj["features"][0]["geometry"]["coordinates"][::-1]
        logger.info(f"Geocoded address '{address}' to postcode {postcode}, lat: {coordinates[0]}, long: {coordinates[1]}")
        return Coordinates(latitude=coordinates[0], longitude=coordinates[1])
    else:
        logger.error(f"Failed to geocode postcode/address: {address}")



class NSWFuelClient():
    def __init__(self):
        self.base_url = os.getenv("NSW_API_BASE_URL")
        self.fuel_api_token = self._get_access_token()

    def get(self, url: str, headers: Dict = None, params: Dict = None, data: Dict = None):
        try:
            response = requests.get(url, headers=headers, data=data, params=params)
            resp_obj = json.loads(response.text)
            return response.status_code, resp_obj
        except Exception as err:
            raise err

    def post(self, url: str, headers: Dict = None, data: Dict = None):
        try:
            response = requests.post(url, data=data, headers=headers)
            resp_obj = json.loads(response.text)
            return response.status_code, resp_obj
        except Exception as err:
            raise err

    def _get_access_token(self) -> str:
        """
        Retrieve access token for NSW Fuel API
        """
        url = f"{self.base_url}/oauth/client_credential/accesstoken"
        querystring = {
            "grant_type": "client_credentials"
        }
        headers = {
            'content-type': "application/json",
            'authorization': os.getenv("NSW_AUTH_HEADER")
        }

        status_code, response = self.get(url, headers=headers, params=querystring)
        if status_code == 200:
            return response['access_token']
        else:
            logger.warning(f"Status code: {status_code}")

    def _get_current_utc(self) -> str:
        """
        Return current UTC date and time as a timezone-aware datetime.
        """
        now = datetime.now(timezone.utc)

        # Format to dd/MM/yyyy hh:mm:ss AM/PM (e.g., 15/11/2025 07:45:12 AM)
        return now.strftime("%d/%m/%Y %I:%M:%S %p")


    @tool
    def get_prices_for_location(self, postcode: str, latitude: float, longitude: float, fueltype: str, brands: List[str]) -> Dict[str, List]:
        """
        Returns current fuel prices for a single fuel type and a named location (postcode).

        :param postcode: The NSW postcode to query fuel prices for (e.g., "2065" or "2000")
        :param latitude: Latitude coordinate for given location in NSW
        :param longitude: Longitude coordinate for given location in NSW
        :param fueltype: The fuel type to search for (e.g., "P95", "P98", "E10", "Diesel")
        :param brands: List of fuel brand names to filter results (e.g., ["Caltex", "Shell", "BP"])
        :return: Dictionary containing fuel price data for the specified location and fuel type,
                 sorted by price in ascending order
        """
        url = f"{self.base_url}/FuelPriceCheck/v2/fuel/prices/location"

        payload = {
            "fueltype": fueltype,
            "brand": brands,
            "namedlocation": postcode,
            "referencepoint": {
                "latitude": str(latitude),
                "longitude": str(longitude)
            },
            "sortby": "Price",
            "sortascending": "true"
        }


        headers = {
            'content-type': 'application/json; charset=utf-8',
            'authorization': f"Bearer {self.fuel_api_token}",
            'apikey': os.getenv("NSW_API_KEY"),
            'transactionid': "1",
            'requesttimestamp': self._get_current_utc()
        }

        status_code, response = self.post(url, data=json.dumps(payload), headers=headers)

        if status_code == 200:
            stations = []
            grouped_prices = defaultdict(list)
            for price in response["prices"]:
                station_code = str(price["stationcode"])
                if station_code is None:
                    continue
                grouped_prices[station_code].append(
                    Price(
                        station_code=station_code,
                        fueltype=price["fueltype"], 
                        price=price["price"], 
                        last_updated=price["lastupdated"]
                    )
                )    
            prices_dict = dict(grouped_prices)

            for station in response["stations"]:
                stations.append(
                    Station(
                        name=station["name"], 
                        brand=station["brand"], 
                        address=station["address"],
                        coordinates=Coordinates(
                            latitude=station["location"]["latitude"], 
                            longitude=station["location"]["longitude"]
                        ),
                        distance=station["location"]["distance"],
                        station_code=str(station["code"]),
                        prices=prices_dict.get(str(station["code"]))
                    )
                )
            return stations
        # return response


    @tool
    def get_nearby_prices(self, postcode: str, latitude: float, longitude: float, radius: int, fueltype: str, brands: List[str]) -> Dict[str, List[Dict]]:
        """
        Returns fuel prices for multiple fuel stations within a specified radius of a location.

        :param address: The NSW postcode to query fuel prices around (e.g., "2065" or "2000")
        :param latitude: Latitude coordinate for given location in NSW
        :param longitude: Longitude coordinate for given location in NSW
        :param radius: Search radius in kilometers (e.g., 4)
        :param fueltype: The fuel type to search for (e.g., "P95", "P98", "E10", "Diesel")
        :param brands: List of fuel brand names to filter results (e.g., ["Caltex", "Shell", "BP"])
        :return: Dictionary containing fuel price data for nearby stations, sorted by price in ascending order
        """
        url = f"{self.base_url}/FuelPriceCheck/v2/fuel/prices/nearby"

        headers = {
            'content-type': 'application/json; charset=utf-8',
            'authorization': f"Bearer {self.fuel_api_token}",
            'apikey': os.getenv("NSW_API_KEY"),
            'transactionid': "1",
            'requesttimestamp': self._get_current_utc()
        }
        payload = {
            "fueltype": fueltype,
            "brand": brands,
            "namedlocation": postcode,
            "latitude": str(latitude),
            "longitude": str(longitude),
            "radius": str(radius),
            "sortby": "Price",
            "sortascending": "true"
        }
        status_code, response = self.post(url, data=json.dumps(payload), headers=headers)

        if status_code == 200:
            stations = []
            grouped_prices = defaultdict(list)
            for price in response["prices"]:
                station_code = str(price["stationcode"])
                if station_code is None:
                    continue
                grouped_prices[station_code].append(
                    Price(
                        station_code=station_code,
                        fueltype=price["fueltype"], 
                        price=price["price"], 
                        last_updated=price["lastupdated"]
                    )
                )    
            prices_dict = dict(grouped_prices)

            for station in response["stations"]:
                stations.append(
                    Station(
                        name=station["name"], 
                        brand=station["brand"], 
                        address=station["address"],
                        coordinates=Coordinates(
                            latitude=station["location"]["latitude"], 
                            longitude=station["location"]["longitude"]
                        ),
                        distance=station["location"]["distance"],
                        station_code=str(station["code"]),
                        prices=prices_dict.get(str(station["code"]))
                    )
                )
            return stations


    @tool
    def get_price_at_station(self, station_code: str) -> Dict[str, List[Dict]]:
        """
        Retrieve the current fuel prices for a single station by station code.

        This calls the NSW Fuel API endpoint for a specific station and returns
        the parsed JSON response when the request succeeds.

        :param station_code: The unique station identifier used by the NSW API
                             (passed into the endpoint path, e.g. "20594").
        :return: Parsed JSON response as a dictionary containing price data
                 for the requested station. Returns None if the request fails.
        """

        url = f"{self.base_url}/FuelPriceCheck/v2/fuel/prices/station/{station_code}"

        querystring = {"state": "NSW"}

        headers = {
            'content-type': "application/json",
            'authorization': f"Bearer {self.fuel_api_token}",
            'apikey': os.getenv("NSW_API_KEY"),
            'transactionid': "2",
            'requesttimestamp': self._get_current_utc()
        }

        status_code, response = self.get(url=url, headers=headers, params=querystring)
        
        if status_code == 200:
            prices = []
            for price in response["prices"]:
                prices.append(
                    Price(
                        station_code=station_code,
                        fueltype=price["fueltype"], 
                        price=price["price"], 
                        last_updated=price["lastupdated"]
                    )
                )
            return prices

@tool
def fuel_price_assistant(query: str) -> str:
    """
    Process and respond to research-related queries.

    Args:
        query: A research question requiring factual information

    Returns:
        A detailed research answer with citations
    """

    print("Routed to Fuel Price Assistant")

    # create a OpenAI model for gpt-5-nano
    fuel_model = OpenAIModel(
        client_args={
            "api_key": os.getenv("OPENAI_API_KEY")
        },
        model_id="gpt-5"
    )
    try:
        fuel_tools = NSWFuelClient()

        fuel_agent = Agent(
            name="fuel_agent",
            description="Agent to get fuel prices for a given location or fuel station",
            model=fuel_model,
            system_prompt=FUEL_ASSISTANT_PROMPT,
            tools=[
                geocode_location,
                fuel_tools.get_prices_for_location, 
                fuel_tools.get_nearby_prices, 
                fuel_tools.get_price_at_station
            ]
        )

        # Call the agent and return its response
        response = fuel_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in fuel pricing assistant: {str(e)}"


@tool
def directions_assistant(query: str) -> str:
    """
    Process and respond to queries related to driving directions using a specialized agent using Mapbox tools.
    Args:
        query: A research question requiring factual information

    Returns:
        A detailed research answer with citations
    """

    # define our Mapbox MCP client 
    streamable_http_mcp_client = MCPClient(
        lambda: streamablehttp_client(
            url="https://mcp.mapbox.com/mcp",
            headers={"Authorization": f"Bearer {os.getenv('MAPBOX_API_KEY')}"}
        ),
        tool_filters={"allowed": [
            "directions_tool", 
            "reverse_geocode_tool", 
            # "static_map_image_tool", 
            # "search_and_geocode_tool"
        ]}
    )
    mapbox_model = OpenAIModel(
        client_args={
            "api_key": os.getenv("OPENAI_API_KEY")
        },
        model_id="gpt-5"
    )
    with streamable_http_mcp_client:
        mapbox_tools = streamable_http_mcp_client.list_tools_sync()
            
        try:
            # Create the directions agent with tools from Mapbox MCP server
            directions_agent = Agent(
                name="directions_agent",
                description="Agent to provide directions",
                model=mapbox_model,
                system_prompt=DIRECTIONS_ASSISTANT_PROMPT,
                tools=[mapbox_tools, geocode_location],
            )
            response = directions_agent(query)
            return str(response)
        except Exception as e:
            return f"Error processing your mathematical query: {str(e)}"