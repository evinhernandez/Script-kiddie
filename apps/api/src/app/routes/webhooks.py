from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import require_api_key
from app.db.models import Webhook
from app.db.session import SessionLocal

router = APIRouter()

_ALLOWED_EVENTS = {"scan.completed", "policy.block", "policy.allow"}


def _validate_webhook_url(url: str) -> str:
    """Validate webhook URL is HTTPS and not targeting private/internal networks."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise HTTPException(400, "webhook URL must use HTTPS")
    if not parsed.hostname:
        raise HTTPException(400, "webhook URL must have a valid hostname")

    # Block private/reserved IPs
    try:
        addrs = socket.getaddrinfo(parsed.hostname, None)
        for _, _, _, _, sockaddr in addrs:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                raise HTTPException(400, "webhook URL must not target private/internal networks")
    except socket.gaierror:
        raise HTTPException(400, "webhook URL hostname could not be resolved")

    return url


class WebhookRequest(BaseModel):
    url: str
    events: list[str] = ["scan.completed"]
    secret: str = ""


@router.post("", dependencies=[Depends(require_api_key)])
def create_webhook(req: WebhookRequest):
    _validate_webhook_url(req.url)

    # Validate events
    invalid = set(req.events) - _ALLOWED_EVENTS
    if invalid:
        raise HTTPException(400, f"invalid events: {invalid}. Allowed: {_ALLOWED_EVENTS}")

    with SessionLocal() as db:
        wh = Webhook(url=req.url, events=req.events, secret=req.secret)
        db.add(wh)
        db.commit()
        db.refresh(wh)
        return {"id": wh.id, "url": wh.url, "events": wh.events}


@router.get("", dependencies=[Depends(require_api_key)])
def list_webhooks():
    with SessionLocal() as db:
        rows = db.query(Webhook).all()
        return [{
            "id": w.id, "url": w.url, "events": w.events, "active": w.active,
            "created_at": str(w.created_at),
        } for w in rows]


@router.delete("/{webhook_id}", dependencies=[Depends(require_api_key)])
def delete_webhook(webhook_id: int):
    with SessionLocal() as db:
        wh = db.get(Webhook, webhook_id)
        if not wh:
            raise HTTPException(404, "webhook not found")
        db.delete(wh)
        db.commit()
    return {"status": "deleted"}
