from langchain_core.language_models.chat_models import BaseChatModel
from trader_chatbot.toolkits.message_handling import ModelMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from trader_chatbot.toolkits.markdonw_rendering import render_md
from typing import Literal, Annotated, Union, Optional, cast, Any
from trader_chatbot.openai_structs import Message
from typing import Callable, Dict, Any, List
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)
from pydantic import BaseModel, Field
from typing import cast

# class FunctionInfo(BaseModel):

# class ToolInfo(BaseModel):
#     id: str
#     function: Any
#     type: Literal["function"]


# class KwArgs(BaseModel):
#     tool_calls = list[ToolInfo] | None
#     refusal: Any = None


class Agent:
    def __init__(
        self,
        model: BaseChatModel,
        read_tools: Dict[str, Callable[..., Any]],
        write_tools: Dict[str, Callable[..., Any]],
    ):
        tool_list = list(read_tools.values()) + list(write_tools.values())
        self.model_with_tools = model.bind_tools(tool_list, parallel_tool_calls=False)
        self.read_tools = read_tools
        self.write_tools = write_tools

    async def ainvoke(self, messages: List[ModelMessage]) -> tuple[str, dict]:
        output = await self.model_with_tools.ainvoke(messages)
        messages.append(output)
        tool_calls = getattr(output, "tool_calls", None)
        content = cast(str, output.content)
        if tool_calls is None or len(tool_calls) == 0:  # normal_messages

            return content, output.additional_kwargs
        else:
            tool_call = tool_calls[0]
            tool_name = tool_call["name"].lower()
            if tool_name in self.write_tools:  # for write tools
                selected_tool = self.write_tools[tool_name]

                return (content, output.additional_kwargs)
            while tool_name in self.read_tools:
                selected_tool = self.read_tools[tool_name]  # for read tools
                tool_msg = await selected_tool.ainvoke(tool_call)
                messages.append(tool_msg)
                output = await self.model_with_tools.ainvoke(messages)
                messages.append(output)
                tool_calls = getattr(output, "tool_calls", None)
                content = cast(str, output.content)
                if tool_calls is None or len(tool_calls) == 0:  # normal_messages
                    return content, output.additional_kwargs
                tool_call = tool_calls[0]
                tool_name = tool_call["name"].lower()
            content = cast(str, output.content)
            return (content, output.additional_kwargs)
