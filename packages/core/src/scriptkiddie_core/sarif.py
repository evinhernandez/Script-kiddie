from __future__ import annotations
from typing import Any, Dict, List
from .models import Finding

def _sarif_level(sev: str) -> str:
    return {"low": "note", "medium": "warning", "high": "error", "critical": "error"}.get(sev, "warning")

def to_sarif(findings: List[Finding]) -> Dict[str, Any]:
    # Minimal SARIF 2.1.0 suitable for GitHub upload
    rules: Dict[str, Any] = {}
    results: List[Dict[str, Any]] = []

    for f in findings:
        if f.rule_id not in rules:
            rules[f.rule_id] = {
                "id": f.rule_id,
                "name": f.title,
                "shortDescription": {"text": f.title},
                "fullDescription": {"text": f.message or f.title},
                "help": {"text": f.remediation or "See rule guidance."},
                "properties": {"severity": f.severity, "category": f.category},
            }

        results.append({
            "ruleId": f.rule_id,
            "level": _sarif_level(f.severity),
            "message": {"text": f.message or f.title},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.file},
                    "region": {"startLine": f.line},
                }
            }]
        })

    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {"name": "script-kiddie", "rules": list(rules.values())}},
            "results": results
        }]
    }
