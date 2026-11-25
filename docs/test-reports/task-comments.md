# Test report: Epic E1 Task comments

Epic: [docs/epics/task-comments.md](../epics/task-comments.md) · Branch tip: `98ca526` (all three feature sub-PRs stacked) · Date: 2026-11-25

## By code

```
88 passed, 3 warnings in 27.30s
```

The warnings are Alembic's `path_separator` deprecation notice from `tests/test_migrations.py`.

New tests in this epic: 32 (56 before the epic, 88 after)

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_task_comment_repository.py` | 4 | create defaults, oldest-first pagination and count, soft-deleted rows hidden, scoped to the task |
| `tests/test_migrations.py` | 1 | `create_task_comments`: upgrade, downgrade, upgrade again on SQLite |
| `tests/test_comments.py` | 14 | add and list: 201, trimming, ordering, pagination, hidden deleted rows, 422, 403, 404, 401 |
| `tests/test_comment_edit_delete.py` | 13 | edit (author only) and delete (author or project owner, soft): 200, 204, 403, 404, 422, 401 |

## By hand on the running API

The API ran with `uvicorn app.main:app --port 8011` against a fresh SQLite database whose
`task_comments` table was created by `alembic upgrade head` (the real migration, not
`create_all`). Three real accounts were registered and logged in through
`/api/v1/auth/register` and `/api/v1/auth/login` (OAuth2 form data): the project owner, the
task assignee and an outsider. The owner created a project and a task and assigned it.

| # | Scenario | Request | Expected | Actual | Result |
|---|----------|---------|----------|--------|--------|
| 1 | Owner adds a comment (spaces trimmed) | `POST /tasks/{id}/comments` | 201 | 201 | ✅ |
| 2 | Assignee adds a comment | `POST /tasks/{id}/comments` | 201 | 201 | ✅ |
| 3 | List, oldest first, page 1 of size 2 | `GET /tasks/{id}/comments?limit=2&offset=0` | 200 | 200 | ✅ |
| 4 | Blank content | `POST /tasks/{id}/comments` | 422 | 422 | ✅ |
| 5 | Content over 5000 characters | `POST /tasks/{id}/comments` | 422 | 422 | ✅ |
| 6 | Invalid pagination (`limit=0`) | `GET /tasks/{id}/comments?limit=0` | 422 | 422 | ✅ |
| 7 | Outsider adds a comment | `POST /tasks/{id}/comments` | 403 | 403 | ✅ |
| 8 | Outsider lists comments | `GET /tasks/{id}/comments` | 403 | 403 | ✅ |
| 9 | Comments on a missing task | `GET /tasks/999999/comments` | 404 | 404 | ✅ |
| 10 | No token | `GET /tasks/{id}/comments` | 401 | 401 | ✅ |
| 11 | Author edits own comment | `PATCH /comments/{id}` | 200 | 200 | ✅ |
| 12 | Project owner edits someone else's comment | `PATCH /comments/{id}` | 403 | 403 | ✅ |
| 13 | Edit with blank content | `PATCH /comments/{id}` | 422 | 422 | ✅ |
| 14 | Assignee deletes the owner's comment | `DELETE /comments/{id}` | 403 | 403 | ✅ |
| 15 | Project owner deletes the assignee's comment | `DELETE /comments/{id}` | 204 | 204 | ✅ |
| 16 | Delete it again | `DELETE /comments/{id}` | 404 | 404 | ✅ |
| 17 | Edit a deleted comment | `PATCH /comments/{id}` | 404 | 404 | ✅ |
| 18 | List after delete | `GET /tasks/{id}/comments` | 200, deleted one gone | 200, `total` 4 of 5, deleted one gone | ✅ |
| 19 | Delete without a token | `DELETE /comments/{id}` | 401 | 401 | ✅ |

Also checked:

- Row 1 returned `"content": "Kick-off notes"` for the input `"  Kick-off notes  "`.
- Row 3 returned the two oldest comments in creation order, with `total`, `limit` and `offset`.
- `/openapi.json` (what `/docs` shows) lists `/api/v1/tasks/{task_id}/comments` and
  `/api/v1/comments/{comment_id}`.

## Accepted with a reason

- On SQLite the timestamps come back without a time zone (`2026-11-25T02:59:16`); the
  columns are `DateTime(timezone=True)`, so PostgreSQL returns them with one. Not a defect of
  this epic; the other tables behave the same way.
- The manual run used SQLite, not PostgreSQL: there is no local PostgreSQL on this machine.
  The migration itself is plain DDL (table, two foreign keys, two indexes).
