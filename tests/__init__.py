"""Main test suite for FastAPI task management application.

This package contains INTEGRATION and UNIT tests for comprehensive coverage.

DIRECTORY STRUCTURE
====================

tests/
├── conftest.py              # Shared fixtures for INTEGRATION tests
├── integration/             # HTTP endpoint integration tests
│   ├── __init__.py
│   ├── test_auth.py        # Auth endpoints (register, login, get_me)
│   ├── test_projects.py    # Project CRUD with ownership isolation
│   └── test_tasks.py       # Task CRUD with lifecycle management
├── unit/                    # Component unit tests
│   ├── __init__.py
│   ├── conftest.py         # Separate fixtures for UNIT tests
│   ├── test_validation.py  # Field validation utility tests
│   ├── test_repositories.py # CRUD layer tests with real DB
│   ├── test_services.py    # Business logic tests with mocks
│   └── test_exceptions.py  # Exception behavior tests
└── TEST_ORGANIZATION.md    # Detailed test documentation


INTEGRATION TESTS (tests/integration/)
========================================

Purpose: Test full HTTP stack end-to-end

Setup:
- Uses conftest.py (root level) for fixtures
- Creates AsyncClient with dependency override to test database
- In-memory SQLite database from root conftest

Coverage:
- 31+ endpoint tests
- Auth: register, login, get_me with token validation
- Projects: CRUD with ownership isolation (Alice only sees Alice's)
- Tasks: CRUD, filtering, status changes

Run: pytest tests/integration/ -v


UNIT TESTS (tests/unit/)
==========================

Purpose: Test components in isolation without HTTP/DB dependencies

Setup:
- Uses conftest.py (unit level) for separate fixtures
- Separate in-memory SQLite engine (no conflicts)
- Service layer tests use mocked repositories
- Repository tests use real in-memory DB

Coverage:
- 65+ component tests
- Validation: Field whitelisting for all resources
- Repositories: CRUD operations and field restrictions
- Services: Business logic with mock dependencies
- Exceptions: Custom exception types and error handling

Run: pytest tests/unit/ -v


SHARED FIXTURES (tests/conftest.py)
====================================

For INTEGRATION tests only:

- event_loop: Session-scoped async loop
- engine: SQLite in-memory database (session-scoped)
- db_session: Per-test database session with rollback
- client: Async HTTP client with test DB dependency override

Helpers:
- TEST_USER: {"email": "alice@example.com", ...}
- SECOND_USER: {"email": "bob@example.com", ...}
- create_user(client, payload): Register user via HTTP
- get_token(client, payload): Get JWT access token
- auth_headers(client, payload): Get Authorization header


KEY DIFFERENCES
================

Integration Tests:
✓ Full HTTP stack
✓ Real endpoints tested
✓ Database integration
✓ Slower but comprehensive
✓ Test workflow end-to-end

Unit Tests:
✓ Single component
✓ Logic isolated
✓ Mocked dependencies
✓ Faster execution
✓ Edge cases and details


RUNNING TESTS
===============

All tests:
    pytest

Integration only:
    pytest tests/integration/

Unit only:
    pytest tests/unit/

Specific test:
    pytest tests/integration/test_auth.py

Verbose output:
    pytest -v

With coverage:
    pytest --cov=app --cov-report=html


SECURITY TESTING
==================

Tests validate:
- Ownership Isolation: Users can't access other's resources
- Permission Enforcement: 403 for non-owners
- Authentication Required: 401 for missing/invalid token
- Field Whitelisting: Protected fields can't be updated
- Input Validation: Invalid data rejected with 422

Integration tests verify end-to-end security via HTTP.
Unit tests verify individual security components.


STRUCTURE SUMMARY
====================

Root tests/conftest.py:
└─ Shared fixtures for integration tests
   ├─ Database fixtures (engine, db_session)
   ├─ HTTP client (client)
   └─ Test data helpers

tests/integration/:
└─ Full HTTP stack tests
   └─ Uses root conftest.py fixtures

tests/unit/:
└─ Component isolation tests
   └─ Uses tests/unit/conftest.py (separate DB)
"""
