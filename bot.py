"""
bot.py - Main Telegram Bot for Halol Crypto AI.
Uses python-telegram-bot v20+ (async PTB).
Button-only navigation — no forced text input.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters,
)
from telegram.constants import ParseMode

import config
from database import (
    init_db, upsert_user, get_watchlist,
    add_to_watchlist, remove_from_watchlist,
    get_alert_settings, update_alert_setting,
    get_user_settings, upsert_user_settings,
    get_all_cached_signals, get_cached_signal,
)
from utils import (
    fetch_market_overview, format_price, format_change,
    format_volume, coin_emoji, paginate,
)
from signals import score_coin, format_signal_message, SIGNAL_STRONG_BUY, SIGNAL_BUY
from scanner import scan_coin, background_scanner, set_bot_app
from education import get_lesson, get_category_items, CATEGORIES

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE),
    ],
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Keyboard helpers
# ──────────────────────────────────────────────

def nav_row() -> list[InlineKeyboardButton]:
    """Standard ◀️ Back and 🏠 Home buttons."""
    return [
        InlineKeyboardButton("◀️ Back", callback_data="back"),
        InlineKeyboardButton("🏠 Home", callback_data="home"),
    ]


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏠 Dashboard", callback_data="dashboard"),
            InlineKeyboardButton("📈 Signals",   callback_data="signals_page_0"),
        ],
        [
            InlineKeyboardButton("🔥 Top Opportunities", callback_data="top_opportunities"),
            InlineKeyboardButton("⭐ Watchlist",          callback_data="watchlist"),
        ],
        [
            InlineKeyboardButton("📊 Market Overview", callback_data="market_overview"),
            InlineKeyboardButton("🎓 Academy",          callback_data="academy"),
        ],
        [
            InlineKeyboardButton("🤖 AI Helper", callback_data="ai_helper"),
            InlineKeyboardButton("⚙️ Settings",  callback_data="settings"),
        ],
        [
            InlineKeyboardButton(
                "🚀 Open Dashboard",
                web_app=WebAppInfo(url=config.MINI_APP_URL),
            ),
        ],
    ])


def coin_grid_keyboard(
    coins: list[str],
    page: int,
    total_pages: int,
    callback_prefix: str = "signal_",
) -> InlineKeyboardMarkup:
    """3-per-row grid with pagination."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i, coin in enumerate(coins):
        row.append(InlineKeyboardButton(
            f"{coin_emoji(coin)} {coin}",
            callback_data=f"{callback_prefix}{coin}",
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    # Pagination
    pag_row: list[InlineKeyboardButton] = []
    if page > 0:
        pag_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"signals_page_{page - 1}"))
    if page < total_pages - 1:
        pag_row.append(InlineKeyboardButton("➡️ Next", callback_data=f"signals_page_{page + 1}"))
    if pag_row:
        rows.append(pag_row)

    rows.append(nav_row())
    return InlineKeyboardMarkup(rows)


