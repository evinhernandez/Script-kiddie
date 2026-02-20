from __future__ import annotations
from typing import Any, Dict, List
from .models import Finding

def _sarif_level(sev: str) -> str:
    return {"low": "note", "medium": "warning", "high": "error", "critical": "error"}.get(sev, "warning")

def to_sarif(findings: List[Finding]) -> Dict[str, Any]:
    rules: Dict[str, Any] = {}
    results: List[Dict[str, Any]] = []

    for f in findings:
        if f.rule_id not in rules:
            tags = []
            tags.extend(f"CWE-{c}" if not c.startswith("CWE-") else c for c in f.cwe_ids)
            tags.extend(f.owasp_ids)
            if f.category:
                tags.append(f.category)

            rules[f.rule_id] = {
                "id": f.rule_id,
                "name": f.title,
                "shortDescription": {"text": f.title},
                "fullDescription": {"text": f.message or f.title},
                "help": {"text": f.remediation or "See rule guidance."},
                "properties": {"severity": f.severity, "category": f.category, "tags": tags},
            }

        result: Dict[str, Any] = {
            "ruleId": f.rule_id,
            "level": _sarif_level(f.severity),
            "message": {"text": f.message or f.title},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.file},
                    "region": {"startLine": f.line},
                }
            }],
        }

        if f.fingerprint:
            result["partialFingerprints"] = {
                "primaryLocationLineHash": f.fingerprint,
            }

        results.append(result)

    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {"name": "script-kiddie", "rules": list(rules.values())}},
            "results": results
        }]
    }
