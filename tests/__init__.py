"""
Unit tests for FastAPI Training Application

Test Structure:
- conftest.py: Shared fixtures and configuration
- test_auth.py: Authentication tests (Issue 18)
- test_tasks.py: Task CRUD & Authorization tests (Issue 19)

Running Tests:
    pytest                              # Run all tests
    pytest tests/test_auth.py           # Run auth tests only
    pytest tests/test_tasks.py          # Run task tests only
    pytest -v                           # Verbose output
    pytest --cov                        # With coverage report
    pytest -k "test_login"              # Run specific test
"""

