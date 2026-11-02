# KITE AI TRADER

AI-assisted Indian-market research dashboard with a manually operated workflow.

> **Important:** The chart integration uses provider-delayed data when configured. The scanner and paper ledger in this MVP still use synthetic demo data. Do not use synthetic or delayed quotes for live trade execution. No live order-placement integration is included.

## Stack
- Backend: Python 3.11+ and FastAPI
- Frontend: React, TypeScript, Vite
- Charts: TradingView Lightweight Charts (open-source chart library)
- Optional delayed data: Indian API free tier
- Indicators: RSI, EMA, VWAP and volume-ratio research heuristics
- Execution: in-memory simulated paper ledger only

## Quick start (Windows)

Backend:
```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Frontend (new terminal):
```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/docs.

## Configure the optional free delayed NSE chart

The chart adapter uses Indian API's documented delayed 1-day intraday endpoint. The endpoint returns price observations at 5-minute intervals during the session; it is a price line, not full OHLC candles. The provider does not publish an exact latency guarantee, so the UI displays the provider timestamp and calls the feed delayed rather than claiming a guaranteed 15-minute delay.

1. Create a free developer API key at https://indianapi.in/indian-stock-market. This is a data-provider account, **not a broker account**. The provider's free tier requires an API key.
2. Open backend/.env and set:
   ```dotenv
   INDIAN_API_KEY=your_private_key
   INDIAN_API_BASE_URL=https://stock.indianapi.in
   ```
3. Restart the backend. The chart checks the provider once per minute and caches a symbol response for 60 seconds to reduce API usage.

Never paste the API key into chat or commit backend/.env to GitHub. The frontend never receives the key.

If the key is not configured, the dashboard displays setup instructions instead of substituting fake chart prices.

## API endpoints
- GET /health — backend status
- GET /api/data/status — optional data-provider configuration status
- GET /api/market/{symbol}/intraday — provider-delayed 5-minute price observations
- GET /api/analysis/signals — **synthetic demo signals only**
- GET /api/paper/trades — simulated trades

## Current limitations
- Indian API's free developer plan and endpoint availability/quotas are controlled by that provider and may change.
- The delayed intraday endpoint documents price observations, not OHLCV candles. KITE does not invent open, high, low or volume values.
- The existing scanner still uses synthetic candles. Its BUY/SELL/WAIT output is explicitly labelled demo and is not actionable.
- NIFTY, SENSEX and BANK NIFTY index tiles are placeholders.
- News analysis, true OHLC candle history, persistent storage, and calibrated signal validation are not implemented yet.
- No broker connection, account credentials, or live order placement is used.

## Tests
```powershell
cd backend
python -m pytest
```
