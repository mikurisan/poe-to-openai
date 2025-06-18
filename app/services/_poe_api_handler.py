import logging
import fastapi_poe as fp

from typing import List


logger = logging.getLogger(__name__)


class PoeApiHandler:
    def __init__(
        self,
        initial_key: str,
        bot_name: str
    ):
        self._api_key = initial_key
        self._bot_name = bot_name

    async def stream_content(
        self,
        messages: List[fp.ProtocolMessage],
        **kwargs
    ):
        MAX_RETRIES = 10
        while MAX_RETRIES > 0:
            try:
                async for partial in fp.get_bot_response(
                    messages=messages,
                    bot_name=self._bot_name,
                    api_key=self._api_key, 
                    skip_system_prompt=True,
                    **kwargs
                ):
                    if isinstance(partial, fp.PartialResponse) and partial.text and not partial.is_replace_response:
                        yield partial.text

                return

            except Exception as e:
                raise e

            finally:
                MAX_RETRIES -= 1