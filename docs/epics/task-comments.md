# Epic E1: Task comments

Branch: `epic/task-comments` · Epic PR: (opened after plan approval) · Workflow: [docs/workflow.md](../workflow.md) ·
Test report: [docs/test-reports/task-comments.md](../test-reports/task-comments.md)

## Goal

People working on a task can discuss it in place: the project owner and the task's
assignee can add comments to a task, read them oldest first, fix their own comments and
remove them. Today the only place for that conversation is outside the app.

## Scope

- `task_comments` table: task, author, content, soft-delete flag, timestamps; Alembic migration.
- `POST /api/v1/tasks/{task_id}/comments`: add a comment (201).
- `GET /api/v1/tasks/{task_id}/comments?limit=&offset=`: list comments, oldest first,
  with `items`, `total`, `limit`, `offset`.
- `PATCH /api/v1/comments/{comment_id}`: edit the content of your own comment.
- `DELETE /api/v1/comments/{comment_id}`: remove a comment (204).
- Tests for every endpoint (happy path, 422, 404, 403, 401) and a test report.

## Out of scope

- @mentions, notifications or emails about new comments.
- Replies / threads, reactions, attachments.
- Edit history (only the latest content is kept; `updated_at` shows it was edited).
- Showing comment counts on task responses (can be a later epic).

## Decisions

- **Who can read and add comments:** the owner of the task's project and the task's
  assignee. Everyone else gets 403. Same rule as the unfinished prototype on
  `feature/task-comments-log`, which keeps comments private to the people on the task.
- **Who can edit:** only the comment's author. The project owner cannot rewrite someone
  else's words.
- **Who can delete:** the author, or the project owner (moderation of their project).
- **Soft delete:** `DELETE` sets `is_deleted = true`; deleted comments are hidden from the
  list and `total`, and editing or deleting them again returns 404. Keeps history for audit.
- **Author removed:** `author_id` is set to NULL (`ON DELETE SET NULL`) so the discussion
  survives; deleting a task deletes its comments (`ON DELETE CASCADE`).
- **Content:** trimmed, 1-5000 characters; blank or whitespace-only is 422.
- **Pagination:** `limit` 1-100 (default 20), `offset` >= 0, like the task list.
- **Index:** `(task_id, is_deleted, created_at)` serves the list query; `author_id` indexed.
- **Migration:** the repo has no baseline revision yet, so `create_task_comments` is the
  first Alembic revision and assumes `users` and `tasks` exist (as the app creates them).
- **Prototype code:** `feature/task-comments-log` is used as reference only; each sub-PR is
  rewritten and reviewed on its own. Its unrelated `tests/test_auth.py` rename is dropped.

## Sub-PRs

- [x] `feat/task-comments/model`: `TaskComment` model, export in `app/models/__init__.py`,
  migration (upgrade / downgrade / upgrade checked), repository (create, get, list, count)
  with tests
- [ ] `feat/task-comments/create-list`: schemas, service with the read/add rule,
  `POST` and `GET` endpoints, router registration, tests (201, list order, pagination,
  hidden deleted rows, 422, 404, 403, 401)
- [ ] `feat/task-comments/edit-delete`: `PATCH` (author only) and `DELETE` (author or
  project owner, soft delete), tests (200/204, 403 for others, 404 for deleted or missing,
  422 for blank content)
- [ ] `test/task-comments/report`: by-hand check of every endpoint on `/docs`, recorded in
  `docs/test-reports/task-comments.md`
