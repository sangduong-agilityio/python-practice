# Training plan: the epic workflow

Goal: by the end, you run a whole feature this way: Claude plans it as an epic,
splits it into small pull requests, verifies each one by code and by hand, reviews the
whole epic, and you only read the plan, review and merge.

Reference: [docs/workflow.md](../workflow.md) and its visual map (artifact "Task API Epic Workflow").

Tools in this repo for it:

| Tool | What it does |
|------|--------------|
| `docs/workflow.md` | The rules Claude follows |
| `docs/epics/_template.md`, `docs/test-reports/_template.md` | Plan and report templates |
| `ticket-worktree` skill | One command: worktree + `.env` + plan-mode prompt |
| `epic-reviewer` agent | Read-only review of a whole epic |
| `fix-ticket`, `add-resource`, `review-checklist`, `how-we-write-migrations` skills | How each sub-PR is built and checked |
| Hooks | Block push to `main`, force-push, `--no-verify`; ruff + pytest before every commit; format on edit |
| `task-api` MCP server | Drive the running API from Claude for the by-hand checks |

Each day: about 2-3 hours, ends with a daily report (I. FINISHED / II. IN-PROGRESS /
III. ISSUES / IV. NEXT PLAN).

---

## Day 1: Set up and read the rules

**Learn:** the three branch levels, who does what, the "never" list, the stop-reviewing rule.

1. Read `docs/workflow.md` end to end, then the Task API Epic Workflow artifact.
2. Push the pending work: `main` is ahead of `origin`; merge `chore/epic-workflow`
   after reviewing it, then Sync in VS Code. From now on nothing goes to `main` except
   through a pull request.
3. Check the tools work:
   ```bash
   python -m unittest discover -s .claude/hooks -p "test_*.py"
   python -m unittest discover -s .claude/skills/ticket-worktree
   python -m pytest -q
   ```
4. Dry run the guard: ask Claude to `git push origin main` and see the hook refuse it.
5. Clean up: the old `.claude/worktrees/capstone-build` worktree holds unfinished
   comments code; copy what you want to keep into a scratch folder (Day 2 restarts it
   properly), then remove that worktree.

**Done when:** all three test commands are green and the push to `main` is blocked.

## Day 2: Plan an epic (E1 Task comments)

**Learn:** plan mode, writing scope / out of scope / decisions, cutting sub-PRs.

1. `python .claude/skills/ticket-worktree/new_worktree.py epic/task-comments`
2. Open Claude Code in the new folder in plan mode with the printed prompt. Ask for
   comments on tasks: add, list, edit own, delete own (the unfinished code from the old
   worktree is a starting point, not the spec).
3. Read the plan like a reviewer: is each sub-PR one concern, under ~400 lines, green on
   its own? Are the decisions written with reasons? Push back once if not.
4. Say go. Claude commits `docs/epics/task-comments.md`, pushes `epic/task-comments` and
   prepares the draft Epic PR `Epic E1: Task comments`.

**Done when:** the plan file is on the epic branch and the draft Epic PR exists.

## Day 3: Sub-PRs, stacked (E1)

**Learn:** branch naming, sub-PR size, stacking, verify-before-push.

1. Let Claude build the sub-PRs from the checklist (for example: model + migration,
   service + endpoints, permissions + edge cases). It should not wait for your merge:
   the second sub-PR stacks on the first.
2. For each sub-PR check the PR description: what changed, how it was verified, the
   decisions it made alone.
3. Review and merge sub-PRs into `epic/task-comments` in order. Ask for one change on an
   earlier sub-PR and watch Claude merge the fix up the stack (no rebase, no force-push).

**Done when:** every checklist item is ticked and merged into the epic branch.

## Day 4: Verify by hand and write the test report (E1)

**Learn:** testing as a client, not only with pytest.

1. Start the API and have Claude walk every new endpoint on `/docs` (or through the
   `task-api` MCP server): happy path, 422, 404, 403 (second user), 401.
2. Claude fills `docs/test-reports/task-comments.md` from the template in a
   `test/task-comments/report` sub-PR.
3. You re-run two rows of the report yourself on `/docs` and compare.

**Done when:** the report is merged and its rows match what you saw.

## Day 5: Review the whole epic and close it (E1)

**Learn:** the epic-reviewer, CONFIRMED vs PLAUSIBLE, when to stop reviewing.

1. Ask Claude to run the `epic-reviewer` agent on `task-comments`.
2. Each medium/high finding becomes a `fix/task-comments/<part>` sub-PR, test first.
   Run the reviewer again on the whole epic. Stop when it is clean; low findings go in
   one last sub-PR or the Epic PR as follow-ups.
3. Claude re-verifies the epic tip, writes the review summary in the Epic PR and marks it
   ready. You review and merge it into `main`.
4. Retro (15 min): what did you have to correct by hand? Add it to `CLAUDE.md` or a skill
   so it does not happen again.

**Done when:** E1 is merged into `main` and the retro note is committed.

## Day 6-7: Epic E2 on your own (Task due-date filters)

**Learn:** running the loop with minimal intervention.

Feature: `GET /projects/{id}/tasks` gets `overdue=true`, `due_before`, `due_after`
(inclusive dates; undated tasks drop out of due filters; `due_after` later than
`due_before` is a 400; overdue = due date before today and status not `done`).

Your only inputs: the one-paragraph request above, the plan review, merges, and the
final Epic PR review. Count how many times you had to step in; the goal is two or fewer
(the plan review and the final merge).

**Done when:** E2 is merged, its test report exists, and your intervention count is noted
in the daily report.

---

## Checklist of skills learned

- [ ] Explain the three branch levels and why `epic/*` is never rebased
- [ ] Read an epic plan critically (scope, out of scope, decisions, sub-PR size)
- [ ] Review and merge a stack of sub-PRs, including a fix on an earlier one
- [ ] Verify an API change by hand and record it in a test report
- [ ] Run the epic-reviewer and apply the stopping rule
- [ ] Ship an epic with only plan review + merges as your input
