# KITE AI TRADER

AI-assisted Indian-market intraday research and paper-trading platform.

> **Safety:** This milestone is research and paper-trading only. It does not place live orders or connect to a broker. Demo prices are synthetic and must not be used for real trading decisions.

## Stack
- Backend: Python 3.11+ and FastAPI
- Frontend: React, TypeScript, Vite
- Initial universe: configurable NSE cash-market watchlist
- Signals: EMA trend, RSI, VWAP, volume confirmation (educational heuristics)
- Execution: simulated paper ledger only

## Quick start (Windows)

Backend:
```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

Frontend (new terminal):
```powershell
cd frontend
npm install
npm run dev
```
Open the Vite URL, normally http://localhost:5173.

Copy `backend/.env.example` to `backend/.env` if changing settings. Never commit keys, tokens, or .env files.

## Current milestone
- Health, market overview, and watchlist endpoints
- Deterministic synthetic demo candles
- RSI, EMA, VWAP, volume-ratio indicators
- Rule-based BUY/SELL/WAIT research signals
- In-memory simulated paper trades
- React dashboard for signals and paper positions

## Planned
Real broker market-data adapters, persistent storage, news ingestion, ML forecasting, event-driven backtesting, and broker order execution. Each requires separate validation and safety controls. Broker integration will remain disabled by default and follow applicable broker/exchange requirements.

## Tests
```powershell
cd backend
python -m pytest
```
