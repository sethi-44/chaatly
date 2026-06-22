"""
test_users.py — Tests for user management endpoints.

Covers:
  GET  /users/{id}   – get single user (authenticated)
  GET  /users        – list all users (authenticated)
  PUT  /users/me     – update current user (authenticated)
  POST /supabase/register — create user via Supabase Auth
"""
from tests.conftest import register_user, register_and_login, auth_header


# ── POST /users ──────────────────────────────────────────────────────────────

class TestCreateUser:
    """POST /users — create a new user."""

    def test_create_user_success(self, client):
        """Creating a user with valid data returns 201 and the user payload."""
        resp = client.post("/supabase/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "strongpass123",
        })

        assert resp.status_code == 201
        data = resp.json()["user"]
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert "password" not in data
        assert "password_hash" not in data

    def test_create_user_duplicate_username(self, client):
        """Registering a user with an already-taken username returns 400."""
        client.post("/supabase/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "strongpass123",
        })

        resp = client.post("/supabase/register", json={
            "username": "alice",              # same username
            "email": "different@example.com",
            "password": "strongpass123",
        })

        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    def test_create_user_duplicate_email(self, client):
        """Registering a user with an already-taken email returns 400."""
        client.post("/supabase/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "strongpass123",
        })

        resp = client.post("/supabase/register", json={
            "username": "bob",
            "email": "alice@example.com",     # same email
            "password": "strongpass123",
        })

        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    def test_create_user_invalid_data_returns_422(self, client):
        """Missing required fields / invalid values return 422."""
        # completely empty body
        resp = client.post("/supabase/register", json={})
        assert resp.status_code == 422

        # password too short (min 8 chars)
        resp = client.post("/supabase/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "short",
        })
        assert resp.status_code == 422

        # invalid email format
        resp = client.post("/supabase/register", json={
            "username": "alice",
            "email": "not-an-email",
            "password": "strongpass123",
        })
        assert resp.status_code == 422

        # username too short (min 3 chars)
        resp = client.post("/supabase/register", json={
            "username": "ab",
            "email": "alice@example.com",
            "password": "strongpass123",
        })
        assert resp.status_code == 422


# ── GET /users/{id} ─────────────────────────────────────────────────────────

class TestGetUser:
    """GET /users/{id} — retrieve a single user by ID."""

    def test_get_user_by_id(self, client):
        """Returns the user when they exist."""
        create_resp, _, headers = register_and_login(client, username="alice", email="alice@example.com")
        user_id = create_resp.json()["user"]["id"]

        resp = client.get(f"/users/{user_id}", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"

    def test_get_user_not_found(self, client):
        """Non-existent user ID returns 404."""
        _, _, headers = register_and_login(client, username="alice", email="alice@example.com")
        resp = client.get("/users/99999", headers=headers)

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# ── GET /users ───────────────────────────────────────────────────────────────

class TestGetAllUsers:
    """GET /users — list users."""

    def test_get_users_empty(self, client):
        """Returns a list of users."""
        _, _, headers = register_and_login(client, username="admin", email="admin@example.com")
        resp = client.get("/users", headers=headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_users_after_creation(self, client):
        """Returns all created users."""
        register_user(client, username="alice", email="alice@example.com")
        _, _, headers = register_and_login(client, username="bob", email="bob@example.com")

        resp = client.get("/users", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        usernames = {u["username"] for u in data}
        assert usernames == {"alice", "bob"}


# ── PUT /users/me ────────────────────────────────────────────────────────────

class TestUpdateUser:
    """PUT /users/me — update the authenticated user's profile."""

    def test_update_username_only(self, client):
        """Sending a new username (email=None) updates only the username."""
        _, _, headers = register_and_login(
            client, username="alice", email="alice@example.com"
        )

        resp = client.put("/users/me", json={
            "username": "alice_updated",
            "email": None,
        }, headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice_updated"
        assert data["email"] == "alice@example.com"   # unchanged

    def test_update_email_only(self, client):
        """Sending a new email (username=None) updates only the email."""
        _, _, headers = register_and_login(
            client, username="alice", email="alice@example.com"
        )

        resp = client.put("/users/me", json={
            "username": None,
            "email": "newalice@example.com",
        }, headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice"             # unchanged
        assert data["email"] == "newalice@example.com"

    def test_update_both_fields(self, client):
        """Updating both username and email at once succeeds."""
        _, _, headers = register_and_login(
            client, username="alice", email="alice@example.com"
        )

        resp = client.put("/users/me", json={
            "username": "alice_v2",
            "email": "alicev2@example.com",
        }, headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice_v2"
        assert data["email"] == "alicev2@example.com"

    def test_update_null_both_fields_keeps_values(self, client):
        """Passing null for both fields keeps the existing values."""
        _, _, headers = register_and_login(
            client, username="alice", email="alice@example.com"
        )

        resp = client.put("/users/me", json={
            "username": None,
            "email": None,
        }, headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"

    def test_update_duplicate_username_returns_400(self, client):
        """Changing to a username already taken by another user returns 400."""
        # Create two users; log in as the second one
        register_user(client, username="alice", email="alice@example.com")
        _, _, headers = register_and_login(
            client, username="bob", email="bob@example.com"
        )

        resp = client.put("/users/me", json={
            "username": "alice",   # taken by the first user
            "email": None,
        }, headers=headers)

        assert resp.status_code == 400
        assert "username already taken" in resp.json()["detail"].lower()

    def test_update_duplicate_email_returns_400(self, client):
        """Changing to an email already taken by another user returns 400."""
        register_user(client, username="alice", email="alice@example.com")
        _, _, headers = register_and_login(
            client, username="bob", email="bob@example.com"
        )

        resp = client.put("/users/me", json={
            "username": None,
            "email": "alice@example.com",  # taken by the first user
        }, headers=headers)

        assert resp.status_code == 400
        assert "email already taken" in resp.json()["detail"].lower()

    def test_update_unauthenticated_returns_401(self, client):
        """PUT /users/me without an Authorization header returns 401."""
        resp = client.put("/users/me", json={
            "username": "hacker",
            "email": None,
        })

        assert resp.status_code == 401
