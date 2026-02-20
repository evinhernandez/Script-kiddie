from __future__ import annotations

from scriptkiddie_core.models import Finding
from scriptkiddie_core.sarif import to_sarif


def _make_finding(**overrides) -> Finding:
    defaults = dict(
        rule_id="TEST-001",
        title="Test finding",
        category="test",
        severity="high",
        file="app.py",
        line=10,
        match="eval(x)",
        message="Bad code",
        remediation="Fix it",
    )
    defaults.update(overrides)
    return Finding(**defaults)


class TestToSarif:
    def test_valid_sarif_structure(self):
        sarif = to_sarif([_make_finding()])
        assert sarif["version"] == "2.1.0"
        assert "$schema" in sarif
        assert len(sarif["runs"]) == 1
        run = sarif["runs"][0]
        assert "tool" in run
        assert "results" in run
        assert run["tool"]["driver"]["name"] == "script-kiddie"

    def test_rules_populated(self):
        sarif = to_sarif([_make_finding(), _make_finding(rule_id="TEST-002", title="Other")])
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 2
        rule_ids = [r["id"] for r in rules]
        assert "TEST-001" in rule_ids
        assert "TEST-002" in rule_ids

    def test_results_populated(self):
        sarif = to_sarif([_make_finding()])
        results = sarif["runs"][0]["results"]
        assert len(results) == 1
        r = results[0]
        assert r["ruleId"] == "TEST-001"
        assert r["level"] == "error"  # high -> error
        loc = r["locations"][0]["physicalLocation"]
        assert loc["artifactLocation"]["uri"] == "app.py"
        assert loc["region"]["startLine"] == 10

    def test_severity_mapping(self):
        for sev, expected in [("low", "note"), ("medium", "warning"), ("high", "error"), ("critical", "error")]:
            sarif = to_sarif([_make_finding(severity=sev)])
            assert sarif["runs"][0]["results"][0]["level"] == expected

    def test_empty_findings(self):
        sarif = to_sarif([])
        assert sarif["runs"][0]["results"] == []
        assert sarif["runs"][0]["tool"]["driver"]["rules"] == []

    def test_dedup_rules(self):
        sarif = to_sarif([_make_finding(), _make_finding(line=20)])
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 1
        results = sarif["runs"][0]["results"]
        assert len(results) == 2
