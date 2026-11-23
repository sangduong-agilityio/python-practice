#!/usr/bin/env python3
"""PreToolUse hook: block-forbidden-command.

Reads the hook payload from stdin and denies shell commands (Bash/PowerShell)
that are destructive: force pushes, recursive force deletes, and destructive
database operations. Prints a JSON permission decision on a match.
"""
import json
import os
import re
import subprocess
import sys

SEPARATORS = re.compile(r"&&|\|\||[;|\n]")
WRAPPERS = {"sudo", "command", "builtin", "nohup", "time", "env"}

# Matched against each command segment (shell statement).
SEGMENT_RULES = [
    (
        r"^git\b.*\bpush\b.*(\s--force\b|--force-with-lease|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s\+\S)",
        "git push --force rewrites remote history",
    ),
    (r"^git\b.*\s--no-verify\b", "--no-verify skips the repository's checks; fix what they report"),
    (
        r"^git\b.*\bpush\b(\s+\S+)*\s+(\+?\S+:)?(refs/heads/)?(main|master)(\s|$)",
        "nothing is pushed to main directly (docs/workflow.md); push a branch and open a pull request",
    ),
    (r"^git\b.*\breset\b.*--hard\b", "git reset --hard discards uncommitted work"),
    (r"^git\b.*\bclean\b.*\s-[a-zA-Z]*f", "git clean -f deletes untracked files"),
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


# Delete commands: POSIX rm, plus Remove-Item and its PowerShell aliases.
DELETE_COMMANDS = {"rm", "rm.exe", "del", "erase", "rd", "rmdir", "ri", "remove-item"}

# Message options of `git commit` / `git tag`. Only values that cannot expand
# into a command (single-quoted, bare words, or double-quoted without `$(` or
# backticks, plus the quoted-delimiter heredoc form) are stripped; anything
# else stays visible to the rules below.
_HEREDOC = (
    r'"\$\(cat\s+<<-?\s*(?P<q>[\'"])(?P<id>\w+)(?P=q)[^\n]*\n.*?\n(?P=id)\s*\)"'
)
_DQ = r'"(?:[^"\\$`]|\\.|\$(?!\())*"'
_SQ = r"'[^']*'"
_BARE = r"[^\s$`;&|<>()'\"]+"
_MSG = rf"(?:-[a-zA-Z]*m|--message)(?:=|\s*)(?:{_HEREDOC}|{_DQ}|{_SQ}|{_BARE})"
_PLAIN = r"[^\s;&|<>()$`'\"]+"
_COMMIT_CMD = re.compile(
    rf"(?<![\w./\\-])git(?:\.exe)?(?:\s+-\S+(?:\s+[^\s-]\S*)?)*\s+(?:commit|tag)\b"
    rf"(?:\s+(?:{_MSG}|{_PLAIN}))*",
    re.DOTALL,
)
_MSG_ARG = re.compile(rf"(?<!\S){_MSG}", re.DOTALL)


def strip_commit_messages(command):
    """Blank out commit/tag message text so prose is not matched as a command."""
    return _COMMIT_CMD.sub(lambda m: _MSG_ARG.sub('-m ""', m.group(0)), command)


def tokens_of(segment):
    toks = segment.split()
    while toks and (toks[0].lower() in WRAPPERS or re.match(r"^\w+=", toks[0])):
        toks = toks[1:]
    return toks


def is_recursive_force_delete(toks):
    name = toks[0].replace("\\", "/").split("/")[-1].lower() if toks else ""
    if name not in DELETE_COMMANDS:
        return False
    recursive = force = False
    for t in toks[1:]:
        if t == "--":
            break
        flag = t.lower().lstrip("-")
        if t.startswith("--"):
            recursive |= flag == "recursive"
            force |= flag == "force"
        elif t.startswith("-"):
            # PowerShell parameters (-Recurse, -Force) match by prefix; short
            # POSIX flags (-rf, -R) are clusters of single letters.
            if len(flag) > 1 and "recurse".startswith(flag):
                recursive = True
            elif len(flag) > 1 and "force".startswith(flag):
                force = True
            else:
                recursive |= "r" in flag
                force |= "f" in flag
    return recursive and force


PROTECTED_BRANCHES = {"main", "master"}


def current_branch(cwd):
    try:
        out = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=cwd or None, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def bare_push_to_protected(toks, cwd):
    """`git push` / `git push origin` / `git push origin HEAD` while on main."""
    if len(toks) < 2 or toks[0].lower() not in ("git", "git.exe"):
        return False
    rest = toks[1:]
    workdir = cwd
    while rest and rest[0].startswith("-"):  # git's global options such as -C dir
        if rest[0] in ("-C", "-c") and len(rest) > 1:
            if rest[0] == "-C":
                workdir = rest[1]
            rest = rest[2:]
        else:
            rest = rest[1:]
    if not rest or rest[0] != "push":
        return False
    positionals = [t for t in rest[1:] if not t.startswith("-")]
    if len(positionals) > 1 and "HEAD" not in positionals[1:]:
        return False  # an explicit refspec: SEGMENT_RULES judges it
    return current_branch(workdir) in PROTECTED_BRANCHES


def find_violation(command, cwd=None):
    command = strip_commit_messages(command)
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
        if is_recursive_force_delete(toks):
            return "rm -rf recursively force-deletes files"
        if bare_push_to_protected(toks, cwd):
            return (
                "this push goes to main (the current branch); push a feature "
                "branch and open a pull request (docs/workflow.md)"
            )
        normalized = " ".join(toks).lower()
        for pattern, reason in SEGMENT_RULES:
            if re.search(pattern, normalized):
                return reason
    return None


def main():
    # Read bytes and decode as UTF-8: on Windows sys.stdin uses the locale
    # codec (cp1252), which fails on non-ASCII commands and made the hook fail open.
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", errors="replace"))
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR")
    reason = find_violation(command, cwd)
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
