from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel, Field

Severity = Literal["low","medium","high","critical"]

class Rule(BaseModel):
    id: str
    title: str
    category: str = "ai-security"
    severity: Severity = "medium"
    file_globs: List[str] = Field(default_factory=lambda: ["**/*"])
    exclude_globs: List[str] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    message: str = ""
    remediation: str = ""

class Finding(BaseModel):
    rule_id: str
    title: str
    category: str
    severity: Severity
    file: str
    line: int
    match: str
    message: str = ""
    remediation: str = ""
