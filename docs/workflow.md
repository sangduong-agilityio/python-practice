# Epic workflow

How feature work moves from idea to `main` in this repo: GitHub pull requests, an
API without a web UI yet, developed on Windows.

Claude follows it without asking; the user reviews and merges pull requests.

```
main ◀── Epic PR (user reviews and merges) ── epic/<slug>
                                          ▲      ▲      ▲
                         sub-PRs (user reviews and merges) from
                         feat/<slug>/<part>, fix/<slug>/<part>, ...
```

## Roles

| Who | Does |
|-----|------|
| Claude | Plans the epic, writes every sub-PR, verifies it, pushes the branch and prepares the pull request. Never merges. |
| `epic-reviewer` agent | Reviews the whole epic once all sub-PRs are merged, before the Epic PR leaves Draft. Read-only. |
| User | Reads the epic plan, reviews and merges sub-PRs into the epic branch, then reviews and merges the Epic PR into `main`. |

## 1. One feature = one epic

- Branch `epic/<slug>` from the latest `origin/main`. `<slug>` is short kebab-case: `task-comments`.
- The first commit adds `docs/epics/<slug>.md`, copied from `docs/epics/_template.md`:
  goal, scope, out of scope, decisions and the sub-PR checklist.
- Write the plan in **plan mode** and stop once for the user to read it. After the
  user says go, do not ask again: decide, and write the reason in the PR description.
- Push the branch and open the **Epic PR** `epic/<slug>` → `main` as a **draft**, titled
  `Epic E<n>: <name>` (`Epic E1: Task comments`). Its description is the same checklist.

## 2. Sub-PRs go into the epic branch

- Branch name: `<type>/<slug>/<part>`, type is `feat`, `fix`, `refactor`, `docs`, `test` or `chore`.
  Example: `feat/task-comments/endpoints`.
- Branch from the tip of `epic/<slug>`, in a worktree (the `ticket-worktree` skill sets it up).
  Never work in the main checkout.
- One sub-PR is one reviewable step: one concern, usually under ~400 changed lines,
  green on its own.
- Tick the item in `docs/epics/<slug>.md` inside the sub-PR that completes it.

### Opening the pull request (GitHub)

`gh` is not installed. After `git push -u origin <branch>`, open the compare page in
the user's Chrome, where they are signed in to GitHub, and fill in the form:

```
https://github.com/sangduong-agilityio/python-practice/compare/<base>...<branch>?expand=1
```

`<base>` is `epic/<slug>` for a sub-PR (or the earlier sub-PR's branch when stacked),
`main` for the Epic PR. Title = commit subject; description = what changed, how it was
verified, `Refs #<epic PR>`. If pushing is not possible from Claude's shell, stop after
the commit and tell the user which branch to push from VS Code.

## 3. Stacked sub-PRs

Claude does not wait for a merge to keep going.

- If the next sub-PR needs code from one that is not merged yet, branch from that
  sub-PR's branch and target the pull request at it.
- When the earlier one is merged and its branch deleted, GitHub retargets the next
  pull request to `epic/<slug>` by itself.
- If the user asks for changes on an earlier sub-PR, fix it there, then merge that
  branch into the stacked branches above it (no rebase, no force-push).

## 4. Verify before every push

### By code

```bash
python -m pytest -q                          # whole suite green
python -m ruff check <changed .py files>     # older code still has findings
python -m ruff format --check <changed .py files>
```

- A migration also runs `alembic upgrade head`, `alembic downgrade -1`,
  `alembic upgrade head` (see the `how-we-write-migrations` skill).
- The test count only goes up. Never weaken, skip or delete a test to get green.
- The `pre_commit_test_gate` hook re-runs ruff and pytest on every `git commit`.

### By hand, on the running API (this repo's "UI test")

The API has no web page yet, so the user-facing check is the API itself:

1. Start it: `uvicorn app.main:app --reload`.
2. Open `http://127.0.0.1:8000/docs` in the browser preview and exercise every new or
   changed endpoint as a real client would: log in, the happy path, a 422, a 404,
   another user's object (403), no token (401).
3. Or drive the same flow through the `task-api` MCP server (`mcp_server/`).
4. Record it in the test report (section 6). A failing check is fixed before the
   push, never pushed.

## 5. Keep the epic in step with `main`

- When `main` moves, merge `origin/main` into the epic through a sub-PR
  `chore/<slug>/sync-main`.
- Never rebase or force-push `epic/*`; it is a shared branch.

## 6. Test report

Every epic gets `docs/test-reports/<slug>.md` (from `docs/test-reports/_template.md`),
updated by the sub-PR that adds or changes behaviour:

- one row per scenario: endpoint, steps, expected, actual, result;
- the `pytest` summary line of the epic tip;
- what was checked by hand on `/docs` or through MCP, with the date.

## 7. Close the epic

When every sub-PR is merged into `epic/<slug>`:

1. **Review the whole epic.** Run the `epic-reviewer` agent with the slug. It reads
   `origin/main...origin/epic/<slug>` and returns verified findings; it never edits.
2. **Act on the findings.** Each confirmed finding gets a `fix/<slug>/<part>` sub-PR,
   tests first. A finding left as is goes in the Epic PR description with the reason.
3. **Verify and publish.** Re-run section 4 on the epic tip, check it merges cleanly into
   `main`, put the results and a review summary in the Epic PR, tick the checklist and
   mark the PR **Ready for review**.
4. The user reviews and merges the Epic PR into `main`.

### When to stop reviewing

A review is **clean** when it has no confirmed or plausible finding of medium or high
severity.

- **Not clean:** fix the medium and high findings, then run the agent again on the new
  tip, on the whole epic, not only on the fixes.
- **Clean:** stop running the agent. Fix the low findings in one last sub-PR or list
  them as follow-ups; after that only the verification runs again.
- **Same area twice:** if two reviews in a row find a medium or high issue in the same
  area, stop patching. Write what keeps breaking in the Epic PR and ask the user whether
  to redesign that part, narrow the scope or accept the risk.

## 8. Messages

- Commit subject: conventional and in English, at most ~60 characters
  (`feat(comments): add task comment endpoints`). The body says what was wrong or
  missing and why.
- Commits and sub-PRs say `Refs #<epic PR>`; the Epic PR says `Closes #N` when there is
  an issue.
- Every decision the user did not make is written in the PR description, with the reason.

## 9. Never

- Never merge a pull request.
- Never push to `main`.
- Never push to `epic/*` directly, except the commit that opens the epic.
- Never force-push, never `--no-verify`.
- Never push work that is unfinished or failing its checks.

The `block-forbidden-command` hook enforces the push, force-push and `--no-verify` rules.

## 10. When to stop and ask

Only when truly blocked: missing access or a secret, or a requirement that conflicts
with CLAUDE.md or another approved decision. Everything else is decided and explained
in the pull request.
