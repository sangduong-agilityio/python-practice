"""Integration tests package.

Integration tests exercise the full HTTP stack end-to-end using:
- Real FastAPI application instance
- Test database (in-memory SQLite from root tests/conftest.py)
- Async HTTP client (AsyncClient via httpx)

Test files:
- test_auth.py: Authentication endpoints (register, login, get_me)
- test_projects.py: Project CRUD endpoints with ownership isolation
- test_tasks.py: Task CRUD endpoints with lifecycle management

Fixtures from root conftest.py:
- client: Async HTTP client with dependency override to test DB
- db_session: SQLite session with rollback after each test
- auth_headers(): Helper to get Bearer token from credentials
- create_user(): Helper to register user via HTTP

Run integration tests:
    pytest tests/integration/
    pytest tests/integration/test_auth.py -v
"""
