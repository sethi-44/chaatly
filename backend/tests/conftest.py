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
from app.rate_limit import limiter

from app.models import Base
from app.dependencies import get_db
from app.main import app


# Mock Supabase client for testing
@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock the Supabase wrapper functions to avoid network calls in tests."""
    with patch("app.routers.supabase_auth.create_supabase_user") as mock_create_user_wrapper, \
         patch("app.routers.supabase_auth.sign_in_supabase_user") as mock_sign_in_wrapper, \
         patch("app.routers.supabase_auth.refresh_supabase_session") as mock_refresh_wrapper, \
         patch("app.routers.supabase_auth.get_supabase_user_by_email") as mock_get_supabase_user_by_email_wrapper, \
         patch("app.routers.supabase_auth.sign_out_supabase_user") as mock_logout_wrapper, \
         patch("app.routers.supabase_auth.update_password_supabase") as mock_update_password_wrapper:
        
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
        mock_logout_wrapper.side_effect = mock_sign_out
        
        from types import SimpleNamespace
        import uuid
        
        def mock_create_user(email, password, username):
            if email in registered_users:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists"
                )
            
            new_user = SimpleNamespace(
                id=str(uuid.uuid4()),
                email=email,
                user_metadata={"username": username},
                email_confirmed_at=None,
                created_at="2024-01-01T00:00:00Z"
            )
            
            registered_users[email] = {"password": password, "user": new_user}
            return {"user": new_user, "session": None}
        mock_create_user_wrapper.side_effect = mock_create_user
        
        def mock_sign_in(email, password):
            from fastapi import HTTPException, status
            if email not in registered_users:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            
            if registered_users[email]["password"] != password:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            
            user = registered_users[email]["user"]
            count = login_counter.get(email, 0) + 1
            login_counter[email] = count
            session = SimpleNamespace(
                access_token=f"access-token-{email}-{count}",
                refresh_token=f"refresh-token-{email}-{count}"
            )
            access_to_refresh[session.access_token] = session.refresh_token
            valid_access_tokens.add(session.access_token)
            return {"user": user, "session": session}
        mock_sign_in_wrapper.side_effect = mock_sign_in
        
        def mock_refresh(refresh_token):
            from fastapi import HTTPException, status
            # Check if refresh token was logged out
            if refresh_token in logged_out_tokens:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
            
            # Check if refresh token matches any registered user's refresh token pattern
            for email, data in registered_users.items():
                if refresh_token.startswith(f"refresh-token-{email}-"):
                    user = data["user"]
                    count = login_counter.get(email, 1)
                    session = SimpleNamespace(
                        access_token=f"access-token-{email}-{count}",
                        refresh_token=f"refresh-token-{email}-{count}"
                    )
                    login_counter[email] = count + 1
                    access_to_refresh[session.access_token] = session.refresh_token
                    valid_access_tokens.add(session.access_token)
                    return {"user": user, "session": session}
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        mock_refresh_wrapper.side_effect = mock_refresh
        
        from fastapi import Depends
        from app.supabase_auth import oauth2_scheme
        from app.dependencies import get_db
        from sqlalchemy.orm import Session

        def mock_get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
            from fastapi import HTTPException, status
            from app.models import User as DBUser
            if token in logged_out_tokens:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            
            # Check if access token matches any registered user's access token pattern
            for email, data in registered_users.items():
                if token.startswith(f"access-token-{email}-"):
                    supabase_user = data["user"]
                    db_user = db.query(DBUser).filter(DBUser.id == supabase_user.id).first()
                    if db_user:
                        return db_user
                    
                    return DBUser(
                        id=supabase_user.id,
                        email=supabase_user.email,
                        username=supabase_user.user_metadata.get("username"),
                        password_hash="managed_by_supabase"
                    )
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        # We need to import the app and the dependency to override it
        from app.main import app
        from app.supabase_auth import get_current_user_supabase
        app.dependency_overrides[get_current_user_supabase] = mock_get_current_user
        
        def mock_get_user_by_email(email):
            if email in registered_users:
                return registered_users[email]["user"]
            return None
        mock_get_supabase_user_by_email_wrapper.side_effect = mock_get_user_by_email
        
        def mock_update_password(access_token, new_password):
            for email, data in registered_users.items():
                if access_token.startswith(f"access-token-{email}-"):
                    registered_users[email]["password"] = new_password
                    return MagicMock()
            from fastapi import HTTPException, status
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        mock_update_password_wrapper.side_effect = mock_update_password

        # Mock the admin client
        mock_admin = MagicMock()
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
        
        yield


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
