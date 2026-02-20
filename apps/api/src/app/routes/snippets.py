from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

SNIPPETS_ROOT = Path("/workspace/snippets")

# Only allow safe path segments (alphanumeric, hyphens, underscores)
_SAFE_SEGMENT = re.compile(r"^[a-zA-Z0-9_-]+$")


@router.get("")
def list_snippets():
    items = []
    if not SNIPPETS_ROOT.is_dir():
        return items
    for meta in SNIPPETS_ROOT.rglob("meta.json"):
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except Exception:
            continue
        rel = meta.parent.relative_to(SNIPPETS_ROOT).as_posix()
        data["path"] = rel
        items.append(data)
    items.sort(key=lambda x: (x.get("language", ""), x.get("title", "")))
    return items


@router.get("/{language}/{name}")
def get_snippet(language: str, name: str):
    # Validate path segments to prevent directory traversal
    if not _SAFE_SEGMENT.match(language) or not _SAFE_SEGMENT.match(name):
        raise HTTPException(400, "invalid language or snippet name")

    folder = (SNIPPETS_ROOT / language / name).resolve()

    # Ensure resolved path is still under SNIPPETS_ROOT
    if not str(folder).startswith(str(SNIPPETS_ROOT.resolve())):
        raise HTTPException(400, "invalid path")

    meta = folder / "meta.json"
    snip = folder / "snippet.md"
    if not meta.exists() or not snip.exists():
        raise HTTPException(404, "snippet not found")
    return {
        "meta": json.loads(meta.read_text(encoding="utf-8")),
        "content": snip.read_text(encoding="utf-8"),
    }
