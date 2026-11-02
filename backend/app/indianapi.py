"""Free-tier delayed intraday data adapter for Indian API.

The provider documents 5-minute intraday price points as delayed. It does not
publish an exact latency guarantee, so callers must use provider timestamps.
This module never places or modifies orders.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from .config import settings

IST = ZoneInfo("Asia/Kolkata")
_CACHE_TTL_SECONDS = 60
_stock_ids: dict[str, str] | None = None
_stock_ids_lock = asyncio.Lock()
_intraday_cache: dict[str, tuple[float, dict[str, Any]]] = {}


class IndianApiNotConfigured(RuntimeError):
    pass


class IndianApiError(RuntimeError):
    pass


def parse_intraday_values(payload: Any) -> list[dict[str, Any]]:
    """Normalize the documented [timeStamp, price] series into chart points."""
    entries: list[dict[str, Any]] = []

    containers = payload if isinstance(payload, list) else [payload]
    for container in containers:
        if not isinstance(container, dict):
            continue
        values = container.get("values")
        if not isinstance(values, list):
            continue
        for item in values:
            if isinstance(item, dict):
                raw_time = item.get("timeStamp") or item.get("timestamp") or item.get("time")
                raw_price = item.get("price") or item.get("close") or item.get("value")
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                raw_time, raw_price = item[0], item[1]
            else:
                continue
            try:
                if isinstance(raw_time, (int, float)):
                    stamp = datetime.fromtimestamp(float(raw_time), tz=IST)
                else:
                    stamp = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
                    if stamp.tzinfo is None:
                        stamp = stamp.replace(tzinfo=IST)
                    else:
                        stamp = stamp.astimezone(IST)
                price = float(raw_price)
                if price <= 0:
                    continue
            except (TypeError, ValueError, OverflowError):
                continue
            entries.append({
                "time": int(stamp.timestamp()),
                "timestamp_ist": stamp.isoformat(),
                "price": round(price, 4),
            })

    # Keep one observation per timestamp and return ascending time order.
    unique = {point["time"]: point for point in entries}
    return [unique[key] for key in sorted(unique)]


async def _get_stock_ids() -> dict[str, str]:
    global _stock_ids
    if _stock_ids is not None:
        return _stock_ids

    async with _stock_ids_lock:
        if _stock_ids is not None:
            return _stock_ids
        url = settings.indian_api_symbols_url
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            # Some free-plan hosts may not expose the static catalogue. The
            # per-symbol industry-search fallback below handles that case.
            payload = []

        rows = payload if isinstance(payload, list) else (payload.get("stocks", []) if isinstance(payload, dict) else [])
        mapping: dict[str, str] = {}
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                symbol = row.get("nse-code") or row.get("nse_code") or row.get("exchangeCodeNsi")
                stock_id = row.get("id") or row.get("stock_id") or row.get("stockId")
                if symbol and stock_id:
                    mapping[str(symbol).upper()] = str(stock_id)
        _stock_ids = mapping
        return mapping


async def _lookup_stock_id(symbol: str) -> str | None:
    """Fallback for providers that do not expose the static symbol catalogue."""
    url = settings.indian_api_base_url.rstrip("/") + "/industry_search"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                url,
                params={"query": symbol},
                headers={"X-API-Key": settings.indian_api_key},
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    rows = payload if isinstance(payload, list) else (payload.get("results", []) if isinstance(payload, dict) else [])
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        found_symbol = row.get("nse-code") or row.get("nse_code") or row.get("exchangeCodeNsi")
        found_id = row.get("id") or row.get("stock_id") or row.get("stockId")
        if str(found_symbol or "").upper() == symbol.upper() and found_id:
            return str(found_id)
    return None


async def get_intraday_prices(symbol: str) -> dict[str, Any]:
    """Fetch provider-delayed 5-minute intraday prices for one NSE symbol."""
    if not settings.indian_api_key.strip():
        raise IndianApiNotConfigured(
            "Add a free Indian API key to backend/.env as INDIAN_API_KEY. "
            "This is a data-provider developer key, not a broker account."
        )

    symbol = symbol.upper().strip()
    cached = _intraday_cache.get(symbol)
    now = time.monotonic()
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    mapping = await _get_stock_ids()
    stock_id = mapping.get(symbol) or await _lookup_stock_id(symbol)
    if not stock_id:
        raise IndianApiError("Could not resolve this NSE symbol to a provider stock ID.")

    url = settings.indian_api_base_url.rstrip("/") + "/1D_intraday_data"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                url,
                params={"stock_id": stock_id},
                headers={"X-API-Key": settings.indian_api_key},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in (401, 403):
            raise IndianApiError("Indian API rejected the key or the free-plan endpoint. Check INDIAN_API_KEY.") from exc
        if status == 429:
            raise IndianApiError("Indian API rate limit reached. Wait before refreshing again.") from exc
        raise IndianApiError("Indian API returned an HTTP error while fetching intraday data.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise IndianApiError("Could not reach Indian API or parse its response.") from exc

    points = parse_intraday_values(payload)
    if not points:
        raise IndianApiError("The provider returned no intraday points for this symbol today.")
    latest = points[-1]
    result = {
        "symbol": symbol,
        "source": "Indian API",
        "data_mode": "PROVIDER_DELAYED",
        "interval": "5-minute price observations",
        "delay_note": "The provider describes this endpoint as delayed intraday data; its exact delay is not specified.",
        "timezone": "Asia/Kolkata",
        "latest_timestamp_ist": latest["timestamp_ist"],
        "latest_price": latest["price"],
        "points": points,
        "fetched_at_ist": datetime.now(IST).isoformat(),
        "refresh_interval_seconds": _CACHE_TTL_SECONDS,
    }
    _intraday_cache[symbol] = (now, result)
    return result


def provider_status() -> dict[str, Any]:
    configured = bool(settings.indian_api_key.strip())
    return {
        "provider": "Indian API",
        "configured": configured,
        "data_mode": "PROVIDER_DELAYED" if configured else "NOT_CONFIGURED",
        "broker_account_required": False,
        "developer_api_key_required": True,
        "message": (
            "Free-tier delayed intraday data is configured."
            if configured
            else "A free Indian API developer key is needed. No broker account is required."
        ),
    }
