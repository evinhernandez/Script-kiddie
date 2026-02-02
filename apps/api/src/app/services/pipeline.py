from __future__ import annotations
import os, json, hashlib
from pathlib import Path
from sqlalchemy.orm import Session

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL_ANALYZER, OLLAMA_MODEL_JUDGE, POLICY_PATH
from app.db.session import SessionLocal
from app.db.models import Job, Finding, ModelCall
from app.services.audit import log as audit_log
from app.services.policy import load_policy, evaluate

from scriptkiddie_core.scanner import scan as static_scan
from scriptkiddie_core.sarif import to_sarif

from model_gateway.providers.ollama import OllamaProvider
from model_gateway.orchestrator import JudgeConfig, run_multi_judge

def run_pipeline(payload: dict) -> dict:
    job_id = payload["job_id"]

    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            return {"error": "job not found"}
        job.status = "running"
        job.policy_path = job.policy_path or POLICY_PATH
        db.commit()

    audit_log(job_id, "job_started", {"job_id": job_id})

    root = Path(job.target_path).resolve()
    ruleset_path = Path("/workspace") / job.ruleset

    # 1) Static scan
    findings_models = static_scan(root=root, ruleset_path=ruleset_path, max_file_kb=512)
    findings = [f.model_dump() for f in findings_models]

    with SessionLocal() as db:
        db.query(Finding).filter(Finding.job_id == job_id).delete()
        for f in findings_models:
            db.add(Finding(
                job_id=job_id,
                rule_id=f.rule_id,
                title=f.title,
                category=f.category,
                severity=f.severity,
                file=f.file,
                line=f.line,
                match=f.match,
                message=f.message,
                remediation=f.remediation
            ))
        db.commit()

    audit_log(job_id, "static_scan_done", {"count": len(findings)})

    # 2) AI review (Ollama)
    ai_review = None
    if job.ai_review:
        provider = OllamaProvider(base_url=OLLAMA_BASE_URL)
        artifact = summarize_target(root)

        analyzer_prompt = f"""You are a secure coding reviewer.
Analyze the artifact excerpt for AI/agent security issues:
- executing model output
- unsafe tool use
- secrets/NHI handling
- unsafe persistence/memory

Keep it short and actionable.

Artifact:
{artifact[:7000]}
"""
        analyzer_resp = provider.generate(OLLAMA_MODEL_ANALYZER, prompt=analyzer_prompt, system="You are a security reviewer.")
        _store_model_call(job_id, provider="ollama", model=OLLAMA_MODEL_ANALYZER, role="analyzer",
                          request=analyzer_prompt, response=analyzer_resp.text, parsed={})
        audit_log(job_id, "analyzer_done", {"model": OLLAMA_MODEL_ANALYZER})

        # Judges: self-consistency (same model twice) — you can add more models later
        judges = [
            JudgeConfig(provider=provider, model=OLLAMA_MODEL_JUDGE),
            JudgeConfig(provider=provider, model=OLLAMA_MODEL_JUDGE),
        ]

        ai_review = run_multi_judge(
            artifact=artifact,
            findings=[{"rule_id": f.get("rule_id"), "severity": f.get("severity"), "title": f.get("title")} for f in findings],
            judges=judges
        )

        # Persist judge results
        for v in ai_review["verdicts"]:
            _store_model_call(job_id, provider="ollama", model=v["judge"].split(":")[1], role="judge",
                              request="judge_prompt_hash_only", response=v.get("raw",""), parsed=v.get("parsed") or {})

        audit_log(job_id, "judge_done", {"aggregate": ai_review.get("aggregate")})

    # 3) Policy decision
    policy = load_policy(Path("/workspace") / (job.policy_path or POLICY_PATH))
    decision = evaluate(policy, findings, (ai_review or {}).get("aggregate") if ai_review else None)

    with SessionLocal() as db:
        job = db.get(Job, job_id)
        job.decision = decision["decision"]
        job.decision_reason = decision["reason"]
        job.status = "done"
        db.commit()

    audit_log(job_id, "job_done", {"decision": decision})

    return {"job_id": job_id, "decision": decision, "findings": findings, "ai_review": ai_review}

def summarize_target(root: Path) -> str:
    parts = []
    allow = {".py",".js",".ts",".md",".yml",".yaml",".json",".env"}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix in allow:
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            parts.append(f"\n--- {p.relative_to(root)} ---\n" + txt[:2500])
        if len(parts) >= 25:
            break
    return "\n".join(parts)

def _store_model_call(job_id: str, provider: str, model: str, role: str, request: str, response: str, parsed: dict):
    h = hashlib.sha256(request.encode("utf-8")).hexdigest()
    with SessionLocal() as db:
        db.add(ModelCall(
            job_id=job_id,
            provider=provider,
            model=model,
            role=role,
            request_hash=h,
            response_excerpt=(response or "")[:2000],
            parsed=parsed or {}
        ))
        db.commit()
