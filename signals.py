"""
signals.py - Signal engine for Halol Crypto AI.
Combines all indicators into a 0-100 score and classifies the result.
HALAL SPOT ONLY — no sell/short signals ever generated.
"""

import logging
import math
from typing import Optional

from indicators import (
    ema, rsi, macd, atr, bollinger_bands, adx,
    support_resistance, volume_analysis,
    detect_order_blocks, detect_fvg, detect_bos,
    detect_choch, detect_liquidity_sweep, detect_breakout_retest,
    detect_premium_discount, detect_market_structure_shift,
)
from config import (
    STRONG_BUY_THRESHOLD, BUY_THRESHOLD, PROFIT_ZONE_THRESHOLD,
    DEFAULT_STOP_LOSS_PCT, TP1_MULTIPLIER, TP2_MULTIPLIER, TP3_MULTIPLIER,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Signal type constants
# ──────────────────────────────────────────────
SIGNAL_STRONG_BUY = "🟢 Strong Buy"
SIGNAL_BUY = "🟢 Buy"
SIGNAL_WAIT = "🟡 Wait"
SIGNAL_PROFIT_ZONE = "💰 Profit Taking Zone"


def classify_signal(score: float, extended: bool = False) -> str:
    """Map numeric score to halal signal label."""
    if extended and score >= PROFIT_ZONE_THRESHOLD:
        return SIGNAL_PROFIT_ZONE
    if score >= STRONG_BUY_THRESHOLD:
        return SIGNAL_STRONG_BUY
    if score >= BUY_THRESHOLD:
        return SIGNAL_BUY
    return SIGNAL_WAIT


# ──────────────────────────────────────────────
# Trade plan calculator
# ──────────────────────────────────────────────

def calculate_trade_plan(
    current_price: float,
    atr_value: float,
    signal_type: str,
    sr: dict[str, float],
) -> dict:
    """Generate entry, SL, TP1/2/3 and R:R ratio."""
    stop_pct = DEFAULT_STOP_LOSS_PCT
    entry = current_price
    sl_distance = max(atr_value * 1.5, entry * stop_pct)
    stop_loss = entry - sl_distance

    # Clamp SL above support when possible
    if sr["support"] > stop_loss and sr["support"] < entry * 0.99:
        stop_loss = sr["support"] * 0.998

    sl_dist = entry - stop_loss
    tp1 = entry + sl_dist * TP1_MULTIPLIER
    tp2 = entry + sl_dist * TP2_MULTIPLIER
    tp3 = entry + sl_dist * TP3_MULTIPLIER

    rr = round(sl_dist * TP2_MULTIPLIER / sl_dist, 2) if sl_dist > 0 else 0

    def fmt(v: float) -> str:
        if v >= 1:
            return f"${v:,.4f}"
        return f"${v:.6f}"

    return {
        "entry": fmt(entry),
        "stop_loss": fmt(stop_loss),
        "tp1": fmt(tp1),
        "tp2": fmt(tp2),
        "tp3": fmt(tp3),
        "rr_ratio": f"1:{rr}",
    }


# ──────────────────────────────────────────────
# Core scoring engine
# ──────────────────────────────────────────────

def score_coin(kline_data: dict) -> dict:
    """
    kline_data: {
        'opens': [...], 'highs': [...], 'lows': [...],
        'closes': [...], 'volumes': [...]
    }
    Returns full signal dict.
    """
    opens   = kline_data["opens"]
    highs   = kline_data["highs"]
    lows    = kline_data["lows"]
    closes  = kline_data["closes"]
    volumes = kline_data["volumes"]

    if len(closes) < 50:
        return _empty_signal()

    score = 0
    max_score = 0
    details: list[str] = []
    bullish_factors: list[str] = []
    caution_factors: list[str] = []

    current = closes[-1]

    # ── EMA trend (20/50/200) ──────────────────
    ema20_s  = ema(closes, 20)
    ema50_s  = ema(closes, 50)
    ema200_s = ema(closes, 200) if len(closes) >= 200 else [None] * len(closes)

    e20 = next((v for v in reversed(ema20_s) if v is not None), None)
    e50 = next((v for v in reversed(ema50_s) if v is not None), None)
    e200 = next((v for v in reversed(ema200_s) if v is not None), None)

    if e20 and e50:
        max_score += 10
        if e20 > e50:
            score += 10
            bullish_factors.append("EMA20 > EMA50 (bullish)")
        else:
            caution_factors.append("EMA20 < EMA50")

    if e50 and e200:
        max_score += 10
        if e50 > e200:
            score += 10
            bullish_factors.append("EMA50 > EMA200 (golden zone)")

    if e20 and current > e20:
        max_score += 5
        score += 5
        bullish_factors.append("Price above EMA20")

    # ── RSI ───────────────────────────────────
    rsi_vals = rsi(closes)
    rsi_val = next((v for v in reversed(rsi_vals) if v is not None), 50.0)
    max_score += 15
    if 40 <= rsi_val <= 60:
        score += 10
        details.append(f"RSI {rsi_val:.1f} (neutral zone)")
    elif 30 <= rsi_val < 40:
        score += 15
        bullish_factors.append(f"RSI {rsi_val:.1f} (oversold recovery)")
    elif rsi_val < 30:
        score += 12
        bullish_factors.append(f"RSI {rsi_val:.1f} (deeply oversold — potential reversal)")
    elif rsi_val > 70:
        caution_factors.append(f"RSI {rsi_val:.1f} (overbought)")

    # ── MACD ──────────────────────────────────
    macd_data = macd(closes)
    m_line  = macd_data["macd_line"]
    m_hist  = macd_data["histogram"]
    ml = next((v for v in reversed(m_line) if v is not None), None)
    mh = next((v for v in reversed(m_hist) if v is not None), None)
    max_score += 10
    if ml is not None and ml > 0:
        score += 5
        bullish_factors.append("MACD positive")
    if mh is not None and mh > 0:
        score += 5
        bullish_factors.append("MACD histogram expanding")
    elif mh is not None and mh < 0:
        caution_factors.append("MACD histogram declining")

    # ── ADX ──────────────────────────────────
    adx_vals = adx(highs, lows, closes)
    adx_val = next((v for v in reversed(adx_vals) if v is not None), 20.0)
    max_score += 10
    if adx_val >= 25:
        score += 10
        bullish_factors.append(f"ADX {adx_val:.1f} (strong trend)")
    elif adx_val >= 20:
        score += 5

    # ── ATR (volatility context) ──────────────
    atr_vals = atr(highs, lows, closes)
    atr_val  = next((v for v in reversed(atr_vals) if v is not None), current * 0.02)

    # ── Bollinger Bands ───────────────────────
    bb = bollinger_bands(closes)
    bb_upper = next((v for v in reversed(bb["upper"]) if v is not None), None)
    bb_lower = next((v for v in reversed(bb["lower"]) if v is not None), None)
    bb_mid   = next((v for v in reversed(bb["middle"]) if v is not None), None)
    max_score += 10
    if bb_lower and bb_upper and bb_mid:
        bb_width = (bb_upper - bb_lower) / bb_mid if bb_mid > 0 else 0
        if current <= bb_mid and current >= bb_lower:
            score += 8
            bullish_factors.append("Price in BB lower half (value zone)")
        elif current < bb_lower:
            score += 10
            bullish_factors.append("Price below BB lower (extreme oversold)")
        elif current > bb_upper:
            caution_factors.append("Price above BB upper (extended)")

    # ── Volume ────────────────────────────────
    vol_data = volume_analysis(volumes)
    rel_vol  = vol_data["relative_volume"]
    max_score += 10
    if rel_vol >= 2.0:
        score += 10
        bullish_factors.append(f"Volume spike {rel_vol:.1f}x average")
    elif rel_vol >= 1.3:
        score += 6
        bullish_factors.append(f"Above-average volume ({rel_vol:.1f}x)")

    # ── Support / Resistance ──────────────────
    sr = support_resistance(highs, lows, closes)
    max_score += 10
    dist_to_support = (current - sr["support"]) / current
    if 0 < dist_to_support < 0.04:
        score += 10
        bullish_factors.append(f"Near support ${sr['support']:,.4f}")
    elif 0 < dist_to_support < 0.08:
        score += 5

    # ── Smart Money Concepts ──────────────────
    smc_score = 0
    smc_max   = 0

    order_blocks = detect_order_blocks(opens, highs, lows, closes)
    smc_max += 5
    if order_blocks:
        smc_score += 5
        bullish_factors.append(f"Bullish Order Block detected ({len(order_blocks)} zones)")

    fvgs = detect_fvg(highs, lows)
    smc_max += 5
    if fvgs:
        smc_score += 4
        bullish_factors.append(f"Fair Value Gap present ({len(fvgs)} FVGs)")

    bos = detect_bos(closes)
    smc_max += 5
    if bos == "bullish":
        smc_score += 5
        bullish_factors.append("Break of Structure (BOS) — bullish")

    choch = detect_choch(closes)
    smc_max += 5
    if choch == "bullish_choch":
        smc_score += 5
        bullish_factors.append("Change of Character (CHoCH) — bullish reversal signal")

    liq_sweep = detect_liquidity_sweep(highs, lows, closes)
    smc_max += 5
    if liq_sweep == "low_sweep":
        smc_score += 5
        bullish_factors.append("Liquidity Sweep (lows swept → potential reversal)")
    elif liq_sweep == "high_sweep":
        caution_factors.append("High Sweep detected — watch for reversal")

    breakout = detect_breakout_retest(closes, highs, lows)
    smc_max += 5
    if breakout == "breakout_up":
        smc_score += 5
        bullish_factors.append("Breakout above resistance confirmed")
    elif breakout == "retest":
        smc_score += 4
        bullish_factors.append("Breakout retest in progress")

    zone = detect_premium_discount(highs, lows, closes)
    smc_max += 5
    if zone == "discount":
        smc_score += 5
        bullish_factors.append("Price in Discount Zone (good entry area)")
    elif zone == "equilibrium":
        smc_score += 2

    mss = detect_market_structure_shift(closes)
    smc_max += 5
    if mss == "bullish_mss":
        smc_score += 5
        bullish_factors.append("Market Structure Shift (bullish MSS)")

    max_score += smc_max
    score     += smc_score

    # ── Normalise to 0-100 ───────────────────
    final_score = round((score / max_score * 100) if max_score > 0 else 0)
    final_score = max(0, min(100, final_score))

    # ── Price above EMA200 = extended ─────────
    extended = bool(e200 and current > e200 * 1.10)

    signal_type = classify_signal(final_score, extended)

    # ── Trend label ───────────────────────────
    if e20 and e50 and e200:
        if current > e200 and e50 > e200:
            trend = "Strong Uptrend"
        elif current > e50:
            trend = "Uptrend"
        elif current < e50 and e20 < e50:
            trend = "Downtrend"
        else:
            trend = "Sideways"
    else:
        trend = "Sideways"

    # ── Momentum ─────────────────────────────
    if rsi_val > 60 and ml is not None and ml > 0:
        momentum = "Strong"
    elif rsi_val > 50:
        momentum = "Moderate"
    elif rsi_val < 40:
        momentum = "Weak"
    else:
        momentum = "Neutral"

    # ── Risk ─────────────────────────────────
    if adx_val >= 25 and vol_data["relative_volume"] >= 1.5:
        risk = "Medium"
    elif adx_val >= 30:
        risk = "Medium-High"
    elif final_score >= 70:
        risk = "Low-Medium"
    else:
        risk = "Low"

    trade_plan = calculate_trade_plan(current, atr_val, signal_type, sr)

    return {
        "symbol":        "",
        "score":         final_score,
        "signal":        signal_type,
        "trend":         trend,
        "momentum":      momentum,
        "risk":          risk,
        "confidence":    final_score,
        "price":         current,
        "rsi":           round(rsi_val, 2),
        "adx":           round(adx_val, 2),
        "ema20":         round(e20, 4) if e20 else None,
        "ema50":         round(e50, 4) if e50 else None,
        "ema200":        round(e200, 4) if e200 else None,
        "atr":           round(atr_val, 4),
        "relative_volume": round(rel_vol, 2),
        "support":       round(sr["support"], 4),
        "resistance":    round(sr["resistance"], 4),
        "zone":          zone,
        "smc": {
            "order_blocks":   len(order_blocks),
            "fvg":            len(fvgs),
            "bos":            bos,
            "choch":          choch,
            "liquidity_sweep": liq_sweep,
            "breakout":       breakout,
            "mss":            mss,
        },
        "bullish_factors": bullish_factors,
        "caution_factors": caution_factors,
        "trade_plan":    trade_plan,
    }


def _empty_signal() -> dict:
    return {
        "symbol":         "",
        "score":          0,
        "signal":         SIGNAL_WAIT,
        "trend":          "Unknown",
        "momentum":       "Unknown",
        "risk":           "Unknown",
        "confidence":     0,
        "price":          0,
        "rsi":            0,
        "adx":            0,
        "ema20":          None,
        "ema50":          None,
        "ema200":         None,
        "atr":            0,
        "relative_volume": 1.0,
        "support":        0,
        "resistance":     0,
        "zone":           "equilibrium",
        "smc":            {},
        "bullish_factors": [],
        "caution_factors": [],
        "trade_plan":     {},
    }


# ──────────────────────────────────────────────
# Format signal as Telegram message
# ──────────────────────────────────────────────

def format_signal_message(sig: dict, symbol: str) -> str:
    """Return a nicely formatted Telegram-safe signal message."""
    tp = sig.get("trade_plan", {})
    smc = sig.get("smc", {})
    bf = sig.get("bullish_factors", [])
    cf = sig.get("caution_factors", [])

    bar = "█" * (sig["score"] // 10) + "░" * (10 - sig["score"] // 10)

    lines = [
        f"📊 *{symbol}/USDT — Signal Analysis*",
        f"",
        f"Signal: *{sig['signal']}*",
        f"Score:  [{bar}] {sig['score']}%",
        f"",
        f"📈 Trend:     {sig['trend']}",
        f"⚡ Momentum: {sig['momentum']}",
        f"⚠️ Risk:      {sig['risk']}",
        f"🎯 Confidence: {sig['confidence']}%",
        f"",
        f"💲 Price:      ${sig['price']:,.4f}",
        f"📉 RSI:        {sig['rsi']}",
        f"📊 ADX:        {sig['adx']}",
        f"📦 Rel. Volume: {sig['relative_volume']}x",
        f"🔵 Zone:       {sig['zone'].title()}",
        f"",
        f"🛡 Support:    ${sig['support']:,.4f}",
        f"🔴 Resistance: ${sig['resistance']:,.4f}",
    ]

    if tp:
        lines += [
            f"",
            f"📋 *Trade Plan*",
            f"🟢 Entry:    {tp.get('entry', '—')}",
            f"🛑 Stop Loss: {tp.get('stop_loss', '—')}",
            f"🎯 TP1:      {tp.get('tp1', '—')}",
            f"🎯 TP2:      {tp.get('tp2', '—')}",
            f"🎯 TP3:      {tp.get('tp3', '—')}",
            f"⚖️ R:R Ratio: {tp.get('rr_ratio', '—')}",
        ]

    smc_hits = []
    if smc.get("order_blocks", 0):
        smc_hits.append(f"✅ Order Block ({smc['order_blocks']} zones)")
    if smc.get("fvg", 0):
        smc_hits.append(f"✅ FVG ({smc['fvg']})")
    if smc.get("bos") == "bullish":
        smc_hits.append("✅ BOS (bullish)")
    if smc.get("choch") == "bullish_choch":
        smc_hits.append("✅ CHoCH (bullish)")
    if smc.get("liquidity_sweep") == "low_sweep":
        smc_hits.append("✅ Liquidity Sweep (lows)")
    if smc.get("breakout") in ("breakout_up", "retest"):
        smc_hits.append(f"✅ {smc['breakout'].replace('_', ' ').title()}")
    if smc.get("mss") == "bullish_mss":
        smc_hits.append("✅ MSS (bullish)")

    if smc_hits:
        lines += ["", "🏦 *Smart Money Concepts*"] + smc_hits

    if bf:
        lines += ["", "💪 *Bullish Factors*"] + [f"  • {f}" for f in bf[:5]]

    if cf:
        lines += ["", "⚠️ *Caution*"] + [f"  • {f}" for f in cf[:3]]

    lines += [
        "",
        "_Analysis is for educational purposes only._",
        "_Always manage your risk. HALAL SPOT ONLY._",
    ]
    return "\n".join(lines)
