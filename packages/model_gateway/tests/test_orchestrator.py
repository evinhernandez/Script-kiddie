from __future__ import annotations

from model_gateway.orchestrator import aggregate


class TestAggregate:
    def _verdict(self, decision: str, confidence: float, weight: float = 1.0):
        return {
            "parsed": {
                "decision": decision,
                "confidence": confidence,
                "confirmed_findings": [],
                "false_positives": [],
                "notes": "",
            },
            "weight": weight,
        }

    def test_block_path(self):
        verdicts = [self._verdict("block", 0.9)]
        result = aggregate(verdicts, block_threshold=0.75)
        assert result["decision"] == "block"

    def test_allow_path_with_consensus(self):
        verdicts = [
            self._verdict("allow", 0.9),
            self._verdict("allow", 0.8),
        ]
        result = aggregate(verdicts, block_threshold=0.75, allow_threshold=0.75, require_consensus_to_allow=True)
        assert result["decision"] == "allow"

    def test_allow_blocked_without_consensus(self):
        verdicts = [
            self._verdict("allow", 0.9),
            self._verdict("block", 0.3),
        ]
        result = aggregate(verdicts, block_threshold=0.75, allow_threshold=0.75, require_consensus_to_allow=True)
        assert result["decision"] == "manual_review"

    def test_allow_without_consensus_requirement(self):
        verdicts = [
            self._verdict("allow", 0.9),
            self._verdict("block", 0.3),
        ]
        result = aggregate(verdicts, block_threshold=0.75, allow_threshold=0.75, require_consensus_to_allow=False)
        assert result["decision"] == "allow"

    def test_manual_review_on_low_confidence(self):
        verdicts = [self._verdict("block", 0.3)]
        result = aggregate(verdicts, block_threshold=0.75)
        assert result["decision"] == "manual_review"

    def test_no_parsed_outputs(self):
        verdicts = [{"parsed": None, "weight": 1.0}]
        result = aggregate(verdicts)
        assert result["decision"] == "manual_review"
        assert "no parsed" in result["reason"]

    def test_weight_affects_confidence(self):
        # confidence=0.9, weight=0.5 => effective=0.45, below 0.75 threshold
        verdicts = [self._verdict("block", 0.9, weight=0.5)]
        result = aggregate(verdicts, block_threshold=0.75)
        assert result["decision"] == "manual_review"

    def test_block_takes_priority_over_allow(self):
        verdicts = [
            self._verdict("block", 0.9),
            self._verdict("allow", 0.9),
        ]
        result = aggregate(verdicts, block_threshold=0.75, allow_threshold=0.75)
        assert result["decision"] == "block"
