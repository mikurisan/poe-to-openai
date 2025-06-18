from typing import List
from app.utils.sse_utils import SSEFormatter
from app.models.openai_responses import ResponseStatus, ResponseTypes, Response
from app.models.openai_responses import Item, Part
from app.models.openai_responses import ContentDelta
from ._poe_internal import create_completed_error_payload, create_usage
from ._poe_internal import sse_handshake, sse_finalize
from ._poe_api_handler import PoeApiHandler
from typing import Optional

import fastapi_poe as fp
import uuid
import time
import logging


logger = logging.getLogger(__name__)


async def get_poe_response_streaming(
        bot_name: str, poe_api_key: str,
        protocol_messages: List[fp.ProtocolMessage],
        instructions_str: str,
        request_model_name: str,
        temperature: Optional[float] = None
):
    response_id = f"resp-{uuid.uuid4().hex}"
    base_response_args = {
        "id": response_id, "model": request_model_name,
        "instructions": instructions_str,"temperature": temperature
    }
    sse_formatter = SSEFormatter()
    item_id = f"msg-{uuid.uuid4().hex}"
    accumulated_text = ""

    try:
        async for handshake_event in sse_handshake(sse_formatter, base_response_args, item_id):
            yield handshake_event

        poe_handler = PoeApiHandler(poe_api_key, bot_name)
        async for text_chunk in poe_handler.stream_content(
            messages=protocol_messages, temperature=temperature
        ):
            accumulated_text += text_chunk
            delta_data = ContentDelta(
                type=ResponseTypes.OUTPUT_TEXT_DELTA.value,
                item_id=item_id,
                delta=text_chunk
            )
            yield sse_formatter.format_reponse(ResponseTypes.OUTPUT_TEXT_DELTA.value, delta_data.to_dict())

        async for finalize_event in sse_finalize(
            sse_formatter, base_response_args, item_id,
            accumulated_text, protocol_messages
        ):
            yield finalize_event

    except Exception as e:
        import traceback

        usage = create_usage(protocol_messages, accumulated_text)
        tb_str = traceback.format_exc()

        logger.error(
            f"An unexpected error occurred during streaming: {str(e)}\n{tb_str}"
        )
        completed_error_payload = create_completed_error_payload(
            base_response_args.copy(),
            type=ResponseTypes.FAILED.value,
            error_message=str(e),
            usage=usage
        )
        yield SSEFormatter.format_reponse(
            ResponseTypes.COMPLETED.value,
            {'type': ResponseTypes.COMPLETED.value, 'response': completed_error_payload.to_dict()}
        )
        raise e


async def get_poe_response_non_streaming(
        bot_name: str, poe_api_key: str,
        protocol_messages: List[fp.ProtocolMessage],
        instructions_str: str,
        request_model_name: str,
        temperature: Optional[float] = None
):
    response_id = f"resp-{uuid.uuid4().hex}"
    base_response_args = {
        "id": response_id, "model": request_model_name,
        "instructions": instructions_str, "temperature": temperature
    }
    item_id = f"msg-{uuid.uuid4().hex}"
    accumulated_text = ""

    try:
        poe_handler = PoeApiHandler(poe_api_key, bot_name)
        async for text_chunk in poe_handler.stream_content(
            messages=protocol_messages, temperature=temperature
        ):
            accumulated_text += text_chunk

        part_base_payload = Part(type="output_text", text=accumulated_text)
        item_base_payload = Item(
            id=item_id, type="message",
            status=ResponseStatus.COMPLETED.value,
            role="assistant",
            content= [part_base_payload]
        )
        usage = create_usage(protocol_messages, accumulated_text)
        response_completed_payload = Response(
            **base_response_args,
            status=ResponseStatus.COMPLETED.value,
            created_at=int(time.time()),
            output=[item_base_payload],
            usage=usage
            )
        return response_completed_payload.to_dict()

    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        logger.error(
            f"An unexpected error occurred during non streaming: {str(e)}\n{tb_str}"
        )
        completed_error_payload = create_completed_error_payload(
            base_response_args.copy(),
            type=ResponseTypes.FAILED.value,
            error_message=str(e),
            error_code="server_error"
        )
        return completed_error_payload.to_dict()