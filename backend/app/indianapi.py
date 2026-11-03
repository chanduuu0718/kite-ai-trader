"""Free-tier historical price adapter for Indian API.

This adapter implements only endpoints present in the supplied Indian Stock API
OpenAPI specification. The documented historical_data endpoint returns dated
price series; it is not a 5-minute intraday candle or streaming endpoint.
"""
from __future__ import annotations

import time
from datetime import date
from typing import Any

import httpx

from .config import settings

VALID_PERIODS = {"1m", "6m", "1yr", "3yr", "5yr", "10yr", "max"}
_CACHE_TTL_SECONDS = 300
_history_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}


class IndianApiNotConfigured(RuntimeError):
    pass


class IndianApiError(RuntimeError):
    pass


def parse_historical_values(payload: Any) -> list[dict[str, Any]]:
    """Extract the Price dataset documented by /historical_data."""
    if not isinstance(payload, dict):
        return []
    datasets = payload.get("datasets")
    if not isinstance(datasets, list):
        return []

    price_dataset = next(
        (
            item for item in datasets
            if isinstance(item, dict)
            and (
                str(item.get("metric", "")).lower() == "price"
                or "price" in str(item.get("label", "")).lower()
            )
        ),
        None,
    )
    if not isinstance(price_dataset, dict) or not isinstance(price_dataset.get("values"), list):
        return []

    points: list[dict[str, Any]] = []
    for row in price_dataset["values"]:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        try:
            day = date.fromisoformat(str(row[0])[:10])
            price = float(row[1])
        except (TypeError, ValueError, OverflowError):
            continue
        if price <= 0:
            continue
        points.append({"date": day.isoformat(), "price": round(price, 4)})

    unique = {point["date"]: point for point in points}
    return [unique[key] for key in sorted(unique)]


async def get_historical_prices(symbol: str, period: str = "1m") -> dict[str, Any]:
    """Fetch historical daily price observations from the free-tier API host."""
    if not settings.indian_api_key.strip():
        raise IndianApiNotConfigured(
            "Add your free Indian API key to backend/.env as INDIAN_API_KEY. "
            "This is a data-provider key, not a broker account."
        )
    if period not in VALID_PERIODS:
        raise IndianApiError("Unsupported history period.")

    symbol = symbol.upper().strip()
    cache_key = (symbol, period)
    now = time.monotonic()
    cached = _history_cache.get(cache_key)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    url = settings.indian_api_base_url.rstrip("/") + "/historical_data"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                params={"stock_name": symbol, "period": period, "filter": "price"},
                headers={"X-API-Key": settings.indian_api_key},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 403):
            raise IndianApiError("Indian API rejected the key or free-plan host. Check INDIAN_API_KEY.") from exc
        if exc.response.status_code == 429:
            raise IndianApiError("Indian API request quota reached. Wait before refreshing.") from exc
        raise IndianApiError("Indian API returned an HTTP error for historical data.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise IndianApiError("Could not reach Indian API or parse its historical-data response.") from exc

    points = parse_historical_values(payload)
    if not points:
        raise IndianApiError("The provider returned no historical Price dataset for this stock and period.")

    result = {
        "symbol": symbol,
        "source": "Indian API",
        "data_mode": "HISTORICAL_DAILY",
        "period": period,
        "interval": "daily historical price points",
        "delay_note": (
            "Historical daily prices from the provider. This endpoint does not provide "
            "5-minute intraday candles or a live WebSocket stream."
        ),
        "latest_date": points[-1]["date"],
        "latest_price": points[-1]["price"],
        "points": points,
        "fetched_at_epoch": int(time.time()),
        "cache_seconds": _CACHE_TTL_SECONDS,
    }
    _history_cache[cache_key] = (now, result)
    return result


def provider_status() -> dict[str, Any]:
    configured = bool(settings.indian_api_key.strip())
    return {
        "provider": "Indian API",
        "configured": configured,
        "data_mode": "HISTORICAL_API_CONFIGURED" if configured else "NOT_CONFIGURED",
        "broker_account_required": False,
        "developer_api_key_required": True,
        "documented_free_endpoint": "/historical_data",
        "message": (
            "Free-tier historical price data is configured."
            if configured
            else "A free Indian API developer key is required. No broker account is required."
        ),
    }
