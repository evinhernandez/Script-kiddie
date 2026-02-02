from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List
import json

from .judge_schema import JudgeVerdict, extract_first_json_object

@dataclass
class JudgeConfig:
    provider: Any
    model: str
    weight: float = 1.0

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
        resp = j.provider.generate(j.model, prompt=prompt, system=system)
        raw = resp.text
        parsed = None
        js = extract_first_json_object(raw)
        if js:
            try:
                parsed = JudgeVerdict.model_validate(json.loads(js)).model_dump()
            except Exception:
                parsed = None

        verdicts.append({
            "judge": f"{getattr(j.provider, 'name', 'provider')}:{j.model}",
            "parsed": parsed,
            "raw": raw[:4000],
            "weight": j.weight,
        })

    agg = aggregate(
        verdicts,
        block_threshold=block_threshold,
        allow_threshold=allow_threshold,
        require_consensus_to_allow=require_consensus_to_allow,
    )
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
    for v in verdicts:
        p = v.get("parsed")
        if not p:
            continue
        weight = v.get("weight", 1.0)
        parsed.append((p, weight))

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

    if block_eff >= block_threshold:
        return {
            "decision": "block",
            "reason": f"max weighted block confidence {block_eff:.2f} >= {block_threshold}",
            "scores": {"block": block_eff, "allow": allow_eff},
            "consensus": {"all_allow": consensus_all_allow},
        }

    if allow_eff >= allow_threshold and (consensus_all_allow or not require_consensus_to_allow):
        reason = f"max weighted allow confidence {allow_eff:.2f} >= {allow_threshold}"
        if require_consensus_to_allow:
            reason += " with consensus"
        return {
            "decision": "allow",
            "reason": reason,
            "scores": {"block": block_eff, "allow": allow_eff},
            "consensus": {"all_allow": consensus_all_allow},
        }

    return {
        "decision": "manual_review",
        "reason": "insufficient consensus or confidence",
        "scores": {"block": block_eff, "allow": allow_eff},
        "consensus": {"all_allow": consensus_all_allow},
    }
