from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import yaml

SEV_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

def load_policy(path: str | Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("policy", {})

def _enforce_decisions(policy: dict, decision: Dict[str, Any]) -> Dict[str, Any]:
    order = policy.get("decisions")
    if not order:
        return decision
    if decision["decision"] in order:
        return decision
    fallback = order[0]
    return {"decision": fallback, "reason": f"policy override: {decision['decision']} not in decisions list"}

def evaluate(policy: dict, findings: List[dict], judge_aggregate: dict | None) -> Dict[str, Any]:
    # 1) Static severity gate
    block_floor = policy.get("block_if_severity_at_or_above", "critical")
    floor_val = SEV_ORDER.get(block_floor, 4)
    worst = 0
    worst_id = None
    for f in findings:
        s = SEV_ORDER.get(f.get("severity","low"), 1)
        if s > worst:
            worst = s
            worst_id = f.get("rule_id")

    if worst >= floor_val:
        return _enforce_decisions(
            policy,
            {"decision": "block", "reason": f"static gate: severity >= {block_floor} (worst={worst_id})"},
        )

    # 2) Judge gate (thresholds handled in judge aggregation)
    if judge_aggregate:
        j_decision = judge_aggregate.get("decision")
        j_reason = judge_aggregate.get("reason", "judge aggregate")
        if j_decision in {"block", "allow"}:
            return _enforce_decisions(
                policy,
                {"decision": j_decision, "reason": f"judge aggregate: {j_reason}"},
            )

    # 3) Allow if no findings
    if not findings:
        return _enforce_decisions(policy, {"decision": "allow", "reason": "no findings"})

    return _enforce_decisions(
        policy,
        {"decision": "manual_review", "reason": "findings present but no blocking conditions"},
    )
