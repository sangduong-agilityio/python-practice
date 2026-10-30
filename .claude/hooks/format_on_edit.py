#!/usr/bin/env python3
"""PostToolUse hook: format-on-edit.

Reads the hook payload from stdin and, when the edited file is a Python file
inside the project, runs `ruff check --fix` and then `ruff format` on it. Uses
the `ruff` binary when it is on PATH, otherwise `python -m ruff`. Always exits 0
so a missing ruff, a timeout or a lint error never blocks an edit.
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


def is_inside(path, directory):
    path = os.path.normcase(os.path.realpath(path))
    directory = os.path.normcase(os.path.realpath(directory))
    try:
        return os.path.commonpath([path, directory]) == directory
    except ValueError:  # different drives on Windows
        return False


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
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd")
    if not project_dir:
        return 0
    file_path = os.path.abspath(os.path.join(project_dir, file_path))
    if not os.path.isfile(file_path) or not is_inside(file_path, project_dir):
        return 0

    ruff = ruff_command()
    # Fix before formatting so fixer output (e.g. sorted imports) gets formatted.
    # F401 is left unfixable: an import added in one edit is often used only in
    # the next, and auto-removing it would break that edit.
    # --force-exclude keeps ruff's `exclude` settings for explicitly passed paths.
    run(
        ruff
        + [
            "check",
            "--fix",
            "--extend-unfixable",
            "F401",
            "--force-exclude",
            file_path,
        ],
        project_dir,
    )
    run(ruff + ["format", "--force-exclude", file_path], project_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
