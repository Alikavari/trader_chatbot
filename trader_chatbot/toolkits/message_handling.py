from trader_chatbot.constants import PROMPT_DIR
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)
from trader_chatbot.openai_structs import Message
import ast

ModelMessage = SystemMessage | HumanMessage | AIMessage | ToolMessage | BaseMessage


def read_prompt():
    with open(PROMPT_DIR, "r") as file:
        content = file.read()  # Reads the entire file as a single string
    return content


def decompose_message(message: str):
    if "\n\n##ADDITIONAL_KWARGS==" in message:
        text_part, dict_part_raw = message.split("\n\n##ADDITIONAL_KWARGS==", 1)
        dict_part_raw = dict_part_raw.strip()
        if dict_part_raw:  # only try parsing if there is actually something
            dict_part = ast.literal_eval(dict_part_raw)
        else:
            dict_part = {}
    else:
        text_part = message
        dict_part = {}
    return text_part.strip(), dict_part


class MessageWrapper:
    def __init__(self):
        self.prompt = read_prompt()

    def wrap_messages_for_agent(self, messages: list[Message]) -> list[ModelMessage]:
        model_messages: list[ModelMessage] = [
            SystemMessage(self.prompt),
            # SystemMessage(content="user still dont connet their wallet address"),
        ]
        for idx, message in enumerate(messages):
            # text_part, dict_part = decompose_message(message.content)

            if message.role == "assistant" or message.role == "hideAssistant":
                print("the tool_calls:\n", message.tool_calls)
                if message.tool_calls == None:
                    model_messages.append(AIMessage(content=message.content))
                else:
                    model_messages.append(
                        AIMessage(
                            content=message.content, tool_calls=message.tool_calls
                        )
                    )
                if idx > 0 and messages[idx - 1].role == "hideUser":
                    model_messages.pop()
            elif message.role == "user":
                model_messages.append(HumanMessage(content=message.content))
            elif message.role == "hideUser":
                model_messages[0].content += "\n" + message.content
                print("prompt content", model_messages[0].content)
                # model_messages.append(HumanMessage(content=message.content))
            elif message.role == "tool":
                print("ffffff:\n", message.name)
                model_messages.append(
                    ToolMessage(
                        content=message.content,
                        name=message.name,
                        tool_call_id=message.tool_call_id,
                    )
                )
        return model_messages
