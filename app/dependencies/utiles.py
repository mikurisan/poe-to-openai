from fastapi import Header, HTTPException
from typing import Optional


def _extract_api_key(
    authorization: Optional[str],
    x_api_key: Optional[str],
    api_key: Optional[str]
) -> Optional[str]:
    if x_api_key:
        return x_api_key
    if api_key:
        return api_key
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    return None


async def get_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    api_key: Optional[str] = Header(None, alias="api-key"),
) -> str:
    extracted_api_key = _extract_api_key(authorization, x_api_key, api_key)
    if not extracted_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    return extracted_api_key