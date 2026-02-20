from __future__ import annotations

from app.services.policy import evaluate


class TestEvaluate:
    def _policy(self, **overrides):
        base = {
            "block_if_severity_at_or_above": "critical",
            "decisions": ["block", "manual_review", "allow"],
        }
        base.update(overrides)
        return base

    def test_block_on_critical(self):
        findings = [{"severity": "critical", "rule_id": "R1"}]
        result = evaluate(self._policy(), findings, None)
        assert result["decision"] == "block"

    def test_allow_no_findings(self):
        result = evaluate(self._policy(), [], None)
        assert result["decision"] == "allow"

    def test_manual_review_with_findings_below_threshold(self):
        findings = [{"severity": "medium", "rule_id": "R1"}]
        result = evaluate(self._policy(), findings, None)
        assert result["decision"] == "manual_review"

    def test_judge_block(self):
        findings = [{"severity": "medium", "rule_id": "R1"}]
        judge_agg = {"decision": "block", "reason": "test"}
        result = evaluate(self._policy(), findings, judge_agg)
        assert result["decision"] == "block"

    def test_judge_allow(self):
        findings = [{"severity": "medium", "rule_id": "R1"}]
        judge_agg = {"decision": "allow", "reason": "clean"}
        result = evaluate(self._policy(), findings, judge_agg)
        assert result["decision"] == "allow"

    def test_severity_gate_at_high(self):
        policy = self._policy(block_if_severity_at_or_above="high")
        findings = [{"severity": "high", "rule_id": "R1"}]
        result = evaluate(policy, findings, None)
        assert result["decision"] == "block"

    def test_decisions_enforcement(self):
        policy = self._policy(decisions=["block", "manual_review"])
        result = evaluate(policy, [], None)
        # "allow" not in decisions list, should fallback
        assert result["decision"] == "block"

    def test_static_gate_priority_over_judge(self):
        findings = [{"severity": "critical", "rule_id": "R1"}]
        judge_agg = {"decision": "allow", "reason": "clean"}
        result = evaluate(self._policy(), findings, judge_agg)
        assert result["decision"] == "block"
