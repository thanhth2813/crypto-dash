# Crypto Dash 🚀

A web-based crypto trading dashboard with real-time prices, portfolio tracking, price alerts, and trading signals.

## Features

- **Real-time Prices**: Live prices of top 20 coins (BTC, ETH, SOL, etc.)
- **Portfolio Tracker**: Track holdings, buy price, current P&L per coin and total
- **Price Alerts**: Set alerts (e.g. BTC > 100k), stored in DB, checked periodically
- **Trading Signals**: RSI + EMA crossover signals — BUY/SELL/HOLD per coin
- **Dashboard**: Candlestick charts, portfolio allocation pie chart, P&L trend line
- **Auth**: User login/register with JWT

## Tech Stack

- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: React + TailwindCSS
- **Infrastructure**: Docker + Nginx (single VPS)
- **External API**: CoinGecko / Binance public API

## Project Structure

```
crypto-dash/
├── docker-compose.yml
├── nginx/
├── backend/          # FastAPI
│   ├── app/
│   │   ├── routers/  # auth, market, portfolio, alerts, signals
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── jobs/     # Background/cron tasks
│   └── alembic/      # DB migrations
└── frontend/         # React + TailwindCSS
    └── src/
        ├── pages/
        ├── components/
        ├── hooks/
        └── services/
```

## Team

- **Cyber** (@num_cyber_bot) — Solution Architect / Tech Lead / DevOps
- **Codex** (@bothothui_bot) — Implementation Specialist (Backend + Frontend)
- **Sonnet** (@num_blum_bot) — QA Lead + Frontend Support

## License

MIT
