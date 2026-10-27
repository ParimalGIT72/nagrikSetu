import os
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.db.database import get_db
from app.main import app


def _isolated_test_url():
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if not raw_url:
        pytest.fail(
            "TEST_DATABASE_URL must point to a dedicated PostgreSQL database ending in _test"
        )

    test_url = make_url(raw_url)
    configured_url = make_url(settings.DATABASE_URL)
    test_identity = (test_url.drivername.split("+")[0], test_url.host, test_url.port, test_url.database)
    configured_identity = (
        configured_url.drivername.split("+")[0],
        configured_url.host,
        configured_url.port,
        configured_url.database,
    )
    if (
        test_url.get_backend_name() != "postgresql"
        or not (test_url.database or "").lower().endswith("_test")
        or test_identity == configured_identity
    ):
        pytest.fail(
            "TEST_DATABASE_URL must be a separate PostgreSQL database whose name ends in _test"
        )
    return test_url


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(_isolated_test_url(), pool_pre_ping=True)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        config.attributes.pop("connection", None)
    yield engine
    engine.dispose()


@pytest.fixture
def db_connection(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_session(db_connection):
    session = Session(bind=db_connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()


@pytest.fixture
def client(db_connection, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", os.urandom(48).hex())

    def override_get_db():
        session = Session(
            bind=db_connection,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def citizen_headers(client, db_session):
    from app.models.user import User
    from app.services.authentication import create_access_token, hash_password

    user = User(
        email=f"citizen-{os.urandom(6).hex()}@example.test",
        password_hash=hash_password("A-long-test-password-123!"),
        role="citizen",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token, _ = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def officer_headers(client, db_session):
    from app.models.user import User
    from app.services.authentication import create_access_token, hash_password

    user = User(
        email=f"officer-{os.urandom(6).hex()}@example.test",
        password_hash=hash_password("A-long-test-password-123!"),
        role="officer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token, _ = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}