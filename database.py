"""
database.py - SQLite database layer for Halol Crypto AI.
Easy to swap to PostgreSQL by changing DATABASE_URL.
"""

import sqlite3
import logging
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from config import SQLITE_PATH

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Connection helper
# ──────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Return a thread-safe SQLite connection with row_factory."""
    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ──────────────────────────────────────────────
# Initialisation
# ──────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they do not exist."""
    conn = get_connection()
    try:
        c = conn.cursor()

        # Users
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # Watchlist
        c.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                symbol      TEXT    NOT NULL,
                added_at    TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, symbol),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Alert settings per watchlist coin
        c.execute("""
            CREATE TABLE IF NOT EXISTS alert_settings (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id             INTEGER NOT NULL,
                symbol              TEXT    NOT NULL,
                strong_buy          INTEGER DEFAULT 1,
                breakout            INTEGER DEFAULT 1,
                order_block         INTEGER DEFAULT 1,
                liquidity_sweep     INTEGER DEFAULT 1,
                target_reached      INTEGER DEFAULT 1,
                stop_loss_reached   INTEGER DEFAULT 1,
                UNIQUE(user_id, symbol),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Sent alerts log
        c.execute("""
            CREATE TABLE IF NOT EXISTS alerts_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                symbol      TEXT    NOT NULL,
                alert_type  TEXT    NOT NULL,
                message     TEXT,
                sent_at     TEXT DEFAULT (datetime('now'))
            )
        """)

        # Cached signal data
        c.execute("""
            CREATE TABLE IF NOT EXISTS signal_cache (
                symbol      TEXT    PRIMARY KEY,
                timeframe   TEXT    NOT NULL,
                signal_json TEXT    NOT NULL,
                cached_at   TEXT DEFAULT (datetime('now'))
            )
        """)

        # User settings
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id         INTEGER PRIMARY KEY,
                default_tf      TEXT    DEFAULT '1h',
                alert_enabled   INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        conn.commit()
        logger.info("Database initialised at %s", SQLITE_PATH)
    except Exception as exc:
        logger.exception("DB init error: %s", exc)
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────

def upsert_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                updated_at = datetime('now')
        """, (user_id, username, first_name))
        conn.commit()
    except Exception as exc:
        logger.exception("upsert_user: %s", exc)
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Watchlist
# ──────────────────────────────────────────────

def get_watchlist(user_id: int) -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT symbol FROM watchlist WHERE user_id=? ORDER BY added_at",
            (user_id,)
        ).fetchall()
        return [r["symbol"] for r in rows]
    finally:
        conn.close()


def add_to_watchlist(user_id: int, symbol: str) -> bool:
    """Returns True if added, False if already exists."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, symbol) VALUES (?, ?)",
            (user_id, symbol.upper())
        )
        # ensure default alert settings exist
        conn.execute("""
            INSERT OR IGNORE INTO alert_settings (user_id, symbol)
            VALUES (?, ?)
        """, (user_id, symbol.upper()))
        conn.commit()
        return True
    except Exception as exc:
        logger.exception("add_to_watchlist: %s", exc)
        return False
    finally:
        conn.close()


def remove_from_watchlist(user_id: int, symbol: str) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM watchlist WHERE user_id=? AND symbol=?",
            (user_id, symbol.upper())
        )
        conn.commit()
        return True
    except Exception as exc:
        logger.exception("remove_from_watchlist: %s", exc)
        return False
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Alert settings
# ──────────────────────────────────────────────

def get_alert_settings(user_id: int, symbol: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM alert_settings WHERE user_id=? AND symbol=?",
            (user_id, symbol.upper())
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_alert_setting(user_id: int, symbol: str, field: str, value: int) -> None:
    allowed = {
        "strong_buy", "breakout", "order_block",
        "liquidity_sweep", "target_reached", "stop_loss_reached"
    }
    if field not in allowed:
        return
    conn = get_connection()
    try:
        conn.execute(f"""
            UPDATE alert_settings SET {field}=? WHERE user_id=? AND symbol=?
        """, (value, user_id, symbol.upper()))
        conn.commit()
    finally:
        conn.close()


def get_users_to_notify(symbol: str, alert_type: str) -> list[int]:
    """Return user_ids who watch symbol and have this alert type enabled."""
    field_map = {
        "strong_buy":     "strong_buy",
        "breakout":       "breakout",
        "order_block":    "order_block",
        "liquidity_sweep":"liquidity_sweep",
        "target_reached": "target_reached",
        "stop_loss":      "stop_loss_reached",
    }
    field = field_map.get(alert_type, "strong_buy")
    conn = get_connection()
    try:
        rows = conn.execute(f"""
            SELECT a.user_id FROM alert_settings a
            JOIN watchlist w ON a.user_id=w.user_id AND a.symbol=w.symbol
            WHERE a.symbol=? AND a.{field}=1
        """, (symbol.upper(),)).fetchall()
        return [r["user_id"] for r in rows]
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Signal cache
# ──────────────────────────────────────────────

def cache_signal(symbol: str, timeframe: str, signal_data: dict) -> None:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO signal_cache (symbol, timeframe, signal_json, cached_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(symbol) DO UPDATE SET
                timeframe   = excluded.timeframe,
                signal_json = excluded.signal_json,
                cached_at   = excluded.cached_at
        """, (symbol.upper(), timeframe, json.dumps(signal_data)))
        conn.commit()
    finally:
        conn.close()


def get_cached_signal(symbol: str, max_age_seconds: int = 300) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT signal_json, cached_at FROM signal_cache
            WHERE symbol=?
              AND (strftime('%s','now') - strftime('%s', cached_at)) < ?
        """, (symbol.upper(), max_age_seconds)).fetchone()
        return json.loads(row["signal_json"]) if row else None
    finally:
        conn.close()


def get_all_cached_signals() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT symbol, signal_json FROM signal_cache"
        ).fetchall()
        result = []
        for r in rows:
            try:
                d = json.loads(r["signal_json"])
                d["symbol"] = r["symbol"]
                result.append(d)
            except Exception:
                pass
        return result
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Alerts log
# ──────────────────────────────────────────────

def log_alert(user_id: int, symbol: str, alert_type: str, message: str) -> None:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO alerts_log (user_id, symbol, alert_type, message)
            VALUES (?, ?, ?, ?)
        """, (user_id, symbol, alert_type, message))
        conn.commit()
    finally:
        conn.close()


# ──────────────────────────────────────────────
# User settings
# ──────────────────────────────────────────────

def get_user_settings(user_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM user_settings WHERE user_id=?", (user_id,)
        ).fetchone()
        if row:
            return dict(row)
        # defaults
        return {"user_id": user_id, "default_tf": "1h", "alert_enabled": 1}
    finally:
        conn.close()


def upsert_user_settings(user_id: int, default_tf: str = "1h", alert_enabled: int = 1) -> None:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO user_settings (user_id, default_tf, alert_enabled)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                default_tf    = excluded.default_tf,
                alert_enabled = excluded.alert_enabled
        """, (user_id, default_tf, alert_enabled))
        conn.commit()
    finally:
        conn.close()
