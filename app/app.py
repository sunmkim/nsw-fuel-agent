import json
import os
import re
import requests
import time
import base64
from typing import Dict, Iterator, List

import boto3
import streamlit as st
from streamlit.logger import get_logger

logger = get_logger(__name__)
logger.setLevel("INFO")

WELCOME_MESSAGE = """
Hello there! I am here to help you about service stations across the beautiful state of New South Wales (NSW)! 
I can get you information on fuel types and prices available for each fuel station, and can give you the directions to get there!

You can ask about following fuel types:
- Ethanol 94 (E10)
- Unleaded 91 (U91)
- Ethanol 105 (E85)
- Premium 95 (P95)
- Premium 98 (P98)
- Diesel (DL)
- Premium Diesel (PDL)
- Biodiesel 20 (B20)
- LPG (LPG)
- CNG/NGV (CNG)
- Electric vehicle charge (EV)

Here are some sample locations you can use to get started:
- Bennelong Point, Sydney NSW 2000
- 159-175 Church St, Parramatta NSW 2150
- 107 Maitland Rd, Mayfield NSW 2304
- 200 Crown St, Wollongong NSW 2500
- 102 Jonson St, Byron Bay NSW 2481

First, please provide me your location in NSW so that I may assist you.
"""


# Page config
st.set_page_config(
    page_title="NSW Fuel Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)


def clean_response_text(text: str, show_thinking: bool = True) -> str:
    """Clean and format response text for better presentation"""
    if not text:
        return text

    # Handle the consecutive quoted chunks pattern
    # Pattern: "word1" "word2" "word3" -> word1 word2 word3
    text = re.sub(r'"\s*"', "", text)
    text = re.sub(r'^"', "", text)
    text = re.sub(r'"$', "", text)

    # Replace literal \n with actual newlines
    text = text.replace("\\n", "\n")

    # Replace literal \t with actual tabs
    text = text.replace("\\t", "\t")

    # Clean up multiple spaces
    text = re.sub(r" {3,}", " ", text)

    # Fix newlines that got converted to spaces
    text = text.replace(" \n ", "\n")
    text = text.replace("\n ", "\n")
    text = text.replace(" \n", "\n")

    # Handle numbered lists
    text = re.sub(r"\n(\d+)\.\s+", r"\n\1. ", text)
    text = re.sub(r"^(\d+)\.\s+", r"\1. ", text)

    # Handle bullet points
    text = re.sub(r"\n-\s+", r"\n- ", text)
    text = re.sub(r"^-\s+", r"- ", text)

    # Handle section headers
    text = re.sub(r"\n([A-Za-z][A-Za-z\s]{2,30}):\s*\n", r"\n**\1:**\n\n", text)

    # Clean up multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def parse_streaming_chunk(chunk: str) -> str:
    """Parse individual streaming chunk and extract meaningful content"""
    try:        
        # return chunk as-is
        # logger.info("parse_streaming_chunk: Not JSON, returning as-is")
        return chunk
    except json.JSONDecodeError as e:
        logger.error(f"parse_streaming_chunk: JSON decode error: {e}")
        raise e


def get_agent_runtimes(region: str = "us-east-1") -> List[Dict]:
    """Fetch available agent runtimes from bedrock-agentcore-control"""
    try:
        client = boto3.client("bedrock-agentcore-control", region_name=region)
        response = client.list_agent_runtimes(maxResults=10)

        # Filter only READY agents and sort by name
        ready_agents = [
            agent
            for agent in response.get("agentRuntimes", [])
            if agent.get("status") == "READY"
        ]

        # Sort by most recent update time (newest first)
        ready_agents.sort(key=lambda x: x.get("lastUpdatedAt", ""), reverse=True)

        return ready_agents
    except Exception as e:
        st.error(f"Error fetching agent runtimes: {e}")
        return []

def invoke_agent_streaming(
    prompt: str,
    agent_arn: str,
    region: str = "us-east-1"
) -> Iterator[str]:
    """Invoke agent and yield streaming response chunks"""
    try:
        # header = {
        #     "Content-Type": "application/json"
        # }
        # body = {
        #     "prompt": prompt
        # }
        # URL = "http://localhost:8080/invocations"
        # response = requests.post(url=URL, json=body, headers=header, stream=True)
        
        agentcore_client = boto3.client("bedrock-agentcore", region_name=region)

        logger.info("Using streaming response path")
       
        # invoke agent hosted on AWS
        response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            payload=json.dumps({"prompt": prompt}),
        )

        # for line in response.iter_lines(chunk_size=1):
        
        for line in response["response"].iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                # logger.info(f"Raw line: {line}")
                if line.startswith("data: "):
                    line = line[6:]
                    # Parse and clean each chunk
                    parsed_chunk = parse_streaming_chunk(line)
                    # if "Used assistant" in parsed_chunk:
                    if "started working" in parsed_chunk or "Handoff" in parsed_chunk or "Using tool" in parsed_chunk: 
                        stripped_str = parsed_chunk.strip()
                        cleaned_str = stripped_str.replace('"', '')
                        st.write(f"{cleaned_str}")
                    elif parsed_chunk.strip():  # Only yield non-empty chunks
                        logger.info(f"parsed_chunk:: {parsed_chunk}")
                        yield parsed_chunk
                else:
                    logger.info(
                        f"Line doesn't start with 'data: ', skipping: {line}"
                    )
    except Exception as e:
        yield f"Error invoking agent: {e}"


def main():

    # get available agent runtimes
    available_agents = get_agent_runtimes()
    runtime_arn = None
    for i,agent in enumerate(available_agents):
        if "nsw_fuel_agent" in agent["agentRuntimeId"]:
            print(agent)
            runtime_arn = available_agents[i]['agentRuntimeArn']
            break

    if runtime_arn is None:
        st.error("No suitable agent runtime found. Please check agent deployment.")
        return

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    with st.chat_message("assistant"):
        st.write(WELCOME_MESSAGE)

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
    
        # Add user message to chat history
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message(name="assistant"):
            message_placeholder = st.empty()
            chunk_buffer = ""
            with st.status("AI is working...", expanded=True) as status: 
                try:
                    # Stream the response
                    for chunk in invoke_agent_streaming(
                        prompt,
                        runtime_arn
                    ):
                        # Let's see what we get
                        logger.debug(f"MAIN LOOP: chunk type: {type(chunk)}")
                        logger.debug(f"MAIN LOOP: chunk content: {chunk}")

                        # Ensure chunk is a string before concatenating
                        if not isinstance(chunk, str):
                            logger.info(
                                f"MAIN LOOP: Converting non-string chunk to string"
                            )
                            chunk = str(chunk)

                        # Add chunk to buffer
                        chunk_buffer += chunk

                        # Only update display every few chunks or when we hit certain characters
                        if (
                            len(chunk_buffer) % 3 == 0
                            or chunk.endswith(" ")
                            or chunk.endswith("\n")
                        ):
                            # Clean the accumulated response
                            cleaned_response = clean_response_text(chunk_buffer)
                            message_placeholder.markdown(cleaned_response + " ▌")
                        
                        time.sleep(0.01)  # Reduced delay since we're batching updates

                    # Final response without cursor
                    full_response = clean_response_text(chunk_buffer, True)
        
                    message_placeholder.markdown(full_response)

                except Exception as e:
                    error_msg = f"❌ **Error:** {str(e)}"
                    message_placeholder.markdown(error_msg)
                    full_response = error_msg
                status.update(
                    label="AI completed task!", state="complete", expanded=False
                )
        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )


if __name__ == "__main__":
    main()