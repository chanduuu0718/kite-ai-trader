# KITE AI TRADER 🇮🇳

AI-assisted Indian market research and intraday paper-trading platform. **Paper trading only** in this starter; no live orders are sent.

## MVP
- FastAPI backend with health, market overview, scanner and paper-trade endpoints
- Deterministic technical signals (EMA, RSI, VWAP) clearly labeled as rules—not AI predictions
- React dashboard with market cards, scanner, and paper portfolio
- Mock market data by default; broker adapter is intentionally not connected

## Run locally (Windows)
### Backend
```cmd
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### Frontend (new terminal)
```cmd
cd frontend
npm install
npm run dev
```
Dashboard: http://localhost:5173

## Safety
This is educational software, not financial advice. Signals are not recommendations. Verify data quality and test strategies with out-of-sample backtests before considering any live deployment. Live execution, broker credentials, and exchange-compliant algo controls are not implemented.
