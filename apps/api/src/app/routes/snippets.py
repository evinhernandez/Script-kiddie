from __future__ import annotations
from pathlib import Path
import json
from fastapi import APIRouter, HTTPException

router = APIRouter()

SNIPPETS_ROOT = Path("/workspace/snippets")

@router.get("")
def list_snippets():
    items = []
    for meta in SNIPPETS_ROOT.rglob("meta.json"):
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except Exception:
            continue
        rel = meta.parent.relative_to(SNIPPETS_ROOT).as_posix()
        data["path"] = rel
        items.append(data)
    items.sort(key=lambda x: (x.get("language",""), x.get("title","")))
    return items

@router.get("/{language}/{name}")
def get_snippet(language: str, name: str):
    folder = SNIPPETS_ROOT / language / name
    meta = folder / "meta.json"
    snip = folder / "snippet.md"
    if not meta.exists() or not snip.exists():
        raise HTTPException(404, "snippet not found")
    return {
        "meta": json.loads(meta.read_text(encoding="utf-8")),
        "content": snip.read_text(encoding="utf-8")
    }