# ──────────────────────────────────────────────
# Handlers — /start
# ──────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    upsert_user(user.id, user.username, user.first_name)
    text = (
        f"🌙 *Assalamu Alaikum, {user.first_name}!*\n\n"
        f"Welcome to *{config.APP_NAME}* — your halal spot crypto assistant.\n\n"
        "✅ Spot analysis only — no futures, no shorts\n"
        "📊 Technical indicators + Smart Money Concepts\n"
        "🎓 Built-in education — no paid APIs needed\n"
        "⭐ Watchlist + alerts for your coins\n\n"
        "Choose from the menu below:"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(),
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🏠 *Main Menu*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# Callback router
# ──────────────────────────────────────────────

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "home" or data == "back":
        await _show_home(query)

    elif data == "dashboard":
        await _show_dashboard(query)

    elif data.startswith("signals_page_"):
        page = int(data.split("_")[-1])
        await _show_signals_menu(query, page)

    elif data.startswith("signal_"):
        symbol = data[len("signal_"):]
        await _show_signal(query, symbol)

    elif data == "top_opportunities":
        await _show_top_opportunities(query)

    elif data == "watchlist":
        await _show_watchlist(query)

    elif data.startswith("wl_add_page_"):
        page = int(data.split("_")[-1])
        await _show_add_coin_menu(query, page)

    elif data.startswith("wl_add_"):
        symbol = data[len("wl_add_"):]
        await _add_to_watchlist(query, symbol)

    elif data.startswith("wl_remove_"):
        symbol = data[len("wl_remove_"):]
        await _remove_from_watchlist(query, symbol)

    elif data.startswith("wl_signal_"):
        symbol = data[len("wl_signal_"):]
        await _show_signal(query, symbol)

    elif data == "market_overview":
        await _show_market_overview(query)

    elif data == "academy":
        await _show_academy(query)

    elif data.startswith("academy_cat_"):
        cat = data[len("academy_cat_"):]
        await _show_academy_category(query, cat)

    elif data.startswith("lesson_"):
        key = data[len("lesson_"):]
        await _show_lesson(query, key)

    elif data == "ai_helper":
        await _show_ai_helper(query)

    elif data.startswith("ai_cat_"):
        cat = data[len("ai_cat_"):]
        await _show_academy_category(query, cat)  # reuse same content

    elif data.startswith("ai_lesson_"):
        key = data[len("ai_lesson_"):]
        await _show_lesson(query, key)

    elif data == "settings":
        await _show_settings(query)

    elif data.startswith("settings_tf_"):
        tf = data[len("settings_tf_"):]
        await _set_timeframe(query, tf)

    elif data.startswith("settings_alerts_toggle"):
        await _toggle_alerts(query)

    else:
        await _show_home(query)


# ──────────────────────────────────────────────
# Screens
# ──────────────────────────────────────────────

async def _show_home(query) -> None:
    await query.edit_message_text(
        "🏠 *Main Menu*\n\nWhat would you like to explore?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(),
    )


async def _show_dashboard(query) -> None:
    user_id = query.from_user.id
    watchlist = get_watchlist(user_id)
    all_signals = get_all_cached_signals()
    strong_buys = [s for s in all_signals if SIGNAL_STRONG_BUY in s.get("signal", "")]
    buys = [s for s in all_signals if SIGNAL_BUY in s.get("signal", "")]

    wl_text = ", ".join(watchlist) if watchlist else "Empty"
    text = (
        "🏠 *Dashboard*\n\n"
        f"⭐ Watchlist: *{len(watchlist)} coins*\n"
        f"   {wl_text}\n\n"
        f"📊 Signal Summary (last scan):\n"
        f"   🟢 Strong Buy: *{len(strong_buys)}* coins\n"
        f"   🟢 Buy: *{len(buys)}* coins\n"
        f"   📈 Total analysed: *{len(all_signals)}* coins\n\n"
        "Use the menu to explore signals, watchlist, or market overview."
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📈 Signals",      callback_data="signals_page_0"),
            InlineKeyboardButton("⭐ Watchlist",    callback_data="watchlist"),
        ],
        [
            InlineKeyboardButton("📊 Market",       callback_data="market_overview"),
            InlineKeyboardButton("🔥 Top Opps",     callback_data="top_opportunities"),
        ],
        nav_row(),
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


async def _show_signals_menu(query, page: int = 0) -> None:
    coins = config.HALAL_COINS
    page_coins, total_pages = paginate(coins, page, 9)
    text = (
        f"📈 *Select a Coin for Signal Analysis*\n"
        f"Page {page + 1}/{total_pages} — {len(coins)} halal coins\n\n"
        "Tap a coin to get the full signal analysis:"
    )
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=coin_grid_keyboard(page_coins, page, total_pages, "signal_"),
    )


async def _show_signal(query, symbol: str) -> None:
    """Fetch (or scan) signal for a coin and display it."""
    await query.edit_message_text(
        f"⏳ Analysing *{symbol}*... please wait.",
        parse_mode=ParseMode.MARKDOWN,
    )
    try:
        sig = get_cached_signal(symbol, max_age_seconds=300)
        if not sig:
            sig = await scan_coin(symbol)
        if not sig:
            await query.edit_message_text(
                f"⚠️ Could not fetch data for *{symbol}*.\nBinance may be temporarily unavailable.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([nav_row()]),
            )
            return
        sig["symbol"] = symbol
        text = format_signal_message(sig, symbol)
        user_id = query.from_user.id
        watchlist = get_watchlist(user_id)
        in_wl = symbol in watchlist
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⭐ Remove from Watchlist" if in_wl else "⭐ Add to Watchlist",
                    callback_data=f"wl_remove_{symbol}" if in_wl else f"wl_add_{symbol}",
                ),
            ],
            [
                InlineKeyboardButton("🔄 Refresh",    callback_data=f"signal_{symbol}"),
                InlineKeyboardButton("📈 Other Coins", callback_data="signals_page_0"),
            ],
            nav_row(),
        ])
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb,
        )
    except Exception as exc:
        logger.exception("_show_signal error: %s", exc)
        await query.edit_message_text(
            "❌ Error generating signal. Please try again.",
            reply_markup=InlineKeyboardMarkup([nav_row()]),
        )


