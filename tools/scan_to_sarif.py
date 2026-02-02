#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys

# Backwards-compatible helper that uses the CLI
def main():
    cmd = [sys.executable, "-m", "scriptkiddie_cli.main", "scan"]
    cmd += sys.argv[1:]
    raise SystemExit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
