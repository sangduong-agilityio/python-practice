"""Unit tests package - tests for individual components in isolation.

Unit tests exercise components without HTTP layer or shared state:
- Service methods: Business logic with mocked repositories
- Repository methods: Data access with isolated in-memory DB
- Validation utilities: Field whitelisting and validation logic
- Exception handling: Custom exception behavior and hierarchy

Fixtures from tests/unit/conftest.py:
- unit_engine: Separate in-memory SQLite for test isolation
- unit_db_session: Isolated DB session with rollback per test
- test_user_data, test_project_data, test_task_data: Sample data
- updatable_fields: Field whitelists for validation testing

Test files:
- test_validation.py: Validation utility tests
- test_repositories.py: CRUD operations with field whitelisting
- test_services.py: Business logic with mocked dependencies
- test_exceptions.py: Exception types and error scenarios

Run unit tests:
    pytest tests/unit/
    pytest tests/unit/test_services.py -v
    pytest tests/unit/ --cov=app.services

Key principles:
- No HTTP layer (no client fixture)
- No shared state between tests
- Mocked external dependencies
- Fast execution (no I/O)
"""
