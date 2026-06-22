"""
conftest.py — shared fixtures for all tests.

Uses an in-memory SQLite database so tests never touch the real Postgres.
The FastAPI app's `get_db` dependency is overridden to use the test session.
"""
import os
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("CSRF_ENABLED", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ALGORITHM", "HS256")

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.security import create_verification_token
from app.rate_limit import limiter

from app.models import Base
from app.dependencies import get_db
from app.main import app


# Mock Supabase client for testing
@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock the Supabase client to avoid network calls in tests."""
    with patch("app.supabase_auth.get_supabase_client") as mock_get_client:
        # Mock client
        mock_client = MagicMock()
        mock_auth = MagicMock()
        mock_client.auth = mock_auth
        
        # Mock admin methods
        mock_admin = MagicMock()
        mock_auth.admin = mock_admin
        
        # Mock create_user response
        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "test@example.com"
        mock_user.user_metadata = {"username": "testuser"}
        mock_user.email_confirmed_at = "2024-01-01T00:00:00Z"
        mock_user.created_at = "2024-01-01T00:00:00Z"
        
        mock_session = MagicMock()
        mock_session.access_token = "mock-access-token"
        mock_session.refresh_token = "mock-refresh-token"
        
        # Track registered users for validation
        registered_users = {}
        logged_out_tokens = set()
        access_to_refresh = {}  # Map access_token -> refresh_token
        valid_access_tokens = set()  # Track all valid access tokens
        login_counter = {}  # Track login count per email for unique tokens
        
        def mock_sign_out(access_token):
            logged_out_tokens.add(access_token)
            # Also invalidate the associated refresh token
            if access_token in access_to_refresh:
                logged_out_tokens.add(access_to_refresh[access_token])
        
        import uuid
        
        def mock_create_user(data):
            email = data.get("email")
            password = data.get("password")
            username = data.get("user_metadata", {}).get("username", email.split("@")[0])
            
            if email in registered_users:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists"
                )
            
            new_user = MagicMock()
            new_user.id = str(uuid.uuid4())
            new_user.email = email
            new_user.user_metadata = {"username": username}
            new_user.email_confirmed_at = None
            new_user.created_at = "2024-01-01T00:00:00Z"
            
            registered_users[email] = {"password": password, "user": new_user}
            return MagicMock(user=new_user)
        
        def mock_sign_in(data):
            email = data.get("email")
            password = data.get("password")
            
            if email not in registered_users:
                from gotrue.errors import AuthApiError
                raise AuthApiError({"message": "Invalid login credentials"}, 400)
            
            if registered_users[email]["password"] != password:
                from gotrue.errors import AuthApiError
                raise AuthApiError({"message": "Invalid login credentials"}, 400)
            
            user = registered_users[email]["user"]
            count = login_counter.get(email, 0) + 1
            login_counter[email] = count
            session = MagicMock()
            session.access_token = f"access-token-{email}-{count}"
            session.refresh_token = f"refresh-token-{email}-{count}"
            access_to_refresh[session.access_token] = session.refresh_token
            valid_access_tokens.add(session.access_token)
            return MagicMock(user=user, session=session)
        
        def mock_refresh(refresh_token):
            # Check if refresh token was logged out
            if refresh_token in logged_out_tokens:
                from gotrue.errors import AuthApiError
                raise AuthApiError({"message": "Invalid refresh token"}, 400)
            
            # Check if refresh token matches any registered user's refresh token pattern
            for email, data in registered_users.items():
                if refresh_token.startswith(f"refresh-token-{email}-"):
                    user = data["user"]
                    count = login_counter.get(email, 1)
                    session = MagicMock()
                    session.access_token = f"access-token-{email}-{count}"
                    session.refresh_token = f"refresh-token-{email}-{count}"
                    login_counter[email] = count + 1
                    access_to_refresh[session.access_token] = session.refresh_token
                    valid_access_tokens.add(session.access_token)
                    return MagicMock(user=user, session=session)
            from gotrue.errors import AuthApiError
            raise AuthApiError({"message": "Invalid refresh token"}, 400)
        
        def mock_get_user(token):
            # Check if access token matches any registered user's access token pattern
            for email, data in registered_users.items():
                if token.startswith(f"access-token-{email}-"):
                    return MagicMock(user=data["user"])
            from gotrue.errors import AuthApiError
            raise AuthApiError({"message": "Invalid token"}, 401)
        
        def mock_update_user(data, access_token):
            # Verify access token is valid
            if access_token not in valid_access_tokens:
                from gotrue.errors import AuthApiError
                raise AuthApiError({"message": "Invalid token"}, 401)
            # Find which user this token belongs to and update password
            for email, user_data in registered_users.items():
                if access_token.startswith(f"access-token-{email}-") or access_token.startswith(f"new-access-token-{email}-"):
                    # Update password if provided
                    if "password" in data:
                        user_data["password"] = data["password"]
                    return None
            from gotrue.errors import AuthApiError
            raise AuthApiError({"message": "Invalid token"}, 401)
        
        def mock_sign_in_for_password_change(data):
            email = data.get("email")
            password = data.get("password")
            
            if email not in registered_users:
                from gotrue.errors import AuthApiError
                raise AuthApiError({"message": "Invalid login credentials"}, 400)
            
            if registered_users[email]["password"] != password:
                from gotrue.errors import AuthApiError
                raise AuthApiError({"message": "Invalid login credentials"}, 400)
            
            user = registered_users[email]["user"]
            new_session = MagicMock()
            new_session.access_token = f"new-access-token-{email}"
            new_session.refresh_token = f"new-refresh-token-{email}"
            valid_access_tokens.add(new_session.access_token)
            return MagicMock(user=user, session=new_session)
        
        mock_admin.create_user.side_effect = mock_create_user
        mock_auth.sign_in_with_password.side_effect = mock_sign_in
        mock_auth.refresh_session.side_effect = mock_refresh
        mock_auth.get_user.side_effect = mock_get_user
        mock_auth.update_user.side_effect = mock_update_user
        mock_auth.verify_otp.return_value = MagicMock(user=mock_user)
        mock_auth.reset_password_for_email.return_value = None
        mock_auth.sign_out.side_effect = mock_sign_out
        
        # For change password, we need a special sign_in that uses current password
        mock_auth.sign_in_with_password.side_effect = mock_sign_in
        
        # Mock list_users - return all registered users
        def mock_list_users():
            users = []
            for email, data in registered_users.items():
                user = data["user"]
                user.email_confirmed_at = "2024-01-01T00:00:00Z"
                user.created_at = "2024-01-01T00:00:00Z"
                user.user_metadata = {"username": user.user_metadata.get("username", email.split("@")[0])}
                users.append(user)
            return users
        mock_admin.list_users.side_effect = mock_list_users
        
        mock_get_client.return_value = mock_client
        
        yield mock_client


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
    Rate limiting is disabled during tests.
    """
    def _override_get_db():
        try:
            yield db
        finally:
            pass  # session lifecycle managed by the `db` fixture

    app.dependency_overrides[get_db] = _override_get_db
    app.state.limiter = limiter
    limiter.enabled = False  # Disable rate limiting for tests
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    limiter.enabled = True  # Re-enable after tests


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def register_user(client: TestClient, username="testuser", email="test@example.com", password="securepassword123"):
    """Register a user, verify their email, and return the registration response."""
    resp = client.post("/supabase/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    # Automatically verify the user's email so login works
    if resp.status_code == 201:
        token = create_verification_token(email)
        client.post("/supabase/verify-email", json={"token": token})
    return resp


def login_user(client: TestClient, email="test@example.com", password="securepassword123"):
    """Login and return the response JSON (contains access_token, refresh_token)."""
    return client.post("/supabase/login", data={
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
