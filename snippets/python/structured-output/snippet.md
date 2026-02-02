# Structured output enforcement (Python)

Use structured outputs so model responses are *data*, not executable instructions.

```python
from pydantic import BaseModel, ValidationError
import json

class LLMResult(BaseModel):
    action: str
    arguments: dict

def parse_llm_json(text: str) -> LLMResult:
    # Extract first JSON object (simple best effort)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")

    candidate = text[start:end+1]
    data = json.loads(candidate)
    return LLMResult.model_validate(data)

# Usage:
# raw = llm(...)
# result = parse_llm_json(raw)
# if result.action not in ALLOWLIST: block
```

**Hard rule:** never run `eval/exec` on model output.
