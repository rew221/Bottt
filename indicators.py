"""
indicators.py - Pure technical-analysis calculations for Halol Crypto AI.
All functions operate on plain Python lists for portability.
No TA-lib dependency — pure maths.
"""

import math
import statistics
from typing import Optional


# ──────────────────────────────────────────────
# Moving Averages
# ──────────────────────────────────────────────

def ema(prices: list[float], period: int) -> list[Optional[float]]:
    """Exponential Moving Average."""
    if len(prices) < period:
        return [None] * len(prices)
    k = 2 / (period + 1)
    result: list[Optional[float]] = [None] * (period - 1)
    seed = sum(prices[:period]) / period
    result.append(seed)
    for price in prices[period:]:
        result.append(price * k + result[-1] * (1 - k))
    return result


def sma(prices: list[float], period: int) -> list[Optional[float]]:
    """Simple Moving Average."""
    result: list[Optional[float]] = [None] * (period - 1)
    for i in range(period - 1, len(prices)):
        result.append(sum(prices[i - period + 1: i + 1]) / period)
    return result


# ──────────────────────────────────────────────
# RSI
# ──────────────────────────────────────────────

def rsi(prices: list[float], period: int = 14) -> list[Optional[float]]:
    """Relative Strength Index (Wilder smoothing)."""
    result: list[Optional[float]] = [None] * period
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    if len(changes) < period:
        return [None] * len(prices)
    gains = [max(0.0, c) for c in changes]
    losses = [abs(min(0.0, c)) for c in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    def _rsi_val(ag: float, al: float) -> float:
        if al == 0:
            return 100.0
        rs = ag / al
        return 100 - (100 / (1 + rs))

    result.append(_rsi_val(avg_gain, avg_loss))
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        result.append(_rsi_val(avg_gain, avg_loss))
    return result


# ──────────────────────────────────────────────
# MACD
# ──────────────────────────────────────────────

def macd(
    prices: list[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> dict[str, list[Optional[float]]]:
    """Returns macd_line, signal_line, histogram."""
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    macd_line: list[Optional[float]] = []
    for f, s in zip(ema_fast, ema_slow):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)
    # signal = EMA of macd_line (non-None values)
    valid_macd = [v for v in macd_line if v is not None]
    signal_vals = ema(valid_macd, signal_period)
    # re-align with None prefix
    none_count = sum(1 for v in macd_line if v is None)
    signal_line: list[Optional[float]] = [None] * none_count + signal_vals
    histogram: list[Optional[float]] = []
    for m, s in zip(macd_line, signal_line):
        if m is None or s is None:
            histogram.append(None)
        else:
            histogram.append(m - s)
    return {"macd_line": macd_line, "signal_line": signal_line, "histogram": histogram}


# ──────────────────────────────────────────────
# ATR
# ──────────────────────────────────────────────

def atr(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[Optional[float]]:
    """Average True Range."""
    trs: list[float] = []
    for i in range(1, len(closes)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        trs.append(max(hl, hc, lc))
    if len(trs) < period:
        return [None] * len(closes)
    result: list[Optional[float]] = [None] * period
    result.append(sum(trs[:period]) / period)
    for i in range(period, len(trs)):
        result.append((result[-1] * (period - 1) + trs[i]) / period)
    return result


# ──────────────────────────────────────────────
# Bollinger Bands
# ──────────────────────────────────────────────

def bollinger_bands(
    prices: list[float],
    period: int = 20,
    num_std: float = 2.0,
) -> dict[str, list[Optional[float]]]:
    middle = sma(prices, period)
    upper: list[Optional[float]] = []
    lower: list[Optional[float]] = []
    for i, mid in enumerate(middle):
        if mid is None or i < period - 1:
            upper.append(None)
            lower.append(None)
        else:
            std = statistics.stdev(prices[i - period + 1: i + 1])
            upper.append(mid + num_std * std)
            lower.append(mid - num_std * std)
    return {"middle": middle, "upper": upper, "lower": lower}


# ──────────────────────────────────────────────
# ADX
# ──────────────────────────────────────────────

def adx(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[Optional[float]]:
    """Average Directional Index."""
    n = len(closes)
    if n < period * 2:
        return [None] * n
    plus_dm: list[float] = []
    minus_dm: list[float] = []
    trs: list[float] = []
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        dn = lows[i - 1] - lows[i]
        plus_dm.append(up if up > dn and up > 0 else 0.0)
        minus_dm.append(dn if dn > up and dn > 0 else 0.0)
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        trs.append(max(hl, hc, lc))

    def _smooth(data: list[float], p: int) -> list[float]:
        smoothed = [sum(data[:p])]
        for v in data[p:]:
            smoothed.append(smoothed[-1] - smoothed[-1] / p + v)
        return smoothed

    smooth_tr = _smooth(trs, period)
    smooth_pdm = _smooth(plus_dm, period)
    smooth_ndm = _smooth(minus_dm, period)
    pdi = [100 * p / t if t != 0 else 0 for p, t in zip(smooth_pdm, smooth_tr)]
    ndi = [100 * n_ / t if t != 0 else 0 for n_, t in zip(smooth_ndm, smooth_tr)]
    dx = [
        100 * abs(p - n_) / (p + n_) if (p + n_) != 0 else 0
        for p, n_ in zip(pdi, ndi)
    ]
    adx_vals = _smooth(dx, period)
    prefix = [None] * (n - len(adx_vals))
    return prefix + adx_vals  # type: ignore[return-value]


# ──────────────────────────────────────────────
# Support & Resistance
# ──────────────────────────────────────────────

def support_resistance(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    lookback: int = 50,
) -> dict[str, float]:
    """Identify key support/resistance from recent pivot highs/lows."""
    recent_h = highs[-lookback:]
    recent_l = lows[-lookback:]
    resistance = max(recent_h)
    support = min(recent_l)
    return {"support": support, "resistance": resistance}


# ──────────────────────────────────────────────
# Volume Analysis
# ──────────────────────────────────────────────

def volume_analysis(volumes: list[float], period: int = 20) -> dict[str, float]:
    """Return average volume and relative volume ratio."""
    if len(volumes) < period:
        return {"avg_volume": 0.0, "relative_volume": 1.0}
    avg = sum(volumes[-period:]) / period
    rel = volumes[-1] / avg if avg > 0 else 1.0
    return {"avg_volume": avg, "relative_volume": rel}


# ──────────────────────────────────────────────
# Smart Money Concepts
# ──────────────────────────────────────────────

def detect_order_blocks(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    lookback: int = 30,
) -> list[dict]:
    """Detect bullish order blocks (last bearish candle before strong up-move)."""
    blocks = []
    data = list(zip(opens, highs, lows, closes))[-lookback:]
    for i in range(1, len(data) - 2):
        o, h, l, c = data[i]
        # Bearish candle
        if c < o:
            # Check if next 2 candles are strongly bullish
            next1 = data[i + 1]
            next2 = data[i + 2]
            if next1[3] > next1[0] and next2[3] > next2[0]:
                avg_up = (next1[3] - next1[0] + next2[3] - next2[0]) / 2
                avg_down = o - c
                if avg_up > avg_down * 0.8:
                    blocks.append({
                        "type": "bullish",
                        "top": o,
                        "bottom": c,
                        "index": len(opens) - lookback + i,
                    })
    return blocks[-3:]  # return last 3


def detect_fvg(
    highs: list[float],
    lows: list[float],
    lookback: int = 30,
) -> list[dict]:
    """Fair Value Gap: gap between candle[i-1] high and candle[i+1] low."""
    fvgs = []
    data_h = highs[-lookback:]
    data_l = lows[-lookback:]
    for i in range(1, len(data_h) - 1):
        gap_top = data_l[i + 1]
        gap_bottom = data_h[i - 1]
        if gap_top > gap_bottom:
            fvgs.append({
                "type": "bullish",
                "top": gap_top,
                "bottom": gap_bottom,
                "index": len(highs) - lookback + i,
            })
    return fvgs[-2:]


def detect_bos(closes: list[float], lookback: int = 50) -> Optional[str]:
    """Break Of Structure: new high breaks previous swing high = bullish BOS."""
    if len(closes) < lookback:
        return None
    recent = closes[-lookback:]
    mid = len(recent) // 2
    prev_high = max(recent[:mid])
    curr_high = max(recent[mid:])
    prev_low = min(recent[:mid])
    curr_low = min(recent[mid:])
    if curr_high > prev_high:
        return "bullish"
    if curr_low < prev_low:
        return "bearish"
    return None


def detect_choch(closes: list[float], lookback: int = 60) -> Optional[str]:
    """Change Of Character: first break against the prevailing trend."""
    if len(closes) < lookback:
        return None
    recent = closes[-lookback:]
    third = lookback // 3
    first = recent[:third]
    last = recent[-third:]
    trend_first = first[-1] - first[0]
    trend_last = last[-1] - last[0]
    if trend_first > 0 and trend_last < -abs(trend_first) * 0.5:
        return "bearish_choch"
    if trend_first < 0 and trend_last > abs(trend_first) * 0.5:
        return "bullish_choch"
    return None


def detect_liquidity_sweep(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    lookback: int = 40,
) -> Optional[str]:
    """Detect wick-based liquidity sweep above recent high or below recent low."""
    if len(closes) < lookback + 2:
        return None
    ref_high = max(highs[-lookback:-2])
    ref_low = min(lows[-lookback:-2])
    last_h = highs[-1]
    last_l = lows[-1]
    last_c = closes[-1]
    # Swept highs then closed back below → bearish sweep (potential reversal)
    if last_h > ref_high and last_c < ref_high:
        return "high_sweep"
    # Swept lows then closed back above → bullish sweep (potential reversal)
    if last_l < ref_low and last_c > ref_low:
        return "low_sweep"
    return None


def detect_breakout_retest(
    closes: list[float],
    highs: list[float],
    lows: list[float],
    lookback: int = 50,
) -> Optional[str]:
    """Detect breakout above resistance with potential retest zone."""
    sr = support_resistance(highs, lows, closes, lookback)
    resistance = sr["resistance"]
    support = sr["support"]
    current = closes[-1]
    # Breakout above resistance
    if current > resistance * 1.002:
        return "breakout_up"
    # Retest after breakout (price pulled back to old resistance = new support)
    if (current > support * 0.998) and (current < resistance * 0.995):
        return "retest"
    return None


def detect_premium_discount(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    lookback: int = 50,
) -> str:
    """Classify current price as Premium, Equilibrium, or Discount zone."""
    sr = support_resistance(highs, lows, closes, lookback)
    mid = (sr["resistance"] + sr["support"]) / 2
    current = closes[-1]
    ratio = (current - sr["support"]) / (sr["resistance"] - sr["support"] + 1e-9)
    if ratio > 0.65:
        return "premium"
    if ratio < 0.35:
        return "discount"
    return "equilibrium"


def detect_market_structure_shift(closes: list[float], lookback: int = 80) -> Optional[str]:
    """Market Structure Shift: significant swing-level break."""
    if len(closes) < lookback:
        return None
    recent = closes[-lookback:]
    half = lookback // 2
    old_range = max(recent[:half]) - min(recent[:half])
    new_range = max(recent[half:]) - min(recent[half:])
    old_dir = recent[half - 1] - recent[0]
    new_dir = recent[-1] - recent[half]
    # Direction flip with notable range
    if old_dir > 0 and new_dir < -old_range * 0.4:
        return "bearish_mss"
    if old_dir < 0 and new_dir > old_range * 0.4:
        return "bullish_mss"
    return None
