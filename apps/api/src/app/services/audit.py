from __future__ import annotations
from typing import Dict, Any
from app.db.session import SessionLocal
from app.db.models import AuditEvent

def log(job_id: str, event_type: str, details: Dict[str, Any] | None = None):
    with SessionLocal() as db:
        db.add(AuditEvent(job_id=job_id, event_type=event_type, details=details or {}))
        db.commit()