async def _show_top_opportunities(query) -> None:
    """Show top coins by signal score."""
    all_signals = get_all_cached_signals()
    if not all_signals:
        # Trigger a quick scan of top 10 coins
        await query.edit_message_text("⏳ Loading top opportunities...")
        tasks = [scan_coin(s) for s in config.HALAL_COINS[:10]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_signals = [r for r in results if isinstance(r, dict) and r]

    ranked = sorted(all_signals, key=lambda x: x.get("score", 0), reverse=True)[:10]

    if not ranked:
        await query.edit_message_text(
            "⚠️ No signal data yet. Please wait for the scanner.",
            reply_markup=InlineKeyboardMarkup([nav_row()]),
        )
        return

    lines = ["🔥 *Top 10 Opportunities*\n"]
    for i, sig in enumerate(ranked, 1):
        sym = sig.get("symbol", "—")
        score = sig.get("score", 0)
        signal = sig.get("signal", "")
        bar = "█" * (score // 20)
        lines.append(f"{i}. *{sym}* — {score}% {signal}\n   {bar}")

    text = "\n".join(lines)
    kb_rows = []
    row: list[InlineKeyboardButton] = []
    for sig in ranked[:9]:
        sym = sig.get("symbol", "")
        row.append(InlineKeyboardButton(f"{sym}", callback_data=f"signal_{sym}"))
        if len(row) == 3:
            kb_rows.append(row)
            row = []
    if row:
        kb_rows.append(row)
    kb_rows.append(nav_row())

    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb_rows),
    )


async def _show_watchlist(query) -> None:
    user_id = query.from_user.id
    watchlist = get_watchlist(user_id)

    if not watchlist:
        await query.edit_message_text(
            "⭐ *Your Watchlist is Empty*\n\nAdd coins to track them and receive alerts.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Coin", callback_data="wl_add_page_0")],
                nav_row(),
            ]),
        )
        return

    lines = ["⭐ *Your Watchlist*\n"]
    for sym in watchlist:
        sig = get_cached_signal(sym, max_age_seconds=600)
        if sig:
            score = sig.get("score", 0)
            signal = sig.get("signal", "—")
            price = format_price(sig.get("price", 0))
            lines.append(f"• *{sym}* — {price} | {score}% | {signal}")
        else:
            lines.append(f"• *{sym}* — (loading...)")

    text = "\n".join(lines)
    kb_rows: list[list[InlineKeyboardButton]] = []
    row_: list[InlineKeyboardButton] = []
    for sym in watchlist:
        row_.append(InlineKeyboardButton(f"📊 {sym}", callback_data=f"wl_signal_{sym}"))
        if len(row_) == 3:
            kb_rows.append(row_)
            row_ = []
    if row_:
        kb_rows.append(row_)

    # Remove buttons
    rem_row: list[InlineKeyboardButton] = []
    for sym in watchlist:
        rem_row.append(InlineKeyboardButton(f"❌ {sym}", callback_data=f"wl_remove_{sym}"))
        if len(rem_row) == 3:
            kb_rows.append(rem_row)
            rem_row = []
    if rem_row:
        kb_rows.append(rem_row)

    kb_rows.append([InlineKeyboardButton("➕ Add Coin", callback_data="wl_add_page_0")])
    kb_rows.append(nav_row())
    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb_rows),
    )


async def _show_add_coin_menu(query, page: int = 0) -> None:
    user_id = query.from_user.id
    watchlist = get_watchlist(user_id)
    available = [c for c in config.HALAL_COINS if c not in watchlist]
    if not available:
        await query.edit_message_text(
            "✅ All supported coins are already in your watchlist!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ View Watchlist", callback_data="watchlist")],
                nav_row(),
            ]),
        )
        return

    page_coins, total_pages = paginate(available, page, 9)
    text = f"➕ *Add Coin to Watchlist*\nPage {page + 1}/{total_pages}"
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=coin_grid_keyboard(page_coins, page, total_pages, "wl_add_"),
    )


async def _add_to_watchlist(query, symbol: str) -> None:
    user_id = query.from_user.id
    add_to_watchlist(user_id, symbol)
    await query.edit_message_text(
        f"✅ *{symbol}* added to your watchlist!\n\nYou will receive alerts for this coin.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 View Signal", callback_data=f"signal_{symbol}")],
            [InlineKeyboardButton("⭐ Watchlist",   callback_data="watchlist")],
            nav_row(),
        ]),
    )


