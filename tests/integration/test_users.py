"""
Integration tests for User Profile management.

Verifies:
- Profile retrieval for authenticated users.
- Profile updates (username/email).
- Conflict prevention (duplicate email/username rejection).
- Security around inactive accounts.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.user import User
from tests.conftest import auth_headers, create_user

@pytest.mark.asyncio
async def test_own_profile_lifecycle(client: AsyncClient):
    """Verify that a user can retrieve and update their own profile information."""
    user_payload = {"email": "lifecycle@example.com", "username": "lifecycle", "password": "password123"}
    await create_user(client, user_payload)
    headers = await auth_headers(client, user_payload)

    # 1. Retrieve
    r = await client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == user_payload["email"]

    # 2. Update
    r = await client.put("/api/v1/users/me", json={"username": "updated_user"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == "updated_user"

@pytest.mark.asyncio
async def test_profile_conflict_prevention(client: AsyncClient):
    """Ensure that updating a profile fails if it conflicts with another user's data."""
    # Alice
    alice_payload = {"email": "alice_uniq@example.com", "username": "alice_uniq", "password": "password123"}
    await create_user(client, alice_payload)
    
    # Bob
    bob_payload = {"email": "bob_uniq@example.com", "username": "bob_uniq", "password": "password123"}
    await create_user(client, bob_payload)
    bob_headers = await auth_headers(client, bob_payload)
    
    # Bob tries to take Alice's email
    r = await client.put("/api/v1/users/me", json={"email": alice_payload["email"]}, headers=bob_headers)
    assert r.status_code == 409
    
    # Bob tries to take Alice's username
    r = await client.put("/api/v1/users/me", json={"username": alice_payload["username"]}, headers=bob_headers)
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_inactive_user_access_rejection(client: AsyncClient, db_session):
    """Verify that tokens belonging to deactivated users are rejected."""
    user_payload = {"email": "inactive_test@example.com", "username": "inactive_test", "password": "password123"}
    await create_user(client, user_payload)
    headers = await auth_headers(client, user_payload)
    
    # Deactivate in DB
    result = await db_session.execute(select(User).where(User.email == user_payload["email"]))
    user_obj = result.scalar_one()
    user_obj.is_active = False
    await db_session.commit()
    
    # Request should fail
    r = await client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 403
    assert "inactive" in r.json()["detail"].lower()
