from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
from dotenv import load_dotenv
from jinja2 import ChoiceLoader
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import uuid
import time
import json
import asyncio
import os

app = FastAPI()
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from ctypes import cast
from typing import Any, List, TypedDict


class GptModelDescriptor(BaseModel):
    id: str
    object: str
    created: int
    owned_by: str


class GptModelResponseFormat(BaseModel):
    object: str
    data: list[GptModelDescriptor]


# Request models
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = 1.0
    max_tokens: int = 256
    stream: bool = False


# Response Models
class Choice(BaseModel):
    index: int = 0
    delta: dict = {}
    logprobs: Dict | None = None
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    provider: str = "provider_name"
    service_tier: str = "default"
    system_fingerprint: str = "null"
    choices: List[Choice]


# Function to generate streamed responses in the desired format
async def generate_stream_response(
    messages, temperature, max_tokens
) -> AsyncGenerator[str, None]:
    unique_id = str(uuid.uuid4())  # Unique request ID
    timestamp = int(time.time())  # Current timestamp
    model_name = "meta-llama/llama-3.2-3b-instruct"  # Replace with your model name
    provider_name = "provider_name"  # Replace with your provider name

    # Simulate token generation from the last message
    user_message = messages[-1].content
    words = user_message.split()  # Simulating splitting into tokens

    # Stream chunks (simulating token generation)
    for i, word in enumerate(words):
        chunk = ChatCompletionChunk(
            id=unique_id,
            created=timestamp,
            model=model_name,
            choices=[Choice(delta={"content": "Hi "})],
        )
        yield f"data: {chunk.model_dump_json()}\n\n"  # SSE format
        await asyncio.sleep(0.2)  # Simulated delay for token streaming

    # Send the final empty chunk with stop finish reason
    chunk = ChatCompletionChunk(
        id=unique_id,
        created=timestamp,
        model=model_name,
        choices=[Choice(finish_reason="stop")],
    )
    yield f"data: {chunk.model_dump_json()}\n\n"

    # Send the final [DONE] message to signal the end of the stream
    yield "data: [DONE]\n\n"


# Chat completions endpoint
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    print("model:", request.model)
    print("stream:", request.stream)
    if request.stream:
        # Handle streaming response
        async def stream_response():
            async for chunk in generate_stream_response(
                request, request.temperature, request.max_tokens
            ):
                yield chunk

        return StreamingResponse(stream_response(), media_type="text/event-stream")
    else:
        # Handle non-streaming response (optional)
        raise HTTPException(
            status_code=400, detail="Non-streaming mode not supported in this example."
        )


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
