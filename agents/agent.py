import os
from typing import Tuple, List, Dict
from strands import Agent
from strands.models.litellm import LiteLLMModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import fuel_price_assistant, mapbox_assistant, geocode_location
from prompts import SYSTEM_PROMPT
from dotenv import load_dotenv
load_dotenv()


# initialize runtime app
app = BedrockAgentCoreApp()

# create a liteLLM model for OpenAI's gpt-5-nano
model = LiteLLMModel(
    client_args={
        "api_key": os.getenv("OPENAI_API_KEY")
    },
    model_id="openai/gpt-5-nano"
)

# # define our Mapbox MCP client 
# streamable_http_mcp_client = MCPClient(
#     lambda: streamablehttp_client(
#         url="https://mcp.mapbox.com/mcp",
#         headers={"Authorization": f"Bearer {os.getenv('MAPBOX_ACCESS_TOKEN')}"}
#     )
# )

# to debug agents
def debugger_callback_handler(**kwargs):
    # Print the values in kwargs so that we can see everything
    print(kwargs)


@app.entrypoint
async def invoke_agent(payload: Dict):
  
            
    # define our agent
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            geocode_location,
            mapbox_assistant,
            fuel_price_assistant
        ]
        # callback_handler=debugger_callback_handler,
        # tool_executor=SequentialToolExecutor(),
    )

    user_input = payload.get("prompt")
    print(f"User query: '{user_input}'")

    tool_name = None

    try:
        async for event in agent.stream_async(user_input):
            if (
                "current_tool_use" in event
                and event["current_tool_use"].get("name") != tool_name
            ):
                tool_name = event["current_tool_use"]["name"]
                yield f"Used tool: {tool_name}"

            if "data" in event:
                yield event["data"]
    except Exception as err:
        yield f"Error: {str(err)}"
    

if __name__ == "__main__":
    print("Agent is running...")
    app.run()