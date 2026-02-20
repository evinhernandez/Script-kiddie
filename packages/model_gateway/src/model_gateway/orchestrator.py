from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .judge_schema import JudgeVerdict, extract_first_json_object
from .pricing import estimate_cost

logger = logging.getLogger(__name__)


@dataclass
class JudgeConfig:
    provider: Any
    model: str
    weight: float = 1.0
    fallback_model: str | None = None
    max_retries: int = 3
    retry_delay: float = 1.0


def _call_with_retry(provider, model: str, prompt: str, system: str, config: JudgeConfig):
    """Call provider with retry and fallback."""
    last_error = None
    for attempt in range(config.max_retries):
        try:
            return provider.generate(model, prompt=prompt, system=system)
        except Exception as e:
            last_error = e
            logger.warning("Judge call failed (attempt %d/%d, model=%s): %s", attempt + 1, config.max_retries, model, e)
            if attempt < config.max_retries - 1:
                time.sleep(config.retry_delay * (2 ** attempt))

    # Try fallback model if configured
    if config.fallback_model and config.fallback_model != model:
        logger.info("Trying fallback model: %s", config.fallback_model)
        try:
            return provider.generate(config.fallback_model, prompt=prompt, system=system)
        except Exception as e:
            logger.warning("Fallback model also failed: %s", e)

    raise last_error


def run_multi_judge(
    artifact: str,
    findings: List[Dict[str, Any]],
    judges: List[JudgeConfig],
    block_threshold: float = 0.75,
    allow_threshold: float | None = None,
    require_consensus_to_allow: bool = True,
) -> Dict[str, Any]:
    if allow_threshold is None:
        allow_threshold = block_threshold
    verdicts: List[Dict[str, Any]] = []
    total_cost = 0.0

    for j in judges:
        system = "You are a strict application security judge for AI/agent apps. Minimize false positives."
        prompt = f"""
Return STRICT JSON:
{{
  "decision": "allow|block|manual_review",
  "confidence": 0.0-1.0,
  "confirmed_findings": ["RULE_ID", ...],
  "false_positives": ["RULE_ID", ...],
  "notes": "short"
}}

Artifact:
{artifact[:6000]}

Proposed findings:
{json.dumps(findings)[:6000]}
"""
        verdict_entry: Dict[str, Any] = {
            "judge": f"{getattr(j.provider, 'name', 'provider')}:{j.model}",
            "parsed": None,
            "raw": "",
            "weight": j.weight,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

        try:
            resp = _call_with_retry(j.provider, j.model, prompt, system, j)
            raw = resp.text
            verdict_entry["raw"] = raw[:4000]

            # Track token usage
            if resp.usage:
                verdict_entry["prompt_tokens"] = resp.usage.prompt_tokens
                verdict_entry["completion_tokens"] = resp.usage.completion_tokens
                cost = estimate_cost(j.model, resp.usage.prompt_tokens, resp.usage.completion_tokens)
                verdict_entry["estimated_cost_usd"] = cost
                total_cost += cost

            js = extract_first_json_object(raw)
            if js:
                try:
                    verdict_entry["parsed"] = JudgeVerdict.model_validate(json.loads(js)).model_dump()
                except Exception:
                    pass
        except Exception as e:
            logger.error("Judge %s:%s failed completely: %s", getattr(j.provider, 'name', '?'), j.model, e)
            verdict_entry["raw"] = f"ERROR: {e}"

        verdicts.append(verdict_entry)

    agg = aggregate(
        verdicts,
        block_threshold=block_threshold,
        allow_threshold=allow_threshold,
        require_consensus_to_allow=require_consensus_to_allow,
    )
    agg["total_estimated_cost_usd"] = round(total_cost, 6)

    return {"verdicts": verdicts, "aggregate": agg}


def _effective_confidence(confidence: float, weight: float) -> float:
    conf = max(0.0, min(1.0, float(confidence)))
    w = max(0.0, float(weight))
    return max(0.0, min(1.0, conf * w))


def aggregate(
    verdicts: List[Dict[str, Any]],
    block_threshold: float = 0.75,
    allow_threshold: float = 0.75,
    require_consensus_to_allow: bool = True,
) -> Dict[str, Any]:
    parsed = []
    provider_families: set[str] = set()

    for v in verdicts:
        p = v.get("parsed")
        if not p:
            continue
        weight = v.get("weight", 1.0)
        parsed.append((p, weight))
        # Track provider family for diversity bonus
        judge_name = v.get("judge", "")
        family = judge_name.split(":")[0] if ":" in judge_name else judge_name
        provider_families.add(family)

    if not parsed:
        return {"decision": "manual_review", "reason": "no parsed judge outputs"}

    block_eff = 0.0
    allow_eff = 0.0
    decisions = []

    for p, weight in parsed:
        decision = p.get("decision")
        decisions.append(decision)
        eff = _effective_confidence(p.get("confidence", 0.0), weight)
        if decision == "block":
            block_eff = max(block_eff, eff)
        elif decision == "allow":
            allow_eff = max(allow_eff, eff)

    consensus_all_allow = all(d == "allow" for d in decisions)

    # Diversity bonus: when different model families agree, boost confidence
    diverse = len(provider_families) > 1
    diversity_bonus = 0.05 if diverse and consensus_all_allow else 0.0

    if block_eff >= block_threshold:
        return {
            "decision": "block",
            "reason": f"max weighted block confidence {block_eff:.2f} >= {block_threshold}",
            "scores": {"block": block_eff, "allow": allow_eff},
            "consensus": {"all_allow": consensus_all_allow},
            "diverse_judges": diverse,
        }

    effective_allow = allow_eff + diversity_bonus
    if effective_allow >= allow_threshold and (consensus_all_allow or not require_consensus_to_allow):
        reason = f"max weighted allow confidence {effective_allow:.2f} >= {allow_threshold}"
        if require_consensus_to_allow:
            reason += " with consensus"
        if diversity_bonus > 0:
            reason += f" (diversity bonus: +{diversity_bonus:.2f})"
        return {
            "decision": "allow",
            "reason": reason,
            "scores": {"block": block_eff, "allow": effective_allow},
            "consensus": {"all_allow": consensus_all_allow},
            "diverse_judges": diverse,
        }

    return {
        "decision": "manual_review",
        "reason": "insufficient consensus or confidence",
        "scores": {"block": block_eff, "allow": allow_eff},
        "consensus": {"all_allow": consensus_all_allow},
        "diverse_judges": diverse,
    }
