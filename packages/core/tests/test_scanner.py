from __future__ import annotations

from pathlib import Path

from scriptkiddie_core.scanner import scan

FIXTURES = Path(__file__).parent / "fixtures"


class TestScan:
    def test_finds_matching_pattern(self, tmp_path):
        (tmp_path / "app.py").write_text('api_key = "TESTTOKEN1234"\n')
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "valid_ruleset.yml")
        rule_ids = [f.rule_id for f in findings]
        assert "TEST-001" in rule_ids

    def test_no_match_returns_empty(self, tmp_path):
        (tmp_path / "clean.py").write_text("print('hello')\n")
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "valid_ruleset.yml")
        assert findings == []

    def test_keyword_fast_path(self, tmp_path):
        # File has pattern match but not keyword — should skip via fast-path
        (tmp_path / "app.py").write_text('secret = "ABCDEFGHIJKLMNOPQR"\n')
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "valid_ruleset.yml")
        # TEST-001 requires keyword "api_key" — so no match
        test_001 = [f for f in findings if f.rule_id == "TEST-001"]
        assert test_001 == []

    def test_eval_rule(self, tmp_path):
        (tmp_path / "bad.py").write_text("result = eval(user_input)\n")
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "valid_ruleset.yml")
        rule_ids = [f.rule_id for f in findings]
        assert "TEST-002" in rule_ids

    def test_encoding_errors_handled(self, tmp_path):
        binary_file = tmp_path / "data.py"
        binary_file.write_bytes(b"\xff\xfe" + b"eval(x)" + b"\x00\x80")
        # Should not raise
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "valid_ruleset.yml")
        assert isinstance(findings, list)

    def test_large_file_skipped(self, tmp_path):
        big = tmp_path / "big.py"
        big.write_text("api_key = " + '"' + "A" * 100 + '"' + "\n" + "x" * (600 * 1024))
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "valid_ruleset.yml", max_file_kb=512)
        assert findings == []

    def test_empty_ruleset(self, tmp_path):
        (tmp_path / "app.py").write_text("eval(x)\n")
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "empty_ruleset.yml")
        assert findings == []

    def test_line_number_correct(self, tmp_path):
        (tmp_path / "app.py").write_text("line1\nline2\neval(something)\nline4\n")
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "valid_ruleset.yml")
        eval_findings = [f for f in findings if f.rule_id == "TEST-002"]
        assert len(eval_findings) == 1
        assert eval_findings[0].line == 3

    def test_finding_fields(self, tmp_path):
        (tmp_path / "app.py").write_text("eval(x)\n")
        findings = scan(root=tmp_path, ruleset_path=FIXTURES / "valid_ruleset.yml")
        f = [x for x in findings if x.rule_id == "TEST-002"][0]
        assert f.title == "Test rule: eval usage"
        assert f.severity == "critical"
        assert f.category == "test"
        assert f.file == "app.py"
