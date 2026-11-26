# Test report: Epic E2 Task due-date filters

Epic: [docs/epics/task-due-date-filters.md](../epics/task-due-date-filters.md) · Branch tip: `98e34a7` (both feature sub-PRs stacked) · Date: 2026-11-26

## By code

```
107 passed, 5 warnings in 34.43s
```

Warnings: Alembic's `path_separator` notice (from `tests/test_migrations.py`) and FastAPI's
deprecation of the `HTTP_422_UNPROCESSABLE_ENTITY` name, which this endpoint already used
for its other filters.

New tests in this epic: 19 (88 before the epic, 107 after)

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_task_due_date_filters_repository.py` | 5 | overdue (done never overdue, later today not overdue, undated excluded), `overdue=false`, inclusive range at 00:00 and 23:30 boundaries, each end alone, combined with status |
| `tests/test_task_due_date_filters_api.py` | 14 | each filter through the API, same-day range, combined with status, 422 for reversed range / malformed / impossible date / bad boolean, message names both dates, 403, 404, 401 |

## By hand on the running API

The API ran with `uvicorn app.main:app --port 8012` on a fresh SQLite database. Two accounts
were registered and logged in (OAuth2 form data): the project owner and another user. The
owner created one project with six tasks, dated relative to the run time
(2026-11-26 02:07 UTC, week Mon 2026-11-23 to Sun 2026-11-29):

| Task | Due | Status |
|------|-----|--------|
| A | yesterday | todo |
| B | a week ago | in_progress |
| C | yesterday | done |
| D | in 2 hours (today) | todo |
| E | in 35 days | todo |
| F | none | todo |

| # | Scenario | Query | Expected | Actual | Result |
|---|----------|-------|----------|--------|--------|
| 1 | No filter | (none) | 200 A-F | 200 A-F | ✅ |
| 2 | Overdue: past due and not done | `?overdue=true` | 200 A,B | 200 A,B | ✅ |
| 3 | `overdue=false` does not filter | `?overdue=false` | 200 A-F | 200 A-F | ✅ |
| 4 | Due this week | `?due_after=2026-11-23&due_before=2026-11-29` | 200 A,C,D | 200 A,C,D | ✅ |
| 5 | Only today | `?due_after=2026-11-26&due_before=2026-11-26` | 200 D | 200 D | ✅ |
| 6 | Due after today | `?due_after=2026-11-27` | 200 E | 200 E | ✅ |
| 7 | Overdue and in progress | `?overdue=true&status=IN_PROGRESS` | 200 B | 200 B | ✅ |
| 8 | Reversed range | `?due_after=2026-11-26&due_before=2026-11-25` | 422 | 422 | ✅ |
| 9 | Malformed date | `?due_after=26-11-2026` | 422 | 422 | ✅ |
| 10 | Impossible date | `?due_before=2026-02-30` | 422 | 422 | ✅ |
| 11 | Another user's project | `?overdue=true` | 403 | 403 | ✅ |
| 12 | No token | `?overdue=true` | 401 | 401 | ✅ |
| 13 | Missing project | `/projects/999999/tasks?overdue=true` | 404 | 404 | ✅ |

## Accepted with a reason

- The manual run used SQLite, not PostgreSQL (no local PostgreSQL on this machine). The
  filters are plain comparisons on `tasks.due_date` against UTC datetimes.
- Days are UTC. A user in Vietnam (UTC+7) asking for "today" between 00:00 and 07:00 local
  time gets the previous UTC day; per-user time zones are out of scope for this epic.
