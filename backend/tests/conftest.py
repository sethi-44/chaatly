"""
conftest.py — shared fixtures for all tests.

Uses an in-memory SQLite database so tests never touch the real Postgres.
The FastAPI app's `get_db` dependency is overridden to use the test session.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.security import create_verification_token

from app.models import Base
from app.dependencies import get_db
from app.main import app


# SQLite in-memory engine — StaticPool forces a single shared connection
# so tables created by create_all are visible to all sessions.
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable FK constraints in SQLite (off by default)
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def mock_resend():
    """Patch resend.Emails.send so tests never hit the real Resend API."""
    with patch("resend.Emails.send", return_value={"id": "mock_email_id"}):
        yield


@pytest.fixture()
def db():
    """Yield a fresh DB session for direct model operations in tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """
    FastAPI TestClient with the get_db dependency overridden
    to use the same test session.
    """
    def _override_get_db():
        try:
            yield db
        finally:
            pass  # session lifecycle managed by the `db` fixture

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def register_user(client: TestClient, username="testuser", email="test@example.com", password="securepassword123"):
    """Register a user, verify their email, and return the registration response."""
    resp = client.post("/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    # Automatically verify the user's email so login works
    if resp.status_code == 201:
        token = create_verification_token(email)
        client.post("/verify-email", json={"token": token})
    return resp


def login_user(client: TestClient, email="test@example.com", password="securepassword123"):
    """Login and return the response JSON (contains access_token, refresh_token)."""
    return client.post("/login", data={
        "username": email,  # OAuth2 form uses 'username' field for the identifier
        "password": password,
    })


def auth_header(access_token: str) -> dict:
    """Return an Authorization header dict."""
    return {"Authorization": f"Bearer {access_token}"}


def register_and_login(client: TestClient, username="testuser", email="test@example.com", password="securepassword123"):
    """Register + login, return (register_response, login_data, auth_headers)."""
    reg = register_user(client, username, email, password)
    log = login_user(client, email, password)
    login_data = log.json()
    headers = auth_header(login_data["access_token"])
    return reg, login_data, headers
