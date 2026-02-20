from __future__ import annotations

import re
from pathlib import Path

import pytest

from scriptkiddie_core.models import Rule
from scriptkiddie_core.rules import compile_patterns, iter_files, load_ruleset

FIXTURES = Path(__file__).parent / "fixtures"


class TestLoadRuleset:
    def test_valid_yaml(self):
        rules = load_ruleset(FIXTURES / "valid_ruleset.yml")
        assert len(rules) == 2
        assert rules[0].id == "TEST-001"
        assert rules[0].severity == "high"
        assert rules[1].id == "TEST-002"
        assert rules[1].severity == "critical"

    def test_empty_ruleset(self):
        rules = load_ruleset(FIXTURES / "empty_ruleset.yml")
        assert rules == []

    def test_invalid_yaml_returns_empty(self):
        rules = load_ruleset(FIXTURES / "invalid_ruleset.yml")
        assert rules == []

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_ruleset(FIXTURES / "nonexistent.yml")


class TestCompilePatterns:
    def test_compiles_regex(self):
        rule = Rule(id="R1", title="t", patterns=[r"\beval\s*\("])
        pats = compile_patterns(rule)
        assert len(pats) == 1
        assert pats[0].search("eval(foo)")

    def test_empty_patterns(self):
        rule = Rule(id="R1", title="t", patterns=[])
        pats = compile_patterns(rule)
        assert pats == []

    def test_case_insensitive(self):
        rule = Rule(id="R1", title="t", patterns=[r"eval"])
        pats = compile_patterns(rule)
        assert pats[0].search("EVAL")


class TestIterFiles:
    def test_includes_matching(self, tmp_path):
        (tmp_path / "a.py").write_text("x")
        (tmp_path / "b.txt").write_text("y")
        files = iter_files(tmp_path, ["**/*.py"], [])
        assert len(files) == 1
        assert files[0].name == "a.py"

    def test_excludes_work(self, tmp_path):
        (tmp_path / "a.py").write_text("x")
        (tmp_path / "vendor").mkdir()
        (tmp_path / "vendor" / "b.py").write_text("y")
        files = iter_files(tmp_path, ["**/*.py"], ["vendor/**"])
        assert len(files) == 1
        assert files[0].name == "a.py"

    def test_wildcard_includes_all(self, tmp_path):
        (tmp_path / "a.py").write_text("x")
        (tmp_path / "b.js").write_text("y")
        files = iter_files(tmp_path, ["**/*"], [])
        assert len(files) == 2
