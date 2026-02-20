from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL_ANALYZER, OLLAMA_MODEL_JUDGE, POLICY_PATH
from app.db.models import Finding, Job, ModelCall
from app.db.session import SessionLocal
from app.services.audit import log as audit_log
from app.services.policy import evaluate, load_policy
from model_gateway.orchestrator import JudgeConfig, run_multi_judge
from model_gateway.pricing import estimate_cost
from model_gateway.registry import load_providers
from scriptkiddie_core.sarif import to_sarif
from scriptkiddie_core.scanner import scan as static_scan


def run_pipeline(payload: dict) -> dict:
    job_id = payload["job_id"]

    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            return {"error": "job not found"}
        job.status = "running"
        job.policy_path = job.policy_path or POLICY_PATH
        target_path = job.target_path
        ruleset_rel = job.ruleset
        ai_review_enabled = job.ai_review
        policy_rel = job.policy_path
        db.commit()

    audit_log(job_id, "job_started", {"job_id": job_id})

    root = Path(target_path).resolve()
    ruleset_path = Path("/workspace") / ruleset_rel
    policy_path = Path("/workspace") / (policy_rel or POLICY_PATH)
    policy = load_policy(policy_path)

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
                remediation=f.remediation,
            ))
        db.commit()

    audit_log(job_id, "static_scan_done", {"count": len(findings)})

    # 2) AI review (multi-provider)
    ai_review = None
    if ai_review_enabled:
        # Load providers from config or fall back to Ollama
        providers = load_providers(
            config_path=os.getenv("PROVIDERS_CONFIG_PATH")
        )

        # Default: use Ollama as before
        default_provider = providers.get("ollama") or next(iter(providers.values()))
        artifact = summarize_target(root)

        analyzer_model = OLLAMA_MODEL_ANALYZER
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
        analyzer_resp = default_provider.generate(
            analyzer_model, prompt=analyzer_prompt, system="You are a security reviewer."
        )
        _store_model_call(
            job_id,
            provider=default_provider.name,
            model=analyzer_model,
            role="analyzer",
            request=analyzer_prompt,
            response=analyzer_resp.text,
            parsed={},
            usage=analyzer_resp.usage,
        )
        audit_log(job_id, "analyzer_done", {"model": analyzer_model})

        # Build judges from config or default self-consistency
        judge_model = OLLAMA_MODEL_JUDGE
        judges = [
            JudgeConfig(provider=default_provider, model=judge_model),
            JudgeConfig(provider=default_provider, model=judge_model),
        ]

        block_thr = float(policy.get("judge_block_confidence_threshold", 0.75))
        allow_thr = float(policy.get("judge_allow_confidence_threshold", block_thr))
        require_consensus = bool(policy.get("require_consensus_to_allow", False))

        ai_review = run_multi_judge(
            artifact=artifact,
            findings=[{"rule_id": f.get("rule_id"), "severity": f.get("severity"), "title": f.get("title")} for f in findings],
            judges=judges,
            block_threshold=block_thr,
            allow_threshold=allow_thr,
            require_consensus_to_allow=require_consensus,
        )

        # Persist judge results with cost tracking
        for v in ai_review["verdicts"]:
            _store_model_call(
                job_id,
                provider=v["judge"].split(":")[0],
                model=v["judge"].split(":")[1] if ":" in v["judge"] else v["judge"],
                role="judge",
                request="judge_prompt_hash_only",
                response=v.get("raw", ""),
                parsed=v.get("parsed") or {},
                prompt_tokens=v.get("prompt_tokens", 0),
                completion_tokens=v.get("completion_tokens", 0),
                estimated_cost=v.get("estimated_cost_usd", 0.0),
            )

        audit_log(job_id, "judge_done", {"aggregate": ai_review.get("aggregate")})

    # 3) Policy decision
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
    allow = {".py", ".js", ".ts", ".md", ".yml", ".yaml", ".json"}
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


def _store_model_call(
    job_id: str,
    provider: str,
    model: str,
    role: str,
    request: str,
    response: str,
    parsed: dict,
    usage=None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    estimated_cost: float = 0.0,
):
    h = hashlib.sha256(request.encode("utf-8")).hexdigest()

    # Use usage object if provided
    if usage:
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        estimated_cost = estimate_cost(model, prompt_tokens, completion_tokens)

    with SessionLocal() as db:
        db.add(ModelCall(
            job_id=job_id,
            provider=provider,
            model=model,
            role=role,
            request_hash=h,
            response_excerpt=(response or "")[:2000],
            parsed=parsed or {},
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost_usd=estimated_cost,
        ))
        db.commit()
