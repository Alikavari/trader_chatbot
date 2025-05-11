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
            SystemMessage(content="user still dont connet their wallet address"),
        ]
        for message in messages:
            text_part, dict_part = decompose_message(message.content)
            if message.role == "assistant":
                model_messages.append(
                    AIMessage(content=text_part, additional_kwargs=dict_part)
                )
            elif message.role == "user" or message.role == "hideUser":
                model_messages.append(HumanMessage(content=message.content))
            elif message.role == "metaMask":
                print("the dict part", dict_part)
                function_name = dict_part["tool_calls"][0]["function"]["name"]
                call_id = dict_part["tool_calls"][0]["id"]
                model_messages.append(
                    ToolMessage(
                        content=text_part, name=function_name, tool_call_id=call_id
                    )
                )
        return model_messages
