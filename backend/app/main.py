from datetime import datetime, timezone
import xml.etree.ElementTree as ET

import httpx

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .indianapi import (
    IndianApiError,
    IndianApiNotConfigured,
    VALID_PERIODS,
    get_historical_prices,
    provider_status,
)
from .indicators import calculate_indicators, generate_signal
from .market import WATCHLIST, candles_for
from .paper import create_trade, list_trades
from .schemas import PaperTradeRequest

app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="Indian-market research API. Free-tier chart data is historical daily pricing; demo signals remain synthetic.",
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
    mode = "HISTORICAL_API_CONFIGURED" if settings.indian_api_key.strip() else "DEMO_SYNTHETIC"
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




@app.get("/api/market/live")
async def live_market():
    """Delayed live NSE batch quote snapshot (requires Indian API developer key)."""
    if not settings.indian_api_key.strip():
        raise HTTPException(status_code=503, detail="Configure INDIAN_API_KEY in backend/.env for real delayed NSE quotes.")
    symbols = [item["symbol"] for item in WATCHLIST]
    url = settings.indian_api_base_url.rstrip("/") + "/nse_stock_batch_live_price"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json={"stock_symbols": symbols}, headers={"X-API-Key": settings.indian_api_key})
            response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("stocks", payload.get("results", [])))
        if isinstance(payload, dict):
            payload = [dict(value, symbol=key) if isinstance(value, dict) else {"symbol": key, "ltp": value} for key, value in payload.items()]
        if not isinstance(payload, list):
            raise ValueError("Unexpected quote response")
        return {"source":"Indian API delayed live quotes", "data_mode":"DELAYED_LIVE", "fetched_at":datetime.now(timezone.utc), "quotes":payload}
    except httpx.HTTPStatusError as exc:
        code=exc.response.status_code
        message="Indian API rejected the key." if code in (401,403) else "Indian API quota reached." if code==429 else "Indian API quote request failed."
        raise HTTPException(status_code=502, detail=message) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Live quote provider unavailable or returned an unexpected response.") from exc

@app.get("/api/market/watchlist")
def watchlist():
    return WATCHLIST


@app.get("/api/crypto/market")
async def crypto_market():
    """Aggregated BTC/ETH INR market snapshots from CoinGecko (cached by provider)."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "inr", "ids": "bitcoin,ethereum", "price_change_percentage": "24h"}
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(url, params=params, headers={"User-Agent": "KITE-AI-Trader/0.1"})
            response.raise_for_status()
        payload = response.json()
        return [
            {
                "id": coin["id"], "symbol": coin["symbol"].upper(), "name": coin["name"],
                "price": coin.get("current_price"), "change_24h": coin.get("price_change_percentage_24h"),
                "market_cap": coin.get("market_cap"), "volume_24h": coin.get("total_volume"),
                "high_24h": coin.get("high_24h"), "low_24h": coin.get("low_24h"),
                "last_updated": coin.get("last_updated"),
            } for coin in payload
        ]
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail="CoinGecko crypto market feed is temporarily unavailable.") from exc


@app.get("/api/crypto/news")
async def crypto_news():
    """Latest CoinDesk RSS headlines for the crypto research panel."""
    feed_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(feed_url, headers={"User-Agent": "KITE-AI-Trader/0.1"})
            response.raise_for_status()
        root = ET.fromstring(response.text)
        items = []
        for item in root.findall(".//item")[:12]:
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            published = item.findtext("pubDate", default="").strip()
            if title and link:
                items.append({"title": title, "link": link, "published": published, "source": "CoinDesk"})
        return items
    except (httpx.HTTPError, ET.ParseError) as exc:
        raise HTTPException(status_code=502, detail="Crypto news feed is temporarily unavailable.") from exc


@app.get("/api/market/{symbol}/history")
async def historical_chart(
    symbol: str,
    period: str = Query(default="1m", description="Lookback period: 1m means one month, not one minute."),
):
    normalized = symbol.upper()
    if normalized not in {item["symbol"] for item in WATCHLIST}:
        raise HTTPException(status_code=404, detail="Symbol is not in the KITE watchlist.")
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=422, detail=f"Period must be one of: {', '.join(sorted(VALID_PERIODS))}.")
    try:
        return await get_historical_prices(normalized, period)
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
