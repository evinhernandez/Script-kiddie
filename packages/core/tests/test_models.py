from __future__ import annotations

import pytest
from pydantic import ValidationError

from scriptkiddie_core.models import Finding, Rule


class TestRule:
    def test_minimal_rule(self):
        r = Rule(id="R1", title="Test")
        assert r.id == "R1"
        assert r.severity == "medium"
        assert r.category == "ai-security"
        assert r.file_globs == ["**/*"]
        assert r.patterns == []
        assert r.keywords == []

    def test_full_rule(self):
        r = Rule(
            id="R1",
            title="Test",
            category="custom",
            severity="critical",
            file_globs=["**/*.py"],
            exclude_globs=["vendor/**"],
            patterns=[r"\beval\("],
            keywords=["eval"],
            message="msg",
            remediation="fix",
        )
        assert r.severity == "critical"
        assert r.file_globs == ["**/*.py"]

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            Rule(id="R1", title="Test", severity="invalid")


class TestFinding:
    def test_minimal_finding(self):
        f = Finding(
            rule_id="R1",
            title="Test",
            category="test",
            severity="high",
            file="a.py",
            line=1,
            match="x",
        )
        assert f.message == ""
        assert f.remediation == ""

    def test_full_finding(self):
        f = Finding(
            rule_id="R1",
            title="Test",
            category="test",
            severity="low",
            file="a.py",
            line=5,
            match="eval(x)",
            message="msg",
            remediation="fix",
        )
        assert f.severity == "low"
        assert f.line == 5

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            Finding(
                rule_id="R1", title="T", category="c", severity="oops",
                file="a.py", line=1, match="x",
            )
