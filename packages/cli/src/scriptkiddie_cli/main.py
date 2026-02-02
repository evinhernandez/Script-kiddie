from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from scriptkiddie_core.scanner import scan
from scriptkiddie_core.sarif import to_sarif


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    ruleset = Path(args.ruleset).resolve()
    findings = scan(root=root, ruleset_path=ruleset)

    if args.format == "sarif":
        out_obj = to_sarif(findings)
        Path(args.out).write_text(json.dumps(out_obj, indent=2), encoding="utf-8")
    else:
        Path(args.out).write_text(json.dumps([f.model_dump() for f in findings], indent=2), encoding="utf-8")

    print(f"[scriptkiddie] scanned={root} ruleset={ruleset} findings={len(findings)} out={args.out}")
    return 0


def cmd_rules_list(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    rulesets = sorted((repo_root / "rulesets").glob("*.yml"))
    for r in rulesets:
        print(r.as_posix())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scriptkiddie", description="Script-kiddie CLI: rules + SARIF")
    sub = p.add_subparsers(dest="cmd", required=True)

    scan_p = sub.add_parser("scan", help="Scan a directory and emit SARIF or JSON findings")
    scan_p.add_argument("--root", default=".", help="Root directory to scan")
    scan_p.add_argument("--ruleset", default="rulesets/owasp-llm-top10.yml", help="Ruleset YAML path")
    scan_p.add_argument("--out", default="script-kiddie.sarif", help="Output file")
    scan_p.add_argument("--format", choices=["sarif", "json"], default="sarif", help="Output format")
    scan_p.set_defaults(func=cmd_scan)

    rules_p = sub.add_parser("rules", help="Ruleset helpers")
    rules_sub = rules_p.add_subparsers(dest="rules_cmd", required=True)

    rules_list = rules_sub.add_parser("list", help="List rulesets under rulesets/")
    rules_list.add_argument("--repo-root", default=".", help="Repo root (contains rulesets/)")
    rules_list.set_defaults(func=cmd_rules_list)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
