from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import require_api_key
from app.db.models import Finding, FindingSuppression, Job, ModelCall
from app.db.session import SessionLocal
from app.services.audit import log as audit_log
from app.worker import run_scan_job
from scriptkiddie_core.exports import to_csv, to_json, to_markdown
from scriptkiddie_core.models import Finding as FindingModel
from scriptkiddie_core.sarif import to_sarif

router = APIRouter()

# Allowed base directories for scan targets
_ALLOWED_SCAN_ROOTS = [Path("/workspace"), Path("/scan")]

# Only allow safe relative path segments
_SAFE_PATH = re.compile(r"^[a-zA-Z0-9_./-]+$")


def _validate_target_path(target_path: str) -> str:
    """Validate target_path is under an allowed root directory."""
    resolved = Path(target_path).resolve()
    for allowed_root in _ALLOWED_SCAN_ROOTS:
        try:
            if resolved == allowed_root.resolve() or str(resolved).startswith(str(allowed_root.resolve()) + "/"):
                return str(resolved)
        except OSError:
            continue
    raise HTTPException(400, f"target_path must be under one of: {[str(r) for r in _ALLOWED_SCAN_ROOTS]}")


def _validate_relative_path(rel_path: str, label: str) -> str:
    """Validate a relative path has no traversal sequences."""
    if ".." in rel_path or rel_path.startswith("/"):
        raise HTTPException(400, f"{label} must be a relative path without '..'")
    if not _SAFE_PATH.match(rel_path):
        raise HTTPException(400, f"{label} contains invalid characters")
    return rel_path


class CreateJobRequest(BaseModel):
    target_path: str = "/workspace"
    ruleset: str = "rulesets/owasp-llm-top10.yml"
    ai_review: bool = True
    policy_path: str = "policies/default.yml"


class SuppressRequest(BaseModel):
    reason: str = ""
    suppressed_by: str = ""


# --- Job CRUD ---


@router.post("", dependencies=[Depends(require_api_key)])
def create_job(req: CreateJobRequest):
    # Validate all paths before creating the job
    validated_target = _validate_target_path(req.target_path)
    validated_ruleset = _validate_relative_path(req.ruleset, "ruleset")
    validated_policy = _validate_relative_path(req.policy_path, "policy_path")

    job_id = uuid.uuid4().hex
    with SessionLocal() as db:
        db.add(Job(
            id=job_id,
            status="queued",
            target_path=validated_target,
            ruleset=validated_ruleset,
            ai_review=req.ai_review,
            policy_path=validated_policy,
        ))
        db.commit()
    run_scan_job.delay({"job_id": job_id})
    return {"job_id": job_id}


@router.get("", dependencies=[Depends(require_api_key)])
def list_jobs(limit: int = Query(default=50, ge=1, le=500)):
    with SessionLocal() as db:
        rows = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
        return [{
            "id": j.id, "status": j.status, "ruleset": j.ruleset, "ai_review": j.ai_review,
            "decision": j.decision, "created_at": str(j.created_at),
        } for j in rows]


@router.get("/{job_id}", dependencies=[Depends(require_api_key)])
def get_job(job_id: str):
    with SessionLocal() as db:
        j = db.get(Job, job_id)
        if not j:
            raise HTTPException(404, "job not found")
        return {
            "id": j.id, "status": j.status, "target_path": j.target_path, "ruleset": j.ruleset,
            "ai_review": j.ai_review, "policy_path": j.policy_path,
            "decision": j.decision, "decision_reason": j.decision_reason,
        }


@router.get("/{job_id}/results", dependencies=[Depends(require_api_key)])
def get_results(job_id: str):
    with SessionLocal() as db:
        j = db.get(Job, job_id)
        if not j:
            raise HTTPException(404, "job not found")
        findings = db.query(Finding).filter(Finding.job_id == job_id).all()
        calls = db.query(ModelCall).filter(ModelCall.job_id == job_id).all()
        return {
            "job": {
                "id": j.id, "status": j.status, "ruleset": j.ruleset,
                "decision": j.decision, "decision_reason": j.decision_reason,
            },
            "findings": [
                {
                    "rule_id": f.rule_id, "severity": f.severity, "category": f.category,
                    "title": f.title, "file": f.file, "line": f.line,
                    "message": f.message, "remediation": f.remediation, "match": f.match,
                } for f in findings
            ],
            "model_calls": [
                {
                    "provider": c.provider, "model": c.model, "role": c.role,
                    "parsed": c.parsed, "response_excerpt": c.response_excerpt,
                    "prompt_tokens": c.prompt_tokens, "completion_tokens": c.completion_tokens,
                    "estimated_cost_usd": c.estimated_cost_usd,
                } for c in calls
            ],
        }