async def _remove_from_watchlist(query, symbol: str) -> None:
    user_id = query.from_user.id
    remove_from_watchlist(user_id, symbol)
    await query.edit_message_text(
        f"❌ *{symbol}* removed from your watchlist.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ View Watchlist", callback_data="watchlist")],
            nav_row(),
        ]),
    )


async def _show_market_overview(query) -> None:
    await query.edit_message_text("⏳ Loading market data...")
    try:
        market = await fetch_market_overview()
        btc = market.get("btc", {})
        eth = market.get("eth", {})
        sentiment = market.get("sentiment", "Neutral")

        emoji_sent = "🟢" if sentiment == "Bullish" else ("🔴" if sentiment == "Bearish" else "🟡")

        def ticker_line(t: dict) -> str:
            if not t:
                return "—"
            return (
                f"*{t['symbol']}* {format_price(t['price'])} "
                f"{format_change(t['change_pct'])}"
            )

        gainers = "\n".join(
            f"  {i+1}. {ticker_line(t)}" for i, t in enumerate(market.get("gainers", []))
        )
        losers = "\n".join(
            f"  {i+1}. {ticker_line(t)}" for i, t in enumerate(market.get("losers", []))
        )
        vol_leaders = "\n".join(
            f"  {i+1}. *{t['symbol']}* {format_volume(t['volume'])}"
            for i, t in enumerate(market.get("volume_leaders", []))
        )

        text = (
            "📊 *Market Overview*\n\n"
            f"₿ BTC: {ticker_line(btc)}\n"
            f"⟠ ETH: {ticker_line(eth)}\n\n"
            f"📡 Market Sentiment: {emoji_sent} *{sentiment}*\n\n"
            f"📈 *Top Gainers*\n{gainers or '—'}\n\n"
            f"📉 *Top Losers*\n{losers or '—'}\n\n"
            f"💹 *Volume Leaders*\n{vol_leaders or '—'}"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="market_overview")],
            nav_row(),
        ])
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception as exc:
        logger.exception("market_overview error: %s", exc)
        await query.edit_message_text(
            "⚠️ Could not load market data. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Retry", callback_data="market_overview")],
                nav_row(),
            ]),
        )


async def _show_academy(query) -> None:
    text = "🎓 *Academy — Choose a Topic*\n\nSelect a category to start learning:"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Crypto Basics",       callback_data="academy_cat_crypto_basics")],
        [InlineKeyboardButton("📈 Technical Analysis",  callback_data="academy_cat_indicators")],
        [InlineKeyboardButton("🕯 Candlestick Patterns",callback_data="academy_cat_candlestick")],
        [InlineKeyboardButton("📊 Indicators",          callback_data="academy_cat_indicators")],
        [InlineKeyboardButton("🏦 Smart Money Concepts",callback_data="academy_cat_smc")],
        [InlineKeyboardButton("⚠️ Risk Management",    callback_data="academy_cat_risk_management")],
        [InlineKeyboardButton("❓ FAQ",                  callback_data="academy_cat_faq")],
        nav_row(),
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


async def _show_ai_helper(query) -> None:
    text = (
        "🤖 *AI Helper — Educational Assistant*\n\n"
        "Ask any question about crypto, trading, or Islamic finance principles.\n"
        "All content is built-in — no internet required!\n\n"
        "Choose a topic:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Crypto Basics",        callback_data="ai_cat_crypto_basics")],
        [InlineKeyboardButton("📈 Technical Analysis",   callback_data="ai_cat_indicators")],
        [InlineKeyboardButton("🕯 Candlestick Patterns", callback_data="ai_cat_candlestick")],
        [InlineKeyboardButton("📊 Indicators",           callback_data="ai_cat_indicators")],
        [InlineKeyboardButton("🏦 Smart Money Concepts", callback_data="ai_cat_smc")],
        [InlineKeyboardButton("⚠️ Risk Management",      callback_data="ai_cat_risk_management")],
        [InlineKeyboardButton("❓ FAQ",                   callback_data="ai_cat_faq")],
        nav_row(),
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


async def _show_academy_category(query, cat: str) -> None:
    items = get_category_items(cat)
    if not items:
        await query.edit_message_text(
            "❌ Category not found.",
            reply_markup=InlineKeyboardMarkup([nav_row()]),
        )
        return
    cat_names = {
        "crypto_basics":   "📚 Crypto Basics",
        "indicators":      "📊 Indicators",
        "smc":             "🏦 Smart Money Concepts",
        "risk_management": "⚠️ Risk Management",
        "candlestick":     "🕯 Candlestick Patterns",
        "faq":             "❓ FAQ",
    }
    title = cat_names.get(cat, cat.replace("_", " ").title())
    text = f"{title}\n\nChoose a lesson:"
    prefix = "ai_lesson_" if query.data and query.data.startswith("ai_") else "lesson_"
    kb_rows = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}{key}")]
        for label, key in items
    ]
    kb_rows.append(nav_row())
    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb_rows),
    )


