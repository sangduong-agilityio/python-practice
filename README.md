# Task Management API

A **production-ready REST API** built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy 2.x async**.



---

## Architecture

```
HTTP Request
    ↓
Route Handler  (validate input, call service, return response)
    ↓
Service        (business logic, ownership checks, raise HTTPException)
    ↓
Repository     (raw SQL queries, return ORM objects)
    ↓
PostgreSQL
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.13 |
| Framework | FastAPI |
| ASGI Server | Uvicorn |
| Database | PostgreSQL (asyncpg) |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Auth | OAuth2 + JWT (python-jose) |
| Password Hashing | bcrypt (passlib) |
| Validation | Pydantic v2 |
| Testing | pytest + httpx |
| Linting | Ruff |
| Container | Docker + Docker Compose |
| Deployment | Render.com |

---

## 🚀 Quick Start (under 5 minutes)

### Option A — Docker Compose (recommended, no setup needed)

```bash
# 1. Clone the repo
git clone https://github.com/yourname/task-management-api.git
cd task-management-api

# 2. Copy environment file
cp .env.example .env

# 3. Start the database + API (builds Docker image automatically)
docker compose up --build

# API is now running at http://localhost:8000
# Swagger UI at     http://localhost:8000/docs
```

### Option B — Local Development (Python + PostgreSQL)

```bash
# 1. Clone and enter the directory
git clone https://github.com/yourname/task-management-api.git
cd task-management-api

# 2. Create a virtual environment
python3.13 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install all dependencies (including dev tools)
pip install -e ".[dev]"

# 4. Set up environment variables
cp .env.example .env
# Edit .env and set DATABASE_URL to your PostgreSQL connection string

# 5. Run database migrations (creates all tables)
alembic upgrade head

# 6. Start the development server
uvicorn app.main:app --reload --port 8000

# API is now running at http://localhost:8000
# Swagger UI at     http://localhost:8000/docs
```

---

## 🗃️ Database Migrations

```bash
# Create a new migration after changing a model
alembic revision --autogenerate -m "describe what you changed"

# Apply all pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1

# View migration history
alembic history
```

---

## 🧪 Running Tests

Tests use **SQLite in-memory** — no PostgreSQL needed for testing.

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_auth.py -v

# Run with code coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html    # View HTML coverage report
```

---

## 🔍 Linting

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

---

## 📡 API Reference

All endpoints are prefixed with `/api/v1`. Interactive docs at `/docs`.

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | None | Register a new account |
| POST | `/auth/login` | None | Get a JWT access token |

### Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/me` | ✅ Bearer | Get your profile |
| PUT | `/users/me` | ✅ Bearer | Update your profile |

### Projects

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/projects` | ✅ Bearer | Create a project |
| GET | `/projects?skip=0&limit=20` | ✅ Bearer | List your projects |
| GET | `/projects/{id}` | ✅ Bearer | Get a project |
| PUT | `/projects/{id}` | ✅ Owner | Update project |
| DELETE | `/projects/{id}` | ✅ Owner | Delete project |

### Tasks

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/projects/{id}/tasks` | ✅ Owner | Create a task |
| GET | `/projects/{id}/tasks?status=todo&priority=high` | ✅ Owner | List tasks (filterable) |
| GET | `/tasks/{id}` | ✅ Bearer | Get a task |
| PUT | `/tasks/{id}` | ✅ Owner | Update task |
| DELETE | `/tasks/{id}` | ✅ Owner | Delete task |
| PATCH | `/tasks/{id}/status` | ✅ Owner | Change status only |
| PATCH | `/tasks/{id}/assign` | ✅ Owner | Assign/unassign user |

### Tags

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/tags` | ✅ Bearer | Create a tag |
| GET | `/tags` | ✅ Bearer | List all tags |
| POST | `/tasks/{id}/tags/{tag_id}` | ✅ Owner | Attach tag to task |
| DELETE | `/tasks/{id}/tags/{tag_id}` | ✅ Owner | Remove tag from task |

---

## 🌐 Deploying to Render.com

1. Push your code to a GitHub repository.
2. Go to [render.com](https://render.com) → **New** → **Blueprint**.
3. Connect your GitHub repo — Render reads `render.yaml` automatically.
4. Set secret environment variables in the Render dashboard:
   - `SECRET_KEY` — a long random string
   - `SMTP_PASSWORD` — your email app password
5. Click **Deploy** — Render builds the Docker image, creates the database, and runs migrations automatically.

---

## 📁 Project Structure

```
task-management-api/
├── app/
│   ├── api/v1/endpoints/   # Route handlers (auth, users, projects, tasks, tags)
│   ├── core/               # Config, security (JWT/bcrypt), dependencies
│   ├── db/                 # SQLAlchemy engine + session factory
│   ├── models/             # ORM models (User, Project, Task, Tag)
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic layer
│   ├── repositories/       # Database query layer
│   ├── middleware/          # Logging middleware
│   └── main.py             # App factory + startup
├── alembic/                # Database migrations
├── tests/                  # pytest test suite
├── Dockerfile
├── docker-compose.yml
├── render.yaml
└── pyproject.toml
```

---

## 🤖 MCP Server (manage tasks from Claude)

`mcp_server/task_api_server.py` exposes this API to Claude Code (or any MCP client):

| Kind | Name | What it does |
| :--- | :--- | :--- |
| Tool | `list_projects` | Projects of the logged-in user |
| Tool | `list_tasks` | Tasks of a project, optional `status` filter |
| Tool | `create_task` | Create a task (`priority`: low / medium / high) |
| Tool | `update_task_status` | Move a task to todo / in_progress / done |
| Resource | `tasks://projects/{project_id}/tasks` | All tasks of a project as JSON |
| Prompt | `standup` | Daily stand-up summary for a project |

It calls the running API over HTTP, so all validation and ownership rules still apply.

1. Install the dev extras (includes `mcp`): `pip install -e ".[dev]"`
2. Start the API: `uvicorn app.main:app --reload`
3. Set the account the server acts as (PowerShell, then open a new terminal):
   ```powershell
   setx TASK_API_EMAIL "you@example.com"
   setx TASK_API_PASSWORD "your-password"
   ```
4. Start Claude Code in this folder. `.mcp.json` registers the server as `task-api`; approve it once, then check with `/mcp`.

Try: *"List my projects"*, *"Create a high priority task 'Fix login timeout' in project 1"*, or the `standup` prompt from the `/` menu.

Tests: `pytest tests/test_mcp_server.py` runs the tools, resource and prompt against the in-process API.

---

## 🔒 Security Notes

- Passwords are hashed with **bcrypt** (never stored in plain text).
- JWTs expire after 30 minutes by default (configurable via `.env`).
- Ownership is checked before any mutating operation (create/update/delete).
- Stack traces are never exposed in API responses.
- CORS origins are restricted via `.env` configuration.
- The Docker container runs as a **non-root user**.

---

## 📝 License

MIT — free to use for learning and production projects.