# --- SARIF & Export ---


@router.get("/{job_id}/sarif", dependencies=[Depends(require_api_key)])
def export_sarif(job_id: str):
    with SessionLocal() as db:
        j = db.get(Job, job_id)
        if not j:
            raise HTTPException(404, "job not found")
        findings = db.query(Finding).filter(Finding.job_id == job_id).all()

    fm = [
        FindingModel(
            rule_id=f.rule_id, title=f.title, category=f.category, severity=f.severity,
            file=f.file, line=f.line, match=f.match, message=f.message, remediation=f.remediation,
        ) for f in findings
    ]
    return to_sarif(fm)


@router.get("/{job_id}/export", dependencies=[Depends(require_api_key)])
def export_findings(job_id: str, format: str = Query("json", pattern="^(csv|json|md)$")):
    with SessionLocal() as db:
        j = db.get(Job, job_id)
        if not j:
            raise HTTPException(404, "job not found")
        findings = db.query(Finding).filter(Finding.job_id == job_id).all()

    fm = [
        FindingModel(
            rule_id=f.rule_id, title=f.title, category=f.category, severity=f.severity,
            file=f.file, line=f.line, match=f.match, message=f.message, remediation=f.remediation,
        ) for f in findings
    ]

    meta = {"target": j.target_path, "ruleset": j.ruleset, "decision": j.decision}

    if format == "csv":
        return {"content_type": "text/csv", "data": to_csv(fm)}
    elif format == "md":
        return {"content_type": "text/markdown", "data": to_markdown(fm, job_meta=meta)}
    else:
        return {"content_type": "application/json", "data": json.loads(to_json(fm, job_meta=meta))}


# --- Baseline Diff ---


@router.get("/{job_id}/diff", dependencies=[Depends(require_api_key)])
def diff_findings_endpoint(job_id: str, baseline_job_id: str = Query(...)):
    from scriptkiddie_core.baseline import diff_findings

    with SessionLocal() as db:
        j = db.get(Job, job_id)
        if not j:
            raise HTTPException(404, "current job not found")
        bj = db.get(Job, baseline_job_id)
        if not bj:
            raise HTTPException(404, "baseline job not found")

        current_rows = db.query(Finding).filter(Finding.job_id == job_id).all()
        baseline_rows = db.query(Finding).filter(Finding.job_id == baseline_job_id).all()

    def _to_finding_model(f):
        return FindingModel(
            rule_id=f.rule_id, title=f.title, category=f.category, severity=f.severity,
            file=f.file, line=f.line, match=f.match, message=f.message, remediation=f.remediation,
        )

    current = [_to_finding_model(f) for f in current_rows]
    baseline = [_to_finding_model(f) for f in baseline_rows]
    result = diff_findings(current, baseline)

    return {
        "summary": result["summary"],
        "new": [f.model_dump() for f in result["new"]],
        "fixed": [f.model_dump() for f in result["fixed"]],
        "unchanged": [f.model_dump() for f in result["unchanged"]],
    }


# --- Finding Suppression ---


@router.post("/findings/{fingerprint}/suppress", dependencies=[Depends(require_api_key)])
def suppress_finding(fingerprint: str, req: SuppressRequest):
    with SessionLocal() as db:
        existing = db.query(FindingSuppression).filter(FindingSuppression.fingerprint == fingerprint).first()
        if existing:
            raise HTTPException(409, "already suppressed")
        # Find the rule_id from any finding with this fingerprint (if available)
        rule_id = ""
        db.add(FindingSuppression(
            fingerprint=fingerprint,
            rule_id=rule_id,
            reason=req.reason,
            suppressed_by=req.suppressed_by,
        ))
        db.commit()
    return {"fingerprint": fingerprint, "status": "suppressed"}


@router.delete("/findings/{fingerprint}/suppress", dependencies=[Depends(require_api_key)])
def unsuppress_finding(fingerprint: str):
    with SessionLocal() as db:
        row = db.query(FindingSuppression).filter(FindingSuppression.fingerprint == fingerprint).first()
        if not row:
            raise HTTPException(404, "suppression not found")
        db.delete(row)
        db.commit()
    return {"fingerprint": fingerprint, "status": "unsuppressed"}


@router.get("/suppressions", dependencies=[Depends(require_api_key)])
def list_suppressions():
    with SessionLocal() as db:
        rows = db.query(FindingSuppression).all()
        return [{
            "fingerprint": s.fingerprint,
            "rule_id": s.rule_id,
            "reason": s.reason,
            "suppressed_by": s.suppressed_by,
            "created_at": str(s.created_at),
        } for s in rows]
