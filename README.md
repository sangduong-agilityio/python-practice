# FastAPI Task Management API

A complete **Task Management REST API** built with FastAPI for learning backend development, authentication, database migrations, and testing.

This project demonstrates:

* RESTful API design with URL Versioning (`/api/v1/`)
* JWT authentication & refresh tokens
* Layered architecture (Controllers → Services → CRUD → Database)
* Request validation using Pydantic
* Async Database operations with SQLModel & SQLAlchemy
* Database migrations with Alembic
* Authorization with Bearer tokens
* Comprehensive testing with Pytest (100+ tests)
* Professional debugging with VSCode

---

## Overview

**Practice 1: Core API with Authentication** - A production-grade REST API demonstrating core FastAPI concepts:

* **User Management**: Registration, login, profile management
* **Task Management**: Full CRUD with filtering and search
* **Project Management**: Organization and task assignment
* **JWT Authentication**: Secure token-based authentication with refresh tokens
* **Authorization**: Users can only access their own resources
* **Request Validation**: Pydantic-based input validation
* **Test Suite**: 100+ pytest cases with comprehensive endpoint coverage

---

## Curriculum Progress: 100% Completed

## Practice 1: Core API with Authentication (Completed)

### PART 1: FASTAPI BASICS
- [x] **Setup & Routing**: Path Parameters, Query Parameters
- [x] **Request Body & Validation**: Pydantic models, Multiple Parameters
- [x] **Data Validation**: Nested Models, Cookie/Header Parameters, Extra Data Types
- [x] **Response Handling**: Response Model, Status Code, Form Data
- [x] **Documentation & Errors**: Handling Errors, OpenAPI docs (Swagger/ReDoc)

### PART 2: INTERMEDIATE FASTAPI
- [x] **Dependency Injection**: Dependencies, Classes as Dependencies
- [x] **Advanced Dependencies**: Sub-dependencies, Global Dependencies
- [x] **Security Intro**: OAuth2, Get Current User
- [x] **OAuth2 & JWT**: Password and Bearer, Hashing
- [x] **Advanced Security**: Role-based access control (Authorization)
- [x] **Async Programming**: Concurrency, `async def` vs `def`
- [x] **Configuration**: Settings and Environment Variables using Pydantic

### Practice 1 Project Features Implemented:
- [x] **User Management**: Register, login, get profile, update profile
- [x] **Task Management**: CRUD, filter by status, search by title
- [x] **Project Management**: Create project, assign tasks
- [x] **Testing**: Pytest & TestClient (Auth flow, Task CRUD, Auth rules, Error cases: 401/403/404)

---

## Practice 2: Database Integration (Completed)

### PART 3: DATABASE INTEGRATION
- [x] **SQLAlchemy Setup**: Async SQLModel & SQLAlchemy
- [x] **CRUD Operations**: Dedicated `crud/` layer for Create, Read, Update, Delete
- [x] **Database Sessions**: `AsyncSession` injected via Dependencies
- [x] **Migrations**: Alembic setup and migrations
- [x] **Relationships**: SQLModel relationships, Foreign keys (`user_id`, `project_id`)

---

## Quick Start

**Get running in 5 minutes:**

```bash
git clone https://gitlab.asoft-python.com/sang.duong/python-practice.git
cd python-practice
git checkout feature/practice-one-task-management-api

# If using standard venv:
python -m venv .venv
# Activate: .venv\Scripts\activate (Windows) or source .venv/bin/activate (Mac/Linux)
pip install -e ".[dev]"

# Or if using uv:
uv sync

# Setup environment variables
cp .env.example .env

# Run database migrations (optional, tests use in-memory DB)
alembic upgrade head

# Start server
uvicorn src.fastapi_training.main:app --reload
```

Then open: **http://127.0.0.1:8000/docs**

---

## Tech Stack

| Technology | Purpose              | Version    |
|-----------|----------------------|-----------|
| FastAPI   | Web framework        | >= 0.100.0 |
| Uvicorn   | ASGI server         | >= 0.24.0 |
| SQLModel / SQLAlchemy  | ORM & Database      | >= 0.0.14 |
| Alembic   | DB Migrations       | >= 1.13.0 |
| Pydantic  | Data validation     | >= 2.0.0 |
| PyJWT     | JWT authentication  | >= 3.3.0 |
| Passlib   | Password hashing    | >= 1.7.4 |
| Pytest    | Testing framework   | >= 7.4.0 |
| Ruff      | Linter & formatter  | >= 0.14.9 |
| Python    | Language            | >= 3.13 |

