from __future__ import annotations
import uuid
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.auth import require_api_key
from app.db.session import SessionLocal
from app.db.models import Job, Finding, ModelCall
from app.worker import run_scan_job

from scriptkiddie_core.sarif import to_sarif
from scriptkiddie_core.models import Finding as FindingModel

router = APIRouter()

class CreateJobRequest(BaseModel):
    target_path: str = "/workspace"
    ruleset: str = "rulesets/owasp-llm-top10.yml"
    ai_review: bool = True
    policy_path: str = "policies/default.yml"

@router.post("", dependencies=[Depends(require_api_key)])
def create_job(req: CreateJobRequest):
    job_id = uuid.uuid4().hex
    with SessionLocal() as db:
        db.add(Job(
            id=job_id,
            status="queued",
            target_path=req.target_path,
            ruleset=req.ruleset,
            ai_review=req.ai_review,
            policy_path=req.policy_path
        ))
        db.commit()
    run_scan_job.delay({"job_id": job_id})
    return {"job_id": job_id}

@router.get("")
def list_jobs(limit: int = 50):
    with SessionLocal() as db:
        rows = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
        return [{
            "id": j.id, "status": j.status, "ruleset": j.ruleset, "ai_review": j.ai_review,
            "decision": j.decision, "created_at": str(j.created_at)
        } for j in rows]

@router.get("/{job_id}")
def get_job(job_id: str):
    with SessionLocal() as db:
        j = db.get(Job, job_id)
        if not j:
            raise HTTPException(404, "job not found")
        return {
            "id": j.id, "status": j.status, "target_path": j.target_path, "ruleset": j.ruleset,
            "ai_review": j.ai_review, "policy_path": j.policy_path,
            "decision": j.decision, "decision_reason": j.decision_reason
        }

@router.get("/{job_id}/results")
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
                "decision": j.decision, "decision_reason": j.decision_reason
            },
            "findings": [
                {
                    "rule_id": f.rule_id, "severity": f.severity, "category": f.category,
                    "title": f.title, "file": f.file, "line": f.line,
                    "message": f.message, "remediation": f.remediation, "match": f.match
                } for f in findings
            ],
            "model_calls": [
                {
                    "provider": c.provider, "model": c.model, "role": c.role,
                    "parsed": c.parsed, "response_excerpt": c.response_excerpt
                } for c in calls
            ]
        }

@router.get("/{job_id}/sarif")
def export_sarif(job_id: str):
    with SessionLocal() as db:
        j = db.get(Job, job_id)
        if not j:
            raise HTTPException(404, "job not found")
        findings = db.query(Finding).filter(Finding.job_id == job_id).all()

    fm = [
        FindingModel(
            rule_id=f.rule_id, title=f.title, category=f.category, severity=f.severity,
            file=f.file, line=f.line, match=f.match, message=f.message, remediation=f.remediation
        ) for f in findings
    ]
    return to_sarif(fm)
