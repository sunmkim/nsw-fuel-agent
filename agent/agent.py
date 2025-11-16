import os
from strands import Agent, tool
from tools import NSWFuelClient


fuel_tools = NSWFuelClient()
agent = Agent(
    tools=[
        fuel_tools.get_prices_for_location, 
        fuel_tools.get_nearby_prices, 
        fuel_tools.get_price_at_station
    ]
)