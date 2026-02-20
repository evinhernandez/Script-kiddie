from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

SEV_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def load_policy(path: str | Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("policy", {})


def _get_rule_overrides(policy: dict) -> Dict[str, Dict[str, Any]]:
    """Parse rule_overrides into a lookup by rule_id."""
    overrides_raw = policy.get("rule_overrides", [])
    overrides = {}
    if isinstance(overrides_raw, list):
        for entry in overrides_raw:
            if isinstance(entry, dict) and "rule_id" in entry:
                overrides[entry["rule_id"]] = entry
    elif isinstance(overrides_raw, dict):
        for rule_id, cfg in overrides_raw.items():
            if isinstance(cfg, dict):
                cfg["rule_id"] = rule_id
                overrides[rule_id] = cfg
    return overrides


def _enforce_decisions(policy: dict, decision: Dict[str, Any]) -> Dict[str, Any]:
    order = policy.get("decisions")
    if not order:
        return decision
    if decision["decision"] in order:
        return decision
    fallback = order[0]
    return {"decision": fallback, "reason": f"policy override: {decision['decision']} not in decisions list"}


def evaluate(policy: dict, findings: List[dict], judge_aggregate: dict | None) -> Dict[str, Any]:
    overrides = _get_rule_overrides(policy)

    # Apply per-rule overrides: suppress findings, override severity
    effective_findings = []
    suppressed_count = 0
    for f in findings:
        rule_id = f.get("rule_id", "")
        override = overrides.get(rule_id)
        if override:
            action = override.get("action", "warn")
            if action == "suppress":
                suppressed_count += 1
                continue
            if override.get("severity_override"):
                f = dict(f)
                f["severity"] = override["severity_override"]
        effective_findings.append(f)

    # 1) Static severity gate
    block_floor = policy.get("block_if_severity_at_or_above", "critical")
    floor_val = SEV_ORDER.get(block_floor, 4)
    worst = 0
    worst_id = None
    for f in effective_findings:
        s = SEV_ORDER.get(f.get("severity", "low"), 1)
        if s > worst:
            worst = s
            worst_id = f.get("rule_id")

    if worst >= floor_val:
        return _enforce_decisions(
            policy,
            {"decision": "block", "reason": f"static gate: severity >= {block_floor} (worst={worst_id})"},
        )

    # 2) Judge gate
    if judge_aggregate:
        j_decision = judge_aggregate.get("decision")
        j_reason = judge_aggregate.get("reason", "judge aggregate")
        if j_decision in {"block", "allow"}:
            return _enforce_decisions(
                policy,
                {"decision": j_decision, "reason": f"judge aggregate: {j_reason}"},
            )

    # 3) Allow if no findings
    if not effective_findings:
        return _enforce_decisions(policy, {"decision": "allow", "reason": "no findings"})

    return _enforce_decisions(
        policy,
        {"decision": "manual_review", "reason": "findings present but no blocking conditions"},
    )
