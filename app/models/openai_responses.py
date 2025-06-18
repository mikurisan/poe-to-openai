from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, List, Any, Optional


class ResponseTypes(Enum):
    CREATED = "response.created"
    IN_PROGRESS = "response.in_progress"
    COMPLETED = "response.completed"
    FAILED = "response.failed"
    
    OUTPUT_ITEM_ADDED = "response.output_item.added"
    OUTPUT_ITEM_DONE = "response.output_item.done"

    CONTENT_PART_ADDED = "response.content_part.added"
    CONTENT_PART_DONE = "response.content_part.done"

    OUTPUT_TEXT_DELTA = "response.output_text.delta"
    OUTPUT_TEXT_DONE = "response.output_text.done"


class ResponseStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CustomBaseModel(BaseModel):
    class Config:
        populate_by_name = True
    
    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude=exclude)
    

class ContentBase(CustomBaseModel):
    type: str
    item_id: str
    output_index: Optional[int] = 0
    content_index: Optional[int] = 0


class Part(CustomBaseModel):
    type: str
    text: Optional[str] = ""
    annotations: List[Dict[str, Any]] = Field(default_factory=list)


class ContentPart(ContentBase):
    part: Part


class ContentDelta(ContentBase):
    delta: str


class ContentText(ContentBase):
    text: str


class Item(CustomBaseModel):
    id: str
    type: str
    status: str
    role: str
    content: List[Part] = Field(default_factory=list)


class OutputItem(CustomBaseModel):
    type: str
    output_index: Optional[int] = 0
    item: Item


class Usage(CustomBaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    output_tokens_details: Optional[Dict[str, int]] = Field(default_factory=dict)


class Error(CustomBaseModel):
    type: Optional[str] = None
    code: Optional[str] = None
    message: str


class Response(CustomBaseModel):
    id: str
    model: str
    created_at: int
    instructions: str
    status: str
    error: Optional[Error] = None
    output: List[Item] = Field(default_factory=list)
    usage: Optional[Usage] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    object: Optional[str] = "response"
    incomplete_details: Optional[Any] = None
    max_output_tokens: Optional[Any] = None
    parallel_tool_calls: Optional[bool] = True
    previous_response_id: Optional[int] = None
    reasoning: Dict[str, None] = Field(default_factory=lambda: {"effort": None, "summary": None})
    store: Optional[bool] = True
    text: Dict[str, Dict[str, str]] = Field(default_factory=lambda: {"format": {"type": "text"}})
    tool_choice: Optional[str] = "auto"
    tools: List = Field(default_factory=list)
    truncation: Optional[str] = "disabled"
    user: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)