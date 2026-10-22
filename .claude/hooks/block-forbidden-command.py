#!/usr/bin/env python3
"""PreToolUse hook: block-forbidden-command.

Reads the hook payload from stdin and denies shell commands (Bash/PowerShell)
that are destructive: force pushes, recursive force deletes, and destructive
database operations. Prints a JSON permission decision on a match.
"""
import json
import re
import sys

SEPARATORS = re.compile(r"&&|\|\||[;|\n]")
WRAPPERS = {"sudo", "command", "builtin", "nohup", "time", "env"}

# Matched against each command segment (shell statement).
SEGMENT_RULES = [
    (
        r"^git\b.*\bpush\b.*(\s--force\b|--force-with-lease|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s\+\S)",
        "git push --force rewrites remote history",
    ),
    (r"^git\b.*\breset\b.*--hard\b", "git reset --hard discards uncommitted work"),
    (r"^git\b.*\bclean\b.*\s-[a-zA-Z]*f", "git clean -f deletes untracked files"),
    (r"^(remove-item|ri)\b(?=.*-recurse)(?=.*-force)", "recursive force delete (Remove-Item)"),
    (r"^(rmdir|rd)\b.*\s/s\b", "recursive directory delete (rmdir /s)"),
    (r"^del\b.*\s/s\b", "recursive delete (del /s)"),
    (r"^alembic\b.*\bdowngrade\s+base\b", "alembic downgrade base drops the whole schema"),
    (r"^docker(-compose|\s+compose)\b.*\bdown\b.*(\s-v\b|--volumes)", "compose down -v deletes database volumes"),
    (r"^(dropdb|dropuser)\b", "dropdb/dropuser destroys a database"),
    (r"^(redis-cli\b.*\b)?(flushall|flushdb)\b", "FLUSHALL/FLUSHDB wipes the datastore"),
]

# Matched against the whole command (SQL usually sits inside quotes).
SQL_RULES = [
    (r"\bdrop\s+(database|schema|table)\b", "DROP DATABASE/SCHEMA/TABLE"),
    (r"\btruncate\s+(table\s+)?\w", "TRUNCATE"),
    (r"\bmetadata\.drop_all\b|\bdrop_all\s*\(", "SQLAlchemy drop_all()"),
]


def tokens_of(segment):
    toks = segment.split()
    while toks and (toks[0].lower() in WRAPPERS or re.match(r"^\w+=", toks[0])):
        toks = toks[1:]
    return toks


def rm_is_recursive_force(toks):
    if not toks or toks[0].replace("\\", "/").split("/")[-1].lower() not in ("rm", "rm.exe"):
        return False
    recursive = force = False
    for t in toks[1:]:
        if t == "--":
            break
        if t.startswith("--"):
            recursive |= t == "--recursive"
            force |= t == "--force"
        elif t.startswith("-"):
            recursive |= any(c in t for c in "rR")
            force |= "f" in t
    return recursive and force


def find_violation(command):
    lowered = command.lower()
    for pattern, reason in SQL_RULES:
        if re.search(pattern, lowered):
            return reason
    if re.search(r"\bdelete\s+from\s+\S+", lowered) and not re.search(r"\bwhere\b", lowered):
        return "DELETE FROM without a WHERE clause"

    for segment in SEPARATORS.split(command):
        toks = tokens_of(segment.strip())
        if not toks:
            continue
        if rm_is_recursive_force(toks):
            return "rm -rf recursively force-deletes files"
        normalized = " ".join(toks).lower()
        for pattern, reason in SEGMENT_RULES:
            if re.search(pattern, normalized):
                return reason
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    reason = find_violation(command)
    if reason:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"block-forbidden-command: {reason}. "
                    "Run it yourself if it is really intended."
                ),
            }
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
