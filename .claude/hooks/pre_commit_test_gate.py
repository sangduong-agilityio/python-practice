#!/usr/bin/env python3
"""PreToolUse hook: pre-commit test gate.

When Claude runs `git commit` (Bash or PowerShell), first run:
  1. `ruff check` on the staged Python files (not the whole repo: older code
     still has lint findings that are out of scope for a single commit), and
  2. the full `pytest` suite.
If either fails, the commit is denied and the failure output is shown to Claude,
which turns the CLAUDE.md rule "never declare a task complete without pytest"
into an automatic check. Commits made by a person outside Claude are not affected.
"""
import json
import os
import re
import subprocess
import sys

GIT_COMMIT = re.compile(r"(?<![\w./\\-])git(?:\.exe)?(?:\s+-\S+(?:\s+[^\s-]\S*)?)*\s+commit\b")
TAIL_LINES = 25


def run(cmd, cwd):
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def tail(text):
    return "\n".join(text.splitlines()[-TAIL_LINES:])


def staged_python_files(cwd):
    code, out = run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd)
    if code != 0:
        return []
    return [f for f in out.splitlines() if f.endswith(".py")]


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"pre-commit-test-gate: {reason}",
        }
    }))


def main():
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", errors="replace"))
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not GIT_COMMIT.search(command):
        return 0

    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()

    files = staged_python_files(cwd)
    if files:
        code, out = run([sys.executable, "-m", "ruff", "check", *files], cwd)
        if code != 0:
            deny(f"ruff found problems in staged files. Fix them, re-stage, then commit.\n{tail(out)}")
            return 0

    code, out = run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"], cwd)
    if code != 0:
        deny(f"pytest is not green. Fix the failing tests before committing.\n{tail(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
