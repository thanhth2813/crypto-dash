from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest_asyncio

from app.main import app
from app.utils import security as sec


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_register_success(client, monkeypatch):
    async def _register(*, db, req):
        user = SimpleNamespace(id=1, email=req.email)
        return "token123", user

    monkeypatch.setattr("app.services.auth_service.AuthService.register", staticmethod(_register))

    res = await client.post("/auth/register", json={"email": "a@b.com", "password": "12345678"})
    assert res.status_code == 200
    data = res.json()
    assert data["token"] == "token123"
    assert data["user"]["email"] == "a@b.com"


@pytest.mark.asyncio
async def test_register_duplicate_email_409(client, monkeypatch):
    async def _register(*, db, req):
        raise ValueError("registration_failed")

    monkeypatch.setattr("app.services.auth_service.AuthService.register", staticmethod(_register))

    res = await client.post("/auth/register", json={"email": "dup@b.com", "password": "12345678"})
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password_422(client):
    res = await client.post("/auth/register", json={"email": "a@b.com", "password": "123"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, monkeypatch):
    async def _login(*, db, req):
        user = SimpleNamespace(id=1, email=req.email)
        return "token123", user

    async def _rl(*, ip, email):
        return True, None

    monkeypatch.setattr("app.services.auth_service.AuthService.login", staticmethod(_login))
    monkeypatch.setattr("app.utils.redis.check_login_rate_limit", _rl)

    res = await client.post("/auth/login", json={"email": "a@b.com", "password": "12345678"})
    assert res.status_code == 200
    assert res.json()["token"] == "token123"


@pytest.mark.asyncio
async def test_login_wrong_password_401(client, monkeypatch):
    async def _login(*, db, req):
        return None

    async def _rl(*, ip, email):
        return True, None

    monkeypatch.setattr("app.services.auth_service.AuthService.login", staticmethod(_login))
    monkeypatch.setattr("app.utils.redis.check_login_rate_limit", _rl)

    res = await client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_401(client, monkeypatch):
    async def _login(*, db, req):
        return None

    async def _rl(*, ip, email):
        return True, None

    monkeypatch.setattr("app.services.auth_service.AuthService.login", staticmethod(_login))
    monkeypatch.setattr("app.utils.redis.check_login_rate_limit", _rl)

    res = await client.post("/auth/login", json={"email": "missing@b.com", "password": "12345678"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client, monkeypatch):
    token = sec.create_access_token(user_id="1", expires_minutes=60)

    async def _get_user_by_id(*, db, user_id: int):
        return SimpleNamespace(id=user_id, email="a@b.com")

    monkeypatch.setattr("app.services.auth_service.AuthService.get_user_by_id", staticmethod(_get_user_by_id))

    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "a@b.com"


@pytest.mark.asyncio
async def test_me_without_token_401(client):
    res = await client.get("/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_expired_token_401(client):
    token = sec.create_access_token(user_id="1", expires_minutes=-1)
    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_429(client, monkeypatch):
    async def _rl(*, ip, email):
        return False, 60

    monkeypatch.setattr("app.utils.redis.check_login_rate_limit", _rl)

    res = await client.post("/auth/login", json={"email": "a@b.com", "password": "12345678"})
    assert res.status_code == 429
    assert "Retry-After" in res.headers
