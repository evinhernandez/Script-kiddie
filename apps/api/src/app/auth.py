from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from app.config import API_KEY


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not x_api_key or not API_KEY:
        raise HTTPException(status_code=401, detail="missing or invalid API key")
    if not hmac.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="missing or invalid API key")
