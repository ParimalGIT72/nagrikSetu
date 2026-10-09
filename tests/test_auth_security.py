import jwt

from app.config import settings
from app.models.user import User
from app.services.authentication import create_access_token, hash_password, verify_password


def test_passwords_use_argon2id_and_verify():
    password = "A-long-test-password-123!"
    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash)
    assert not verify_password("incorrect-password", password_hash)


def test_access_token_has_configured_expiry_and_identity(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-only-signing-key-" * 3)
    user = User(id=17, token_version=4)

    token, expires_in = create_access_token(user)
    claims = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=["HS256"],
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
    )

    assert expires_in == settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert claims["sub"] == "17"
    assert claims["ver"] == 4