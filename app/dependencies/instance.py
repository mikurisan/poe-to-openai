from fastapi import Request
from app.utils import ImageManager


def get_image_manager(request: Request) -> ImageManager:
    return request.app.state.image_manager