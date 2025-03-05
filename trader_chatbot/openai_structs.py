from pydantic import BaseModel
from typing import Optional


# v1/chat/completion  Stream Response Structs
class Message(BaseModel):
    role: str
    content: str
    refusal: Optional[str] = None


class NormalChoice(BaseModel):
    index: int = 0
    message: Message
    logprobs: Optional[str] = None
    finish_reason: str = "stop"


class PromptTokensDetails(BaseModel):
    cached_tokens: int = 0
    audio_tokens: int = 0


class CompletionTokensDetails(BaseModel):
    reasoning_tokens: int = 0
    audio_tokens: int = 0
    accepted_prediction_tokens: int = 0
    rejected_prediction_tokens: int = 0


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_tokens_details: PromptTokensDetails = PromptTokensDetails()
    completion_tokens_details: CompletionTokensDetails = CompletionTokensDetails()


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[NormalChoice]
    usage: Usage = Usage()
    service_tier: str = "default"
    system_fingerprint: str


# v1/chat/completion Stream Response Structs
class StreamChoice(BaseModel):
    index: int = 0
    delta: dict = {}
    logprobs: None = None
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    provider: str = "provider_name"
    service_tier: str = "default"
    system_fingerprint: str = "fp_72ed7ab54c"
    choices: list[StreamChoice]


# /v1/models Response Structs
class GptModelDescriptor(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "system"


class GptModelResponseFormat(BaseModel):
    object: str = "list"
    data: list[GptModelDescriptor]


# Model Request Struct
class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float = 1.0
    max_tokens: int = 256
    stream: bool = False
