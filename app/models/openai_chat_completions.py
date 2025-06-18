from pydantic import Field
from typing import Dict, List, Any, Optional
from .openai_responses import CustomBaseModel


class Delta(CustomBaseModel):
    role: Optional[str] = None
    content: Optional[str] = ""


class Message(Delta):
    tool_calls: Optional[str] = None
    function_call: Optional[str] = None
    refusal: Optional[Any] = None
    annotations: Optional[List] = Field(default_factory=list)


class Choice(CustomBaseModel):
    index: Optional[int] = 0
    delta: Optional[Delta | Dict[str, Any]] = Field(default_factory=dict)
    message: Optional[Message | Dict[str, Any]] = Field(default_factory=dict)
    logprobs: Optional[Any] = None
    finish_reason: Optional[Any] = None


class Usage(CustomBaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: Dict[str, int] = Field(default_factory=dict)
    completion_tokens_details: Dict[str, int] = Field(default_factory=dict)


class ChatCompletion(CustomBaseModel):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: str
    choices: List[Choice]
    usage: Optional[Usage] = None
    service_tier: Optional[str] = None