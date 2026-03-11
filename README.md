# FastAPI Task Management API

A complete Task Management REST API built with FastAPI, featuring JWT authentication, role-based authorization, and comprehensive test coverage. This project demonstrates core FastAPI concepts including dependency injection, security, validation, and async programming.

## Overview

This is **Practice 1: Core API with Authentication** from the FastAPI learning curriculum. The project implements a production-grade REST API with:

- **User Management System**: Registration, login, profile management
- **Task Management**: Full CRUD operations with filtering and search
- **Project/Category Management**: Organization and task assignment
- **JWT Authentication**: Secure token-based authentication
- **Authorization Controls**: Users can only access their own data
- **Comprehensive Validation**: Pydantic-based input validation
- **Complete Test Suite**: 58 pytest test cases with 100% endpoint coverage

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | FastAPI | >= 0.100.0 |
| **Server** | Uvicorn | >= 0.24.0 |
| **Validation** | Pydantic | >= 2.0.0 |
| **Auth** | PyJWT + Passlib | >= 3.3.0, >= 1.7.4 |
| **Testing** | pytest + FastAPI TestClient | >= 7.4.0 |
| **Python** | Python | >= 3.13 |
| **Email Validation** | email-validator | >= 2.0.0 |
| **ORM Ready** | SQLAlchemy | >= 2.0.0 *(for future DB integration)* |

**Current Data Storage**: In-memory dictionaries (mock database)

## Project Structure

```
python-practice/
├── src/
│   └── fastapi_training/
│       └── app/
│           ├── main.py                 # Application entry point
│           ├── core/
│           │   ├── config.py           # Settings management
│           │   └── security.py         # JWT & password hashing
│           ├── db/
│           │   └── fake_db.py          # In-memory data storage
│           ├── models/
│           │   └── user.py             # User data models
│           ├── schemas/
│           │   ├── user.py             # User request/response schemas
│           │   ├── task.py             # Task schemas
│           │   └── project.py          # Project schemas
│           ├── services/
│           │   ├── auth_service.py     # Authentication logic
│           │   ├── user_service.py     # User business logic
│           │   ├── task_service.py     # Task business logic
│           │   └── project_service.py  # Project business logic
│           ├── routes/
│           │   ├── auth.py             # /auth endpoints
│           │   ├── user.py             # /users endpoints
│           │   ├── task.py             # /tasks endpoints
│           │   └── project.py          # /projects endpoints
│           └── dependencies/
│               └── auth.py             # Dependency injection helpers
├── tests/
│   ├── test_auth.py                    # Authentication tests
│   ├── test_users.py                   # User endpoint tests
│   ├── test_tasks.py                   # Task endpoint tests
│   ├── test_projects.py                # Project endpoint tests
│   └── conftest.py                     # Test fixtures & setup
├── .env                                 # Environment configuration
├── pyproject.toml                       # Project dependencies
└── README.md                            # This file
```

## Installation

### Prerequisites

- Python 3.13+
- pip
- Git

### Clone the repository:

```bash
git clone git@gitlab.asoft-python.com:sang.duong/python-practice.git
```

### Checkout branch:

```bash
git checkout <feature/practice-one-task-management-api>
```

### Pull origin branch:

```bash
git pull origin <feature/practice-one-task-management-api>
```

### Create Virtual Environment

```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### Install dependencies:

```bash
pip install -e .
```

Or with dev dependencies for testing:
```bash
pip install -e ".[dev]"
```

This installs all packages defined in `pyproject.toml`:
- Core: FastAPI, Uvicorn, Pydantic, PyJWT, Passlib
- Dev: pytest, pytest-asyncio, httpx, pytest-cov



## API Documentation

### Interactive API Documentation

Once the server is running, access:

- **Swagger UI (Interactive)**: http://127.0.0.1:8000/docs
- **ReDoc (Alternative)**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

### Authentication Flow

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

**Steps:**
1. Register: `POST /auth/register` → Get user ID
2. Login: `POST /auth/token` → Get JWT token
3. Use token in Protected Endpoints


## Testing

### Run All Tests

```bash
# Navigate to project root
cd python-practice

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src/fastapi_training/app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test function
pytest tests/test_auth.py::test_register_user -v
```


### Test Structure

```python
# tests/conftest.py - Shared fixtures
- TestClient setup
- Database isolation
- Test user fixtures
- Authentication token fixtures

# tests/test_auth.py - Authentication tests
- User registration
- User login
- Token validation

# tests/test_users.py - User endpoint tests
- Get profile
- Update profile

# tests/test_tasks.py - Task endpoint tests
- Create/Read/Update/Delete
- Filter by status
- Search by title
- Authorization checks

# tests/test_projects.py - Project tests
- Project CRUD
- Task assignment
```

**Loading Configuration:**
- Framework: Pydantic Settings
- Location: `src/fastapi_training/app/core/config.py`
- All required settings must be in `.env` (application fails to start if missing)
- Optional settings have safe defaults

## Run Project

### Run development server:

```bash
cd src
python -m uvicorn fastapi_training.app.main:app --reload
```

**Output:**
```
INFO:     Will watch for changes in these directories: ['D:\\python\\python-practice\\src']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete
```

Then open http://127.0.0.1:8000/docs

### Run tests:

```bash
# From project root
cd python-practice

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src/fastapi_training/app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Run production server:

```bash
cd src
python -m uvicorn fastapi_training.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Layered Pattern

```
Requests
   ↓
[Routes Layer] - HTTP handling, dependency injection
   ↓
[Services Layer] - Business logic, validation
   ↓
[Database Layer] - Data access, storage
   ↓
Response
```










