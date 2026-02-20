from __future__ import annotations

from sqlalchemy import func as sa_func

from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.db.models import Finding, Job, ModelCall
from app.db.session import SessionLocal

router = APIRouter()


@router.get("", dependencies=[Depends(require_api_key)])
def get_stats():
    with SessionLocal() as db:
        total_jobs = db.query(sa_func.count(Job.id)).scalar() or 0
        total_findings = db.query(sa_func.count(Finding.id)).scalar() or 0
        total_model_calls = db.query(sa_func.count(ModelCall.id)).scalar() or 0

        # Severity breakdown
        severity_counts = {}
        for row in db.query(Finding.severity, sa_func.count(Finding.id)).group_by(Finding.severity).all():
            severity_counts[row[0]] = row[1]

        # Decision breakdown
        decision_counts = {}
        for row in db.query(Job.decision, sa_func.count(Job.id)).group_by(Job.decision).all():
            decision_counts[row[0]] = row[1]

        # Top rules
        top_rules = []
        for row in db.query(Finding.rule_id, sa_func.count(Finding.id)).group_by(Finding.rule_id).order_by(
            sa_func.count(Finding.id).desc()
        ).limit(10).all():
            top_rules.append({"rule_id": row[0], "count": row[1]})

        # Total cost
        total_cost = db.query(sa_func.sum(ModelCall.estimated_cost_usd)).scalar() or 0.0

    return {
        "total_jobs": total_jobs,
        "total_findings": total_findings,
        "total_model_calls": total_model_calls,
        "total_estimated_cost_usd": round(float(total_cost), 4),
        "by_severity": severity_counts,
        "by_decision": decision_counts,
        "top_rules": top_rules,
    }
