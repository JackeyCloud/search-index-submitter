#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPOSITORY_HOME = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight or submit sites through search-index-submitter")
    parser.add_argument("targets", nargs="*")
    parser.add_argument("--file")
    parser.add_argument("--sitemap", default="")
    parser.add_argument("--providers", default="indexnow,baidu,google,bing,yandex")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--no-deduplicate", action="store_true")
    args = parser.parse_args()

    home = Path(os.environ.get("SEARCH_SUBMITTER_HOME", REPOSITORY_HOME)).expanduser()
    python = home / ".venv" / "bin" / "python"
    if not python.exists():
        print(f"Missing environment: {python}. Run the setup commands in README.md.", file=sys.stderr)
        return 2
    command = [str(python), "-m", "search_submitter.cli", *args.targets, "--providers", args.providers, "--json"]
    if args.file:
        command.extend(["--file", args.file])
    if args.sitemap:
        command.extend(["--sitemap", args.sitemap])
    if not args.execute:
        command.append("--dry-run")
    if args.no_deduplicate:
        command.append("--no-deduplicate")
    return subprocess.run(command, cwd=home, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
