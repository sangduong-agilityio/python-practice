# FastAPI Task Management API

A complete **Task Management REST API** built with FastAPI for learning backend development, authentication, and testing.

This project demonstrates:

* RESTful API design
* JWT authentication & refresh tokens
* Layered architecture (Routes → Services → Database)
* Request validation using Pydantic
* Authorization with Bearer tokens
* Comprehensive testing with Pytest (58+ tests, 91% coverage)
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
* **Test Suite**: 58 pytest cases with 91% endpoint coverage

---

## Quick Start

**Get running in 5 minutes:**

```bash
git clone https://gitlab.asoft-python.com/sang.duong/python-practice.git
cd python-practice
git checkout feature/practice-one-task-management-api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn src.fastapi_training.app.main:app --reload
```

Then open: **http://127.0.0.1:8000/docs**

---

## Tech Stack

| Technology | Purpose              | Version    |
|-----------|----------------------|-----------|
| FastAPI   | Web framework        | >= 0.100.0 |
| Uvicorn   | ASGI server         | >= 0.24.0 |
| Pydantic  | Data validation     | >= 2.0.0 |
| PyJWT     | JWT authentication  | >= 3.3.0 |
| Passlib   | Password hashing    | >= 1.7.4 |
| Pytest    | Testing framework   | >= 7.4.0 |
| Ruff      | Linter & formatter  | >= 0.14.9 |
| Python    | Language            | >= 3.13 |

**Data Storage**: In-memory dictionaries (mock database)

---

## Project Structure

```
python-practice
│
├── src
│   └── fastapi_training
│       └── app
│           ├── core
│           │   ├── config.py
│           │   └── security.py
│           │
│           ├── db
│           │   └── fake_db.py
│           │
│           ├── dependencies
│           │   └── auth.py
│           │
│           ├── models
│           │   └── user.py
│           │
│           ├── routes
│           │   ├── auth.py
│           │   ├── user.py
│           │   ├── task.py
│           │   └── project.py
│           │
│           ├── schemas
│           │   ├── user.py
│           │   ├── task.py
│           │   └── project.py
│           │
│           ├── services
│           │   ├── user_service.py
│           │   ├── task_service.py
│           │   └── project_service.py
│           │
│           └── main.py
│
├── tests
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_tasks.py
│   └── test_projects.py
│
├── .vscode
│   └── launch.json
│
├── .env
├── pyproject.toml
├── pytest.ini
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd python-practice
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

Activate the environment:

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Configure Environment Variables

Create `.env` file:

```env
# Application Settings
APP_NAME=FastAPI Task Management API
DEBUG=True

# Security Settings (Change in production!)
SECRET_KEY=your-secret-key-min-32-chars-change-in-production!

# JWT Settings
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

**Important:** `.env` is in `.gitignore` - never commit secrets!

### 4. Install dependencies

```bash
pip install -e ".[dev]"
```

This installs all packages from `pyproject.toml`:
- **Core**: FastAPI, Uvicorn, Pydantic, PyJWT, Passlib
- **Dev**: pytest, pytest-cov, ruff

---

## Run API

**Start development server:**

```bash
uvicorn src.fastapi_training.app.main:app --reload
```

**Access the API:**
- Interactive Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|---------|
| `POST` | `/auth/register` | Register new user | No |
| `POST` | `/auth/login` | Login, get tokens | No |
| `POST` | `/auth/refresh` | Refresh access token | No |
| `GET` | `/users/me` | Get current user | Yes |
| `POST` | `/tasks/` | Create task | Yes |
| `GET` | `/tasks/` | List all tasks | Yes |
| `GET` | `/tasks/{id}` | Get task by ID | Yes |
| `PUT` | `/tasks/{id}` | Update task | Yes |
| `DELETE` | `/tasks/{id}` | Delete task | Yes |
| `GET` | `/tasks/filter/status` | Filter tasks by status | Yes |
| `GET` | `/tasks/search/title` | Search tasks by title | Yes |
| `POST` | `/projects/` | Create project | Yes |
| `GET` | `/projects/` | List projects | Yes |

---

## Run Tests

**Run all tests:**

```bash
pytest -v
```

**With output (see prints):**

```bash
pytest -v -s
```

**Specific test file:**

```bash
pytest tests/test_auth.py -v
```

**Specific test:**

```bash
pytest tests/test_auth.py::TestAuthLogin::test_login_success -v
```

**Stop on first failure:**

```bash
pytest -v -x
```

---

## Test Coverage

**Generate full coverage report (HTML + terminal):**

```bash
pytest --cov=src/fastapi_training/app --cov-report=html --cov-report=term-missing -v
```

**View HTML report:**

```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

**Quick summary:**

```bash
pytest --cov=src/fastapi_training/app --cov-report=term
```

---

## Example API Flow

### 1. Register User

```bash
POST /auth/register
```

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com"
}
```

### 2. Login

```bash
POST /auth/login
```

Request (form data):
```
username: user@example.com
password: securepassword123
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 3. Access Protected Route

```bash
GET /users/me
```

Header:
```
Authorization: Bearer <access_token>
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com"
}
```

---

## Development Notes

### Architecture

The application follows a **layered architecture**:

```
Route → Service → Database
```

Example auth flow:

```
POST /auth/login
    ↓
routes/auth.py (receive request)
    ↓
services/user_service.py (authenticate_user)
    ↓
fake_db.py (lookup user)
    ↓
core/security.py (verify password, create tokens)
```

### Token Management

- **Access Token**: 15 minutes (fast API access)
- **Refresh Token**: 7 days (long-term session)
- Use `/auth/refresh` to get new access token

### Authorization

Protected routes use dependency injection:

```python
from fastapi import Depends
from dependencies.auth import get_current_user

@app.get("/users/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    return current_user
```

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

### .gitignore Configuration

Already configured to **NOT commit**:
- `.venv/` - Virtual environment
- `.env` - Environment variables with secrets
- `__pycache__/`, `.pytest_cache/` - Cache files
- `.coverage` - Coverage data

**WHY?** These break builds and expose secrets!

### Security Best Practices

- **Never commit `.env`** - Contains SECRET_KEY
- **Change SECRET_KEY in production** - Use secure random 32+ chars
- **Each developer uses local `.env`** - Don't share across team
- **Store real secrets in CI/CD** - Use env vars in production

### Debug Tests in VSCode

1. Open test file (e.g., `tests/test_auth.py`)
2. Click margin to set breakpoint (red dot)
3. Press `F5` to debug
4. Use available configs in Debug panel

---











