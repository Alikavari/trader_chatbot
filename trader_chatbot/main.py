from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel

from typing import List, AsyncGenerator
import uuid
import time
import os
from openai import AsyncOpenAI, BaseModel
from openai.types.chat import ChatCompletionMessageParam
from typing import Any, List, TypedDict, cast
from web3 import Web3
from langchain_core.tools import tool


from trader_chatbot.chatbot import (
    ChatBot,
    BotResponse,
    WalletBot,
)

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

# Consts
HIGHLIGHT = "\033[1;43m"  # Yellow background with bold text
RESET = "\033[0m"
TAB = """<button>Click Me</button>"""
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class TradeInfo(TypedDict):
    coin: str
    action: str
    amount: float
    exchange: str


dummy_database = [
    {"id": 1, "wallet_address": None},
]


@tool
def is_valid_eth_address(address: str) -> bool:
    """
    Validates if the provided Ethereum address is correctly formatted (starts with '0x' and contains 40 hexadecimal characters).
    Returns True if valid, False otherwise.
    """
    valet_valdation = Web3.is_address(address)
    if valet_valdation == True:
        dummy_database[0]["wallet_address"] = address
    return valet_valdation


load_dotenv()
os.system("clear")
models_dict: dict[str, BaseChatModel] = {
    "muon-llm-v0.1": ChatOpenAI(model="gpt-4o-mini", temperature=0),
    # "gpt-4o": ChatOpenAI(model="gpt-4o", temperature=0),
    "llama3.2:3b": ChatOllama(model="llama3.2:3b", temperature=0),
    "gpt-4o-mini": ChatOpenAI(model="gpt-4o-mini", temperature=0),
}


app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def llm_router(
    chatbot: ChatBot, walletbot: WalletBot, message, model_name
) -> BotResponse:
    if dummy_database[0]["wallet_address"] == None:
        return walletbot.run_agent(message)
    else:
        return chatbot.send_message(model_name, message)


chatbot = ChatBot(models_dict)
# walletbot = WalletBot(models_dict["gpt-4o-mini"], is_valid_eth_address)


# Function to generate streamed responses in the desired format
async def generate_stream_response(
    messages: list[Message], model_name: str
) -> AsyncGenerator[str, None]:
    unique_id = str(uuid.uuid4())  # Unique request ID
    timestamp = int(time.time())  # Current timestamp
    last_msg = messages[-1].content

    model_response = chatbot.send_message(model_name, last_msg)
    message_content = model_response.response
    trade_api = model_response.api
    get_status = model_response.get_status
    # output_content, output_struct = ast.literal_eval(model_output)
    chunk = ChatCompletionChunk(
        id="chatcmpl-AvPUCpUAdofwp2ePGw0bSHL1USHZ1",
        created=timestamp,
        model=model_name,
        choices=[StreamChoice(delta={"content": f"{ message_content} "})],  #
    )
    yield f"data: {chunk.model_dump_json()}\n\n"  # SSE format

    chunk = ChatCompletionChunk(
        id="chatcmpl-AvPUCpUAdofwp2ePGw0bSHL1USHZ1",
        created=timestamp,
        model=model_name,
        choices=[StreamChoice(delta={"content": f"{  "\n"} "})],  #
    )
    yield f"data: {chunk.model_dump_json()}\n\n"  # SSE format

    if trade_api is not None:
        print(trade_api.model_dump_json(indent=4))
    if get_status is not None:
        out = {}
        out["status"] = get_status
        chunk = ChatCompletionChunk(
            id="chatcmpl-AvPUCpUAdofwp2ePGw0bSHL1USHZ1",
            created=timestamp,
            model=model_name,
            choices=[StreamChoice(delta={"content": f"```json\n\n{ out}  \n\n```"})],  #
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


# @app.get("/v1/models")
# async def get_v1_models() -> GptModelResponseFormat:
#     print("a")
#     if OPENAI_API_KEY is not None:
#         models_info = await get_open_ai_models(OPENAI_API_KEY)
#     else:
#         raise RuntimeError("❌ ERROR: 'API_KEY' environment variable is missing!")
#     target_ids = [
#         "gpt-4o",
#         "gpt-4-turbo",
#         "gpt-4o-mini",
#     ]
#     models_info = filter_models_by_id(models_info, target_ids)
#     return models_info


# Chat completions endpoint
@app.post("/v1/chat/completions")
async def v1_chat_comletions(
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

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
