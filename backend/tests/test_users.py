import uuid

from tests.conftest import bearer, login


async def test_list_users_requires_superuser(client, user_headers, admin_headers, user, superuser):
    forbidden = await client.get("/api/v1/users", headers=user_headers)
    assert forbidden.status_code == 403
    page = await client.get("/api/v1/users?limit=1", headers=admin_headers)
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 2 and len(body["items"]) == 1 and body["limit"] == 1
    page2 = await client.get("/api/v1/users?limit=1&offset=1", headers=admin_headers)
    assert page2.json()["items"][0]["email"] != body["items"][0]["email"]
    assert (await client.get("/api/v1/users?limit=0", headers=admin_headers)).status_code == 422


async def test_superuser_creates_user_and_handles_duplicates(client, admin_headers):
    created = await client.post(
        "/api/v1/users",
        json={
            "email": "ops@example.com",
            "password": "ops12345",
            "full_name": "Ops",
            "is_superuser": True,
        },
        headers=admin_headers,
    )
    assert created.status_code == 201 and created.json()["is_superuser"] is True
    dup = await client.post(
        "/api/v1/users",
        json={"email": "ops@example.com", "password": "ops12345"},
        headers=admin_headers,
    )
    assert dup.status_code == 409


async def test_user_can_read_and_update_self_only(client, user_headers, user, superuser):
    me = await client.get(f"/api/v1/users/{user.id}", headers=user_headers)
    assert me.status_code == 200 and me.json()["email"] == "akib@example.com"
    other = await client.get(f"/api/v1/users/{superuser.id}", headers=user_headers)
    assert other.status_code == 403

    updated = await client.patch(
        f"/api/v1/users/{user.id}",
        json={"full_name": "A. Jafor", "password": "newpass99"},
        headers=user_headers,
    )
    assert updated.status_code == 200 and updated.json()["full_name"] == "A. Jafor"
    assert (await login(client, "akib@example.com", "newpass99"))["access_token"]

    escalate = await client.patch(
        f"/api/v1/users/{user.id}", json={"is_superuser": True}, headers=user_headers
    )
    assert escalate.status_code == 403
    others = await client.patch(
        f"/api/v1/users/{superuser.id}", json={"full_name": "x"}, headers=user_headers
    )
    assert others.status_code == 403


async def test_superuser_updates_and_deletes_others_not_self(
    client, admin_headers, user, superuser
):
    promote = await client.patch(
        f"/api/v1/users/{user.id}",
        json={"is_superuser": True, "is_active": False},
        headers=admin_headers,
    )
    assert promote.status_code == 200
    assert promote.json()["is_superuser"] is True and promote.json()["is_active"] is False

    conflict = await client.patch(
        f"/api/v1/users/{user.id}", json={"email": "admin@example.com"}, headers=admin_headers
    )
    assert conflict.status_code == 409

    self_delete = await client.delete(f"/api/v1/users/{superuser.id}", headers=admin_headers)
    assert self_delete.status_code == 400
    deleted = await client.delete(f"/api/v1/users/{user.id}", headers=admin_headers)
    assert deleted.status_code == 204
    assert (await client.get(f"/api/v1/users/{user.id}", headers=admin_headers)).status_code == 404
    assert (
        await client.delete(f"/api/v1/users/{uuid.uuid4()}", headers=admin_headers)
    ).status_code == 404


async def test_user_cannot_delete(client, user_headers, superuser):
    response = await client.delete(f"/api/v1/users/{superuser.id}", headers=user_headers)
    assert response.status_code == 403


async def test_deleted_user_token_stops_working(client, admin_headers, user):
    tokens = await login(client, "akib@example.com", "secret123")
    await client.delete(f"/api/v1/users/{user.id}", headers=admin_headers)
    response = await client.get("/api/v1/auth/me", headers=bearer(tokens))
    assert response.status_code == 401
