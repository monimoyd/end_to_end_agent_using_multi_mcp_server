from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from sse_starlette.sse import EventSourceResponse
from mcp.server.fastmcp import FastMCP
from fastapi.middleware.cors import CORSMiddleware
from telegram import Bot
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from mcp import Tool
import logging
import asyncio
import os
import traceback

load_dotenv()


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

class TelegramInput(BaseModel):
     message:str

class TelegramOutput(BaseModel):
    status: str
    detail: str
   
    

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

mcp = FastMCP(name="telegram", transport="sse")
app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

queue = asyncio.Queue()

@app.get("/sse")
async def sse_endpoint(request: Request):
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await queue.get()
                yield {
                    "event": "message",
                    "data": message
                }
        finally:
            pass

    return EventSourceResponse(event_generator())
    
@app.get("/get_telegram_message")
async def get_telegram_message():
    try:
        message = await queue.get()
        return JSONResponse(content={"message": message})
    except Exception as e:
        return JSONResponse(content={"message": ""})

@app.post("/put_telegram_message")
async def put_telegram_message(user_id:str, message:str):
    try:
        await queue.put(message)
        return JSONResponse(content={"status": "SUCCESS", "detail": f"Successfully put mssage: {message}"})
    except Exception as e:
        return JSONResponse(content={"status": "FAIL", "detail": f"Failed to put mssage: {e}"})
    
 
bot = Bot(token=TELEGRAM_BOT_TOKEN)


@mcp.tool(name="send_telegram_message", description="sends a message to telegram")
async def send_telegram_message(inp: TelegramInput) -> TelegramOutput:
    """sends a message to telegram. Usage: send_telegram_message|input={"message":"The email has been delivered succesfully"}"""
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=inp.message)
        logging.info(f"Telegram message sent: {inp.message}")
        return TelegramOutput(status="SUCCESS", detail="Message sent successfully")
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")
        return TelegramOutput(status="FAIL", detail=f"Error sending Telegram message: {e}")


@app.post("/send")
#async def send_message(payload: dict):
async def send_message(message: str, tool: str="send_telegram_message"):
    #tool = payload.get("tool", "send_telegram_message")
    try:
        if tool == "send_telegram_message":
            #inp = TelegramInput(message=payload.get("message", ""))
            inp = TelegramInput(message=message)
            output = await send_telegram_message(inp)      
            return JSONResponse(content={"status": output.status, "detail": output.detail, "content": output.detail})
    except:
        traceback.print_exc()
        return JSONResponse(content={"status": "FAIL", "detail": "Failed to send message to telegram", "content": "Failed to send message to telegram" })
    
# Mount the MCP application
app.mount("/", mcp)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)    