from langchain_core.language_models.chat_models import BaseChatModel
from trader_chatbot.toolkits.message_handling import ModelMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from trader_chatbot.toolkits.markdonw_rendering import render_md
from trader_chatbot.web3_read_functions import getting_balance
from typing import cast, Any
from trader_chatbot.openai_structs import Message
from typing import Callable, Dict, Any, List
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)
from trader_chatbot.web3_read_functions import has_active_node
from pydantic import BaseModel, Field
from typing import cast, Literal
import json
import re
import time

# from trader_chatbot.database import database
# from trader_chatbot.models import WalletTable


class ResMessageModel(BaseModel):
    role: Literal["assistant", "tool"]
    content: Any
    tool_calls: List[Any] | None = None
    name: str | None = None
    tool_call_id: str | None = None


class WalletUsageResponse(BaseModel):
    wallet_address: str
    token_usage: int


async def create_row_data(user_wallet_address: str, database: Any, user_wallet: Any):
    query = user_wallet.insert().values(
        user_wallet_address=user_wallet_address, token_usage=0
    )
    try:
        await database.execute(query)
    except Exception as e:
        pass


async def read_used_tokens(user_wallet_address: str, database: Any, user_wallet: Any):
    query = user_wallet.select().where(
        user_wallet.c.user_wallet_address == user_wallet_address
    )
    wallet = await database.fetch_one(query)
    if wallet is None:
        await create_row_data(user_wallet_address, database, user_wallet)
        return 0
    return wallet["token_usage"]


async def aggregate_used_tokens(
    user_wallet_address: str, database: Any, user_wallet: Any, used_tokens: int
):
    pre_used_tokens = await read_used_tokens(user_wallet_address, database, user_wallet)
    print("all_tokens", used_tokens + pre_used_tokens)
    query = (
        user_wallet.update()
        .where(user_wallet.c.user_wallet_address == user_wallet_address)
        .values(token_usage=used_tokens + pre_used_tokens)
    )
    result = await database.execute(query)


async def get_wallet_msgs(
    messages: list[ModelMessage], database: Any, user_wallet: Any
):
    if len(messages) > 0:
        pattern = r"(?:^|\s)(0x[a-fA-F0-9]{40})(?=\s|[.,;:]|$)"
        match = re.search(pattern, cast(str, messages[0].content))
        if match:
            user_wallet_address = match.group(1)
            balance = await getting_balance(user_wallet_address)
            used_tokens = await read_used_tokens(
                user_wallet_address, database, user_wallet
            )
            return user_wallet_address, balance, used_tokens
        else:
            return None, 0, 0
    else:
        return None, 0, 0


def trim_messages(messages: List[ModelMessage]) -> List[ModelMessage]:
    # Step 1: Find the index of the last HumanMessage
    last_human_index = None
    for i in reversed(range(len(messages))):
        if isinstance(messages[i], HumanMessage):
            last_human_index = i
            break

    if last_human_index is None:
        # If no HumanMessage is found, return only the SystemMessages
        return [msg for msg in messages if isinstance(msg, SystemMessage)]

    # Step 2: Keep all SystemMessages + slice from last HumanMessage to end
    trimmed = [msg for msg in messages if isinstance(msg, SystemMessage)]
    trimmed += messages[last_human_index:]

    return trimmed


class Agent:
    def __init__(
        self,
        model: BaseChatModel,
        second_model: BaseChatModel,
        read_tools: Dict[str, Callable[..., Any]],
        write_tools: Dict[str, Callable[..., Any]],
        database: Any,
        user_wallet: Any,
    ):
        tool_list = list(read_tools.values()) + list(write_tools.values())
        self.model_with_tools = model.bind_tools(tool_list, parallel_tool_calls=False)
        self.second_model_with_tools = second_model.bind_tools(
            tool_list, parallel_tool_calls=False
        )
        self.read_tools = read_tools
        self.write_tools = write_tools
        self.merged = {**read_tools, **write_tools}
        self.database = database
        self.user_wallet = user_wallet

    async def ainvoke(self, messages: List[ModelMessage]):
        # messages = [messages[0], messages[-1]]
        # print("messages:\n", messages)
        messages = trim_messages(messages)
        new_messages: List[ResMessageModel] = []
        last_msg_size = len(messages[-1].content)
        if last_msg_size > 200 and isinstance(messages[-1], HumanMessage):
            return [
                ResMessageModel(
                    role="assistant",
                    content="Oops, your message is too long for me to process. Please shorten.",
                )
            ]
        user_wallet_address, balance, used_token = await get_wallet_msgs(
            messages,
            self.database,
            self.user_wallet,
        )

        if user_wallet_address is None:
            return [
                ResMessageModel(
                    role="assistant",
                    content="Looks like your wallet isn't connected yet. Please connect your wallet and refresh the page to start chatting with the Muon chatbot.",
                )
            ]

        if (balance < 500) & (has_active_node(user_wallet_address) == False):
            return [
                ResMessageModel(
                    role="assistant",
                    content="Looks like you don’t have enough balance or an active node to start a chat with the Muon bot.",
                )
            ]

        if used_token >= 90000:
            return [
                ResMessageModel(
                    role="assistant",
                    content="You have used up all your MUON chatbot tokens",
                )
            ]
        while True:

            output = await self.model_with_tools.ainvoke(messages)
            output = cast(AIMessage, output)
            response_output = ResMessageModel(
                role="assistant",
                content=output.content,
                tool_calls=output.tool_calls,
            )
            new_messages.append(response_output)
            total_tokens = output.response_metadata["token_usage"]["total_tokens"]
            await aggregate_used_tokens(
                user_wallet_address, self.database, self.user_wallet, total_tokens
            )

            messages.append(output)
            tool_calls = getattr(output, "tool_calls", None)
            content = cast(str, output.content)
            if tool_calls is None:
                return new_messages
            if len(tool_calls) == 0:
                return new_messages
            for tool_call in tool_calls:
                tool_name = tool_call["name"].lower()
                selected_tool = self.merged[tool_name]

                tool_msg = await selected_tool.ainvoke(tool_call)
                new_messages.append(
                    ResMessageModel(
                        role="tool",
                        content=tool_msg.content,
                        name=tool_msg.name,
                        tool_call_id=tool_msg.tool_call_id,
                    )
                )

                if (
                    tool_name == "boost"
                    or tool_name == "approve"
                    or tool_name == "unstake"
                    or tool_name == "claim"
                    or tool_name == "claim_reward"
                    or tool_name == "transfer"
                    or tool_name == "add_node"
                ):
                    _, ready = json.loads(tool_msg.content)
                    if ready == True:
                        new_messages.pop()
                        print("new_messages:", new_messages)
                        return new_messages
                messages.append(tool_msg)
