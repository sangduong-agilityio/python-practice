# Test report: Epic E<n> <Name>

Epic: [docs/epics/<slug>.md](../epics/<slug>.md) · Branch tip: `<commit>` · Date: <YYYY-MM-DD>

## By code

```
<last line of `python -m pytest -q`, e.g. 63 passed in 14.2s>
```

New tests in this epic: <count> (<file names>)

## By hand on the running API

Checked on `http://127.0.0.1:8000/docs` (or through the `task-api` MCP server).

| # | Scenario | Request | Expected | Actual | Result |
|---|----------|---------|----------|--------|--------|
| 1 | <happy path> | `POST /api/v1/...` | 201 + body | | ✅ / ❌ |
| 2 | <invalid input> | | 422 | | |
| 3 | <not found> | | 404 | | |
| 4 | <another user's object> | | 403 | | |
| 5 | <no token> | | 401 | | |

## Accepted with a reason

- <Anything not fixed in this epic, and why.>
