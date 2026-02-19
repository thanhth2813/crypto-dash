"""Tests for Portfolio API endpoints."""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import HTTPException

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app


@pytest_asyncio.fixture
async def client():
    async def _fake_get_db():
        yield None

    app.dependency_overrides[get_db] = _fake_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def auth_header():
    """Mock JWT header for authenticated requests."""
    return {"Authorization": "Bearer fake_token_for_testing"}


@pytest.fixture
def mock_user():
    """Mock current user."""
    return SimpleNamespace(id=1, email="test@crypto.com")


# ============================================================
# POST /portfolio — Add Holding
# ============================================================


@pytest.mark.asyncio
async def test_add_holding_success(client, monkeypatch, auth_header, mock_user):
    """Test add holding returns 200 with holding data."""
    holding = SimpleNamespace(
        id=1,
        coin_id="bitcoin",
        symbol="BTC",
        amount=Decimal("0.5"),
        buy_price=Decimal("50000"),
    )

    async def _add(db, user_id, req):
        return holding

    async def mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_current_user
    monkeypatch.setattr("app.services.portfolio_service.PortfolioService.add_holding", _add)

    res = await client.post(
        "/portfolio",
        json={"coin_id": "bitcoin", "symbol": "BTC", "amount": 0.5, "buy_price": 50000},
        headers=auth_header,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["coin_id"] == "bitcoin"
    assert data["symbol"] == "BTC"
    assert data["amount"] == 0.5
    assert data["buy_price"] == 50000.0


@pytest.mark.asyncio
async def test_add_holding_negative_amount_422(client, auth_header, mock_user, monkeypatch):
    """Test add holding with negative amount returns 422."""

    async def mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_current_user

    res = await client.post(
        "/portfolio",
        json={"coin_id": "bitcoin", "symbol": "BTC", "amount": -1, "buy_price": 50000},
        headers=auth_header,
    )
    assert res.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_add_holding_unauthorized_401(client):
    """Test add holding without auth returns 401."""
    app.dependency_overrides.pop(get_current_user, None)
    res = await client.post(
        "/portfolio",
        json={"coin_id": "bitcoin", "symbol": "BTC", "amount": 0.5, "buy_price": 50000},
    )
    assert res.status_code == 401


# ============================================================
# GET /portfolio — List Holdings
# ============================================================


@pytest.mark.asyncio
async def test_list_holdings_success(client, monkeypatch, auth_header, mock_user):
    """Test list holdings returns 200 with P&L calculations."""
    holdings = [
        SimpleNamespace(
            id=1,
            coin_id="bitcoin",
            symbol="BTC",
            amount=Decimal("0.5"),
            buy_price=Decimal("50000"),
        ),
    ]

    async def _list(db, user_id):
        return holdings

    async def _prices():
        return [{"id": "bitcoin", "current_price": 60000}]

    async def mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_current_user

    monkeypatch.setattr("app.services.portfolio_service.PortfolioService.list_holdings", _list)
    # patch where it's used (imported into router module)
    monkeypatch.setattr("app.routers.portfolio.MarketService.get_top_prices", _prices)

    res = await client.get("/portfolio", headers=auth_header)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["coin_id"] == "bitcoin"
    assert data[0]["current_price"] == 60000
    assert data[0]["pnl"] == (60000 - 50000) * 0.5  # (current - buy) * amount


@pytest.mark.asyncio
async def test_list_holdings_unauthorized_401(client):
    """Test list holdings without auth returns 401."""
    app.dependency_overrides.pop(get_current_user, None)
    res = await client.get("/portfolio")
    assert res.status_code == 401


# ============================================================
# PUT /portfolio/{holding_id} — Update Holding
# ============================================================


@pytest.mark.asyncio
async def test_update_holding_success(client, monkeypatch, auth_header, mock_user):
    """Test update holding returns 200."""
    holding = SimpleNamespace(
        id=1,
        coin_id="bitcoin",
        symbol="BTC",
        amount=Decimal("1.0"),
        buy_price=Decimal("55000"),
    )

    async def _update(db, user_id, holding_id, req):
        return holding

    async def mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_current_user

    monkeypatch.setattr("app.services.portfolio_service.PortfolioService.update_holding", _update)

    res = await client.put(
        "/portfolio/1",
        json={"amount": 1.0, "buy_price": 55000},
        headers=auth_header,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["amount"] == 1.0
    assert data["buy_price"] == 55000.0


@pytest.mark.asyncio
async def test_update_holding_not_found_404(client, monkeypatch, auth_header, mock_user):
    """Test update non-existent holding returns 404."""

    async def _update(db, user_id, holding_id, req):
        raise HTTPException(status_code=404, detail="holding not found")

    async def mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_current_user

    monkeypatch.setattr("app.services.portfolio_service.PortfolioService.update_holding", _update)

    res = await client.put(
        "/portfolio/999",
        json={"amount": 1.0},
        headers=auth_header,
    )
    assert res.status_code == 404


# ============================================================
# DELETE /portfolio/{holding_id}
# ============================================================


@pytest.mark.asyncio
async def test_delete_holding_success(client, monkeypatch, auth_header, mock_user):
    """Test delete holding returns 200."""

    async def _delete(db, user_id, holding_id):
        pass  # success

    async def mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_current_user

    monkeypatch.setattr("app.services.portfolio_service.PortfolioService.delete_holding", _delete)

    res = await client.delete("/portfolio/1", headers=auth_header)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True


@pytest.mark.asyncio
async def test_delete_holding_not_found_404(client, monkeypatch, auth_header, mock_user):
    """Test delete non-existent holding returns 404."""

    async def _delete(db, user_id, holding_id):
        raise HTTPException(status_code=404, detail="holding not found")

    async def mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_current_user

    monkeypatch.setattr("app.services.portfolio_service.PortfolioService.delete_holding", _delete)

    res = await client.delete("/portfolio/999", headers=auth_header)
    assert res.status_code == 404


# ============================================================
# GET /portfolio/summary
# ============================================================


@pytest.mark.asyncio
async def test_summary_success(client, monkeypatch, auth_header, mock_user):
    """Test summary returns 200 with invested/value/pnl."""

    async def _summary(db, user_id):
        return {
            "total_invested": 50000.0,
            "total_value": 60000.0,
            "total_pnl": 10000.0,
            "allocation": [],
        }

    async def mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_current_user

    monkeypatch.setattr("app.services.portfolio_service.PortfolioService.get_summary", _summary)

    res = await client.get("/portfolio/summary", headers=auth_header)
    assert res.status_code == 200
    data = res.json()
    assert data["total_invested"] == 50000.0
    assert data["total_value"] == 60000.0
    assert data["total_pnl"] == 10000.0
