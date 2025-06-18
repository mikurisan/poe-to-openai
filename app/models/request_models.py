from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Union, Any, Dict, Union


class ClientInputTextContent(BaseModel):
    text: str
    type: Optional[str] = None


class ClientInputImgContent(BaseModel):
    detail: str
    type: str
    image_url: str


class ClientInput(BaseModel):
    role: str
    content: Union[str, List[ClientInputTextContent | ClientInputImgContent]]


class ClientRequest(BaseModel):
    model: str
    input: List[ClientInput] = Field(default_factory=list)
    stream: bool = False
    service_tier: Optional[str] = None

    @classmethod
    def _transform_content_item(cls, item: Dict) -> Dict:
        if not isinstance(item, dict):
            return item

        item_copy = item.copy()
        content_type = item_copy.get("type")

        type_mapping = {
            "text": "input_text",
            "image_url": "input_image"
        }
        
        if content_type in type_mapping:
            item_copy["type"] = type_mapping[content_type]
        
        if content_type == "image_url":
            item_copy["detail"] = "auto"
            if "image_url" in item_copy and isinstance(item_copy["image_url"], dict):
                item_copy["image_url"] = item_copy["image_url"].get("url")

        return item_copy

    @classmethod
    def _transform_content(cls, content: Any) -> list:
        if isinstance(content, str):
            return [{"type": "input_text", "text": content}]

        if isinstance(content, list):
            return [cls._transform_content_item(item) for item in content]

        return content

    @model_validator(mode="before")
    @classmethod
    def _transform_message_content(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        messages = data.get("messages", [])
        if not messages:
            return data

        transformed_messages = []
        for msg in messages:
            transformed_msg = {
                "role": msg.get("role", "user"),
                "content": cls._transform_content(msg.get("content"))
            }
            transformed_messages.append(transformed_msg)

        data["input"] = transformed_messages
        data.pop("messages", None)

        return data

    @model_validator(mode="before")
    @classmethod
    def _transform_input_content(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        messages = data.get("input", [])
        
        if isinstance(messages, str):
            data["input"] = [{
                "role": "user",
                "content": [{"type": "input_text", "text": messages}]
            }]

            return data

        if not messages:
            return data
        
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, str):
                msg["content"] = [{"type": "input_text", "text": content}]
            continue
        
        return data