from __future__ import annotations

import json
from pathlib import Path

from scriptkiddie_cli.main import build_parser, cmd_rules_list, cmd_scan

CORE_FIXTURES = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "core" / "tests" / "fixtures"


class TestCmdScan:
    def test_scan_sarif_output(self, tmp_path):
        # Create a target file
        (tmp_path / "app.py").write_text("result = eval(user_input)\n")
        out_file = tmp_path / "output.sarif"

        parser = build_parser()
        args = parser.parse_args([
            "scan",
            "--root", str(tmp_path),
            "--ruleset", str(CORE_FIXTURES / "valid_ruleset.yml"),
            "--out", str(out_file),
            "--format", "sarif",
        ])
        ret = cmd_scan(args)
        assert ret == 0
        assert out_file.exists()

        sarif = json.loads(out_file.read_text())
        assert sarif["version"] == "2.1.0"
        assert len(sarif["runs"][0]["results"]) > 0

    def test_scan_json_output(self, tmp_path):
        (tmp_path / "app.py").write_text("eval(x)\n")
        out_file = tmp_path / "output.json"

        parser = build_parser()
        args = parser.parse_args([
            "scan",
            "--root", str(tmp_path),
            "--ruleset", str(CORE_FIXTURES / "valid_ruleset.yml"),
            "--out", str(out_file),
            "--format", "json",
        ])
        ret = cmd_scan(args)
        assert ret == 0

        data = json.loads(out_file.read_text())
        assert isinstance(data, list)

    def test_scan_no_findings(self, tmp_path):
        (tmp_path / "clean.py").write_text("print('hello')\n")
        out_file = tmp_path / "output.sarif"

        parser = build_parser()
        args = parser.parse_args([
            "scan",
            "--root", str(tmp_path),
            "--ruleset", str(CORE_FIXTURES / "valid_ruleset.yml"),
            "--out", str(out_file),
        ])
        ret = cmd_scan(args)
        assert ret == 0


class TestCmdRulesList:
    def test_list_rulesets(self, tmp_path, capsys):
        rulesets_dir = tmp_path / "rulesets"
        rulesets_dir.mkdir()
        (rulesets_dir / "test.yml").write_text("rules: []\n")

        parser = build_parser()
        args = parser.parse_args(["rules", "list", "--repo-root", str(tmp_path)])
        ret = cmd_rules_list(args)
        assert ret == 0
        captured = capsys.readouterr()
        assert "test.yml" in captured.out


class TestBuildParser:
    def test_parser_scan_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["scan"])
        assert args.root == "."
        assert args.format == "sarif"
