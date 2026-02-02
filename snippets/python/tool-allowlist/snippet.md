# Tool allowlist + argument validation

Model output decides *which* action, but your code decides *what is allowed*.

```python
from pydantic import BaseModel, ValidationError
from typing import Literal

class ToolCall(BaseModel):
    tool: Literal["lookup_user", "search_tickets"]
    query: str

def lookup_user(query: str) -> dict:
    # safe implementation
    return {"ok": True, "query": query}

def search_tickets(query: str) -> dict:
    return {"ok": True, "query": query}

TOOLS = {
    "lookup_user": lookup_user,
    "search_tickets": search_tickets,
}

def dispatch_toolcall(raw_text: str) -> dict:
    # parse JSON strictly like the structured-output snippet
    call = ToolCall.model_validate_json(raw_text)
    fn = TOOLS[call.tool]
    return fn(call.query)
```

**Never:** map model output directly into `os.system`, SQL, or arbitrary HTTP without allowlists.
