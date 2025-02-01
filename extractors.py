import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
from typing import Annotated, TypedDict, cast, Type
import json
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class LlmOutputStruct(TypedDict):
    pass


class TradeInfo(LlmOutputStruct):
    is_trading_related: Annotated[
        bool,
        "Indicates whether the user command involves cryptocurrency trading or not",
    ]
    action: Annotated[str | None, 'Either "buy", "sell", or null']
    coin: Annotated[str, "The name of the cryptocurrency (e.g., Bitcoin, Ethereum)"]
    amount: Annotated[float, "The amount to trade (as a float)"]
    exchange: Annotated[str, "The name of the exchange (e.g., Binance, Coinbase)"]


class CryptoInfo(LlmOutputStruct):
    coin: Annotated[str, "The name of the cryptocurrency "]


class AmountInfo(LlmOutputStruct):
    amount: Annotated[float | None, "the bitcoin value"]


class ExchangeInfo(LlmOutputStruct):
    exchange: Annotated[str | None, "The name of the exchange"]


class ActionInfo(LlmOutputStruct):
    action: Annotated[str | None, "The action 'buy','sell' or null"]


def read_prompt(file_name: str):
    with open(file_name, "r") as file:
        content = file.read()
    return content


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def structured_model(
    model: BaseChatModel,
    output_foramt: Type[LlmOutputStruct],
    system_msg: str,
    user_msg: str,
) -> LlmOutputStruct:
    structured_llm = model.with_structured_output(output_foramt)
    messages = [
        SystemMessage(system_msg),
        HumanMessage(user_msg),
    ]
    model_out = await structured_llm.ainvoke(messages)
    return cast(LlmOutputStruct, model_out)


async def trade_extractor(model: BaseChatModel, user_msg: str) -> TradeInfo:
    system = read_prompt("./prompts/trade_prompt.txt")
    bitcoin_exchange_struct = await structured_model(model, TradeInfo, system, user_msg)
    return cast(TradeInfo, bitcoin_exchange_struct)


async def crypto_extractor(model: BaseChatModel, user_msg: str) -> CryptoInfo:
    system = read_prompt("./prompts/crypto_prompt.txt")
    bitcoin_exchange_struct = await structured_model(
        model, CryptoInfo, system, user_msg
    )
    return cast(CryptoInfo, bitcoin_exchange_struct)


async def amount_extractor(model: BaseChatModel, user_msg: str) -> AmountInfo:
    system = read_prompt("./prompts/amount_prompt.txt")
    bitcoin_exchange_struct = await structured_model(
        model, AmountInfo, system, user_msg
    )
    return cast(AmountInfo, bitcoin_exchange_struct)


async def exchange_extractor(model: BaseChatModel, user_msg: str) -> ExchangeInfo:
    system = read_prompt("./prompts/exchange_prompt.txt")
    bitcoin_exchange_struct = await structured_model(
        model, ExchangeInfo, system, user_msg
    )
    return cast(ExchangeInfo, bitcoin_exchange_struct)


async def action_extractor(model: BaseChatModel, user_msg: str) -> ActionInfo:
    system = read_prompt("./prompts/exchange_prompt.txt")
    bitcoin_exchange_struct = await structured_model(
        model, ActionInfo, system, user_msg
    )
    return cast(ActionInfo, bitcoin_exchange_struct)
