---
name: review-checklist
description: Use when asked to review a diff, branch, commit or PR in task-management-api, or before opening a PR. Reviews in the team's fixed order (correctness, tests, readability, security, scope) and checks the repo rules in CLAUDE.md.
---

# Review Checklist

Review the change in this order and stop to report after each section. Every finding must be actionable and cite `file:line`.

## 0. Gather
- `git diff --stat <base>...HEAD` and `git diff <base>...HEAD` (base is `main` unless told otherwise).
- Read the ticket or PR description if given.

## 1. Correctness
- Does the change do what the ticket asks, including edge cases (None, empty, casing, whitespace)?
- Async safety: no lazy-loaded relationships without `selectinload`, every DB call awaited.
- Enum inputs normalized case-insensitively; invalid values still return 422.
- Schema changes have an Alembic migration (see the `how-we-write-migrations` skill).

## 2. Tests
- Is there a test that fails without the fix and passes with it?
- Are regression guards present (invalid input still rejected)?
- Run the full `pytest` and report pass/fail counts. Never call a review done without it.

## 3. Readability
- Names say what things are; no shadowed variables; no dead code.
- Comments and docstrings explain why, not what.

## 4. Security basics
- No secrets, tokens or real customer data in code, tests or fixtures.
- Auth and ownership checks are not bypassed; login still takes OAuth2 form data.

## 5. Scope
- One topic per PR. Flag unrelated files, including line-ending-only (CRLF) diffs.
- Commit messages, PR text, comments and docstrings are in English.

## Output
A short summary verdict (approve / request changes), then findings grouped by the sections above, most severe first. Say explicitly which checks you ran and which you only read.
