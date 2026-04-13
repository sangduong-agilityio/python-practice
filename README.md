
# Task Management API

**A production-ready REST API for managing projects, tasks, and teams**

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=flat&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Local Development (without Docker)](#local-development-without-docker)
- [Docker Setup](#docker-setup)
- [Running Migrations](#running-migrations)
- [Running the Celery Worker](#running-the-celery-worker)
- [Running Tests](#running-tests)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)

---

## Overview

Task Management API is a **FastAPI**-based REST API built to production engineering standards. It provides full user authentication, project and task management, tagging, background email notifications, Redis caching, and structured JSON logging — all containerised with Docker Compose.

This project was developed as a practice submission for the **FastAPI Training Plan** (Advanced Features phase), covering:

| Category | Implementation |
|---|---|
| Background Tasks | Celery + Redis — async email on register & task assignment |
| Middleware / CORS | Request logging middleware + environment-driven CORS |
| Caching | Redis cache for list endpoints with TTL and auto-invalidation |
| Logging | structlog JSON structured logging with per-request context |
| Containerisation | Multi-stage Dockerfile + Docker Compose (4 services) |
| Database | PostgreSQL 16 with async SQLAlchemy 2.x + Alembic migrations |

---

## Architecture

The codebase follows a strict **three-layer architecture**. Each layer has a single responsibility and calls only the layer below it.

```
┌─────────────────────────────────────────────────┐
│            Route Handlers  (app/api/)            │
│   Validate input · Call service · Return response│
└───────────────────────┬─────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────┐
│              Services  (app/services/)            │
│  Business logic · Ownership checks · HTTP errors │
│  Dispatch Celery tasks                           │
└───────────────────────┬─────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────┐
│           Repositories  (app/repositories/)      │
│  Pure async DB queries · Return ORM objects only │
└───────────────────────┬─────────────────────────┘
                        │
                  PostgreSQL 16
```

**Cross-cutting concerns** (authentication, caching, logging, config) live in `app/core/` and are injected via FastAPI's dependency system — route handlers never import repositories directly.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.13 |
| Framework | FastAPI 0.115 |
| ASGI Server | Uvicorn |
| Database | PostgreSQL 16 (asyncpg driver) |
| ORM | SQLAlchemy 2.x async |
| Migrations | Alembic |
| Authentication | OAuth2 Password Flow · JWT (python-jose) · argon2 (passlib) |
| Validation | Pydantic v2 |
| Configuration | pydantic-settings (reads `.env`) |
| Background Tasks | Celery 5 + Redis |
| Caching | Redis async (redis-py) |
| Logging | structlog (JSON output) |
| Testing | Pytest · httpx AsyncClient · SQLite in-memory |
| Linting | Ruff (rules: E, W, F, I, B, UP) |
| Containerisation | Docker multi-stage · Docker Compose |


---

## Project Structure

```
task-management-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py         # POST /auth/register · POST /auth/login
│   │       │   ├── users.py        # GET /users/me · PUT /users/me
│   │       │   ├── projects.py     # CRUD /projects (paginated, cached)
│   │       │   ├── tasks.py        # CRUD /tasks + PATCH /status + PATCH /assign
│   │       │   └── tags.py         # CRUD /tags + attach/detach to tasks
│   │       └── router.py           # Aggregates all routers under /api/v1
│   ├── core/
│   │   ├── config.py               # Pydantic-settings — reads all env vars
│   │   ├── security.py             # bcrypt hashing · JWT create/decode
│   │   ├── dependencies.py         # get_current_user · DB session injection
│   │   ├── cache.py                # Async Redis get/set/delete helpers
│   │   └── logging.py              # structlog JSON pipeline configuration
│   ├── db/
│   │   └── session.py              # Async engine · session factory · Base
│   ├── middleware/
│   │   └── logging.py              # Per-request timing and structured logging
│   ├── models/                     # SQLAlchemy ORM models (one per table)
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── task.py                 # Includes TaskStatus and TaskPriority enums
│   │   ├── tag.py                  # Includes task_tags pivot Table
│   │   └── refresh_token.py        # Opaque token hashing and rotation
│   ├── schemas/                    # Pydantic v2 request/response schemas
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── task.py
│   │   └── tag.py
│   ├── repositories/               # Pure async DB query layer
│   │   ├── user_repository.py
│   │   ├── project_repository.py
│   │   ├── task_repository.py
│   │   └── tag_repository.py
│   ├── services/                   # Business logic layer
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── task_service.py
│   │   └── tag_service.py
│   ├── worker/
│   │   ├── celery_app.py           # Celery factory — broker, result, config
│   │   └── tasks.py                # send_welcome_email · send_task_assigned_email
│   └── main.py                     # App factory · middleware · global error handler
├── alembic/
│   ├── versions/                   # Migration scripts (commit these)
│   └── env.py                      # Async-aware Alembic environment
├── tests/
│   ├── conftest.py                 # Fixtures — SQLite in-memory DB, test client
│   ├── test_auth.py                # Register · login · token validation
│   ├── test_projects.py            # Project CRUD + auth/ownership
│   └── test_tasks.py               # Task CRUD + status + assign
├── .env.example                    # Environment variable template
├── .gitignore
├── Dockerfile                      # Multi-stage build
├── docker-compose.yml              # 4-service orchestration
├── alembic.ini
├── pyproject.toml                  # Dependencies + Ruff config
└── README.md
```

---

## Prerequisites

Make sure the following are installed before getting started:

- [Python 3.13+](https://www.python.org/downloads/)
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)
- [PostgreSQL 16](https://www.postgresql.org/) *(only for local dev without Docker)*
- [Redis 7](https://redis.io/) *(only for local dev without Docker)*

---

## Quick Start

Get the API running in under 5 minutes using Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/your-username/task-management-api.git
cd python-practice

# 2. Create your environment file
cp .env.example .env

# 3. Generate a secure secret key and paste it into .env as SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 4. Start all services (migrations run automatically on startup)
docker compose up --build

# 5. Verify the API is healthy
curl http://localhost:8000/health
# → {"status": "ok"}

# 6. Open interactive API documentation
open http://localhost:8000/docs
```

---

## Local Development (without Docker)

```bash
# 1. Create and activate a virtual environment
python3.13 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install all dependencies including dev tools
pip install -e ".[dev]"

# 3. Copy and configure environment variables
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, REDIS_URL

# 4. Apply database migrations
alembic upgrade head

# 5. Start the API server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000**

Interactive docs:
- Swagger UI — http://localhost:8000/docs
- ReDoc — http://localhost:8000/redoc

---

## Docker Setup

```bash
# Start all 4 services in the background
docker compose up --build -d

# View logs from all services
docker compose logs -f

# View logs from a specific service
docker compose logs -f app
docker compose logs -f worker

# Stop all services
docker compose down

# Stop and remove all volumes (wipes the database)
docker compose down -v
```

**Services started by Docker Compose:**

| Service | Description | Port |
|---|---|---|
| `app` | FastAPI application (Uvicorn) | 8000 |
| `worker` | Celery background task worker | — |
| `db` | PostgreSQL 16 database | 5432 |
| `redis` | Redis 7 (cache + broker + results) | 6379 |

The `app` service automatically runs `alembic upgrade head` before starting Uvicorn. Both `app` and `worker` wait for `db` and `redis` to pass their health checks before starting.

---

## Running Migrations

```bash
# Apply all pending migrations to the database
alembic upgrade head

# Generate a new migration after modifying a model
alembic revision --autogenerate -m "add_due_date_to_tasks"

# Roll back the most recent migration
alembic downgrade -1

# Show full migration history
alembic history --verbose

# Show current revision applied to the database
alembic current
```

> **Note:** In Docker, migrations run automatically on container startup. For local dev, run `alembic upgrade head` manually after any model change.

---

## Running the Celery Worker

```bash
# Start the worker (local dev)
celery -A app.worker.celery_app.celery_app worker --loglevel=info

# Start with custom concurrency
celery -A app.worker.celery_app.celery_app worker --loglevel=info --concurrency=4

# Monitor tasks with Flower (install first: pip install flower)
celery -A app.worker.celery_app.celery_app flower --port=5555
# Open http://localhost:5555 to see task queue and worker status
```

In Docker, the `worker` service starts automatically with `docker compose up`.

---

## Running Tests

The test suite uses **SQLite in-memory** — no PostgreSQL or Redis instance required.

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_auth.py -v

# Run a specific test
pytest tests/test_tasks.py::TestAssignTask::test_assign_task_happy_path -v
```

**Test coverage:**

| Scenario | Status Code Tested |
|---|---|
| Happy path | `200` / `201` |
| Unauthenticated request | `401` |
| Resource not found | `404` |
| Forbidden — not the owner | `403` |
| Validation error | `422` |
| Duplicate resource (email/username) | `409` |

All Celery tasks and Redis cache operations are **mocked** — tests run fully offline.

---

## API Reference

All endpoints are prefixed with `/api/v1`. Protected endpoints require:

```
Authorization: Bearer <access_token>
```

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | No | Register a new user — triggers `send_welcome_email` Celery task |
| `POST` | `/auth/login` | No | Login with email + password, returns JWT app token + Opaque refresh token |
| `POST` | `/auth/refresh`| No | Exchange refresh token for new access/refresh pair + Token reuse detection |
| `POST` | `/auth/logout` | Yes| Revoke session: Blacklists JWT in Redis & Revokes Refresh Token in DB |

**Register request body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword"
}
```

**Login request body** *(form data)*:
```
username=user@example.com&password=securepassword
```

**Login response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Users

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users/me` | Yes | Get current authenticated user profile |
| `PUT` | `/users/me` | Yes | Update own profile (email and/or username) |

---

### Projects

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/projects` | Yes | Create a new project |
| `GET` | `/projects` | Yes | List own projects (paginated, **Redis cached**) |
| `GET` | `/projects/{id}` | Yes | Get project detail |
| `PUT` | `/projects/{id}` | Yes (owner) | Update project — returns `403` if not owner |
| `DELETE` | `/projects/{id}` | Yes (owner) | Delete project and all its tasks |

**Query parameters for `GET /projects`:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | `1` | Page number (1-based) |
| `page_size` | int | `20` | Items per page (max 100) |

---

### Tasks

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/projects/{id}/tasks` | Yes (owner) | Create task inside a project |
| `GET` | `/projects/{id}/tasks` | Yes | List tasks with optional filters |
| `GET` | `/tasks/{id}` | Yes | Get single task with attached tags |
| `PUT` | `/tasks/{id}` | Yes (owner) | Update task fields |
| `DELETE` | `/tasks/{id}` | Yes (owner) | Delete task |
| `PATCH` | `/tasks/{id}/status` | Yes (owner) | Update task status only |
| `PATCH` | `/tasks/{id}/assign` | Yes (owner) | Assign task — triggers `send_task_assigned_email` |

**Query parameters for `GET /projects/{id}/tasks`:**

| Parameter | Type | Values | Description |
|---|---|---|---|
| `status` | string | `todo`, `in_progress`, `done` | Filter by status |
| `priority` | string | `low`, `medium`, `high` | Filter by priority |
| `page` | int | — | Page number |
| `page_size` | int | — | Items per page |

**Task create/update body:**
```json
{
  "title": "Write unit tests",
  "description": "Cover all edge cases",
  "status": "todo",
  "priority": "high",
  "due_date": "2024-12-31T00:00:00Z",
  "assignee_id": 2
}
```

---

### Tags

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/tags` | Yes | Create a new tag |
| `GET` | `/tags` | Yes | List all tags (**Redis cached**) |
| `POST` | `/tasks/{id}/tags/{tag_id}` | Yes (owner) | Attach tag to task |
| `DELETE` | `/tasks/{id}/tags/{tag_id}` | Yes (owner) | Remove tag from task |

---

### Health Check

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | No | Liveness probe for load balancers |

---

### Error Responses

All error responses follow a consistent format:

```json
{
  "detail": "Descriptive error message"
}
```

| Status Code | Meaning |
|---|---|
| `400` | Bad request |
| `401` | Missing or invalid JWT token |
| `403` | Authenticated but not the resource owner |
| `404` | Resource not found |
| `409` | Conflict — email or username already taken |
| `422` | Validation error — invalid request body or parameters |
| `500` | Internal server error — detail is intentionally generic |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | — | Async PostgreSQL URL: `postgresql+asyncpg://user:pass@host:5432/db` |
| `SECRET_KEY` | **Yes** | — | Random secret for JWT signing — never commit this |
| `ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Opaque refresh token lifetime in days |
| `CORS_ORIGINS` | No | `[]` | JSON array of allowed origins: `["http://localhost:3000"]` |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis URL for the async cache client (DB 0) |
| `CELERY_BROKER_URL` | No | `redis://localhost:6379/1` | Redis URL for Celery broker (DB 1) |
| `CELERY_RESULT_BACKEND` | No | `redis://localhost:6379/2` | Redis URL for Celery result storage (DB 2) |
| `SMTP_HOST` | No | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `SMTP_USER` | No | `""` | SMTP authentication username |
| `SMTP_PASSWORD` | No | `""` | SMTP authentication password |
| `CACHE_TTL_SECONDS` | No | `60` | Default Redis cache TTL in seconds |
| `LOG_LEVEL` | No | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

> Three separate Redis databases (0, 1, 2) are used to prevent key collisions between the cache, the Celery broker, and the Celery result backend.



