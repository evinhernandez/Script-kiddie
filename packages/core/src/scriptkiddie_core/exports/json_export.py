from __future__ import annotations

import json
from typing import Any, Dict, List

from scriptkiddie_core.models import Finding


def to_json(findings: List[Finding], job_meta: Dict[str, Any] | None = None) -> str:
    output = {
        "metadata": job_meta or {},
        "total_findings": len(findings),
        "findings": [f.model_dump() for f in findings],
        "summary": _summarize(findings),
    }
    return json.dumps(output, indent=2)


def _summarize(findings: List[Finding]) -> Dict[str, Any]:
    by_severity: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    by_rule: Dict[str, int] = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_category[f.category] = by_category.get(f.category, 0) + 1
        by_rule[f.rule_id] = by_rule.get(f.rule_id, 0) + 1
    return {
        "by_severity": by_severity,
        "by_category": by_category,
        "by_rule": by_rule,
    }
