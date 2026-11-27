# Epic E3: Task search

Branch: `epic/task-search` · Epic PR: (opened after plan approval) · Workflow: [docs/workflow.md](../workflow.md) ·
Test report: [docs/test-reports/task-search.md](../test-reports/task-search.md)

## Goal

A project owner can find a task by a word they remember ("login", "invoice") instead of paging
through the whole list: `GET /projects/{id}/tasks` gains a `q` search parameter.

## Scope

- `q`: case-insensitive substring search in the task's title **or** description.
- Combines with every existing filter (`status`, `priority`, `overdue`, `due_after`,
  `due_before`) and with `skip` / `limit`.
- Tests and a test report.

## Out of scope

- Full-text search, relevance ranking, typo tolerance.
- Searching comments, tags or assignee names.
- Searching across projects.

## Decisions

- **Literal search:** `%` and `_` in `q` match themselves (LIKE with `autoescape=True`), so
  `q=100%` finds "100% done" and not everything.
- **Trimmed:** surrounding spaces are removed; a `q` that is empty after trimming is ignored,
  like leaving the parameter out (a cleared search box should show the whole list).
- **Length:** at most 100 characters, longer is 422 like the other list filters.
- **Case-insensitive:** SQL `ILIKE` (SQLAlchemy `ilike`). PostgreSQL folds Vietnamese and other
  non-ASCII letters too; SQLite, used by the tests, only folds ASCII, so tests use ASCII words.
- **No index:** substring search cannot use a B-tree index; acceptable at this project's size.
  A trigram index can come with a later epic if lists get large.
- **Order unchanged:** results keep the list's `created_at` newest-first order.

## Sub-PRs

- [ ] `feat/task-search/repository`: `q` in `TaskRepository.list_by_project` (title or
  description, case-insensitive, wildcards escaped), repository tests
- [ ] `feat/task-search/endpoint`: `q` query parameter (trimmed, empty ignored, max 100 → 422),
  service pass-through, API tests (match in title, in description, both filters combined,
  wildcards, 422, 403, 401)
- [ ] `test/task-search/report`: by-hand check on the running API, recorded in
  `docs/test-reports/task-search.md`
