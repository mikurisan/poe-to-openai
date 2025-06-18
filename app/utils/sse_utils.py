from pydantic import BaseModel
from typing import Any

import json


class SSEFormatter(BaseModel):
    
    def format_reponse(self, event: str, data: Any) -> str:
        data_json = json.dumps(data) if not isinstance(data, str) else data
        return f"event: {event}\ndata: {data_json}\n\n"

    def format_chat_completion(self, data: Any) -> str:
        data_json = json.dumps(data) if not isinstance(data, str) else data
        return f"data: {data_json}\n\n"