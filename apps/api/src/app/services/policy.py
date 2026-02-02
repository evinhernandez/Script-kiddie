from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import yaml

SEV_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

def load_policy(path: str | Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("policy", {})

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
        return {"decision": "block", "reason": f"static gate: severity >= {block_floor} (worst={worst_id})"}

    # 2) Judge gate
    thr = float(policy.get("judge_block_confidence_threshold", 0.75))
    if judge_aggregate and judge_aggregate.get("decision") == "block":
        return {"decision": "block", "reason": f"judge aggregate: block (thr={thr})"}

    # 3) Allow if no findings
    if not findings:
        return {"decision": "allow", "reason": "no findings"}

    return {"decision": "manual_review", "reason": "findings present but no blocking conditions"}
