"""
test_meetups.py — comprehensive tests for meetup endpoints.

Covers: create, list, get, update, delete, join, leave,
        participants, attendance, my-meetups, my-joined-meetups.
"""

from tests.conftest import register_and_login, register_user, login_user, auth_header


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def create_meetup(
    client,
    headers,
    title="Test Meetup",
    location="Test City",
    max_attendees=10,
    description="A test meetup",
):
    return client.post(
        "/meetups",
        json={
            "title": title,
            "location": location,
            "max_attendees": max_attendees,
            "description": description,
        },
        headers=headers,
    )


# ===================================================================
# CREATE MEETUP  (POST /meetups)
# ===================================================================

class TestCreateMeetup:
    def test_authenticated_user_can_create_meetup(self, client):
        _, _, headers = register_and_login(client)
        resp = create_meetup(client, headers)

        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["title"] == "Test Meetup"
        assert data["location"] == "Test City"
        assert data["max_attendees"] == 10
        assert data["description"] == "A test meetup"
        assert data["attendee_count"] == 0
        assert data["spots_left"] == 10
        assert "host" in data
        assert data["host"]["username"] == "testuser"

    def test_unauthenticated_request_returns_401(self, client):
        resp = client.post("/meetups", json={
            "title": "Unauthorized Meetup",
            "location": "Nowhere",
            "max_attendees": 5,
        })
        assert resp.status_code == 401

    def test_invalid_data_returns_422(self, client):
        _, _, headers = register_and_login(client)

        # Title too short (min_length=3)
        resp = client.post("/meetups", json={
            "title": "AB",
            "location": "Valid City",
            "max_attendees": 5,
        }, headers=headers)
        assert resp.status_code == 422

        # max_attendees = 0 (must be gt 0)
        resp = client.post("/meetups", json={
            "title": "Valid Title",
            "location": "Valid City",
            "max_attendees": 0,
        }, headers=headers)
        assert resp.status_code == 422


# ===================================================================
# GET MEETUPS  (GET /meetups)
# ===================================================================

class TestGetMeetups:
    def test_returns_empty_list_when_no_meetups(self, client):
        resp = client.get("/meetups")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_meetups_after_creation(self, client):
        _, _, headers = register_and_login(client)
        create_meetup(client, headers, title="Meetup One")
        create_meetup(client, headers, title="Meetup Two")

        resp = client.get("/meetups")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        titles = {m["title"] for m in data}
        assert titles == {"Meetup One", "Meetup Two"}


# ===================================================================
# GET SINGLE MEETUP  (GET /meetups/{id})
# ===================================================================

