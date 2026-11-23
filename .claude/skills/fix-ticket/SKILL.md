---
name: fix-ticket
description: Use when asked to fix a bug, ticket or GitHub issue in task-management-api (e.g. "fix ticket #123", "fix TICKET-201", "this endpoint returns 422 for X"). Runs the team's bug-fix workflow - reproduce with a failing test first, then the smallest fix, full pytest, review-checklist, and a conventional commit plus PR description.
---

# Fix Ticket

A fixed chain of steps. Do them in order and do not skip the red test: a fix without a test that failed first is not done.

## 1. Understand the ticket
- Get the ticket text: from the user, or `gh issue view <number>` when it is a GitHub issue number.
- Write down in 2-3 lines: **expected behaviour**, **actual behaviour**, **how to trigger it** (endpoint, method, payload, query params, user).
- If any of the three is unclear, ask before writing code.

## 2. Branch
- Start from an up-to-date `main`: `git checkout main && git pull`.
- Create `fix/<ticket-id>-<short-kebab-summary>`, e.g. `fix/201-status-filter-case`.

## 3. Reproduce with a failing test (RED)
- Add the test to the test file of the affected area (`tests/test_tasks.py`, `tests/test_projects.py`, `tests/test_auth.py`); create a new file only if no file fits.
- Name it `test_<ticket_id>_<what_should_happen>` and start the docstring with the ticket id and the expected behaviour.
- Reuse the existing helpers and fixtures: `client`, `auth_headers`, `test_user` from `tests/conftest.py`, and `create_project` / `create_task` from `tests/test_tasks.py`.
- Login in tests uses OAuth2 form data: `data={"username": email, "password": ...}`, never `json=`.
- Run only this test and confirm it **fails for the reason in the ticket** (not an import error or a fixture problem):
  ```bash
  pytest tests/<file>.py -k <test_name> -v
  ```
  Report the failing assertion to the user before fixing.

## 4. Fix (smallest change that makes the test pass)
- Fix the cause in the right layer: validation in `app/schemas/`, query logic in `app/repositories/`, business rules in `app/services/`, HTTP mapping in `app/api/v1/endpoints/`.
- Follow CLAUDE.md: `selectinload` for relationships, `await` every DB call, enum inputs normalized with `.strip().lower()` and invalid values still 422, Pydantic schemas on every boundary.
- If the fix changes a model, follow the `how-we-write-migrations` skill.
- Add a **regression guard** next to the new test when it applies, e.g. an invalid value is still rejected with 422.
- No unrelated refactors or formatting changes in the same branch.

## 5. Verify (GREEN)
```bash
pytest tests/<file>.py -k <test_name> -v   # the new test passes
pytest                                      # the whole suite is green
ruff check <the .py files you changed>      # older code still has lint findings; don't fix those here
```
Never say the ticket is fixed without the full `pytest` run and its pass/fail counts. The `pre_commit_test_gate` hook also re-runs ruff on staged files and the full suite on every `git commit`, and blocks the commit if either fails.

## 6. Self-review
Run the `review-checklist` skill against `main...HEAD` and fix every finding before committing.

## 7. Commit
- `git diff --stat`: only the files this fix needs; no line-ending-only (CRLF) changes.
- One commit, conventional and in English:
  ```
  fix(<area>): <what now works> (#<ticket-id>)
  ```
  e.g. `fix(tasks): accept uppercase status in list filter (#201)`.

## 8. PR description
Give the user a ready-to-paste description (open the PR only if they ask):
```markdown
## Ticket
#<id>: <title>

## Root cause
<one or two sentences>

## Fix
<what changed and in which layer>

## Tests
- New: `<test name>` (failed before the fix, passes now)
- Full suite: <N> passed
```

## Output to the user
After each of steps 3, 5 and 7, report in one short paragraph: what you ran, the result, and what comes next.
