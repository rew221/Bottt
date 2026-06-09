"""
utils.py - Shared helpers for Halol Crypto AI.
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

import aiohttp

from config import (
    BINANCE_BASE_URL, COINGECKO_BASE_URL,
    KLINE_LIMIT, DEFAULT_TIMEFRAME,
    BINANCE_SYMBOLS, COINGECKO_IDS,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Simple in-memory cache
# ──────────────────────────────────────────────

_cache: dict[str, tuple[Any, float]] = {}


def cache_get(key: str, ttl: int = 60) -> Optional[Any]:
    if key in _cache:
        value, ts = _cache[key]
        if time.time() - ts < ttl:
            return value
    return None


def cache_set(key: str, value: Any) -> None:
    _cache[key] = (value, time.time())


# ──────────────────────────────────────────────
# HTTP helpers with retry
# ──────────────────────────────────────────────

async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: Optional[dict] = None,
    retries: int = 3,
    backoff: float = 1.5,
) -> Optional[Any]:
    """GET JSON with exponential backoff retry."""
    for attempt in range(retries):
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("HTTP %d for %s (attempt %d)", resp.status, url, attempt + 1)
        except asyncio.TimeoutError:
            logger.warning("Timeout for %s (attempt %d)", url, attempt + 1)
        except Exception as exc:
            logger.warning("Request error %s (attempt %d): %s", url, attempt + 1, exc)
        if attempt < retries - 1:
            await asyncio.sleep(backoff ** attempt)
    return None


# ──────────────────────────────────────────────
# Binance public API helpers
# ──────────────────────────────────────────────

async def fetch_klines(
    symbol: str,
    interval: str = DEFAULT_TIMEFRAME,
    limit: int = KLINE_LIMIT,
) -> Optional[dict]:
    """
    Fetch OHLCV klines from Binance.
    Returns dict with opens/highs/lows/closes/volumes lists.
    """
    binance_symbol = BINANCE_SYMBOLS.get(symbol.upper(), f"{symbol.upper()}USDT")
    url = f"{BINANCE_BASE_URL}/klines"
    params = {"symbol": binance_symbol, "interval": interval, "limit": limit}

    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url, params)

    if not data:
        return None

    opens   = [float(k[1]) for k in data]
    highs   = [float(k[2]) for k in data]
    lows    = [float(k[3]) for k in data]
    closes  = [float(k[4]) for k in data]
    volumes = [float(k[5]) for k in data]

    return {
        "opens": opens, "highs": highs,
        "lows": lows, "closes": closes, "volumes": volumes,
    }


async def fetch_ticker(symbol: str) -> Optional[dict]:
    """Fetch 24h ticker stats from Binance."""
    binance_symbol = BINANCE_SYMBOLS.get(symbol.upper(), f"{symbol.upper()}USDT")
    cache_key = f"ticker_{binance_symbol}"
    cached = cache_get(cache_key, ttl=30)
    if cached:
        return cached

    url = f"{BINANCE_BASE_URL}/ticker/24hr"
    params = {"symbol": binance_symbol}
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url, params)

    if data:
        cache_set(cache_key, data)
    return data


async def fetch_market_overview() -> dict:
    """Fetch top tickers for market overview."""
    cache_key = "market_overview"
    cached = cache_get(cache_key, ttl=60)
    if cached:
        return cached

    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
               "ADAUSDT", "DOGEUSDT", "LINKUSDT", "TONUSDT", "AVAXUSDT"]
    url = f"{BINANCE_BASE_URL}/ticker/24hr"

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_json(session, url, {"symbol": s}) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    tickers = []
    for r in results:
        if isinstance(r, dict) and "symbol" in r:
            tickers.append({
                "symbol": r["symbol"].replace("USDT", ""),
                "price": float(r.get("lastPrice", 0)),
                "change_pct": float(r.get("priceChangePercent", 0)),
                "volume": float(r.get("quoteVolume", 0)),
            })

    gainers = sorted(tickers, key=lambda x: x["change_pct"], reverse=True)[:5]
    losers  = sorted(tickers, key=lambda x: x["change_pct"])[:5]
    by_vol  = sorted(tickers, key=lambda x: x["volume"], reverse=True)[:5]

    btc = next((t for t in tickers if t["symbol"] == "BTC"), None)
    eth = next((t for t in tickers if t["symbol"] == "ETH"), None)

    total_up = sum(1 for t in tickers if t["change_pct"] > 0)
    sentiment = "Bullish" if total_up >= 6 else ("Bearish" if total_up <= 3 else "Neutral")

    result = {
        "btc": btc,
        "eth": eth,
        "sentiment": sentiment,
        "gainers": gainers,
        "losers": losers,
        "volume_leaders": by_vol,
    }
    cache_set(cache_key, result)
    return result


# ──────────────────────────────────────────────
# Format helpers
# ──────────────────────────────────────────────

def format_price(price: float) -> str:
    if price >= 1000:
        return f"${price:,.2f}"
    if price >= 1:
        return f"${price:,.4f}"
    return f"${price:.6f}"


def format_change(pct: float) -> str:
    arrow = "📈" if pct >= 0 else "📉"
    sign = "+" if pct >= 0 else ""
    return f"{arrow} {sign}{pct:.2f}%"


def format_volume(vol: float) -> str:
    if vol >= 1_000_000_000:
        return f"${vol / 1_000_000_000:.2f}B"
    if vol >= 1_000_000:
        return f"${vol / 1_000_000:.2f}M"
    return f"${vol:,.0f}"


def coin_emoji(symbol: str) -> str:
    emojis = {
        "BTC": "₿", "ETH": "⟠", "BNB": "🔶", "SOL": "◎",
        "XRP": "💧", "ADA": "🌊", "DOGE": "🐕", "LINK": "🔗",
        "TON": "💎", "AVAX": "🔺", "DOT": "⚫", "MATIC": "🟣",
    }
    return emojis.get(symbol.upper(), "🪙")


def paginate(items: list, page: int, page_size: int = 9) -> tuple[list, int]:
    """Return (page_items, total_pages)."""
    total = math.ceil(len(items) / page_size)
    start = page * page_size
    return items[start: start + page_size], max(1, total)


import math
