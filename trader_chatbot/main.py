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

from trader_chatbot.chatbot import Agent, ModelMessage
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
    get_balance,
    wellcome_message,
    transfer,
)


# Consts
HIGHLIGHT = "\033[1;43m"  # Yellow background with bold text
RESET = "\033[0m"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


load_dotenv()
os.system("clear")
models_dict: dict[str, Any] = {
    "muon-llm-v0.1": None,
    # "gpt-4o": ChatOpenAI(model="gpt-4o", temperature=0),
    "llama3.2:3b": None,
    "gpt-4o-mini": None,
}

wrapper = MessageWrapper()
app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


read_tools = {
    "wellcome_message": wellcome_message,
    "get_balance": get_balance,
}
write_tools = {"transfer": transfer}


model = init_chat_model("gpt-4o", model_provider="openai")
agent = Agent(model, read_tools, write_tools)


# Function to generate streamed responses in the desired format
async def generate_stream_response(
    messages: list[Message], model_name: str
) -> AsyncGenerator[str, None]:
    unique_id = str(uuid.uuid4())  # Unique request ID
    timestamp = int(time.time())  # Current timestamp
    print(messages)
    agent_message = wrapper.wrap_messages_for_agent(messages)

    response, kwargs = await agent.ainvoke(agent_message)
    str_kwargs = kwargs.__str__()
    print(str_kwargs)
    chunk = ChatCompletionChunk(
        id="chatcmpl-AvPUCpUAdofwp2ePGw0bSHL1USHZ1",
        created=timestamp,
        model=model_name,
        choices=[
            StreamChoice(
                delta={
                    "content": f"{ response + f"\n\n##ADDITIONAL_KWARGS=={str_kwargs}"} "
                }
            )
        ],  #
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
