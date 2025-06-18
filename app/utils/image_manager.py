from typing import Optional
from fastapi_poe.types import Attachment
from datetime import timedelta

import redis
import os
import logging
import json

logger = logging.getLogger(__name__)


class RedisConnectionError(Exception):
    pass


class ImageManager:
    def __init__(self, redis_url: str = None, cache_ttl: int = 600):
        if redis_url is None:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Redis at {redis_url}: {e}")
            raise RedisConnectionError(f"Redis connection failed: {e}") from e
        
        self.cache_ttl = cache_ttl
        self.key_prefix = "image_attachment:"

    def _get_cache_key(self, image_url: str) -> str:
        return f"{self.key_prefix}{image_url}"
    
    def get_attachment(self, image_url: str) -> Optional[Attachment]:
        try:
            cache_key = self._get_cache_key(image_url)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                logger.info(f"Cache hit for image: {image_url[-4:]}")
                attachment_dict = json.loads(cached_data)
                return Attachment(**attachment_dict)
            else:
                logger.info(f"Cache miss for image: {image_url[-4:]}")
                return None
        except (redis.exceptions.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error retrieving attachment from cache for {image_url[-4:]}: {e}")
            return None
        
    def set_attachment(self, image_url: str, attachment: Attachment) -> bool:
        try:
            cache_key = self._get_cache_key(image_url)
            attachment_dict = attachment.model_dump()
            cached_data = json.dumps(attachment_dict)

            success = self.redis_client.setex(
                cache_key, 
                timedelta(seconds=self.cache_ttl), 
                cached_data
            )

            if success:
                logger.info(f"Cached attachment for image: {image_url[-4:]}")
            else:
                logger.warning(f"Failed to cache attachment for image: {image_url[-4:]}")
                
            return bool(success)

        except (redis.exceptions.RedisError, json.JSONEncodeError) as e:
            logger.error(f"Error caching attachment for {image_url[-4:]}: {e}")
            return False
        
    def clear_all_cache(self):
        try:
            pattern = f"{self.key_prefix}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} image caches")
        except redis.exceptions.RedisError as e:
            logger.error(f"Error clearing all cache: {e}")
            raise e