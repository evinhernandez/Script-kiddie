from __future__ import annotations

import csv
import io
from typing import List

from scriptkiddie_core.models import Finding

COLUMNS = [
    "rule_id", "title", "category", "severity", "file", "line",
    "match", "message", "remediation", "cwe_ids", "owasp_ids", "fingerprint",
]


def to_csv(findings: List[Finding]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS)
    writer.writeheader()
    for f in findings:
        row = f.model_dump()
        row["cwe_ids"] = ";".join(row.get("cwe_ids", []))
        row["owasp_ids"] = ";".join(row.get("owasp_ids", []))
        writer.writerow({k: row.get(k, "") for k in COLUMNS})
    return buf.getvalue()
