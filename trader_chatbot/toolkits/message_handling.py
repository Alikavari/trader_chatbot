from trader_chatbot.constants import PROMPT_DIR
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)
from trader_chatbot.openai_structs import Message


ModelMessage = SystemMessage | HumanMessage | AIMessage | ToolMessage | BaseMessage


def read_prompt():
    with open(PROMPT_DIR, "r") as file:
        content = file.read()  # Reads the entire file as a single string
    return content


class MessageWrapper:
    def __init__(self):
        self.prompt = read_prompt()

    def wrap_messages_for_agent(self, messages: list[Message]) -> list[ModelMessage]:
        model_messages: list[ModelMessage] = [SystemMessage(self.prompt)]
        for message in messages:
            if message.role == "assistant":
                model_messages.append(AIMessage(content=message.content))
            elif message.role == "user" or message.role == "hideUser":
                model_messages.append(HumanMessage(content=message.content))
        return model_messages
