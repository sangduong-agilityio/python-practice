"""
Integration tests for user profiles.

Check profile retrieval, updates, conflict prevention, and inactive account limits.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User
from tests.conftest import auth_headers, create_user


@pytest.mark.asyncio
async def test_own_profile_lifecycle(client: AsyncClient):
    """Make sure a user can fetch and update their own stuff."""
    user_payload = {"email": "lifecycle@example.com", "username": "lifecycle", "password": "password123"}
    await create_user(client, user_payload)
    headers = await auth_headers(client, user_payload)

    # fetch current profile
    r = await client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == user_payload["email"]

    # update it
    r = await client.put("/api/v1/users/me", json={"username": "updated_user"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == "updated_user"

@pytest.mark.asyncio
async def test_profile_conflict_prevention(client: AsyncClient):
    """A user shouldn't be able to steal another user's email or username."""
    # set up alice
    alice_payload = {"email": "alice_uniq@example.com", "username": "alice_uniq", "password": "password123"}
    await create_user(client, alice_payload)

    # set up bob
    bob_payload = {"email": "bob_uniq@example.com", "username": "bob_uniq", "password": "password123"}
    await create_user(client, bob_payload)
    bob_headers = await auth_headers(client, bob_payload)

    # bob tries to steal alice's email
    r = await client.put("/api/v1/users/me", json={"email": alice_payload["email"]}, headers=bob_headers)
    assert r.status_code == 409

    # bob tries to steal alice's username
    r = await client.put("/api/v1/users/me", json={"username": alice_payload["username"]}, headers=bob_headers)
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_inactive_user_access_rejection(client: AsyncClient, db_session):
    """Deactivated accounts shouldn't be able to fetch anything."""
    user_payload = {"email": "inactive_test@example.com", "username": "inactive_test", "password": "password123"}
    await create_user(client, user_payload)
    headers = await auth_headers(client, user_payload)

    # manually deactivate the user in the db
    result = await db_session.execute(select(User).where(User.email == user_payload["email"]))
    user_obj = result.scalar_one()
    user_obj.is_active = False
    await db_session.commit()

    # api calls should now bounce
    r = await client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 403
    assert "inactive" in r.json()["detail"].lower()
