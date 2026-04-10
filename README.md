# Task Management API

A REST API for managing projects and tasks, built with FastAPI and PostgreSQL.

## Stack

- Python 3.13
- FastAPI + Uvicorn
- PostgreSQL + asyncpg
- SQLAlchemy 2 (async)
- Alembic
- JWT via python-jose
- Pydantic v2
- Pytest + httpx

## Project structure

```
app/
  api/v1/endpoints/   route handlers (no logic)
  core/               config, security, dependencies
  db/                 engine and session factory
  middleware/         logging
  models/             SQLAlchemy ORM models
  repositories/       raw database queries
  schemas/            Pydantic request/response models
  services/           business logic
  main.py             app factory
alembic/              migration scripts
tests/                pytest test suite
```

## Local setup

**1. Install uv**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Clone and create the virtual environment**

```bash
git clone <repo-url>
cd task-management-api
uv venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

**3. Configure environment**

```bash
cp .env.example .env
# Open .env and set DATABASE_URL and SECRET_KEY at minimum.
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**4. Create the database**

```bash
createdb taskdb   # or use psql to create it manually
```

**5. Run migrations**

```bash
alembic upgrade head
```

**6. Start the server**

```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Running tests

Tests use an in-memory SQLite database. No PostgreSQL needed.

```bash
pytest -v
```

## API reference

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | Register a new account |
| POST | /api/v1/auth/login | Login, returns JWT |

### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/users/me | Get current user |
| PUT | /api/v1/users/me | Update current user |

### Projects

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/projects | Create project |
| GET | /api/v1/projects | List own projects |
| GET | /api/v1/projects/{id} | Get project |
| PUT | /api/v1/projects/{id} | Update project |
| DELETE | /api/v1/projects/{id} | Delete project |

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/projects/{id}/tasks | Create task |
| GET | /api/v1/projects/{id}/tasks | List tasks (filter by ?status= and ?priority=) |
| GET | /api/v1/tasks/{id} | Get task |
| PUT | /api/v1/tasks/{id} | Update task |
| DELETE | /api/v1/tasks/{id} | Delete task |
| PATCH | /api/v1/tasks/{id}/status | Change status |
| PATCH | /api/v1/tasks/{id}/assign | Assign or unassign |
| POST | /api/v1/tasks/{id}/tags/{tag_id} | Attach tag |
| DELETE | /api/v1/tasks/{id}/tags/{tag_id} | Detach tag |

### Tags

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/tags | Create tag |
| GET | /api/v1/tags | List all tags |

## Authentication

All endpoints except `/auth/register` and `/auth/login` require a Bearer token.

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=you@example.com&password=yourpassword"

# Use the token
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <token>"
```

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | yes | - | asyncpg connection string |
| SECRET_KEY | yes | - | JWT signing key |
| ALGORITHM | no | HS256 | JWT algorithm |
| ACCESS_TOKEN_EXPIRE_MINUTES | no | 30 | Token TTL |
| CORS_ORIGINS | no | [] | Allowed origins as JSON array |
| SMTP_HOST | no | smtp.gmail.com | Email host |
| SMTP_PORT | no | 587 | Email port |
| SMTP_USER | no | (blank) | Email user -- leave blank to disable email |
| SMTP_PASSWORD | no | (blank) | Email password |
