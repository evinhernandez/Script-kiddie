from __future__ import annotations
from pathlib import Path
from typing import List
from .models import Finding, Rule
from .rules import compile_patterns, iter_files, load_ruleset

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
                continue

            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # keyword fast-path
            if rule.keywords:
                low = txt.lower()
                if not any(k.lower() in low for k in rule.keywords) and rule.patterns:
                    # continue to regex-only? keep running if patterns exist but no keywords match?
                    # We'll skip to reduce CPU; rules can omit keywords if needed.
                    continue
                if not any(k.lower() in low for k in rule.keywords) and not rule.patterns:
                    continue

            for rx in pats:
                for m in rx.finditer(txt):
                    line = txt[:m.start()].count("\n") + 1
                    snippet = (m.group(0) or "").strip()
                    findings.append(Finding(
                        rule_id=rule.id,
                        title=rule.title,
                        category=rule.category,
                        severity=rule.severity,
                        file=f.relative_to(root).as_posix(),
                        line=line,
                        match=snippet[:200],
                        message=rule.message,
                        remediation=rule.remediation
                    ))
    return findings
