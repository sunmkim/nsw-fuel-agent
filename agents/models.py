from typing import List, Optional
from pydantic import BaseModel, Field



class Price(BaseModel):
    station_code: str = Field(description="Code value associated with the station for this price")
    fueltype: str = Field(description="Type of fuel")
    price: float = Field(description="Price of the associated fueltype, in AUD per litre")
    last_updated: str = Field(description="Date time of the most recent price of fuel")


class Coordinates(BaseModel):
    latitude: float = Field(description="Latitude of the given address, as float")
    longitude: float = Field(description="Longitude of the given address, as float")


class Station(BaseModel):
    name: str = Field(description="Name of the service station")
    brand: str = Field(description="Station brand, e.g. BP, Shell, 7-Eleven, etc")
    brandid: Optional[str] = Field(default=None, description="Unique identifier for the brand")
    address: str = Field(description="Address of the station")
    coordinates: Coordinates
    distance: Optional[float] = None
    station_code: str = Field(description="Code value associated with that station")
    stationid: Optional[str] = Field(default=None, description="Unique identifier for the station")
    prices: List[Price]
    