import pytest

from app.core.security import create_token, hash_password, verify_password
from tests.conftest import bearer, login


def test_password_hashing_roundtrip():
    hashed = hash_password("secret123")
    assert hashed.startswith("$2b$")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("x", "not-a-bcrypt-hash")


async def test_register_login_me(client):
    created = await client.post(
        "/api/v1/auth/register",
        json={"email": "Rafiq@Example.com", "password": "pass1234", "full_name": "Rafiqul Islam"},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["email"] == "rafiq@example.com" and body["is_superuser"] is False
    assert "hashed_password" not in body

    tokens = await login(client, "rafiq@example.com", "pass1234")
    assert tokens["token_type"] == "bearer" and tokens["expires_in"] == 300
    me = await client.get("/api/v1/auth/me", headers=bearer(tokens))
    assert me.status_code == 200 and me.json()["full_name"] == "Rafiqul Islam"


async def test_register_duplicate_and_weak_password(client, user):
    dup = await client.post(
        "/api/v1/auth/register", json={"email": "akib@example.com", "password": "pass1234"}
    )
    assert dup.status_code == 409
    weak = await client.post(
        "/api/v1/auth/register", json={"email": "x@example.com", "password": "12345678"}
    )
    assert weak.status_code == 422
    assert "mix letters and digits" in weak.text
    short = await client.post(
        "/api/v1/auth/register", json={"email": "x@example.com", "password": "ab1"}
    )
    assert short.status_code == 422


async def test_login_rejects_bad_credentials_and_inactive(client, user, app):
    bad = await client.post(
        "/api/v1/auth/login", json={"email": "akib@example.com", "password": "nope"}
    )
    assert bad.status_code == 401 and bad.headers["WWW-Authenticate"] == "Bearer"
    unknown = await client.post(
        "/api/v1/auth/login", json={"email": "ghost@example.com", "password": "x"}
    )
    assert unknown.status_code == 401
    async with app.state.session_factory() as db:
        db_user = await db.get(type(user), user.id)
        db_user.is_active = False
        await db.commit()
    inactive = await client.post(
        "/api/v1/auth/login", json={"email": "akib@example.com", "password": "secret123"}
    )
    assert inactive.status_code == 401


@pytest.mark.parametrize("header", [None, "Bearer not-a-token", "Basic abc"])
async def test_me_requires_valid_access_token(client, header):
    headers = {"Authorization": header} if header else {}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


async def test_refresh_token_cannot_be_used_as_access_token(client, user):
    tokens = await login(client, "akib@example.com", "secret123")
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert response.status_code == 401
    assert "expected a access token" in response.json()["detail"]


async def test_refresh_rotates_and_revokes_old_token(client, user):
    tokens = await login(client, "akib@example.com", "secret123")
    rotated = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert rotated.status_code == 200
    new_tokens = rotated.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert (await client.get("/api/v1/auth/me", headers=bearer(new_tokens))).status_code == 200

    reused = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reused.status_code == 401 and reused.json()["detail"] == "refresh token revoked"


async def test_logout_revokes_refresh_token(client, user):
    tokens = await login(client, "akib@example.com", "secret123")
    out = await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert out.status_code == 200
    denied = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert denied.status_code == 401
    garbage = await client.post("/api/v1/auth/logout", json={"refresh_token": "garbage"})
    assert garbage.status_code == 200


async def test_expired_token_is_rejected(client, user, settings):
    expired_settings = settings.model_copy(update={"access_token_expire_minutes": -1})
    token, _ = create_token(str(user.id), "access", expired_settings)
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401 and response.json()["detail"] == "token expired"
