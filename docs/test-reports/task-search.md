# Test report: Epic E3 Task search

Epic: [docs/epics/task-search.md](../epics/task-search.md) · Branch tip: `7df40cc` (both feature sub-PRs stacked) · Date: 2026-11-27

## By code

```
124 passed, 5 warnings in 36.09s
```

Warnings: unchanged from E2 (Alembic `path_separator` notice, FastAPI's deprecated
`HTTP_422_UNPROCESSABLE_ENTITY` name).

New tests in this epic: 16 (108 before the epic, 124 after)

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_task_search_repository.py` | 6 | title or description, any case, part of a word, NULL description, literal `%` / `_`, no match, combined with status |
| `tests/test_task_search_api.py` | 10 | search through the API, trimmed spaces, empty search shows all, literal `%`, combined with `overdue`, no match, 422 over 100 characters, 403, 401 |

## By hand on the running API

`uvicorn app.main:app --port 8013` on a fresh SQLite database, two real accounts (owner and
another user), one project with five tasks:

| Task | Title | Description | Status / due |
|------|-------|-------------|--------------|
| A | Fix login timeout | Users are logged out after 5 minutes | todo, due 2020-01-10 (overdue) |
| B | Write invoice export | CSV export for the LOGIN audit | done |
| C | Release notes | (none) | todo |
| D | Reach 100% coverage | unit_tests only | todo |
| E | Sửa lỗi đăng nhập | Lỗi khi đăng nhập bằng Google | todo |

| # | Scenario | Query | Expected | Actual | Result |
|---|----------|-------|----------|--------|--------|
| 1 | Word in a title or description, any case | `?q=LOGIN` | 200 A,B | 200 A,B | ✅ |
| 2 | Part of a word | `?q=voic` | 200 B | 200 B | ✅ |
| 3 | Spaces around the search | `?q=  release  ` | 200 C | 200 C | ✅ |
| 4 | Empty search shows everything | `?q=   ` | 200 A-E | 200 A-E | ✅ |
| 5 | `%` is literal | `?q=100%` | 200 D | 200 D | ✅ |
| 6 | `_` is literal | `?q=t_t` | 200 D | 200 D | ✅ |
| 7 | Vietnamese text, same case | `?q=đăng nhập` | 200 E | 200 E | ✅ |
| 8 | With the status filter | `?q=login&status=done` | 200 B | 200 B | ✅ |
| 9 | With the overdue filter | `?q=login&overdue=true` | 200 A | 200 A | ✅ |
| 10 | No match | `?q=zzz` | 200 (empty) | 200 (empty) | ✅ |
| 11 | Over 100 characters | `?q=<101 chars>` | 422 | 422 | ✅ |
| 12 | Another user's project | `?q=login` | 403 | 403 | ✅ |
| 13 | No token | `?q=login` | 401 | 401 | ✅ |

## Accepted with a reason

- **Vietnamese in a different case does not match on SQLite:** `?q=ĐĂNG NHẬP` returned nothing,
  because SQLite's `lower()` only folds ASCII. The query uses `lower(...) LIKE lower(...)`;
  PostgreSQL's `lower()` folds Vietnamese letters, so production is not affected. Recorded in the
  epic plan's decisions; worth one check on PostgreSQL before relying on it.
- The manual run used SQLite, not PostgreSQL (no local PostgreSQL on this machine).
