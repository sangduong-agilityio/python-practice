# Repository Loop Playbook (`loop.md`)

This file documents standard automated loops for `task-management-api` using Claude Code's `/loop` command.

## Recommended Loops

### 1. Test Suite Watcher (Local Development)
Automatically re-runs the task test suite while implementing features or refactoring:
```text
/loop 5m pytest tests/test_tasks.py -v
```

### 2. PR Review & CI Babysitter
Periodically monitors branch status, CI build progress, and incoming review feedback on open pull requests:
```text
/loop 15m check git status and verify if all local test suites pass cleanly
```

### 3. Migration & DB Health Check
Verifies Alembic migrations are clean and in sync with the database head:
```text
/loop 10m alembic current
```

---
*Note: Press `Esc` at any time to cancel an active `/loop`.*
