import os
from typing import Tuple, List, Dict
from strands import Agent, tool
from strands.models.litellm import LiteLLMModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import NSWFuelClient
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

@app.entrypoint
def invoke_agent(payload: Dict):
    fuel_tools = NSWFuelClient()
    # define our agent
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            fuel_tools.get_prices_for_location, 
            fuel_tools.get_nearby_prices, 
            fuel_tools.get_price_at_station
        ]
    )

    user_input = payload.get("prompt")
    print(f"User query: '{user_input}'")

    result = agent(user_input)
    return {"result": result.message}
    

if __name__ == "__main__":
    print("Agent running...")
    app.run()