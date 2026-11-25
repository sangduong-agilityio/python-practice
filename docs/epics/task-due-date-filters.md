# Epic E2: Task due-date filters

Branch: `epic/task-due-date-filters` · Epic PR: (opened after plan approval) · Workflow: [docs/workflow.md](../workflow.md) ·
Test report: [docs/test-reports/task-due-date-filters.md](../test-reports/task-due-date-filters.md)

## Goal

A project owner can ask "what is late?" and "what is due this week?" directly from the task
list instead of scanning every task: `GET /projects/{id}/tasks` gains filters on the due date.

## Scope

- `overdue=true`: tasks whose due date has passed and whose status is not `done`.
- `due_after=YYYY-MM-DD` and `due_before=YYYY-MM-DD`: tasks due within a date range.
- The new filters combine with each other and with the existing `status`, `priority`,
  `skip` and `limit`.
- Tests for every filter and its validation, and a test report.

## Out of scope

- Reminders or notifications about due or overdue tasks.
- Sorting by due date (the list keeps its `created_at` newest-first order).
- An index on `tasks.due_date` (the task table has no baseline migration yet; worth a
  separate change once it does).
- Time zones per user: dates are interpreted in UTC.
- The three low follow-ups from the E1 review.

## Decisions

- **Dates, not datetimes, in the query:** `due_after` / `due_before` take `YYYY-MM-DD`,
  which is what a person asks for ("due this week"). `due_date` is stored as a datetime, so a
  day means the whole UTC day.
- **Both ends inclusive:** `due_after=2026-12-01&due_before=2026-12-31` is all of December.
  In SQL: `due_date >= after 00:00 UTC` and `due_date < (before + 1 day) 00:00 UTC`.
- **Overdue:** has a due date, the due date is earlier than now (UTC), and the status is not
  `done`. `in_progress` tasks can be overdue.
- **`overdue=false` does not filter:** it means "not asking for overdue only", not "only on-time
  tasks". It behaves like leaving the parameter out.
- **Undated tasks** drop out of every due filter (a NULL due date matches none of them).
- **Invalid input is 422**, like the existing `status` / `priority` filters in this endpoint:
  a malformed date, or `due_after` later than `due_before`. (The training plan said 400;
  this repo already answers bad list filters with 422, so the endpoint stays consistent.)
- **No schema change:** the filters only read `tasks.due_date`, so no migration.

## Sub-PRs

- [ ] `feat/task-due-date-filters/repository`: `overdue`, `due_after`, `due_before` in
  `TaskRepository.list_by_project`, with repository tests (inclusive ends, undated tasks,
  done tasks never overdue, combined with status)
- [ ] `feat/task-due-date-filters/endpoint`: query parameters on
  `GET /projects/{id}/tasks`, validation (bad date, reversed range → 422), service pass-through,
  API tests (happy path per filter, combinations, 422, 403, 404, 401)
- [ ] `test/task-due-date-filters/report`: by-hand check on the running API, recorded in
  `docs/test-reports/task-due-date-filters.md`
