from email import message
from unittest.mock import Base
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field

from typing import Literal, Annotated, Union, Optional, cast, Any


status_type = Literal["balance", "position" "exposure", "positions", "opened", "uPnL"]
method_type = Literal["percent", "dollars"]
asset_type = Literal["BTC", "ETH"]


class StopLossConditoin(BaseModel):
    value: int = Field(..., alias="SL_value")
    method: method_type = Field(..., alias="SL_type")


class TakeProfitCondition(BaseModel):
    value: int = Field(..., alias="TP_value")
    method: method_type = Field(..., alias="TP_type")


class OpenPosition(BaseModel):
    action: Literal["open"]
    position: Literal["long", "short"]
    asset: asset_type
    position_size: Annotated[int, Field(description="The position size (in dollar$)")]
    leverage: int
    stop_loss: Optional[StopLossConditoin] = None
    take_profit: Optional[TakeProfitCondition] = None


class ClosePosition(BaseModel):
    action: Literal["close"]
    position: Literal["long", "short"]
    asset: asset_type


class BotResponse(BaseModel):
    response: Annotated[str, Field(description="The response for user")]
    api: Annotated[
        Union[OpenPosition, ClosePosition, None],
        Field(description="The API field, no API generated set to None"),
    ]
    get_status: Annotated[
        Union[status_type, None],
        Field(description="The statuses field, no status generated set to None"),
    ]


PROMPT_DIR = "./prompts/prompt.txt"
ModelMessage = SystemMessage | HumanMessage | AIMessage


def read_prompt(prompt_dir: str):
    with open(prompt_dir, "r") as file:
        content = file.read()  # Reads the entire file as a single string
    return content


class StructChatModel:
    def __init__(self, llms_dict: dict[str, BaseChatModel]) -> None:
        prompt = read_prompt(PROMPT_DIR)
        self.structured_llm: dict[str, Any] = {}
        for llm_key in llms_dict:
            this_model = llms_dict[llm_key]
            self.structured_llm[llm_key] = this_model.with_structured_output(
                BotResponse
            )
        self.msg_list: list[ModelMessage] = [SystemMessage(prompt)]

    def send_message(self, llm_name: str, msg: str) -> BotResponse:
        self.msg_list.append(HumanMessage(msg))
        current_model = self.structured_llm[llm_name]
        structure_output = cast(BotResponse, current_model.invoke(self.msg_list))
        self.msg_list.append(AIMessage(structure_output.model_dump_json()))
        return structure_output


class ChatBot:
    def __init__(self, llms_dict: dict[str, BaseChatModel]) -> None:
        prompt = read_prompt(PROMPT_DIR)
        self.msg_list: list[ModelMessage] = [SystemMessage(prompt)]
        self.llms_dict = llms_dict

    def send_message(self, llm_name: str, msg: str) -> str:
        self.msg_list.append(HumanMessage(msg))
        response = self.llms_dict[llm_name].invoke(self.msg_list)
        if isinstance(response.content, str):
            self.msg_list.append(AIMessage(response.content))
            return response.content
        else:
            raise RuntimeError

    # async def send_message_stram(self, chat_model: BaseChatModel, msg: str):
    #     self.msg_list.append(HumanMessage(msg))
    #     async for event in chat_model.astream_events(self.msg_list, version="v1"):
    #         if event["event"] == "on_chat_model_end" and "output" in event["data"]:
    #             contnet = event["data"]["output"].content
    #             self.msg_list.append(AIMessage(contnet))
    #         if event["event"] == "on_chat_model_stream" and "chunk" in event["data"]:
    #             yield event["data"]["chunk"].content

    def clear_message_history(self) -> None:
        self.msg_list = []


from ctypes import Structure
import json
from typing import Annotated, Literal, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool
import os
from web3 import Web3

from openai import BaseModel


class GetWalletAddress:
    def __init__(self, llm, wallet_fucntion: BaseTool):
        system_prompt = """
        You are an intelligent agent designed solely to collect and verify a wallet address from the user.

        1. Your only purpose is to request and confirm the user's wallet address.
        2. Politely ask the user: "Please provide your wallet address to continue. or sth like this"
        3. When the user provides an address, call the `is_wallet_confirmed` function to verify it.
        4. If the address is valid, respond with: "Wallet address confirmed ✅." or sth like this 
        5. If the address is invalid, politely ask the user to re-enter it and repeat the validation until a valid address is provided.
        6. Do not answer any questions unrelated to wallet address submission. If the user asks anything else, ask him/his  wallet address. 
        7. Never proceed without confirming a valid wallet address.
        """
        memory = MemorySaver()
        tools = [wallet_fucntion]  # Using the realistic dummy weather tool
        self.agent_executor = create_react_agent(
            llm, tools, checkpointer=memory, prompt=system_prompt
        )
        # Step 3: Use the Agent (No Streaming)
        self.config: RunnableConfig = {"configurable": {"thread_id": "abc123"}}

    def run_agent(self, user_message: str) -> str:
        # First messageA
        response_1 = self.agent_executor.invoke(
            {
                "messages": [
                    HumanMessage(content=user_message),
                ]
            },
            self.config,
        )

        model_response: list = response_1["messages"]
        return model_response[-1].content
