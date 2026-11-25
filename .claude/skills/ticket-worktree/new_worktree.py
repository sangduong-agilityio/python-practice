"""Create a worktree for one epic or sub-PR and print the plan-mode prompt.

Usage (from the main checkout):
    python .claude/skills/ticket-worktree/new_worktree.py <branch> [--base REF] [--path DIR]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

BRANCH = re.compile(r"^(epic/[a-z0-9-]+|(feat|fix|refactor|docs|test|chore)/[a-z0-9-]+/[a-z0-9-]+)$")


class SetupError(Exception):
    pass


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise SetupError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def default_base(branch: str) -> str:
    """Epics start from origin/main; a sub-PR from its epic branch."""
    if branch.startswith("epic/"):
        return "origin/main"
    slug = branch.split("/")[1]
    return f"epic/{slug}"


def default_path(repo: Path, branch: str) -> Path:
    return repo.parent / f"task-api-{branch.replace('/', '-')}"


def plan_prompt(branch: str, base: str, others: list[str]) -> str:
    slug = branch.split("/")[1]
    lines = [
        f"Branch `{branch}` (from `{base}`). Follow docs/workflow.md.",
        "",
    ]
    if branch.startswith("epic/"):
        lines += [
            f"Plan epic `{slug}`: copy docs/epics/_template.md to docs/epics/{slug}.md and fill in",
            "goal, scope, out of scope, decisions and the sub-PR checklist (each sub-PR one",
            "concern, under ~400 lines, green on its own). Stop after the plan for my review.",
        ]
    else:
        lines += [
            f"Implement this sub-PR of epic `{slug}` as described in docs/epics/{slug}.md:",
            "<which checklist item>. Tests first, verify per docs/workflow.md section 4,",
            f"update docs/test-reports/{slug}.md, tick the item, commit, push, prepare the PR.",
        ]
    lines += ["", "CLAUDE.md rules this touches: <fill in>."]
    if others:
        lines += ["", "Other worktrees (other sessions own their files, do not change them):"]
        lines += [f"  - {o}" for o in others]
    return "\n".join(lines)


def other_worktrees(repo: Path) -> list[str]:
    out = git("worktree", "list", "--porcelain", cwd=repo)
    paths = [line[len("worktree ") :] for line in out.splitlines() if line.startswith("worktree ")]
    return [p for p in paths if Path(p).resolve() != repo.resolve()]


def create(repo: Path, branch: str, base: str | None, path: Path | None, fetch: bool = True) -> Path:
    if not BRANCH.match(branch):
        raise SetupError(
            f"branch {branch!r} must be epic/<slug> or <type>/<slug>/<part> "
            "(type: feat, fix, refactor, docs, test, chore; lowercase kebab-case)"
        )
    base = base or default_base(branch)
    path = path or default_path(repo, branch)
    if path.exists():
        raise SetupError(f"{path} already exists; pick another --path or remove it first")
    if fetch:
        git("fetch", "-q", "origin", cwd=repo)
    if git("branch", "--list", branch, cwd=repo):
        raise SetupError(f"branch {branch} already exists; check it out in a worktree yourself")
    git("worktree", "add", "-b", branch, str(path), base, cwd=repo)
    env = repo / ".env"
    if env.is_file():
        shutil.copy2(env, path / ".env")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("branch")
    parser.add_argument("--base")
    parser.add_argument("--path", type=Path)
    parser.add_argument("--no-fetch", action="store_true", help="skip git fetch (offline)")
    args = parser.parse_args(argv)

    repo = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()))
    try:
        others = other_worktrees(repo)
        path = create(repo, args.branch, args.base, args.path, fetch=not args.no_fetch)
    except SetupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    base = args.base or default_base(args.branch)
    print(f"Worktree ready: {path}\n")
    print("Start Claude Code there in plan mode with this prompt:\n")
    print(plan_prompt(args.branch, base, others))
    return 0


if __name__ == "__main__":
    sys.exit(main())
