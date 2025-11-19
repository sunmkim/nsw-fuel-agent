import os
from typing import Tuple, List, Dict
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.multiagent import Swarm
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import NSWFuelClient, geocode_location
from memory.utils import create_memory_resource, create_memory_session
from prompts import SYSTEM_PROMPT, FUEL_ASSISTANT_PROMPT, DIRECTIONS_ASSISTANT_PROMPT
from dotenv import load_dotenv
load_dotenv()


# initialize runtime app
app = BedrockAgentCoreApp()

# create a liteLLM model for OpenAI's gpt-5-nano
model = OpenAIModel(
    client_args={
        "api_key": os.getenv("OPENAI_API_KEY")
    },
    model_id="gpt-5"
)

# set up tools for our specialized agents
fuel_tools = NSWFuelClient()

# get Mapbox tools by creating a Mapbox MCP client 
streamable_http_mcp_client = MCPClient(
    lambda: streamablehttp_client(
        url="https://mcp.mapbox.com/mcp",
        headers={"Authorization": f"Bearer {os.getenv('MAPBOX_API_KEY')}"}
    ),
    tool_filters={"allowed": [
        "directions_tool", 
        "reverse_geocode_tool",
    ]}
)

@app.entrypoint
async def invoke_agent(payload: Dict):
    # create memory manager and user session
    # memory = create_memory_resource(
    #     memory_name=MEMORY_NAME
    # )
    # user_session = create_memory_session(
    #     actor_id=ACTOR_ID,
    #     session_id=SESSION_ID,
    #     memory_id=memory.id
    # )

    # get user input prompt
    user_input = payload.get("prompt")
    print(f"User query: '{user_input}'")

    # Create specialized agents
    fuel_agent = Agent(
        name="fuel_agent",
        description="Agent to get fuel prices for a given location or fuel station",
        model=model,
        system_prompt=FUEL_ASSISTANT_PROMPT,
        tools=[
            geocode_location,
            fuel_tools.get_prices_for_location, 
            fuel_tools.get_nearby_prices, 
            fuel_tools.get_price_at_station
        ]
    )

    with streamable_http_mcp_client:
        mapbox_tools = streamable_http_mcp_client.list_tools_sync()
            
        # Create the directions agent with tools from Mapbox MCP server
        directions_agent = Agent(
            name="directions_agent",
            description="Agent to provide directions",
            model=model,
            system_prompt=DIRECTIONS_ASSISTANT_PROMPT,
            tools=[mapbox_tools, geocode_location],
        )

        # create agent swarm
        swarm = Swarm(
            [fuel_agent, directions_agent],
            max_handoffs=8,
            max_iterations=5,
            execution_timeout=350.0,  # 10 minutes
            node_timeout=150.0,       # 2.5 minutes per agent
            repetitive_handoff_detection_window=8,  # There must be >= 3 unique agents in the last 8 handoffs
            repetitive_handoff_min_unique_agents=2
        )

        try:
            tool_name = None

            async for event in swarm.stream_async(user_input):
                 # Track node execution
                if event.get("type") == "multiagent_node_start":
                    log_str = f"🔄 Agent '{event['node_id']}' started working..."
                    print(log_str)
                    yield log_str

                # Monitor agent events, including tool use
                elif event.get("type") == "multiagent_node_stream":
                    inner_event = event["event"]
                    if "current_tool_use" in inner_event and tool_name != inner_event["current_tool_use"]["name"] and inner_event["current_tool_use"]["name"] != "handoff_to_agent":
                        tool_name = inner_event["current_tool_use"]["name"]
                        yield f"🛠️ - Using tool: {tool_name}"
                    if "data" in inner_event:
                        yield inner_event["data"]

                # Track handoffs
                elif event.get("type") == "multiagent_handoff":
                    from_nodes = ", ".join(event['from_node_ids'])
                    to_nodes = ", ".join(event['to_node_ids'])
                    log_str = f"🔀 Handoff: {from_nodes} → {to_nodes}"
                    print(log_str)
                    yield log_str

                # Get final result
                elif event.get("type") == "multiagent_result":
                    result = event["result"]
                    print(f"Swarm complete status: {result.status}")

        except Exception as err:
            raise err
    

if __name__ == "__main__":
    print("Agent is running...")
    app.run()