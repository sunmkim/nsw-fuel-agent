from typing import List, Optional
from pydantic import BaseModel, Field



class Price(BaseModel):
    """A single fuel price record for a station.

    Attributes
    - station_code: Station identifier (as provided by the NSW API).
    - fueltype: Fuel code (e.g. `U91`, `P95`, `DL`).
    - price: Numeric price value in AUD per litre (or relevant unit).
    - last_updated: Timestamp when this price was last updated (string).
    """

    station_code: str = Field(description="Code value associated with the station for this price")
    fueltype: str = Field(description="Type of fuel")
    price: float = Field(description="Price of the associated fueltype, in AUD per litre")
    last_updated: str = Field(description="Date time of the most recent price of fuel")


class Coordinates(BaseModel):
    """Geographic coordinates for a location.

    Attributes
    - latitude: Decimal degrees north.
    - longitude: Decimal degrees east.
    """

    latitude: float = Field(description="Latitude of the given address, as float")
    longitude: float = Field(description="Longitude of the given address, as float")


class Station(BaseModel):
    """Information about a fuel station and its current prices.

    Attributes
    - name: Station display name.
    - brand: Brand name (e.g. "BP", "Shell").
    - brandid: Optional internal brand identifier.
    - address: Human-readable address.
    - coordinates: Location of the station.
    - distance: Optional distance (e.g. from a query point) in kilometres.
    - station_code: Station identifier used by NSW APIs.
    - stationid: Optional internal station identifier.
    - prices: List of `Price` records associated with the station.
    """

    name: str = Field(description="Name of the service station")
    brand: str = Field(description="Station brand, e.g. BP, Shell, 7-Eleven, etc")
    brandid: Optional[str] = Field(default=None, description="Unique identifier for the brand")
    address: str = Field(description="Address of the station")
    coordinates: Coordinates
    distance: Optional[float] = None
    station_code: str = Field(description="Code value associated with that station")
    stationid: Optional[str] = Field(default=None, description="Unique identifier for the station")
    prices: List[Price]
    