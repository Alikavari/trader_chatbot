from typing import Dict
from click import Choice
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
from dotenv import load_dotenv
from jinja2 import ChoiceLoader
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import uuid
import time
import json
import asyncio
import os
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from regex import FULLCASE

from extractors import (
    TradeInfo,
    amount_extractor,
    crypto_extractor,
    exchange_extractor,
    trade_extractor,
)
from openai_structs import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    NormalChoice,
    StreamChoice,
    Message,
    GptModelDescriptor,
    GptModelResponseFormat,
    ChatRequest,
)  # Import correct type


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


state = ["None"]


class TradeInfoType(BaseModel):
    is_trading_related: bool = False
    action: str | None = None
    coin: str | None = None
    amount: float | None = None
    exchange: str | None = None


global_json_list: list[TradeInfoType] = [TradeInfoType()]


client = AsyncOpenAI()  # Replace with your actual API key
app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Any, List, TypedDict, cast


def generte_response() -> str:
    if global_json_list[0].is_trading_related == False:
        return (
            "I am an LLM model designed exclusively to handle crypto trading commands."
        )
    elif global_json_list[0].coin == None:
        state[0] = "coin"
        return "Please enter crypto name."
    elif global_json_list[0].amount == None:
        state[0] = "amount"
        return "Please enter the amount of crypto."
    elif global_json_list[0].exchange == None:
        state[0] = "exchange"
        return "Please enter the Exchange name."
    else:
        return global_json_list[0].model_dump_json(exclude={"is_trading_related"})


async def call_models(llm, msg):
    if state[0] == "None":
        model_response = await trade_extractor(llm, msg)
        global_json_list[0] = TradeInfoType(**model_response)
        # print(global_json_list[0])
    elif state[0] == "coin":
        coin = await crypto_extractor(llm, msg)
        global_json_list[0].coin = coin["coin"]
    elif state[0] == "amount":
        amount = await amount_extractor(llm, msg)
        global_json_list[0].amount = amount["amount"]
    elif state[0] == "exchange":
        exchange_name = await exchange_extractor(llm, msg)
        global_json_list[0].exchange = exchange_name["exchange"]
    state[0] = "None"


# Function to generate streamed responses in the desired format
async def generate_stream_response(
    messages: List[Message], model_name: str
) -> AsyncGenerator[str, None]:
    print(state)
    unique_id = str(uuid.uuid4())  # Unique request ID
    timestamp = int(time.time())  # Current timestamp
    last_msg = messages[-1].content
    llm = ChatOpenAI(model="gpt-4o-mini")
    await call_models(llm, last_msg)
    content = generte_response()
    chunk = ChatCompletionChunk(
        id="chatcmpl-AvPUCpUAdofwp2ePGw0bSHL1USHZ1",
        created=timestamp,
        model=model_name,
        choices=[StreamChoice(delta={"content": f"{content} "})],
    )
    yield f"data: {chunk.model_dump_json()}\n\n"  # SSE format

    # Send the final empty chunk with stop finish reason
    chunk = ChatCompletionChunk(
        id="chatcmpl-AvPUCpUAdofwp2ePGw0bSHL1USHZ1",
        created=timestamp,
        model=model_name,
        choices=[StreamChoice(finish_reason="stop")],
    )
    yield f"data: {chunk.model_dump_json()}\n\n"

    # Send the final [DONE] message to signal the end of the stream
    yield "data: [DONE]\n\n"


# Chat completions endpoint
@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
) -> Response:
    if request.stream == True:  # if clinet needs stream response
        # Handle streaming response
        async def stream_response():
            async for chunk in generate_stream_response(
                request.messages,
                request.model,
            ):
                yield chunk

        return StreamingResponse(stream_response(), media_type="text/event-stream")
    else:  # if clinet needs non-stream response
        normal_response = ChatCompletionResponse(
            id="chatcmpl-AwC6ciPHpVBcw6Iy89FWSil7RRssE",
            created=int(time.time()),
            model="gpt-4o",
            choices=[
                NormalChoice(
                    message=Message(
                        role="assistant", content="The Cryptocurrency Exchanger ChatBot"
                    )
                )
            ],
            system_fingerprint="some_finger",
        )
        return JSONResponse(normal_response.model_dump())


async def get_open_ai_models(
    api_token: str,
    url: str = "https://api.openai.com/v1/models",
) -> GptModelResponseFormat:
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Custom-Header": "SomeValue",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    return GptModelResponseFormat(**response.json())


def filter_models_by_id(
    data: GptModelResponseFormat, target_ids: List[str]
) -> GptModelResponseFormat:
    filtered_list_data = [item for item in data.data if item.id in target_ids]
    filtered_data = {"object": "list", "data": filtered_list_data}
    return GptModelResponseFormat(**filtered_data)


@app.get("/v1/models")
async def list_models() -> GptModelResponseFormat:
    if OPENAI_API_KEY:
        models_info = await get_open_ai_models(OPENAI_API_KEY)
    else:
        raise RuntimeError("❌ ERROR: 'API_KEY' environment variable is missing!")
    target_ids = [
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-4o-mini",
    ]
    models_info = filter_models_by_id(models_info, target_ids)
    return models_info
