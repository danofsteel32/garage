import pytest


@pytest.mark.asyncio
async def test_dashboard(app):
    client = app.test_client()
    response = await client.get("/garage/status")
    assert response.status_code == 200
    data = await response.data
    assert "<!doctype html>" in data.decode("utf-8")


@pytest.mark.asyncio
async def test_post_status(app):
    client = app.test_client()
    data = {"message": 50.0}
    bad_data = {"message": "kitty cat"}
    bad_headers = {"X-Api-Key": "badkey"}
    good_headers = {"X-Api-Key": "testkey"}
    no_key = await client.post("/garage/status", json=data)
    assert no_key.status_code == 401
    bad_key = await client.post("/garage/status", json=data, headers=bad_headers)
    assert bad_key.status_code == 401
    good_key = await client.post("/garage/status", json=data, headers=good_headers)
    assert good_key.status_code == 200
    bad_post = await client.post("/garage/status", json=bad_data, headers=good_headers)
    assert bad_post.status_code == 400


@pytest.mark.asyncio
async def test_sse(app):
    client = app.test_client()
    post_headers = {"X-Api-Key": "testkey"}
    accept_headers = {
        "Content-Type": "text/event-stream",
        "Accept": "text/event-stream, text/html",
        "Keep-Alive": "timeout=2, max=2",
    }
    post_data = {"message": 500.0}
    async with client.request("/garage/sse", headers=accept_headers) as connection:
        await client.post("/garage/status", json=post_data, headers=post_headers)
        data = await connection.receive()
        assert "500.0" in data.decode("utf-8")
        await connection.disconnect()
