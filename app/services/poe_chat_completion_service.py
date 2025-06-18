from typing import List
from app.utils import SSEFormatter
from app.models.openai_chat_completions import Message
from app.models.openai_chat_completions import Delta
from typing import Optional
from ._poe_api_handler import PoeApiHandler
from ._poe_internal import craete_chat_completion

import fastapi_poe as fp
import uuid
import logging


logger = logging.getLogger(__name__)


async def get_poe_chat_completion_streaming(
        bot_name: str, poe_api_key: str,
        protocol_messages: List[fp.ProtocolMessage],
        request_model_name: str,
        temperature: Optional[float] = None
):
    response_id = f"chatcmpl-{uuid.uuid4().hex}"
    system_fingerprint = f"fp_{uuid.uuid4().hex[:10]}"
    base_response_args = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "system_fingerprint": system_fingerprint,
        "model": request_model_name,
    }
    sse_formatter = SSEFormatter()

    is_first_chunk = True
    try:
        poe_handler = PoeApiHandler(poe_api_key, bot_name)
        async for text_chunk in poe_handler.stream_content(
            messages=protocol_messages, temperature=temperature
        ):
            if is_first_chunk:
                delta_payload = Delta(
                    role="assistant",
                    content=text_chunk
                )
                is_first_chunk = False
            else:
                delta_payload = Delta(content=text_chunk)

            chat_completion_payload = craete_chat_completion(
                base_args=base_response_args.copy(),
                delta=delta_payload,
            )

            yield sse_formatter.format_chat_completion(chat_completion_payload.to_dict())

    except Exception as e:
        import traceback

        tb_str = traceback.format_exc()
        logger.error(
            f"An unexpected error occurred during streaming: {str(e)}\n{tb_str}"
        )

        error_message_payload = Message(refusal=str(e))
        error_chat_completion_payload = craete_chat_completion(
            base_args=base_response_args.copy(),
            message=error_message_payload,
            finish_reason="stop"
        )

        yield sse_formatter.format_chat_completion(error_chat_completion_payload.to_dict())
        raise e

    final_chat_completion_payload = craete_chat_completion(
        base_args=base_response_args.copy(),
        finish_reason="stop"
    )

    yield sse_formatter.format_chat_completion(final_chat_completion_payload.to_dict())

    yield sse_formatter.format_chat_completion("[DONE]")


async def get_poe_chat_completion_non_streaming(
        bot_name: str, poe_api_key: str,
        protocol_messages: List[fp.ProtocolMessage],
        request_model_name: str,
        temperature: Optional[float] = None
):
    response_id = f"chatcmpl-{uuid.uuid4().hex}"
    system_fingerprint = f"fp_{uuid.uuid4().hex[:10]}"
    base_response_args = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "system_fingerprint": system_fingerprint,
        "model": request_model_name,
    }

    accumulated_text = ""
    try:
        poe_handler = PoeApiHandler(poe_api_key, bot_name)
        async for text_chunk in poe_handler.stream_content(
            messages=protocol_messages, temperature=temperature
        ):
            accumulated_text += text_chunk

    except Exception as e:
        import traceback

        tb_str = traceback.format_exc()
        logger.error(
            f"An unexpected error occurred during streaming: {str(e)}\n{tb_str}"
        )

        error_message_payload = Message(refusal=str(e),role="assistant")
        error_chat_completion_payload = craete_chat_completion(
            base_args=base_response_args.copy(),
            message=error_message_payload,
            finish_reason="stop"
        )

        return error_chat_completion_payload.to_dict()

    message_payload = Message(content=accumulated_text, role="assistant")
    chat_completion_payload = craete_chat_completion(
        base_response_args.copy(),
        message=message_payload,
        finish_reason="stop"
    )

    return chat_completion_payload.to_dict()