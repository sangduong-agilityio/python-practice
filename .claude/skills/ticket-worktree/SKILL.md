---
name: ticket-worktree
description: Set up a git worktree for one epic, sub-PR or ticket in task-management-api (branch from the right base, copy .env) and print the plan-mode prompt to start it with. Use when starting an epic or a sub-PR, or when asked to "make a worktree for <slug>" or "start epic <name>".
---

# Ticket worktree

Every epic and sub-PR is worked on in its own worktree next to the main checkout
(`docs/workflow.md`, section 2). This skill does the setup in one command and prints the
prompt to start the plan with.

## Run

From the main checkout:

```bash
python .claude/skills/ticket-worktree/new_worktree.py <branch> [--base <ref>] [--path <dir>]
```

- `<branch>`:
  - an epic: `epic/<slug>` (base `origin/main`, the default);
  - a sub-PR: `feat/<slug>/<part>`, `fix/<slug>/<part>`, ... with `--base epic/<slug>`
    (or `--base <earlier sub-PR branch>` when stacked).
- The worktree goes to `../task-api-<branch with / replaced by ->`; `--path` changes it.
- The script fetches `origin` first, refuses a path or branch that already exists, never
  changes files in the main checkout, and only copies its `.env` (git-ignored).

## After it runs

1. Read the epic plan (`docs/epics/<slug>.md`) or the ticket and fill in the printed prompt.
2. Check the "other worktrees" list it prints: those belong to other sessions, so the plan
   must not change the files they own.
3. Start Claude Code in the new folder in **plan mode** (Shift+Tab until it says plan mode)
   with that prompt.

When the pull request is merged, remove the worktree with
`git worktree remove <path>` (never `--force`: a worktree with uncommitted changes
should stop the removal).

## Tests

```bash
python -m unittest discover -s .claude/skills/ticket-worktree
```
