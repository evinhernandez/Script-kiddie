from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

Decision = Literal["allow","block","manual_review"]

class JudgeVerdict(BaseModel):
    decision: Decision = "manual_review"
    confidence: float = 0.5
    confirmed_findings: List[str] = Field(default_factory=list)
    false_positives: List[str] = Field(default_factory=list)
    notes: str = ""

def extract_first_json_object(text: str) -> Optional[str]:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None
