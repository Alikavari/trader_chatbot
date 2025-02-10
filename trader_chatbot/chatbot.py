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
    get_stauts: Annotated[
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
