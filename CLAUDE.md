# CLAUDE.md — Task Management API Guidelines

## Commands
- **Run dev server:** `uvicorn app.main:app --reload`
- **Run all tests:** `pytest`
- **Run specific test:** `pytest tests/test_tasks.py -v`
- **Apply migrations:** `alembic upgrade head`
- **Create migration:** `alembic revision --autogenerate -m "description"`

## Architecture & Conventions
- **Stack:** FastAPI + SQLAlchemy 2.0 (Async) + Pydantic v2.
- **Dependencies:** Inject `DbSession` and `CurrentUser` from `app.core.dependencies`.
- **Async Safety:** ALWAYS eager-load relationships (e.g. `selectinload(Task.tags)`) in repository queries to prevent `MissingGreenlet` exceptions.
- **Data Validation:** Normalize enum inputs (status, priority) case-insensitively using `.strip().lower()` or `@field_validator(..., mode="before")`. Invalid values must raise HTTP 422.
- **Security:** Do not remove the 72-byte bcrypt truncation patch in `app/core/security.py`.
- **Language:** All commit messages, PR titles/descriptions, code comments, and docstrings must be in English.
- **Commits:** Before committing, check `git diff --stat`; never commit files whose only change is line endings (CRLF).
- **Auth login:** Takes OAuth2 form data (`username=<email>`), not JSON. Tests must send `data=`, not `json=`.

## "Never Do" List
- NEVER access lazy-loaded async ORM relationships without `selectinload`.
- NEVER use synchronous DB calls or forget `await` on async queries.
- NEVER bypass Pydantic schemas on API request/response boundaries.
- NEVER alter database schema definitions without an accompanying Alembic migration.
- NEVER declare a task complete without executing `pytest` to confirm tests are green.
