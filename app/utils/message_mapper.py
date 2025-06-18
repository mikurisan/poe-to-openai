from typing import List, Tuple, Optional, BinaryIO
from fastapi import HTTPException
from app.models.request_models import ClientInput
from io import BytesIO
from fastapi_poe.types import Attachment
from .image_manager import ImageManager

import logging
import fastapi_poe as fp
import re
import base64
import time
import string
import random


logger = logging.getLogger(__name__)


def _convert_role_to_poe(role: str) -> str:
    role_mapping = {
        "system": "system",
        "assistant": "bot",
        "user": "user",
        "bot": "bot"
    }

    if role in role_mapping:
        return role_mapping[role]

    logger.warning(f"Unknown role '{role}', defaulting to 'user'.")
    return "user"


def _parse_image_url(image_url: str) -> Tuple[BinaryIO, str]:
    pattern = r'^data:image/([^;,]+)(?:;[^,]*)?;base64,(.+)$'
    match = re.match(pattern, image_url)

    if not match:
        raise ValueError("Invalid image data url format.")
    
    image_format = match.group(1)
    base64_data = match.group(2)

    try:
        decoded_data = base64.b64decode(base64_data)
        return BytesIO(decoded_data), image_format
    except Exception as e:
        raise ValueError(f"Failed to decode base64 data: {e}")


def _normalize_image_format(image_format: str) -> str:
    format_mapping = {
        'jpeg': 'jpg',
        'svg+xml': 'svg',
        'x-icon': 'ico',
        'vnd.microsoft.icon': 'ico',
    }
    
    normalized = image_format.lower()
    return format_mapping.get(normalized, normalized)


def _generate_image_filename(
    image_format: str,
    prefix: str = "img"
) -> str:
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    extension = _normalize_image_format(image_format)
    return f"{prefix}_{timestamp}_{random_str}.{extension}"


async def _convert_image_to_attachment(
    img_data: BinaryIO,
    img_format: str,
    api_key: str
) -> Attachment:
    file_name = _generate_image_filename(img_format)
    attachment = await fp.upload_file(
        file=img_data,
        file_name=file_name,
        api_key=api_key
    )
    logger.info(f"Image {file_name} has been uploaed.")

    return attachment


async def _process_single_image(image_url: str, api_key: str, image_manager: ImageManager) -> Attachment:
    cached_attachment = image_manager.get_attachment(image_url)
    if cached_attachment:
        logger.info(f"Using cached attachment for image: {image_url[-4:]}")
        return cached_attachment

    logger.info(f"Processing image from source: {image_url[-4:]}")
    img_data, img_format = _parse_image_url(image_url)
    attachment = await _convert_image_to_attachment(img_data, img_format, api_key)
    if attachment:
        image_manager.set_attachment(image_url, attachment)

    return attachment


def _attach_image_to_last_user_message(
    protocol_messages: List[fp.ProtocolMessage], 
    attachment: Attachment
) -> None:
    for i in range(len(protocol_messages) - 1, -1, -1):
        if protocol_messages[i].role == "user":
            current_attachments = getattr(protocol_messages[i], 'attachments', None) or []
            protocol_messages[i].attachments = current_attachments + [attachment]
            return

    new_user_message = fp.ProtocolMessage(
        role="user",
        content="",
        attachments=[attachment]
    )
    
    protocol_messages.append(new_user_message)


async def to_poe_message(
        source_messages: List[ClientInput],
        api_key: str,
        image_manager: ImageManager
) -> Tuple[List[fp.ProtocolMessage], Optional[str]]:

    protocol_messages: List[fp.ProtocolMessage] = []
    instructions_str = "You are a helpful assistant."

    for msg in source_messages:
        for content in msg.content:
            if content.type == "input_image":
                attachment = await _process_single_image(content.image_url, api_key, image_manager)
                _attach_image_to_last_user_message(protocol_messages, attachment)
                continue

            if msg.role == "system":
                instructions_str = content.text

            poe_role = _convert_role_to_poe(msg.role)
            protocol_messages.append(fp.ProtocolMessage(
                role=poe_role, 
                content=content.text
            ))

    if not protocol_messages:
        raise HTTPException(
            status_code=400, detail="Messages list (derived from 'input') cannot be empty.")

    return protocol_messages, instructions_str