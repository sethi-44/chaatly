"""
test_auth.py — comprehensive tests for authentication endpoints.

Covers: /register, /login, /refresh, /logout, /me, /users/me/change-password
"""
import pytest
from tests.conftest import register_user, login_user, auth_header, register_and_login


# =========================================================================
# /register POST
# =========================================================================

class TestRegister:
    """Tests for the POST /register endpoint."""

    def test_register_success(self, client):
        """Successful registration returns 201 with id, username, and email."""
        resp = register_user(client)
        assert resp.status_code == 201

        data = resp.json()
        assert "id" in data
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        # password must never be returned
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_username(self, client):
        """Registering with an already-taken username returns 400."""
        register_user(client, username="taken", email="first@example.com")
        resp = register_user(client, username="taken", email="second@example.com")
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    def test_register_duplicate_email(self, client):
        """Registering with an already-taken email returns 400."""
        register_user(client, username="user1", email="same@example.com")
        resp = register_user(client, username="user2", email="same@example.com")
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    def test_register_missing_fields(self, client):
        """Omitting required fields returns 422 (validation error)."""
        # completely empty body
        resp = client.post("/register", json={})
        assert resp.status_code == 422

    def test_register_missing_password(self, client):
        """Omitting the password field returns 422."""
        resp = client.post("/register", json={
            "username": "nopass",
            "email": "nopass@example.com",
        })
        assert resp.status_code == 422

    def test_register_password_too_short(self, client):
        """A password shorter than 8 characters returns 422."""
        resp = register_user(client, password="short")
        assert resp.status_code == 422

    def test_register_invalid_email_format(self, client):
        """A malformed email address returns 422."""
        resp = register_user(client, email="not-an-email")
        assert resp.status_code == 422

    def test_register_username_too_short(self, client):
        """A username shorter than 3 characters returns 422."""
        resp = register_user(client, username="ab")
        assert resp.status_code == 422


# =========================================================================
# /login POST
# =========================================================================

class TestLogin:
    """Tests for the POST /login endpoint (OAuth2 form-based)."""

    def test_login_success(self, client):
        """Successful login returns access_token, refresh_token, and token_type=bearer."""
        register_user(client)
        resp = login_user(client)
        assert resp.status_code == 200

        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_email(self, client):
        """Login with a non-existent email returns 401."""
        register_user(client)
        resp = login_user(client, email="wrong@example.com")
        assert resp.status_code == 401
        assert "invalid credentials" in resp.json()["detail"].lower()

    def test_login_wrong_password(self, client):
        """Login with an incorrect password returns 401."""
        register_user(client)
        resp = login_user(client, password="wrongpassword123")
        assert resp.status_code == 401
        assert "invalid credentials" in resp.json()["detail"].lower()

    def test_login_unregistered_user(self, client):
        """Login without any prior registration returns 401."""
        resp = login_user(client, email="ghost@example.com", password="doesntmatter1")
        assert resp.status_code == 401


# =========================================================================
# /refresh POST
# =========================================================================

class TestRefreshToken:
    """Tests for the POST /refresh endpoint."""

    def test_refresh_success(self, client):
        """A valid refresh token returns a new access_token."""
        register_user(client)
        login_resp = login_user(client)
        refresh_tok = login_resp.json()["refresh_token"]

        resp = client.post("/refresh", json={"refresh_token": refresh_tok})
        assert resp.status_code == 200

        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_with_invalid_token(self, client):
        """A completely made-up token string returns 401."""
        resp = client.post("/refresh", json={"refresh_token": "this.is.garbage"})
        assert resp.status_code == 401
        assert "invalid refresh token" in resp.json()["detail"].lower()

    def test_refresh_with_access_token_instead(self, client):
        """Using the access_token (not refresh) in the refresh endpoint should fail.

        The access token is a valid JWT but won't be stored in the
        refresh_tokens table, so the endpoint should reject it with 401.
        """
        register_user(client)
        login_data = login_user(client).json()
        access_tok = login_data["access_token"]

        resp = client.post("/refresh", json={"refresh_token": access_tok})
        assert resp.status_code == 401

    def test_refresh_new_token_is_usable(self, client):
        """The new access_token obtained via /refresh can authenticate /me."""
        register_user(client)
        login_data = login_user(client).json()

        refresh_resp = client.post("/refresh", json={
            "refresh_token": login_data["refresh_token"]
        })
        new_access = refresh_resp.json()["access_token"]

        me_resp = client.get("/me", headers=auth_header(new_access))
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "testuser"


