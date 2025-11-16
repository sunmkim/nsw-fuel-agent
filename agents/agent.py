import os
from typing import Tuple, List, Dict
from strands import Agent
from strands.models.litellm import LiteLLMModel
from strands.tools.executors import SequentialToolExecutor
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import fuel_price_assistant, geocode_location
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

# to debug agents
def debugger_callback_handler(**kwargs):
    # Print the values in kwargs so that we can see everything
    print(kwargs)


@app.entrypoint
def invoke_agent(payload: Dict):

    streamable_http_mcp_client = MCPClient(
        lambda: streamablehttp_client(
            url="https://mcp.mapbox.com/mcp",
            headers={"Authorization": f"Bearer {os.getenv('MAPBOX_ACCESS_TOKEN')}"}
        )
    )
    with streamable_http_mcp_client:
        mapbox_tools = streamable_http_mcp_client.list_tools_sync()
        # define our agent
        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=[
                geocode_location,
                mapbox_tools,
                fuel_price_assistant
            ]
            # callback_handler=debugger_callback_handler,
            # tool_executor=SequentialToolExecutor(),
        )

        user_input = payload.get("prompt")
        print(f"User query: '{user_input}'")

        result = agent(user_input)
        return {"result": result.message}
    

if __name__ == "__main__":
    print("Agent is running...")
    app.run()