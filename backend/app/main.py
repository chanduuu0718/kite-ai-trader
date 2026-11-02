from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .indianapi import (
    IndianApiError,
    IndianApiNotConfigured,
    get_intraday_prices,
    provider_status,
)
from .indicators import calculate_indicators, generate_signal
from .market import WATCHLIST, candles_for
from .paper import create_trade, list_trades
from .schemas import PaperTradeRequest

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Indian intraday research API. External chart data is provider-delayed; demo signals remain synthetic.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    mode = "PROVIDER_DELAYED_CONFIGURED" if settings.indian_api_key.strip() else "DEMO_SYNTHETIC"
    return {"status": "ok", "mode": mode, "time": datetime.now(timezone.utc)}


@app.get("/api/data/status")
def data_status():
    return provider_status()


@app.get("/api/market/overview")
def overview():
    return {
        "market": "INDIA",
        "data_mode": "SYNTHETIC_DEMO",
        "indices": [
            {"symbol": x, "value": 0, "change_pct": 0, "status": "NOT_CONNECTED"}
            for x in ["NIFTY 50", "SENSEX", "BANK NIFTY"]
        ],
    }


@app.get("/api/market/watchlist")
def watchlist():
    return WATCHLIST


@app.get("/api/market/{symbol}/intraday")
async def intraday_chart(symbol: str):
    normalized = symbol.upper()
    if normalized not in {item["symbol"] for item in WATCHLIST}:
        raise HTTPException(status_code=404, detail="Symbol is not in the KITE watchlist.")
    try:
        return await get_intraday_prices(normalized)
    except IndianApiNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except IndianApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/market/{symbol}/candles")
def get_candles(symbol: str, count: int = 90):
    try:
        return [item.model_dump() for item in candles_for(symbol.upper(), max(25, min(count, 300)))]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Symbol not in demo watchlist.") from exc


@app.get("/api/analysis/signals")
def signals():
    output = []
    for item in WATCHLIST:
        metrics = calculate_indicators(item["symbol"], candles_for(item["symbol"]))
        output.append({**metrics, **generate_signal(metrics), "name": item["name"], "data_mode": "SYNTHETIC_DEMO"})
    return output


@app.get("/api/paper/trades")
def trades():
    return list_trades()


@app.post("/api/paper/trades")
def new_trade(req: PaperTradeRequest):
    if req.symbol.upper() not in {item["symbol"] for item in WATCHLIST}:
        raise HTTPException(status_code=404, detail="Symbol not in watchlist.")
    try:
        return create_trade(req.symbol, req.side, req.quantity, req.reference_price)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
