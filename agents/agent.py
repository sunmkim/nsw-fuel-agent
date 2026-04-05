import os
import uuid
import httpx
from typing import Dict
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamable_http_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from memory.utils import setup_memory, create_memory_resource
from memory.MemoryHook import MemoryHook
from tools import NSWFuelClient, geocode_location
from prompts import SYSTEM_PROMPT
from dotenv import load_dotenv
load_dotenv()

# set model
MODEL_ID = "gpt-5.4-mini"

# initialize runtime app
app = BedrockAgentCoreApp()

# unique per microVM instance — stable across multi-turn messages, isolated between sessions
SESSION_ID = str(uuid.uuid4())

# create model for OpenAI's gpt-5-nano
model = OpenAIModel(
    client_args={
        "api_key": os.getenv("OPENAI_API_KEY")
    },
    model_id=MODEL_ID
)

# set up tools for our specialized agents
fuel_tools = NSWFuelClient()



@app.entrypoint
async def invoke_agent(payload: Dict):
    memory_name = "nsw_fuel_agent_memory" 
    actor_id = "nsw_fuel_agent"
    session_id = SESSION_ID

    # get or create memory resource by name
    memory_resource = create_memory_resource(memory_name=memory_name)

    # set up memory session for agent
    memory = setup_memory(
        memory_id=memory_resource.id,
        actor_id=actor_id,
        session_id=session_id,
    )

    # get user input prompt
    user_input = payload.get("prompt")
    print(f"User query: '{user_input}'")

    mcp_header = {"Authorization": f"Bearer {os.getenv('MAPBOX_API_KEY')}"}

    with MCPClient(
        lambda: streamable_http_client(
            url="https://mcp.mapbox.com/mcp",
            http_client=httpx.AsyncClient(headers=mcp_header),
        ),
        tool_filters={"allowed": [
            "directions_tool",
            # "reverse_geocode_tool",
        ]}
    ) as mcp_client:
        directions_tool = mcp_client.list_tools_sync()

        # create single agent with memory
        agent = Agent(
            name="nsw_fuel_agent",
            description="Agent to help answer user questions about fuel prices and location information across gas stations in NSW",
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=[
                geocode_location, 
                fuel_tools.get_prices_for_location, 
                fuel_tools.get_nearby_prices, 
                fuel_tools.get_price_at_station,
                directions_tool,
            ],
            hooks=[MemoryHook(session_id, memory)],
            state={"actor_id": actor_id, "session_id": session_id}
        )

        try:
            tool_name = None
            async for event in agent.stream_async(user_input):
                # Monitor tool use
                if "current_tool_use" in event and tool_name != event["current_tool_use"]["name"]:
                    tool_name = event["current_tool_use"]["name"]
                    yield f"🛠️ - Using tool: {tool_name}"

                # Stream text output
                if "data" in event:
                    yield event["data"]

                # Get final result
                if "result" in event:
                    result = event["result"]
                    print(f"\nAgent work complete status: {result.stop_reason}")

        except Exception as err:
            raise err
    

if __name__ == "__main__":
    print("Agent is running...")
    app.run()