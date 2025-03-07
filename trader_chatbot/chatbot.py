from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field

from typing import Literal, Annotated, Union, Optional, cast, Any
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables.config import RunnableConfig

ModelMessage = SystemMessage | HumanMessage | AIMessage
Statuses = Literal["balance", "position" "exposure", "positions", "opened", "uPnL"]
Methods = Literal["percent", "dollars"]
Assets = Literal[
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "USDC",
    "XRP",
    "DOGE",
    "TON",
    "TRON",
    "ADA",
    "AVAX",
    "1000SHIB",
    "LINK",
    "BCH",
    "DOT",
    "LTC",
    "KAS",
    "UNI",
    "ICP",
    "FET",
    "XMR",
    "SUI",
    "1000PEPE",
    "APT",
    "XLM",
    "POL",
    "ETC",
    "TAO",
    "STX",
    "IMX",
    "AAVE",
    "FIL",
    "INJ",
    "ARB",
    "RENDER",
    "HBAR",
    "OP",
    "VET",
    "ATOM",
    "FTM",
    "WIF",
    "RUNE",
    "GRT",
    "AR",
    "1000FLOKI",
    "1000BONK",
    "TIA",
    "PYTH",
    "ALGO",
    "JUP",
    "SEI",
    "JASMY",
    "BSV",
    "OM",
    "LDO",
    "QNT",
    "ONDO",
    "FLOW",
    "CKB",
    "NOT",
    "BRETT",
    "BEAMX",
    "EOS",
    "EGLD",
    "AXS",
    "STRK",
    "POPCAT",
    "WLD",
    "NEO",
    "ORDI",
    "GALA",
    "XTZ",
    "CFX",
    "1000XEC",
    "BNX",
    "SAND",
    "ENS",
    "W",
    "MANA",
    "PENDLE",
    "RONIN",
    "KLAY",
    "DOGS",
    "MINA",
    "ZEC",
    "CHZ",
    "1000LUNC",
    "CAKE",
    "SNX",
    "APE",
    "ASTR",
    "ZRO",
    "LPT",
    "ENA",
    "ROSE",
    "BOME",
    "IOTA",
    "ZK",
    "SUPER",
    "AXELAR",
]

PROMPT_DIR = "./prompts/prompt.txt"


class StopLossConditoin(BaseModel):
    value: int = Field(..., alias="SL_value")
    method: Methods = Field(..., alias="SL_type")


class TakeProfitCondition(BaseModel):
    value: int = Field(..., alias="TP_value")
    method: Methods = Field(..., alias="TP_type")


class OpenPosition(BaseModel):
    action: Literal["open"]
    position: Literal["long", "short"]
    asset: Assets
    position_size: Annotated[int, Field(description="The position size (in dollar$)")]
    leverage: int
    stop_loss: Optional[StopLossConditoin] = None
    take_profit: Optional[TakeProfitCondition] = None


class ClosePosition(BaseModel):
    action: Literal["close"]
    position: Literal["long", "short"]
    asset: Assets


class BotResponse(BaseModel):
    response: Annotated[str, Field(description="The response for user")]
    api: Annotated[
        Union[OpenPosition, ClosePosition, None],
        Field(description="The API field, no API generated set to None"),
    ]
    get_status: Annotated[
        Union[Statuses, None],
        Field(description="The statuses field, no status generated set to None"),
    ]


def read_prompt(prompt_dir: str):
    with open(prompt_dir, "r") as file:
        content = file.read()  # Reads the entire file as a single string
    return content


class ChatBot:
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


class WalletBot:
    def __init__(self, llm, wallet_fucntion: BaseTool):
        system_prompt = """
        You are an intelligent agent designed solely to collect and verify a wallet address from the user.

        1. Your only purpose is to request and confirm the user's wallet address.
        2. Politely ask the user to provides his/her wallet address
        3. When the user provides an address, call the `is_wallet_confirmed` function to verify it.
        4. If the address is valid, respond with: "Wallet address confirmed ✅." or sth like this 
        5. If the address is invalid, politely ask the user to re-enter it and repeat the validation until a valid address is provided.
        6. Do not answer any questions unrelated to wallet address submission. If the user asks anything else, ask him/his  wallet address. 
        7. Never proceed without confirming a valid wallet address.
        """
        memory = MemorySaver()
        tools = [wallet_fucntion]
        self.agent_executor = create_react_agent(
            llm, tools, checkpointer=memory, prompt=system_prompt
        )
        self.config: RunnableConfig = {"configurable": {"thread_id": "abc123"}}

    def run_agent(self, user_message: str) -> BotResponse:
        response_1 = self.agent_executor.invoke(
            {
                "messages": [
                    HumanMessage(content=user_message),
                ]
            },
            self.config,
        )

        model_response: list = response_1["messages"]
        last_response: str = model_response[-1].content
        return BotResponse(response=last_response, api=None, get_status=None)
