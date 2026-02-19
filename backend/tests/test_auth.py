from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.services.auth_service import AuthService
from app.utils import security as sec


@pytest_asyncio.fixture
async def client():
    """ASGI client with DB dependency overridden (no real DB needed)."""

    async def _fake_get_db():
        yield None

    app.dependency_overrides[get_db] = _fake_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_register_success(client, monkeypatch):
    async def _register(*, db, req):
        user = SimpleNamespace(id=1, email=req.email)
        return "access123", "refresh123", user

    monkeypatch.setattr(AuthService, "register", staticmethod(_register))

    res = await client.post("/auth/register", json={"email": "a@b.com", "password": "12345678"})
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"] == "access123"
    assert data["refresh_token"] == "refresh123"
    assert data["user"]["email"] == "a@b.com"


@pytest.mark.asyncio
async def test_register_duplicate_email_409(client, monkeypatch):
    async def _register(*, db, req):
        raise ValueError("registration_failed")

    monkeypatch.setattr(AuthService, "register", staticmethod(_register))

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
        return "access123", "refresh123", user

    async def _rl(*, ip, email):
        return True, None

    monkeypatch.setattr(AuthService, "login", staticmethod(_login))
    monkeypatch.setattr("app.routers.auth.check_login_rate_limit", _rl)

    res = await client.post("/auth/login", json={"email": "a@b.com", "password": "12345678"})
    assert res.status_code == 200
    assert res.json()["access_token"] == "access123"
    assert res.json()["refresh_token"] == "refresh123"


@pytest.mark.asyncio
async def test_login_wrong_password_401(client, monkeypatch):
    async def _login(*, db, req):
        return None

    async def _rl(*, ip, email):
        return True, None

    monkeypatch.setattr(AuthService, "login", staticmethod(_login))
    monkeypatch.setattr("app.routers.auth.check_login_rate_limit", _rl)

    res = await client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_401(client, monkeypatch):
    async def _login(*, db, req):
        return None

    async def _rl(*, ip, email):
        return True, None

    monkeypatch.setattr(AuthService, "login", staticmethod(_login))
    monkeypatch.setattr("app.routers.auth.check_login_rate_limit", _rl)

    res = await client.post("/auth/login", json={"email": "missing@b.com", "password": "12345678"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client):
    async def mock_current_user():
        return SimpleNamespace(id=1, email="test@crypto.com")

    app.dependency_overrides[get_current_user] = mock_current_user

    token = sec.create_access_token(user_id="1", expires_minutes=60)
    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    assert res.json()["email"] == "test@crypto.com"

    app.dependency_overrides.pop(get_current_user, None)


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

    monkeypatch.setattr("app.routers.auth.check_login_rate_limit", _rl)

    res = await client.post("/auth/login", json={"email": "a@b.com", "password": "12345678"})
    assert res.status_code == 429
    assert "Retry-After" in res.headers
