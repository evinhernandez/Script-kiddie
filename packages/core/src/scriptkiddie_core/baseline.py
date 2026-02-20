from __future__ import annotations

from typing import List

from .models import Finding


def diff_findings(
    current: List[Finding],
    baseline: List[Finding],
) -> dict:
    """Diff findings by fingerprint. Returns new, fixed, and unchanged findings."""
    current_fps = {f.fingerprint: f for f in current if f.fingerprint}
    baseline_fps = {f.fingerprint: f for f in baseline if f.fingerprint}

    new = [f for fp, f in current_fps.items() if fp not in baseline_fps]
    fixed = [f for fp, f in baseline_fps.items() if fp not in current_fps]
    unchanged = [f for fp, f in current_fps.items() if fp in baseline_fps]

    return {
        "new": new,
        "fixed": fixed,
        "unchanged": unchanged,
        "summary": {
            "new_count": len(new),
            "fixed_count": len(fixed),
            "unchanged_count": len(unchanged),
        },
    }
