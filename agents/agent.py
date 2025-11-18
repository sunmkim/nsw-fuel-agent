import os
import asyncio
from typing import Tuple, List, Dict
from strands import Agent
from strands.models.openai import OpenAIModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import fuel_price_assistant, directions_assistant
from memory.utils import create_memory_resource, create_memory_session
from prompts import SYSTEM_PROMPT
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


# to debug agents
def debugger_callback_handler(**kwargs):
    # Print the values in kwargs so that we can see everything
    print(kwargs)


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
    
    # define our agent
    agent = Agent(
        model=model,
        description="You are an orchestrator agent helping to assist the user regarding fuel prices in NSW.",
        system_prompt=SYSTEM_PROMPT,
        tools=[
            fuel_price_assistant,
            directions_assistant,
        ],
        # hooks=[MemoryHook(ACTOR_ID, SESSION_ID, user_session)],
        # callback_handler=debugger_callback_handler,
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