async def _show_lesson(query, key: str) -> None:
    lesson = get_lesson(key)
    if not lesson:
        await query.edit_message_text(
            "❌ Lesson not found.",
            reply_markup=InlineKeyboardMarkup([nav_row()]),
        )
        return
    text = f"*{lesson['title']}*\n\n{lesson['content']}"
    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([nav_row()]),
    )


async def _show_settings(query) -> None:
    user_id = query.from_user.id
    prefs = get_user_settings(user_id)
    tf = prefs.get("default_tf", "1h")
    alerts_on = bool(prefs.get("alert_enabled", 1))
    alert_icon = "🔔 ON" if alerts_on else "🔕 OFF"

    text = (
        "⚙️ *Settings*\n\n"
        f"📊 Default Timeframe: *{tf}*\n"
        f"🔔 Alerts: *{alert_icon}*\n\n"
        "Choose an option:"
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1h", callback_data="settings_tf_1h"),
            InlineKeyboardButton("4h", callback_data="settings_tf_4h"),
            InlineKeyboardButton("1d", callback_data="settings_tf_1d"),
        ],
        [InlineKeyboardButton(f"Toggle Alerts ({alert_icon})", callback_data="settings_alerts_toggle")],
        nav_row(),
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


async def _set_timeframe(query, tf: str) -> None:
    user_id = query.from_user.id
    prefs = get_user_settings(user_id)
    upsert_user_settings(user_id, default_tf=tf, alert_enabled=prefs.get("alert_enabled", 1))
    await query.answer(f"✅ Timeframe set to {tf}")
    await _show_settings(query)


async def _toggle_alerts(query) -> None:
    user_id = query.from_user.id
    prefs = get_user_settings(user_id)
    new_val = 0 if prefs.get("alert_enabled", 1) else 1
    upsert_user_settings(user_id, default_tf=prefs.get("default_tf", "1h"), alert_enabled=new_val)
    await query.answer(f"Alerts {'enabled' if new_val else 'disabled'}")
    await _show_settings(query)


# ──────────────────────────────────────────────
# Fallback for unexpected text
# ──────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch any free-text message and redirect to menu."""
    text = update.message.text.strip().upper()
    # Check if it looks like a coin symbol
    if text in config.HALAL_COINS:
        msg = await update.message.reply_text(
            f"⏳ Analysing *{text}*...",
            parse_mode=ParseMode.MARKDOWN,
        )
        sig = await scan_coin(text)
        if sig:
            sig["symbol"] = text
            user_id = update.effective_user.id
            upsert_user(user_id, update.effective_user.username, update.effective_user.first_name)
            watchlist = get_watchlist(user_id)
            in_wl = text in watchlist
            signal_text = format_signal_message(sig, text)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⭐ Remove from Watchlist" if in_wl else "⭐ Add to Watchlist",
                    callback_data=f"wl_remove_{text}" if in_wl else f"wl_add_{text}",
                )],
                nav_row(),
            ])
            await msg.edit_text(signal_text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        else:
            await msg.edit_text(
                f"⚠️ Could not fetch data for *{text}*.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([nav_row()]),
            )
    else:
        await update.message.reply_text(
            "🏠 Use the buttons to navigate — no typing needed!",
            reply_markup=main_menu_keyboard(),
        )


# ──────────────────────────────────────────────
# Application setup
# ──────────────────────────────────────────────

def build_app() -> Application:
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Please configure .env")
        sys.exit(1)

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


async def main() -> None:
    init_db()
    logger.info("Starting %s v%s", config.APP_NAME, config.APP_VERSION)

    app = build_app()
    set_bot_app(app)

    # Start background scanner as a concurrent task
    asyncio.create_task(background_scanner())

    webhook_url = config.TELEGRAM_WEBHOOK_URL
    if webhook_url:
        logger.info("Starting in webhook mode: %s", webhook_url)
        await app.bot.set_webhook(
            url=f"{webhook_url}/webhook",
            drop_pending_updates=True,
        )
        await app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", "8080")),
            webhook_url=f"{webhook_url}/webhook",
        )
    else:
        logger.info("Starting in polling mode")
        await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
