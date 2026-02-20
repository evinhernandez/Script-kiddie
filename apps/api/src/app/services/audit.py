from __future__ import annotations

from typing import Any, Dict

from app.db.models import AuditEvent
from app.db.session import SessionLocal


def log(job_id: str, event_type: str, details: Dict[str, Any] | None = None, actor: str = "system"):
    with SessionLocal() as db:
        db.add(AuditEvent(
            job_id=job_id,
            event_type=event_type,
            actor=actor,
            details=details or {},
        ))
        db.commit()
