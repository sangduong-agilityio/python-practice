---
name: add-resource
description: Use when adding a new feature, endpoint, entity or field to task-management-api (e.g. "add task comments", "add a due_date filter", "new endpoint to archive a project"). Walks through every layer in the repo's order - model, migration, schema, repository, service, endpoint, router, tests - so no layer or convention is missed.
---

# Add Resource

The API is layered. A change flows through the layers in this order; skip a layer only when the change really does not touch it, and say which ones you skipped.

```
model -> migration -> schema -> repository -> service -> endpoint -> router -> tests
```

Use the `tags` stack as the reference implementation:
`app/models/tag.py`, `app/schemas/tag.py`, `app/repositories/tag_repository.py`, `app/services/tag_service.py`, `app/api/v1/endpoints/tags.py`.

## 0. Plan first
Before writing code, list for the user: the endpoints (method + path + status codes), the fields and their validation, who may access it (owner only? any logged-in user?), and the files you will touch. Wait for a go-ahead on anything ambiguous.

Branch: `feature/<short-kebab-summary>` from an up-to-date `main`.

## 1. Model (`app/models/<name>.py`)
- SQLAlchemy 2.0 typed style: `Mapped[...]` + `mapped_column(...)`, a module docstring and a class docstring listing the columns.
- Index foreign keys and columns you filter on; set `ondelete="CASCADE"` where child rows must go with the parent.
- Relationships use `back_populates` on both sides.
- Export the model in `app/models/__init__.py` (Alembic imports models from there).

## 2. Migration
Follow the `how-we-write-migrations` skill: autogenerate, read the generated file, zero-downtime rules, upgrade/downgrade/upgrade loop. Never change a model without a migration.

## 3. Schema (`app/schemas/<name>.py`)
- `<Name>Base` (shared fields with `Field(...)` limits), `<Name>Create`, `<Name>Update` (all fields optional) and `<Name>Out` with `model_config = {"from_attributes": True}`.
- Enum-like inputs: normalize with `@field_validator(..., mode="before")` and `.strip().lower()`; an invalid value must still give 422.
- Never return ORM objects past the endpoint without an `Out` schema.

## 4. Repository (`app/repositories/<name>_repository.py`)
- Only SQL lives here; no `HTTPException`, no business rules.
- Every relationship the response needs is eager-loaded with `selectinload(...)` (otherwise `MissingGreenlet`).
- Every query is awaited. Writes use `self.db.add(...)`, `await self.db.flush()`, `await self.db.refresh(...)`; do not call `commit()`, because `get_db` in `app/core/dependencies.py` commits per request.

## 5. Service (`app/services/<name>_service.py`)
- Business rules and errors: 404 when the parent/object does not exist, 403 when it belongs to another user (see `project_service.py` / `task_service.py` for the owner check), 400 for rule violations such as duplicates.
- Uses the repository; never builds SQL itself.

## 6. Endpoint (`app/api/v1/endpoints/<name>.py`) and router
- `router = APIRouter(tags=["<Name>s"])`; each route has `response_model`, an explicit `status_code` for creates (201) and deletes (204), and a `summary`.
- Inject `current_user: CurrentUser` and `db: DbSession` from `app.core.dependencies`.
- The endpoint only calls the service and returns its result.
- Register it in `app/api/v1/router.py`: import the module and `api_router.include_router(<name>.router)`.

## 7. Tests (`tests/test_<name>.py`)
For each endpoint cover at least:
- the happy path (status code + response body),
- validation: an invalid value returns 422,
- not found: 404,
- another user's object: 403 (create a second user and log in with OAuth2 form data: `data={"username": ..., "password": ...}`),
- unauthenticated: 401.
Reuse fixtures from `tests/conftest.py` (`client`, `auth_headers`, `test_user`) and helpers such as `create_project` / `create_task` from `tests/test_tasks.py`.

## 8. Verify and finish
```bash
pytest                                   # whole suite green, report the counts
ruff check <the .py files you changed>
```
- Check `/docs` shows the new endpoints if the dev server is running.
- Run the `review-checklist` skill on `main...HEAD`.
- Commit in English with a conventional message, e.g. `feat(comments): add task comments endpoints`. The pre-commit test gate hook re-runs ruff and pytest before the commit goes through.