class TestGetSingleMeetup:
    def test_returns_meetup_by_id(self, client):
        _, _, headers = register_and_login(client)
        created = create_meetup(client, headers).json()

        resp = client.get(f"/meetups/{created['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == created["id"]
        assert data["title"] == "Test Meetup"

    def test_nonexistent_meetup_returns_404(self, client):
        resp = client.get("/meetups/99999")
        assert resp.status_code == 404


# ===================================================================
# UPDATE MEETUP  (PUT /meetups/{id})
# ===================================================================

class TestUpdateMeetup:
    def test_host_can_update_their_meetup(self, client):
        _, _, headers = register_and_login(client)
        created = create_meetup(client, headers).json()

        resp = client.put(
            f"/meetups/{created['id']}",
            json={
                "title": "Updated Title",
                "location": "New Location",
                "max_attendees": 20,
                "description": "Updated description",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Title"
        assert data["location"] == "New Location"
        assert data["max_attendees"] == 20
        assert data["description"] == "Updated description"

    def test_non_host_gets_403(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()

        # Register a second user
        _, _, other_headers = register_and_login(
            client, username="other", email="other@example.com", password="securepassword123"
        )

        resp = client.put(
            f"/meetups/{created['id']}",
            json={
                "title": "Hijacked",
                "location": "Evil Lair",
                "max_attendees": 1,
            },
            headers=other_headers,
        )
        assert resp.status_code == 403

    def test_nonexistent_meetup_returns_404(self, client):
        _, _, headers = register_and_login(client)
        resp = client.put(
            "/meetups/99999",
            json={
                "title": "Ghost",
                "location": "Void",
                "max_attendees": 5,
            },
            headers=headers,
        )
        assert resp.status_code == 404

    def test_cannot_reduce_max_attendees_below_current_attendance(self, client):
        # Host creates meetup with max_attendees=5
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers, max_attendees=5).json()
        meetup_id = created["id"]

        # Two other users join
        _, _, user2_headers = register_and_login(
            client, username="user2", email="user2@example.com"
        )
        _, _, user3_headers = register_and_login(
            client, username="user3", email="user3@example.com"
        )
        client.post(f"/meetups/{meetup_id}/join", headers=user2_headers)
        client.post(f"/meetups/{meetup_id}/join", headers=user3_headers)

        # Try to reduce max_attendees to 1 (below current attendance of 2)
        resp = client.put(
            f"/meetups/{meetup_id}",
            json={
                "title": "Test Meetup",
                "location": "Test City",
                "max_attendees": 1,
                "description": "A test meetup",
            },
            headers=host_headers,
        )
        assert resp.status_code == 400
        assert "Cannot reduce" in resp.json()["detail"]


# ===================================================================
# DELETE MEETUP  (DELETE /meetups/{id})
# ===================================================================

class TestDeleteMeetup:
    def test_host_can_delete_their_meetup(self, client):
        _, _, headers = register_and_login(client)
        created = create_meetup(client, headers).json()

        resp = client.delete(f"/meetups/{created['id']}", headers=headers)
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

        # Confirm it's gone
        resp = client.get(f"/meetups/{created['id']}")
        assert resp.status_code == 404

    def test_non_host_gets_403(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()

        _, _, other_headers = register_and_login(
            client, username="other", email="other@example.com"
        )
        resp = client.delete(f"/meetups/{created['id']}", headers=other_headers)
        assert resp.status_code == 403

    def test_deleting_meetup_with_participants_succeeds(self, client):
        """Cascade delete should remove participants too."""
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()
        meetup_id = created["id"]

        # Another user joins
        _, _, joiner_headers = register_and_login(
            client, username="joiner", email="joiner@example.com"
        )
        join_resp = client.post(f"/meetups/{meetup_id}/join", headers=joiner_headers)
        assert join_resp.status_code == 201

        # Host deletes
        resp = client.delete(f"/meetups/{meetup_id}", headers=host_headers)
        assert resp.status_code == 200

        # Meetup is gone
        assert client.get(f"/meetups/{meetup_id}").status_code == 404

    def test_nonexistent_meetup_returns_404(self, client):
        _, _, headers = register_and_login(client)
        resp = client.delete("/meetups/99999", headers=headers)
        assert resp.status_code == 404


# ===================================================================
# JOIN MEETUP  (POST /meetups/{id}/join)
# ===================================================================

class TestJoinMeetup:
    def test_user_can_join_meetup(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()

        _, _, joiner_headers = register_and_login(
            client, username="joiner", email="joiner@example.com"
        )
        resp = client.post(f"/meetups/{created['id']}/join", headers=joiner_headers)
        assert resp.status_code == 201
        assert "joined" in resp.json()["message"].lower()

    def test_cannot_join_twice(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()

        _, _, joiner_headers = register_and_login(
            client, username="joiner", email="joiner@example.com"
        )
        client.post(f"/meetups/{created['id']}/join", headers=joiner_headers)
        resp = client.post(f"/meetups/{created['id']}/join", headers=joiner_headers)
        assert resp.status_code == 400
        assert "already" in resp.json()["detail"].lower()

    def test_cannot_join_full_meetup(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers, max_attendees=1).json()
        meetup_id = created["id"]

        # First user fills the only spot
        _, _, first_headers = register_and_login(
            client, username="first", email="first@example.com"
        )
        resp1 = client.post(f"/meetups/{meetup_id}/join", headers=first_headers)
        assert resp1.status_code == 201

        # Second user should be rejected
        _, _, second_headers = register_and_login(
            client, username="second", email="second@example.com"
        )
        resp2 = client.post(f"/meetups/{meetup_id}/join", headers=second_headers)
        assert resp2.status_code == 400
        assert "full" in resp2.json()["detail"].lower()

    def test_host_cannot_join_own_meetup(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()

        resp = client.post(f"/meetups/{created['id']}/join", headers=host_headers)
        assert resp.status_code == 400
        assert "host" in resp.json()["detail"].lower()

    def test_nonexistent_meetup_returns_404(self, client):
        _, _, headers = register_and_login(client)
        resp = client.post("/meetups/99999/join", headers=headers)
        assert resp.status_code == 404


# ===================================================================
# LEAVE MEETUP  (POST /meetups/{id}/leave)
# ===================================================================

class TestLeaveMeetup:
    def test_participant_can_leave(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()
        meetup_id = created["id"]

        _, _, joiner_headers = register_and_login(
            client, username="joiner", email="joiner@example.com"
        )
        client.post(f"/meetups/{meetup_id}/join", headers=joiner_headers)

        resp = client.post(f"/meetups/{meetup_id}/leave", headers=joiner_headers)
        assert resp.status_code == 200
        assert "left" in resp.json()["message"].lower()

    def test_non_participant_gets_400(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()

        _, _, stranger_headers = register_and_login(
            client, username="stranger", email="stranger@example.com"
        )
        resp = client.post(f"/meetups/{created['id']}/leave", headers=stranger_headers)
        assert resp.status_code == 400
        assert "not a participant" in resp.json()["detail"].lower()

    def test_nonexistent_meetup_returns_404(self, client):
        _, _, headers = register_and_login(client)
        resp = client.post("/meetups/99999/leave", headers=headers)
        assert resp.status_code == 404


# ===================================================================
# GET PARTICIPANTS  (GET /meetups/{id}/participants)
# ===================================================================

class TestGetParticipants:
    def test_returns_list_of_participants(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers).json()
        meetup_id = created["id"]

        # Two users join
        _, _, u1_headers = register_and_login(
            client, username="user1", email="u1@example.com"
        )
        _, _, u2_headers = register_and_login(
            client, username="user2", email="u2@example.com"
        )
        client.post(f"/meetups/{meetup_id}/join", headers=u1_headers)
        client.post(f"/meetups/{meetup_id}/join", headers=u2_headers)

        resp = client.get(f"/meetups/{meetup_id}/participants")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        usernames = {p["username"] for p in data}
        assert usernames == {"user1", "user2"}

    def test_nonexistent_meetup_returns_404(self, client):
        resp = client.get("/meetups/99999/participants")
        assert resp.status_code == 404


# ===================================================================
# GET ATTENDANCE  (GET /meetups/{id}/attendance)
# ===================================================================

class TestGetAttendance:
    def test_returns_correct_attendance_info(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers, max_attendees=5).json()
        meetup_id = created["id"]

        # Two users join
        _, _, u1_headers = register_and_login(
            client, username="user1", email="u1@example.com"
        )
        _, _, u2_headers = register_and_login(
            client, username="user2", email="u2@example.com"
        )
        client.post(f"/meetups/{meetup_id}/join", headers=u1_headers)
        client.post(f"/meetups/{meetup_id}/join", headers=u2_headers)

        resp = client.get(f"/meetups/{meetup_id}/attendance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["attendees"] == 2
        assert data["capacity"] == 5
        assert data["spots_left"] == 3


# ===================================================================
# MY MEETUPS  (GET /my-meetups)
# ===================================================================

class TestMyMeetups:
    def test_returns_meetups_hosted_by_current_user(self, client):
        _, _, headers = register_and_login(client)
        create_meetup(client, headers, title="My Event")

        resp = client.get("/my-meetups", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "My Event"

    def test_does_not_include_meetups_hosted_by_others(self, client):
        # Host A creates a meetup
        _, _, host_a_headers = register_and_login(client)
        create_meetup(client, host_a_headers, title="A's Meetup")

        # Host B creates a different meetup
        _, _, host_b_headers = register_and_login(
            client, username="hostb", email="hostb@example.com"
        )
        create_meetup(client, host_b_headers, title="B's Meetup")

        # Host A should only see their own
        resp = client.get("/my-meetups", headers=host_a_headers)
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "A's Meetup"

        # Host B should only see their own
        resp = client.get("/my-meetups", headers=host_b_headers)
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "B's Meetup"


# ===================================================================
# MY JOINED MEETUPS  (GET /my-joined-meetups)
# ===================================================================

class TestMyJoinedMeetups:
    def test_returns_meetups_user_has_joined(self, client):
        _, _, host_headers = register_and_login(client)
        created = create_meetup(client, host_headers, title="Joinable Meetup").json()

        _, _, joiner_headers = register_and_login(
            client, username="joiner", email="joiner@example.com"
        )
        client.post(f"/meetups/{created['id']}/join", headers=joiner_headers)

        resp = client.get("/my-joined-meetups", headers=joiner_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Joinable Meetup"

    def test_does_not_include_meetups_user_has_not_joined(self, client):
        _, _, host_headers = register_and_login(client)
        create_meetup(client, host_headers, title="Not Joined")

        # Second user never joins
        _, _, bystander_headers = register_and_login(
            client, username="bystander", email="bystander@example.com"
        )

        resp = client.get("/my-joined-meetups", headers=bystander_headers)
        assert resp.status_code == 200
        assert resp.json() == []
