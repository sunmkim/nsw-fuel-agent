import os
from strands import Agent
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient
from dotenv import load_dotenv 
load_dotenv()


streamable_http_mcp_client = MCPClient(
    lambda: streamablehttp_client(
        url="https://mcp.mapbox.com/mcp",
        headers={"Authorization": f"Bearer {os.getenv('MAPBOX_ACCESS_TOKEN')}"}
    )
)

# Manual approach
with streamable_http_mcp_client:
    tools = streamable_http_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
    agent("Geocode the following postcode in NSW, Australia: 2065. Return only latitude and longitude as a Python tuple.")

