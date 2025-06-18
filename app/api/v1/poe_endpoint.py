from fastapi import APIRouter, Depends
from app.models.request_models import ClientRequest
from app.dependencies.instance import get_image_manager
from app.dependencies.utiles import get_api_key
from fastapi.responses import StreamingResponse, JSONResponse
from app.services import get_poe_response_streaming, get_poe_response_non_streaming
from app.services import get_poe_chat_completion_non_streaming, get_poe_chat_completion_streaming
from app.utils import to_poe_message
from app.utils import ImageManager

import logging


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
        "/v1/responses",
        response_model=None
)
async def create_model_responses(
    request_data: ClientRequest,
    poe_api_key: str = Depends(get_api_key),
    image_manager: ImageManager = Depends(get_image_manager)
):
    protocol_messages, instructions_str = await to_poe_message(request_data.input, poe_api_key, image_manager)

    if request_data.stream:
        return StreamingResponse(
            get_poe_response_streaming(
                bot_name=request_data.model,
                poe_api_key=poe_api_key,
                protocol_messages=protocol_messages,
                instructions_str=instructions_str,
                request_model_name=request_data.model,
            ),
            media_type="text/event-stream"
        )
    else:
        response = await get_poe_response_non_streaming(
            bot_name=request_data.model,
            poe_api_key=poe_api_key,
            protocol_messages=protocol_messages,
            instructions_str=instructions_str,
            request_model_name=request_data.model,
            )
        return JSONResponse(response)


@router.post(
        "/v1/chat/completions",
        response_model=None
)
async def create_model_chat_completions(
    request_data: ClientRequest,
    poe_api_key: str = Depends(get_api_key),
    image_manager: ImageManager = Depends(get_image_manager)
):
    protocol_messages, _ = await to_poe_message(request_data.input, poe_api_key, image_manager)

    if request_data.stream:
        return StreamingResponse(
            get_poe_chat_completion_streaming(
                bot_name=request_data.model,
                poe_api_key=poe_api_key,
                protocol_messages=protocol_messages,
                request_model_name=request_data.model,
            ),
            media_type="text/event-stream"
        )
    else:
        response =  await get_poe_chat_completion_non_streaming(
            bot_name=request_data.model,
            poe_api_key=poe_api_key,
            protocol_messages=protocol_messages,
            request_model_name=request_data.model,
            )
        return JSONResponse(response)
