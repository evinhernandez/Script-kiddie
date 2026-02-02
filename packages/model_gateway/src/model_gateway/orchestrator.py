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

def run_multi_judge(artifact: str, findings: List[Dict[str, Any]], judges: List[JudgeConfig]) -> Dict[str, Any]:
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
            "raw": raw[:4000]
        })

    agg = aggregate(verdicts)
    return {"verdicts": verdicts, "aggregate": agg}

def aggregate(verdicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    parsed = [v["parsed"] for v in verdicts if v.get("parsed")]
    if not parsed:
        return {"decision": "manual_review", "reason": "no parsed judge outputs"}

    blocks = [p for p in parsed if p["decision"] == "block" and p["confidence"] >= 0.75]
    allows = [p for p in parsed if p["decision"] == "allow" and p["confidence"] >= 0.75]
    if blocks:
        return {"decision": "block", "reason": "high-confidence block from at least one judge"}
    if allows and len(allows) == len(parsed):
        return {"decision": "allow", "reason": "all parsed judges high-confidence allow"}
    return {"decision": "manual_review", "reason": "insufficient consensus"}
