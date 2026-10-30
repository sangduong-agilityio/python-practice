#!/usr/bin/env python3
"""PostToolUse hook: format-on-edit.

Reads the hook payload from stdin and, when the edited file is a Python file,
runs `ruff format` and then `ruff check --fix` on it. Uses the `ruff` binary
when it is on PATH, otherwise `python -m ruff`. Always exits 0 so a missing
ruff, a timeout or a lint error never blocks an edit.
"""

import json
import os
import shutil
import subprocess
import sys

TIMEOUT_SECONDS = 10


def ruff_command():
    exe = shutil.which("ruff")
    return [exe] if exe else [sys.executable, "-m", "ruff"]


def run(args, cwd):
    try:
        subprocess.run(
            args,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def main():
    # Read bytes and decode as UTF-8: on Windows sys.stdin uses the locale
    # codec (cp1252), which fails on non-ASCII file paths.
    try:
        payload = json.loads(
            sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
        )
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not isinstance(file_path, str) or not file_path.lower().endswith(".py"):
        return 0
    if not os.path.isfile(file_path):
        return 0

    # ruff finds pyproject.toml from the file path; cwd only anchors a relative path.
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or None
    ruff = ruff_command()
    run(ruff + ["format", file_path], cwd)
    run(ruff + ["check", "--fix", file_path], cwd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
