from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db
from app.models import Session as ChatSession


def test_public_customer_id_cannot_authenticate_a_chat(db):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        response = TestClient(app).post(
            "/chat",
            json={
                "message": "What is the status of order ORD-ALICE?",
                "session_id": "untrusted-client-session",
                "customer_id": "customer-1",
            },
        )
        assert response.status_code == 200
        assert response.json()["customer_verified"] is False
        assert db.get(ChatSession, "untrusted-client-session").customer_id is None

        session_token = response.json()["session_token"]
        denied = TestClient(app).post(
            "/chat",
            json={
                "message": "What is the status of order ORD-ALICE?",
                "session_id": "untrusted-client-session",
            },
        )
        assert denied.status_code == 403

        allowed = TestClient(app).post(
            "/chat",
            json={
                "message": "What is the status of order ORD-ALICE?",
                "session_id": "untrusted-client-session",
                "session_token": session_token,
            },
        )
        assert allowed.status_code == 200
    finally:
        app.dependency_overrides.clear()
