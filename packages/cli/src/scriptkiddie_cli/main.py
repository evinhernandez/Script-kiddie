from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Optional

from scriptkiddie_core.scanner import scan, scan_multi
from scriptkiddie_core.sarif import to_sarif


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()

    # Support multiple rulesets via comma-separated or glob
    ruleset_strs = args.ruleset if isinstance(args.ruleset, list) else [args.ruleset]
    ruleset_paths: list[Path] = []
    for rs in ruleset_strs:
        expanded = glob.glob(rs, recursive=True)
        if expanded:
            ruleset_paths.extend(Path(p).resolve() for p in sorted(expanded))
        else:
            ruleset_paths.append(Path(rs).resolve())

    if len(ruleset_paths) == 1:
        findings = scan(root=root, ruleset_path=ruleset_paths[0])
    else:
        findings = scan_multi(root=root, ruleset_paths=ruleset_paths)

    fmt = args.format

    if fmt == "sarif":
        out_obj = to_sarif(findings)
        Path(args.out).write_text(json.dumps(out_obj, indent=2), encoding="utf-8")
    elif fmt == "csv":
        from scriptkiddie_core.exports import to_csv
        Path(args.out).write_text(to_csv(findings), encoding="utf-8")
    elif fmt == "md":
        from scriptkiddie_core.exports import to_markdown
        meta = {"target": str(root), "ruleset": ", ".join(str(p) for p in ruleset_paths)}
        Path(args.out).write_text(to_markdown(findings, job_meta=meta), encoding="utf-8")
    else:
        Path(args.out).write_text(json.dumps([f.model_dump() for f in findings], indent=2), encoding="utf-8")

    print(f"[scriptkiddie] scanned={root} rulesets={len(ruleset_paths)} findings={len(findings)} out={args.out}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    from scriptkiddie_core.baseline import diff_findings
    from scriptkiddie_core.models import Finding

    current_data = json.loads(Path(args.current).read_text(encoding="utf-8"))
    baseline_data = json.loads(Path(args.baseline).read_text(encoding="utf-8"))

    def _extract_findings(data) -> list[Finding]:
        """Extract findings from SARIF or JSON array."""
        if isinstance(data, list):
            return [Finding(**f) for f in data]
        if isinstance(data, dict) and "runs" in data:
            findings = []
            for run in data.get("runs", []):
                for r in run.get("results", []):
                    loc = (r.get("locations") or [{}])[0].get("physicalLocation", {})
                    findings.append(Finding(
                        rule_id=r.get("ruleId", ""),
                        title=r.get("message", {}).get("text", ""),
                        category="",
                        severity="medium",
                        file=loc.get("artifactLocation", {}).get("uri", ""),
                        line=loc.get("region", {}).get("startLine", 0),
                        match="",
                        fingerprint=r.get("partialFingerprints", {}).get("primaryLocationLineHash", ""),
                    ))
            return findings
        return []

    current = _extract_findings(current_data)
    baseline = _extract_findings(baseline_data)
    result = diff_findings(current, baseline)

    print(f"New: {result['summary']['new_count']}")
    print(f"Fixed: {result['summary']['fixed_count']}")
    print(f"Unchanged: {result['summary']['unchanged_count']}")

    if result["new"]:
        print("\n--- New findings ---")
        for f in result["new"]:
            print(f"  [{f.severity}] {f.rule_id}: {f.file}:{f.line}")

    if result["fixed"]:
        print("\n--- Fixed findings ---")
        for f in result["fixed"]:
            print(f"  [{f.severity}] {f.rule_id}: {f.file}:{f.line}")

    # Exit 1 if new findings (useful for CI)
    return 1 if result["new"] else 0


def cmd_rules_list(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    rulesets = sorted((repo_root / "rulesets").glob("*.yml"))
    for r in rulesets:
        print(r.as_posix())
    return 0


def cmd_validate_ruleset(args: argparse.Namespace) -> int:
    from scriptkiddie_core.rules import load_ruleset
    path = Path(args.path).resolve()
    try:
        rules = load_ruleset(path)
        print(f"Valid ruleset: {path.name} ({len(rules)} rules)")
        for r in rules:
            print(f"  {r.id}: {r.title} [{r.severity}]")
        return 0
    except Exception as e:
        print(f"Invalid ruleset: {e}")
        return 1


def cmd_validate_policy(args: argparse.Namespace) -> int:
    from scriptkiddie_core.policy_schema import load_policy_config
    import yaml
    path = Path(args.path).resolve()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        config = load_policy_config(data)
        print(f"Valid policy: {config.id} — {config.title}")
        print(f"  Block threshold: severity >= {config.block_if_severity_at_or_above}")
        print(f"  Judge block threshold: {config.judge_block_confidence_threshold}")
        print(f"  Rule overrides: {len(config.rule_overrides)}")
        return 0
    except Exception as e:
        print(f"Invalid policy: {e}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scriptkiddie", description="Script-kiddie CLI: rules + SARIF")
    sub = p.add_subparsers(dest="cmd", required=True)

    scan_p = sub.add_parser("scan", help="Scan a directory and emit SARIF or JSON findings")
    scan_p.add_argument("--root", default=".", help="Root directory to scan")
    scan_p.add_argument("--ruleset", nargs="+", default=["rulesets/owasp-llm-top10.yml"],
                        help="Ruleset YAML path(s) or glob pattern")
    scan_p.add_argument("--out", default="script-kiddie.sarif", help="Output file")
    scan_p.add_argument("--format", choices=["sarif", "json", "csv", "md"], default="sarif", help="Output format")
    scan_p.set_defaults(func=cmd_scan)

    diff_p = sub.add_parser("diff", help="Diff findings between two scans")
    diff_p.add_argument("--current", required=True, help="Current scan output (SARIF or JSON)")
    diff_p.add_argument("--baseline", required=True, help="Baseline scan output")
    diff_p.set_defaults(func=cmd_diff)

    rules_p = sub.add_parser("rules", help="Ruleset helpers")
    rules_sub = rules_p.add_subparsers(dest="rules_cmd", required=True)
    rules_list = rules_sub.add_parser("list", help="List rulesets under rulesets/")
    rules_list.add_argument("--repo-root", default=".", help="Repo root (contains rulesets/)")
    rules_list.set_defaults(func=cmd_rules_list)

    val_rs = sub.add_parser("validate-ruleset", help="Validate a ruleset YAML file")
    val_rs.add_argument("path", help="Path to ruleset YAML")
    val_rs.set_defaults(func=cmd_validate_ruleset)

    val_pol = sub.add_parser("validate-policy", help="Validate a policy YAML file")
    val_pol.add_argument("path", help="Path to policy YAML")
    val_pol.set_defaults(func=cmd_validate_policy)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
