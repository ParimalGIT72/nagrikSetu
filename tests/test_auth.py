from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.models.user import User


def register(client, email="citizen@example.com", password="A-long-test-password-123!"):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )


def test_register_login_and_get_current_user(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "citizen@example.com"
    assert body["role"] == "citizen"
    assert "password_hash" not in body

    login_response = client.post(
        "/api/auth/login",
        json={"email": "Citizen@example.com", "password": "A-long-test-password-123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert login_response.json()["expires_in"] == settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["id"] == body["id"]
    assert "password_hash" not in me_response.json()


def test_duplicate_email_is_rejected_case_insensitively(client):
    assert register(client).status_code == 201
    response = register(client, email="Citizen@example.com")
    assert response.status_code == 409


def test_invalid_password_is_rejected(client):
    assert register(client).status_code == 201
    response = client.post(
        "/api/auth/login",
        json={"email": "citizen@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401


def test_inactive_account_cannot_login(client, db_session):
    assert register(client).status_code == 201
    user = db_session.query(User).filter(User.email == "citizen@example.com").first()
    assert user is not None
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "citizen@example.com", "password": "A-long-test-password-123!"},
    )
    assert response.status_code == 401


def test_malformed_and_expired_tokens_are_rejected(client, db_session):
    assert register(client).status_code == 201
    user = db_session.query(User).filter(User.email == "citizen@example.com").first()
    assert user is not None
    expired_token = jwt.encode(
        {
            "sub": str(user.id),
            "ver": user.token_version,
            "iat": datetime.now(timezone.utc) - timedelta(hours=1),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    invalid_signature_token = jwt.encode(
        {
            "sub": str(user.id),
            "ver": user.token_version,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        },
        settings.JWT_SECRET_KEY + "invalid-signature",
        algorithm="HS256",
    )

    malformed_response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
    )
    expired_response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    invalid_signature_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {invalid_signature_token}"},
    )
    assert malformed_response.status_code == 401
    assert expired_response.status_code == 401
    assert invalid_signature_response.status_code == 401


def test_logout_revokes_existing_tokens(client, db_session):
    assert register(client).status_code == 201
    user = db_session.query(User).filter(User.email == "citizen@example.com").first()
    assert user is not None
    from app.services.authentication import create_access_token

    token, _ = create_access_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_public_registration_cannot_assign_privileged_role(client):
    weak_password_response = client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert weak_password_response.status_code == 422
    assert '"input"' not in weak_password_response.text
    assert '"short"' not in weak_password_response.text

    response = client.post(
        "/api/auth/register",
        json={
            "email": "officer@example.com",
            "password": "A-long-test-password-123!",
            "role": "admin",
        },
    )
    assert response.status_code == 422
    assert "A-long-test-password-123!" not in response.text