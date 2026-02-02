from __future__ import annotations
import re
from pathlib import Path
from typing import List
import yaml
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern
from .models import Rule

def load_ruleset(path: str | Path) -> List[Rule]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [Rule(**r) for r in data.get("rules", [])]

def _spec(globs: List[str]) -> PathSpec:
    return PathSpec.from_lines(GitWildMatchPattern, globs)

def iter_files(root: Path, include: List[str], exclude: List[str]) -> List[Path]:
    inc = _spec(include or ["**/*"])
    exc = _spec(exclude or [])
    out: List[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if not inc.match_file(rel):
            continue
        if exclude and exc.match_file(rel):
            continue
        out.append(p)
    return out

def compile_patterns(rule: Rule) -> List[re.Pattern]:
    return [re.compile(p, flags=re.IGNORECASE | re.MULTILINE) for p in rule.patterns]
