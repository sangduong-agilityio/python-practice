import pytest
from fastapi.testclient import TestClient
import threading
import uuid

from app.core.dependencies import get_db
from app.core.rate_limit import limiter
from app.main import app
from tests.conftest import create_user


@pytest.mark.asyncio
async def test_chat_ws_message_delivery(client, db_session):
    """
    End-to-end:
    - create 2 users
    - connect websocket as recipient
    - connect websocket as sender and send message
    - recipient receives `chat.message` event
    """
    uniq = uuid.uuid4().hex[:8]
    sender_payload = {
        "email": f"alice-{uniq}@example.com",
        "username": f"alice_{uniq}",
        "password": "strongpassword1",
    }
    recipient_payload = {
        "email": f"bob-{uniq}@example.com",
        "username": f"bob_{uniq}",
        "password": "strongpassword2",
    }

    sender_user = await create_user(client, sender_payload)
    recipient_user = await create_user(client, recipient_payload)

    r = await client.post(
        "/api/v1/auth/login",
        data={"username": sender_payload["email"], "password": sender_payload["password"]},
    )
    assert r.status_code == 200, r.text
    sender_token = r.json()["access_token"]

    r = await client.post(
        "/api/v1/auth/login",
        data={
            "username": recipient_payload["email"],
            "password": recipient_payload["password"],
        },
    )
    assert r.status_code == 200, r.text
    recipient_token = r.json()["access_token"]

    # Override DB dependency for TestClient websocket requests to share the same DB session.
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False

    with TestClient(app) as tc:
        with tc.websocket_connect(
            "/api/v1/chat/ws",
            headers={"Authorization": f"Bearer {recipient_token}"},
        ) as ws_recipient:
            with tc.websocket_connect(
                "/api/v1/chat/ws",
                headers={"Authorization": f"Bearer {sender_token}"},
            ) as ws_sender:
                ws_sender.send_json(
                    {"recipient_id": recipient_user["id"], "content": "hello"}
                )

                received: dict | None = None
                err: Exception | None = None

                def _recv():
                    nonlocal received, err
                    try:
                        received = ws_recipient.receive_json()
                    except Exception as e:  # pragma: no cover
                        err = e

                t = threading.Thread(target=_recv, daemon=True)
                t.start()
                t.join(timeout=2.0)
                assert err is None
                assert received is not None, "Timed out waiting for websocket message"

                assert received["type"] == "chat.message"
                assert received["data"]["content"] == "hello"
                assert received["data"]["sender_id"] == sender_user["id"]
                assert received["data"]["recipient_id"] == recipient_user["id"]

    app.dependency_overrides.clear()
    limiter.enabled = True


@pytest.mark.asyncio
async def test_chat_thread_history_endpoint(client):
    uniq = uuid.uuid4().hex[:8]
    a = {"email": f"a-{uniq}@example.com", "username": f"a_{uniq}", "password": "strongpassword1"}
    b = {"email": f"b-{uniq}@example.com", "username": f"b_{uniq}", "password": "strongpassword2"}
    await create_user(client, a)
    b_user = await create_user(client, b)

    r = await client.post(
        "/api/v1/auth/login",
        data={"username": a["email"], "password": a["password"]},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    # No messages yet
    r = await client.get(
        f"/api/v1/chat/threads/{b_user['id']}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json() == []

