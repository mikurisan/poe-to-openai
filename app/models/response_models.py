from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class Message(BaseModel):
    role: str
    content: str
    refusal: Optional[Any] = None
    annotations: Optional[List] = Field(default_factory=list)


class Choice(BaseModel):
    index: int
    message: Message
    logprobs: Optional[Any] = None
    finish_reason: Optional[str] = "stop"


class Usage(BaseModel):
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    total_tokens: Optional[int] = 0
    prompt_tokens_details: Optional[Dict[str, int]] = Field(default_factory=dict)
    completion_tokens_details: Optional[Dict[str, int]] = Field(default_factory=dict)


class ChatCompletionResponse(BaseModel):
    id: str
    object: Optional[str] = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = Field(default_factory=Usage)
    service_tier: Optional[str] = "default"