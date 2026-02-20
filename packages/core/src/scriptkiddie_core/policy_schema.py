from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class RuleOverride(BaseModel):
    rule_id: str
    action: Literal["block", "warn", "suppress"] = "warn"
    severity_override: Optional[str] = None
    reason: str = ""


class PolicyConfig(BaseModel):
    id: str = "default"
    title: str = "Default policy"
    description: str = ""
    block_if_severity_at_or_above: str = "critical"
    judge_block_confidence_threshold: float = 0.75
    judge_allow_confidence_threshold: Optional[float] = None
    require_consensus_to_allow: bool = False
    decisions: List[str] = Field(default_factory=lambda: ["block", "manual_review", "allow"])
    rule_overrides: List[RuleOverride] = Field(default_factory=list)


def load_policy_config(data: dict) -> PolicyConfig:
    """Parse and validate a policy configuration dict."""
    policy_data = data.get("policy", data)
    # Convert rule_overrides from dict format if needed
    overrides_raw = policy_data.get("rule_overrides", [])
    if isinstance(overrides_raw, dict):
        overrides_list = []
        for rule_id, override in overrides_raw.items():
            if isinstance(override, dict):
                override["rule_id"] = rule_id
                overrides_list.append(override)
        policy_data["rule_overrides"] = overrides_list
    return PolicyConfig.model_validate(policy_data)
