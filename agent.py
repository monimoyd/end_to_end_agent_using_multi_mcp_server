# agent.py

import asyncio
import yaml
from core.loop import AgentLoop
from core.session import MultiMCP
import requests
import sseclient
import traceback
import asyncio
import aiohttp
import time

def log(stage: str, msg: str):
    """Simple timestamped console logger."""
    import datetime
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")



async def send_message_async(message: str, tool: str = "send_telegram_message"):
    url = "http://localhost:8000/send"  # Replace with your FastAPI server URL

    params = {"message": message, "tool": tool}  # Parameters as a dictionary

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:  # Use params=
                if response.status == 200:
                    data = await response.json()
                    #print("Success:", data)
                    return data
                else:
                    #print(f"Error: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"An error occurred: {e}")
        return None

async def get_telegram_message():
    url = "http://localhost:8000/get_telegram_message"  # Replace with your FastAPI server URL

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:  # Use params=
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"Error: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"An error occurred: {e}")
        return None


async def main():
    print("🧠 Cortex-R Agent Ready")
    #user_input = input("🧑 What do you want to solve today? → ")
    try:
        result = await send_message_async(message="🧑 What do you want to solve today? → ", tool="send_telegram_message")
        if result:
            print("Request was successfully to telegram for prompt from user")
 
    except:
        traceback.print_exc()


    user_input = None
    
    while user_input is None or user_input == "":
        try:
            result = await get_telegram_message()
            if result:
                user_input = result["message"]
                if user_input is None or user_input == "":
                    print("Have not received any command from telegram: sleeping 10 seconds")
                    time.sleep(10)
        except:
            traceback.print_exc()

    print(f"Received user_input from telegram: {user_input}")
    x = input("Press any key to proceed?")

    # Load MCP server configs from profiles.yaml
    with open("config/profiles.yaml", "r") as f:
        profile = yaml.safe_load(f)
        mcp_servers = profile.get("mcp_servers", [])

    
    # Add Telegram MCP server configuration with SSE transport
    telegram_config = {
        "name": "telegram",
        "script": "final_telegram_mcp_server.py",
        "transport": "sse",
        "url": "http://localhost:8000/",  # SSE server URL
        "endpoints": {
            "send_telegram_message": "send"
        #    "events": "/events"  # SSE events endpoint
        }
    }

    mcp_servers.append(telegram_config)

    multi_mcp = MultiMCP(server_configs=mcp_servers)
    print("Agent before initialize")
    await multi_mcp.initialize()

    agent = AgentLoop(
        user_input=user_input,
        dispatcher=multi_mcp  # now uses dynamic MultiMCP
    )

    try:
        final_response = await agent.run()
        print("\n💡 Final Answer:\n", final_response.replace("FINAL_ANSWER:", "").strip())

    except Exception as e:
        log("fatal", f"Agent failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())


# Find the ASCII values of characters in INDIA and then return sum of exponentials of those values.
# How much Anmol singh paid for his DLF apartment via Capbridge? 
# What do you know about Don Tapscott and Anthony Williams?
# What is the relationship between Gensol and Go-Auto?
# which course are we teaching on Canvas LMS?
# Summarize this page: https://theschoolof.ai/
# What is the log value of the amount that Anmol singh paid for his DLF apartment via Capbridge? 