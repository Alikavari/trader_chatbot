from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from fastapi import FastAPI, WebSocket
from trader_chatbot.toolkits.message_handling import ModelMessage
from trader_chatbot.toolkits.message_handling import MessageWrapper
from typing import List, AsyncGenerator
import uuid
import time
import os
from openai import AsyncOpenAI, BaseModel
from openai.types.chat import ChatCompletionMessageParam
from typing import Any, List, TypedDict, cast

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from trader_chatbot.chatbot import Agent, ModelMessage, ResMessageModel
from trader_chatbot.openai_structs import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    NormalChoice,
    StreamChoice,
    Message,
    GptModelDescriptor,
    GptModelResponseFormat,
    ChatRequest,
)  # Import correct type

from trader_chatbot.tool_functions import (
    get_variables,
    climable_time,
    transfer,
    approve,
    add_node,
    unstake,
    claim,
    claim_reward,
    boost,
    handle_wallet_connect,
    chek_for_adding_node,
)
import json

# from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace


# Consts
HIGHLIGHT = "\033[1;43m"  # Yellow background with bold text
RESET = "\033[0m"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class Wallet(BaseModel):
    wallet_address: str
    token_usage: int


load_dotenv()
os.system("clear")
models_dict: dict[str, Any] = {
    "muon-llm-v0.1": None,
    # "gpt-4o": ChatOpenAI(model="gpt-4o", temperature=0),
    "llama3.2:3b": None,
    "gpt-4o-mini": None,
}

from databases import Database
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    BigInteger,
    create_engine,
    MetaData,
)


DATABASE_URL = "sqlite:///./wallet.db"

database = Database(DATABASE_URL)
metadata = MetaData()

# Define the table schema
user_wallet = Table(
    "user_wallet",
    metadata,
    Column("user_wallet_address", String, primary_key=True),
    Column("token_usage", BigInteger),
)

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)
    await database.connect()
    yield
    await database.disconnect()


wrapper = MessageWrapper()
app = FastAPI(lifespan=lifespan)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


read_tools = {
    "get_variables": get_variables,
    "climable_time": climable_time,
    "chek_for_adding_node": chek_for_adding_node,
    # "handle_wallet_connect": handle_wallet_connect,
}
write_tools = {
    "transfer": transfer,
    "approve": approve,
    "add_node": add_node,
    "unstake": unstake,
    "claim": claim,
    "claim_reward": claim_reward,
    "boost": boost,
}


gpt_mini = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
# llama_8b = init_chat_model("llama3.1:8b", model_provider="ollama")
agent = Agent(gpt_mini, gpt_mini, read_tools, write_tools, database, user_wallet)

# from trader_chatbot.database import database  # your Database() instance


# from models import WalletTable


# Function to generate streamed responses in the desired format
async def generate_stream_response(
    messages: list[Message], model_name: str
) -> AsyncGenerator[str, None]:
    unique_id = str(uuid.uuid4())  # Unique request ID
    timestamp = int(time.time())  # Current timestamp

    agent_message = wrapper.wrap_messages_for_agent(messages)

    responses = await agent.ainvoke(agent_message)
    json_data = json.dumps([response.model_dump() for response in responses])

    chunk = ChatCompletionChunk(
        id="chatcmpl-AvPUCpUAdofwp2ePGw0bSHL1USHZ1",
        created=timestamp,
        model=model_name,
        choices=[StreamChoice(delta={"content": f"{ json_data} "})],  #
    )
    yield f"data: {chunk.model_dump_json()}\n\n"  # SSE format

    chunk = ChatCompletionChunk(
        id="chatcmpl-AvPUCpUAdofwp2ePGw0bSHL1USHZ1",
        created=timestamp,
        model=model_name,
        choices=[StreamChoice(delta={"content": f"{  "\n"} "})],  #
    )
    yield f"data: {chunk.model_dump_json()}\n\n"  # SSE format

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
async def v1_chat_comletions(
    request: ChatRequest,
) -> Response:
    if request.stream == True:  # if clinet needs stream response
        # Handle streaming response
        print("requestMessages: ", request.messages)

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
                NormalChoice(message=Message(role="assistant", content="Muon LLM"))
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
    model_descripter_list: list[GptModelDescriptor] = []
    for model in models_dict:
        model_descripter = GptModelDescriptor(id=model)
        model_descripter_list.append(model_descripter)

    return GptModelResponseFormat(data=model_descripter_list)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