# =========================================================================
# /logout POST
# =========================================================================

class TestLogout:
    """Tests for the POST /logout endpoint."""

    def test_logout_success(self, client):
        """Logout with a valid refresh token returns a success message."""
        register_user(client)
        login_data = login_user(client).json()

        resp = client.post("/logout", json={
            "refresh_token": login_data["refresh_token"]
        })
        assert resp.status_code == 200
        assert "logged out" in resp.json()["message"].lower()

    def test_refresh_token_invalidated_after_logout(self, client):
        """After logout, the same refresh token can no longer be used to refresh."""
        register_user(client)
        login_data = login_user(client).json()
        refresh_tok = login_data["refresh_token"]

        # Logout
        logout_resp = client.post("/logout", json={"refresh_token": refresh_tok})
        assert logout_resp.status_code == 200

        # Attempt to refresh — should fail
        resp = client.post("/refresh", json={"refresh_token": refresh_tok})
        assert resp.status_code == 401

    def test_logout_with_unknown_token(self, client):
        """Logging out with a token that doesn't exist still returns 200
        (idempotent — the token is simply not in the DB).
        """
        resp = client.post("/logout", json={"refresh_token": "nonexistent.token.value"})
        assert resp.status_code == 200


# =========================================================================
# /me GET
# =========================================================================

class TestMe:
    """Tests for the GET /me endpoint."""

    def test_me_returns_current_user(self, client):
        """A valid access token returns the authenticated user's data."""
        _, login_data, headers = register_and_login(client)

        resp = client.get("/me", headers=headers)
        assert resp.status_code == 200

        data = resp.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        # Sensitive fields must not leak
        assert "password" not in data
        assert "password_hash" not in data

    def test_me_without_token(self, client):
        """Hitting /me with no Authorization header returns 401."""
        resp = client.get("/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token(self, client):
        """Hitting /me with a bogus token returns 401."""
        resp = client.get("/me", headers=auth_header("invalid.token.here"))
        assert resp.status_code == 401

    def test_me_response_model_fields(self, client):
        """The /me response only contains the UserResponse fields (username, email)."""
        _, _, headers = register_and_login(client)
        data = client.get("/me", headers=headers).json()
        assert set(data.keys()) == {"username", "email"}


# =========================================================================
# /users/me/change-password POST
# =========================================================================

class TestChangePassword:
    """Tests for the POST /users/me/change-password endpoint."""

    def test_change_password_success(self, client):
        """Changing password with correct current password returns success."""
        _, _, headers = register_and_login(client)

        resp = client.post("/users/me/change-password", json={
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456",
        }, headers=headers)
        assert resp.status_code == 200
        assert "password changed" in resp.json()["message"].lower()

    def test_change_password_wrong_current(self, client):
        """Providing an incorrect current password returns 400."""
        _, _, headers = register_and_login(client)

        resp = client.post("/users/me/change-password", json={
            "current_password": "wrongoldpassword1",
            "new_password": "newsecurepassword456",
        }, headers=headers)
        assert resp.status_code == 400
        assert "incorrect" in resp.json()["detail"].lower()

    def test_can_login_with_new_password(self, client):
        """After changing password, the new password works for login."""
        _, login_data, headers = register_and_login(client)

        # Change password
        client.post("/users/me/change-password", json={
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456",
        }, headers=headers)

        # Logout first to clear the old refresh token (avoids UNIQUE
        # constraint collision when the new login happens in the same second).
        client.post("/logout", json={
            "refresh_token": login_data["refresh_token"]
        })

        # Login with new password
        resp = login_user(client, password="newsecurepassword456")
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_old_password_stops_working_after_change(self, client):
        """After changing password, the old password no longer works."""
        _, _, headers = register_and_login(client)

        client.post("/users/me/change-password", json={
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456",
        }, headers=headers)

        # Old password should fail
        resp = login_user(client, password="securepassword123")
        assert resp.status_code == 401

    def test_change_password_unauthenticated(self, client):
        """Calling change-password without auth returns 401."""
        resp = client.post("/users/me/change-password", json={
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456",
        })
        assert resp.status_code == 401

    def test_change_password_new_too_short(self, client):
        """A new password shorter than 8 characters returns 422."""
        _, _, headers = register_and_login(client)

        resp = client.post("/users/me/change-password", json={
            "current_password": "securepassword123",
            "new_password": "short",
        }, headers=headers)
        assert resp.status_code == 422
