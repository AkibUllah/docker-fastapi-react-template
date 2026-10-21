from app import __version__


async def test_live(client):
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


async def test_ready_checks_database_and_redis(client):
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "redis": "ok"}


async def test_request_id_is_generated_or_propagated(client):
    generated = await client.get("/api/v1/health/live")
    assert len(generated.headers["X-Request-ID"]) == 32
    echoed = await client.get("/api/v1/health/live", headers={"X-Request-ID": "trace-123"})
    assert echoed.headers["X-Request-ID"] == "trace-123"


async def test_openapi_served_under_api_prefix(client):
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/auth/login" in paths and "/api/v1/users" in paths
