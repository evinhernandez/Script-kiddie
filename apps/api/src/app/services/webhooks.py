from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Dict

import requests

from app.db.models import Webhook
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _sign_payload(payload: str, secret: str) -> str:
    """HMAC-SHA256 signature."""
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def dispatch(event_type: str, data: Dict[str, Any]):
    """Send webhook to all registered endpoints for this event."""
    with SessionLocal() as db:
        webhooks = db.query(Webhook).filter(Webhook.active.is_(True)).all()
        targets = []
        for wh in webhooks:
            events = wh.events if isinstance(wh.events, list) else []
            if event_type in events or "*" in events:
                targets.append({"url": wh.url, "secret": wh.secret})

    payload = json.dumps({"event": event_type, "data": data})

    for target in targets:
        headers = {"Content-Type": "application/json", "X-ScriptKiddie-Event": event_type}
        if target["secret"]:
            headers["X-ScriptKiddie-Signature"] = _sign_payload(payload, target["secret"])

        try:
            resp = requests.post(target["url"], data=payload, headers=headers, timeout=10)
            logger.info("Webhook %s responded %d", target["url"], resp.status_code)
        except Exception as e:
            logger.warning("Webhook %s failed: %s", target["url"], e)
