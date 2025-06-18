from typing import List
from app.utils.sse_utils import SSEFormatter
from app.models.openai_responses import ResponseStatus, ResponseTypes, Response
from app.models.openai_responses import Item, OutputItem, Part, ContentPart
from app.models.openai_responses import ContentText, Error
from app.models.openai_responses import Usage
from app.utils.token import count_tokens
from app.models.openai_chat_completions import Delta, Choice, ChatCompletion, Message
from typing import Dict, Any, AsyncGenerator, Optional

import fastapi_poe as fp
import time


def create_completed_error_payload(
    base_args: Dict[str, Any],
    type: str,
    usage: Usage,
    error_message: Optional[str] = None,
    error_code: Optional[str] = None
) -> Response:    
    error_obj = Error(type=type, message=error_message, error_code=error_code)
    return Response(
        **base_args,
        store=False,
        created_at=int(time.time()),
        status="failed",
        error=error_obj,
        usage=usage
    )


def create_usage(
    input_messages: List[fp.ProtocolMessage],
    output_messages: str
) -> Usage:
    
    input_token_counts = 0
    output_token_counts = count_tokens(output_messages)

    for msg in input_messages:
        input_token_counts += count_tokens(msg.content)
    
    return Usage(
        input_tokens=input_token_counts,
        output_tokens=output_token_counts,
        total_tokens=input_token_counts+output_token_counts
    )


async def sse_handshake(
    sse_formatter: SSEFormatter,
    base_response_args: Dict[str, Any],
    item_id: str
) -> AsyncGenerator[str, None]:
    
    created_payload = Response(
        **base_response_args,
        created_at=int(time.time()),
        status=ResponseStatus.IN_PROGRESS.value
    )
    yield sse_formatter.format_reponse(
        ResponseTypes.CREATED.value,
        {'type': ResponseTypes.CREATED.value, 'response': created_payload.to_dict()}
    )
    
    in_progress_payload = Response(
        **base_response_args, 
        created_at=int(time.time()),
        status=ResponseStatus.IN_PROGRESS.value
    )
    yield sse_formatter.format_reponse(
        ResponseTypes.IN_PROGRESS.value,
        {'type': ResponseTypes.IN_PROGRESS.value, 'response': in_progress_payload.to_dict()}
    )

    item_base_payload = Item(
        id=item_id,
        type="message",
        status=ResponseStatus.IN_PROGRESS.value,
        role="assistant"
    )
    output_item_added_payload = OutputItem(
        type=ResponseTypes.OUTPUT_ITEM_ADDED.value,
        item=item_base_payload
    )
    yield sse_formatter.format_reponse(ResponseTypes.OUTPUT_ITEM_ADDED.value, output_item_added_payload.to_dict())

    part_base_payload = Part(type="output_text")
    content_part_payload = ContentPart(
        type=ResponseTypes.CONTENT_PART_ADDED.value,
        item_id=item_id,
        part=part_base_payload
    )
    yield sse_formatter.format_reponse(ResponseTypes.CONTENT_PART_ADDED.value, content_part_payload.to_dict())
    

async def sse_finalize(
    sse_formatter: SSEFormatter,
    base_response_args: Dict[str, Any],
    item_id: str,
    accumulated_text: str,
    protocol_messages: List[fp.ProtocolMessage]
) -> AsyncGenerator[str, None]:

    output_text_done_payload = ContentText(
        type=ResponseTypes.OUTPUT_TEXT_DONE.value,
        item_id=item_id,
        text=accumulated_text
    )
    yield sse_formatter.format_reponse(ResponseTypes.OUTPUT_TEXT_DONE.value, output_text_done_payload.to_dict())

    part_base_payload = Part(type="output_text", text=accumulated_text)
    content_part_done_payload = ContentPart(
        type=ResponseTypes.CONTENT_PART_DONE.value,
        item_id=item_id,
        part=part_base_payload
    )
    yield sse_formatter.format_reponse(ResponseTypes.CONTENT_PART_DONE.value, content_part_done_payload.to_dict())

    item_base_payload = Item(
        id=item_id, type="message",
        status=ResponseStatus.COMPLETED.value,
        role="assistant",
        content= [part_base_payload]
    )
    output_item_done_payload = OutputItem(
        type=ResponseTypes.OUTPUT_ITEM_DONE.value,
        item=item_base_payload
    )
    yield sse_formatter.format_reponse(ResponseTypes.OUTPUT_ITEM_DONE.value, output_item_done_payload.to_dict())

    usage = create_usage(protocol_messages, accumulated_text)
    response_completed_payload = Response(
        **base_response_args.copy(), status=ResponseStatus.COMPLETED.value,
        created_at=int(time.time()), output=[item_base_payload], usage=usage
    )
    yield sse_formatter.format_reponse(
        ResponseTypes.COMPLETED.value,
        {'type': ResponseTypes.COMPLETED.value, 'response': response_completed_payload.to_dict()}
    )


def craete_chat_completion(
    base_args: Dict,
    delta: Optional[Delta | Dict[str, Any]] = None,
    message: Optional[Message | Dict[str, Any]] = None,
    finish_reason: Optional[str] = None
) -> ChatCompletion:
    choice = Choice(
        delta=delta,
        message=message,
        index=0,
        finish_reason=finish_reason
    )
    return ChatCompletion(
        **base_args,
        created=int(time.time()),
        choices=[choice]
    )