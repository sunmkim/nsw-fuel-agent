import os
import requests
import json
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from strands import tool
from dotenv import load_dotenv 
load_dotenv()



class NSWFuelClient():
    def __init__(self):
        self.mapbox_access_token = os.getenv("MAPBOX_ACCESS_TOKEN")
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
            print("Status code: ", status_code)

    def _get_current_utc(self) -> str:
        """
        Return current UTC date and time as a timezone-aware datetime.
        """
        now = datetime.now(timezone.utc)

        # Format to dd/MM/yyyy hh:mm:ss AM/PM (e.g., 15/11/2025 07:45:12 AM)
        return now.strftime("%d/%m/%Y %I:%M:%S %p")
    

    def _geocode_location(self, postcode: str) -> Tuple[float, float]:
        """Helper function to convert a location into its latitute and longitude"""
    
        url = f"https://api.mapbox.com/search/geocode/v6/forward?q=Postcode {postcode}, NSW&country=AU&limit=1&access_token={self.mapbox_access_token}"
        status_code, resp = self.get(url=url)

        if status_code == 200:
            return resp["features"][0]["geometry"]["coordinates"][::-1]
        else:
            print(f"Failed to geocode postcode: {postcode}")


    @tool
    def get_prices_for_location(self, postcode: str, fueltype: str, brands: List[str]) -> Dict[str, List]:
        url = f"{self.base_url}/FuelPriceCheck/v2/fuel/prices/location"

        payload = {
            "fueltype": fueltype,
            "brand": brands,
            "namedlocation": postcode,
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
        return response


    @tool
    def get_nearby_prices(self, postcode: str, radius: int, fueltype: str, brands: List[str]) -> Dict[str, List[Dict]]:
        url = f"{self.base_url}/FuelPriceCheck/v2/fuel/prices/nearby"
        lat, long = self._geocode_location(postcode)
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
            "latitude": str(lat),
            "longitude": str(long),
            "radius": str(radius),
            "sortby": "Price",
            "sortascending": "true"
        }
        status_code, response = self.post(url, data=json.dumps(payload), headers=headers)
        return response


    @tool
    def get_price_at_station(self, station_code: str) -> Dict[str, List[Dict]]:
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
            return response

    


# if __name__ == "__main__":
#     fuel_client = NSWFuelClient()

    # resp = fuel_client.get_fuel_prices_for_location(
    #     postcode="2065",
    #     fueltype="P95",
    #     brands=["Caltex", "Shell", "BP"]
    # )
    # resp = fuel_client.get_nearby_prices(
    #     postcode="2065",
    #     radius=4,
    #     fueltype="P95",
    #     brands=["Caltex", "Shell", "BP"]
    # )

    # resp = fuel_client.get_price_at_station(station_code="20594")
    # print(resp)
