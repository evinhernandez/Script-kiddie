from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import List

from .models import Finding, Rule
from .rules import compile_patterns, iter_files, load_ruleset

logger = logging.getLogger(__name__)


def _fingerprint(rule_id: str, file: str, match: str) -> str:
    data = f"{rule_id}:{file}:{match}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def scan(root: Path, ruleset_path: Path, max_file_kb: int = 512) -> List[Finding]:
    rules: List[Rule] = load_ruleset(ruleset_path)
    findings: List[Finding] = []

    for rule in rules:
        pats = compile_patterns(rule)
        targets = iter_files(root, rule.file_globs, rule.exclude_globs)

        for f in targets:
            try:
                if f.stat().st_size > max_file_kb * 1024:
                    continue
            except OSError:
                logger.debug("Could not stat file: %s", f)
                continue

            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                logger.debug("Could not read file: %s", f, exc_info=True)
                continue

            # keyword fast-path
            if rule.keywords:
                low = txt.lower()
                if not any(k.lower() in low for k in rule.keywords) and rule.patterns:
                    continue
                if not any(k.lower() in low for k in rule.keywords) and not rule.patterns:
                    continue

            rel_path = f.relative_to(root).as_posix()

            for rx in pats:
                for m in rx.finditer(txt):
                    line = txt[:m.start()].count("\n") + 1
                    snippet = (m.group(0) or "").strip()[:200]
                    findings.append(Finding(
                        rule_id=rule.id,
                        title=rule.title,
                        category=rule.category,
                        severity=rule.severity,
                        file=rel_path,
                        line=line,
                        match=snippet,
                        message=rule.message,
                        remediation=rule.remediation,
                        cwe_ids=rule.cwe_ids,
                        owasp_ids=rule.owasp_ids,
                        fingerprint=_fingerprint(rule.id, rel_path, snippet),
                    ))
    return findings


def scan_multi(root: Path, ruleset_paths: List[Path], max_file_kb: int = 512) -> List[Finding]:
    all_findings: List[Finding] = []
    for rp in ruleset_paths:
        all_findings.extend(scan(root=root, ruleset_path=rp, max_file_kb=max_file_kb))
    return all_findings
