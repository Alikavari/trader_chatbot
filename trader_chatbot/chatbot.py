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


class ModelOutput(BaseModel):
    content: str
    tool_name: str | None = None
    args: dict[str, Any] | None = None


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

    async def ainvoke(self, messages: List[ModelMessage]) -> ModelOutput:
        output = await self.model_with_tools.ainvoke(messages)
        messages.append(output)
        tool_calls = getattr(output, "tool_calls", None)
        if tool_calls is None or len(tool_calls) == 0:  # normal_messages
            content = cast(str, output.content)
            return ModelOutput(content=content)
        else:
            tool_call = tool_calls[0]
            tool_name = tool_call["name"].lower()
            if tool_name in self.write_tools:  # for write tools
                selected_tool = self.write_tools[tool_name]
                tool_args = tool_call["args"]
                rendered_content = render_md(
                    f"pls confirm the information bellow in order to {tool_name}",
                    tool_args,
                    "",
                )
                return ModelOutput(
                    content=rendered_content, tool_name=tool_name, args=tool_args
                )
            selected_tool = self.read_tools[tool_name]  # for read tools
            tool_msg = await selected_tool.ainvoke(tool_call)
            messages.append(tool_msg)
            output = await self.model_with_tools.ainvoke(messages)
            content = cast(str, output.content)
            return ModelOutput(content=content)