**Data Storage**: PostgreSQL (Async via `asyncpg`)
 
---

## Project Structure

```text
python-practice/
├── src/fastapi_training/
│   ├── main.py                  # Entrypoint
│   ├── core/                    # Config & Security 
│   ├── db/                      # DB Session & Engines
│   ├── models/                  # SQLModel Table Definitions
│   ├── schemas/                 # Pydantic Schemas (Input/Output validation)
│   ├── crud/                    # Data Access Layer (DB queries only)
│   ├── services/                # Business Logic Layer (No DB execution)
│   └── api/                     
│       ├── deps.py              # FastAPI dependencies (Auth, DB)
│       └── v1/                  # API Routers Version 1
│           ├── router.py
│           ├── auth.py, users.py, projects.py, tasks.py
├── tests/
│   ├── conftest.py              # Test Config & Fixtures
│   ├── unit/                    # Unit Tests
│   └── integration/             # Integration/API Tests
├── alembic/                     # Database Migrations folder
├── .env.example                 # Env variables template
└── pyproject.toml               # Package dependencies
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd python-practice
```

### 2. Configure Environment Variables

Copy the example env file:

```bash
cp .env.example .env
```

Ensure your `.env` has the necessary settings:

```env
APP_NAME="FastAPI Training"
DEBUG=False
SECRET_KEY="your-secret-key-must-be-at-least-32-characters-long"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/fastapi_training"
```

**Important:** `.env` is in `.gitignore` - never commit secrets!

---

## Run API

**Start development server:**

```bash
uvicorn src.fastapi_training.main:app --reload
# Or with uv:
uv run uvicorn src.fastapi_training.main:app --reload
```

**Access the API:**
- Interactive Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints (v1)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|---------|
| `POST` | `/api/v1/auth/register` | Register new user | No |
| `POST` | `/api/v1/auth/login` | Login, get tokens | No |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | No |
| `GET` | `/api/v1/users/me` | Get current user | Yes |
| `PUT` | `/api/v1/users/{id}` | Update user info | Yes |
| `POST` | `/api/v1/tasks/` | Create task | Yes |
| `GET` | `/api/v1/tasks/` | List all tasks | Yes |
| `GET` | `/api/v1/tasks/{id}` | Get task by ID | Yes |
| `PUT` | `/api/v1/tasks/{id}` | Update task | Yes |
| `DELETE` | `/api/v1/tasks/{id}` | Delete task | Yes |
| `GET` | `/api/v1/tasks/filter/status` | Filter tasks by status | Yes |
| `GET` | `/api/v1/tasks/search/title` | Search tasks by title | Yes |
| `POST` | `/api/v1/projects/` | Create project | Yes |
| `GET` | `/api/v1/projects/` | List projects | Yes |
| `POST` | `/api/v1/projects/{pid}/tasks/{tid}` | Assign task to project | Yes |

---

## Run Tests

**Run all tests (Integration & Unit):**

```bash
pytest tests/ -v
# Or with uv:
uv run pytest tests/ -v
```

**With output (see prints):**

```bash
pytest tests/ -v -s
```

**Specific test file:**

```bash
pytest tests/integration/api/v1/test_auth.py -v
```

**Specific test:**

```bash
pytest tests/integration/api/v1/test_auth.py::TestLoginRoute::test_login_success -v
```

**Stop on first failure:**

```bash
pytest tests/ -v -x
```

---

## Architecture Design

The application follows a strictly **Layered Architecture** (Controller-Service-Repository pattern):

```
HTTP Request → Router (API) → Service → CRUD (Repository) → Database
```

Example Auth Flow (`POST /api/v1/auth/login`)

1. **`api/v1/auth.py` (Router)**: Receives HTTP request, extracts username/password.
2. **`services/user_service.py` (Service)**: Checks if user exists. Validates if password matches hash.
3. **`crud/user.py` (CRUD)**: Executes `select(User).where(User.email == email)` to fetch user from DB.
4. If successful, router creates JWT and returns `200 OK`.

---

## Linting & Formatting

**Check code style:**

```bash
ruff check .
```

**Fix issues automatically:**

```bash
ruff check --fix .
```

**Format code:**

```bash
ruff format .
```

---

## Important Notes

### Debug Tests in VSCode

1. Open a test file (e.g., `tests/integration/api/v1/test_auth.py`)
2. Click the left margin to set a breakpoint (red dot)
3. Go to the "Run and Debug" panel in VSCode
4. Select `Debug: "Current Test File"` or other configurations
5. Press `F5` to debug
