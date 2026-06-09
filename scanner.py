"""
scanner.py - Background scanner for Halol Crypto AI.
Runs continuously, updates signal cache, triggers alerts.
"""

import asyncio
import logging
from typing import Optional

from config import (
    HALAL_COINS, SCAN_INTERVAL_SECONDS, DEFAULT_TIMEFRAME,
    STRONG_BUY_THRESHOLD,
)
from database import (
    cache_signal, get_users_to_notify, log_alert
)
from utils import fetch_klines, fetch_ticker
from signals import score_coin, SIGNAL_STRONG_BUY

logger = logging.getLogger(__name__)

# Reference to the running bot application (set from bot.py)
_bot_app: Optional[object] = None


def set_bot_app(app: object) -> None:
    """Pass the running telegram Application so scanner can send alerts."""
    global _bot_app
    _bot_app = app


# ──────────────────────────────────────────────
# Per-coin scan
# ──────────────────────────────────────────────

async def scan_coin(symbol: str, timeframe: str = DEFAULT_TIMEFRAME) -> Optional[dict]:
    """Fetch klines, calculate signal, cache result."""
    try:
        kline_data = await fetch_klines(symbol, timeframe)
        if not kline_data or len(kline_data["closes"]) < 50:
            logger.debug("Not enough data for %s", symbol)
            return None

        sig = score_coin(kline_data)
        sig["symbol"] = symbol

        # Enrich with live ticker
        ticker = await fetch_ticker(symbol)
        if ticker:
            sig["price"]      = float(ticker.get("lastPrice", sig["price"]))
            sig["change_24h"] = float(ticker.get("priceChangePercent", 0))
            sig["volume_24h"] = float(ticker.get("quoteVolume", 0))

        cache_signal(symbol, timeframe, sig)
        return sig

    except Exception as exc:
        logger.exception("scan_coin(%s) error: %s", symbol, exc)
        return None


# ──────────────────────────────────────────────
# Alert dispatcher
# ──────────────────────────────────────────────

async def dispatch_alerts(sig: dict) -> None:
    """Send Telegram messages to users who should be alerted."""
    if not _bot_app:
        return

    symbol = sig.get("symbol", "")
    score  = sig.get("score", 0)
    signal = sig.get("signal", "")
    smc    = sig.get("smc", {})

    async def _send(user_id: int, text: str, alert_type: str) -> None:
        try:
            await _bot_app.bot.send_message(  # type: ignore[attr-defined]
                chat_id=user_id, text=text, parse_mode="Markdown"
            )
            log_alert(user_id, symbol, alert_type, text)
        except Exception as exc:
            logger.warning("Alert send failed user=%d: %s", user_id, exc)

    # Strong Buy alert
    if signal == SIGNAL_STRONG_BUY:
        users = get_users_to_notify(symbol, "strong_buy")
        msg = (
            f"🚨 *Strong Buy Signal: {symbol}*\n"
            f"Score: {score}% | {signal}\n"
            f"Entry: {sig.get('trade_plan', {}).get('entry', '—')}\n"
            f"TP1: {sig.get('trade_plan', {}).get('tp1', '—')} | "
            f"SL: {sig.get('trade_plan', {}).get('stop_loss', '—')}"
        )
        for uid in users:
            await _send(uid, msg, "strong_buy")

    # Breakout
    if smc.get("breakout") == "breakout_up":
        users = get_users_to_notify(symbol, "breakout")
        msg = f"🚀 *Breakout Detected: {symbol}*\nPrice broke above resistance!\nScore: {score}%"
        for uid in users:
            await _send(uid, msg, "breakout")

    # Order Block
    if smc.get("order_blocks", 0) >= 2:
        users = get_users_to_notify(symbol, "order_block")
        msg = f"📦 *Order Block Confirmed: {symbol}*\n{smc['order_blocks']} bullish order blocks identified"
        for uid in users:
            await _send(uid, msg, "order_block")

    # Liquidity Sweep
    if smc.get("liquidity_sweep") == "low_sweep":
        users = get_users_to_notify(symbol, "liquidity_sweep")
        msg = f"💧 *Liquidity Sweep: {symbol}*\nLows swept — potential reversal incoming"
        for uid in users:
            await _send(uid, msg, "liquidity_sweep")


# ──────────────────────────────────────────────
# Background scan loop
# ──────────────────────────────────────────────

async def scan_all_coins(timeframe: str = DEFAULT_TIMEFRAME) -> list[dict]:
    """Scan every halal coin sequentially (rate-limit friendly)."""
    results = []
    for symbol in HALAL_COINS:
        sig = await scan_coin(symbol, timeframe)
        if sig:
            results.append(sig)
            await dispatch_alerts(sig)
        # Small sleep to avoid rate limits
        await asyncio.sleep(0.3)
    logger.info("Scan complete — %d coins analysed", len(results))
    return results


async def background_scanner() -> None:
    """Infinite loop: scan all coins then sleep."""
    logger.info("Background scanner started (interval=%ds)", SCAN_INTERVAL_SECONDS)
    while True:
        try:
            await scan_all_coins()
        except Exception as exc:
            logger.exception("Scanner loop error: %s", exc)
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)
