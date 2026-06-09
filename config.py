"""
config.py - Central configuration for Halol Crypto AI
All environment variables and constants are managed here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Telegram
# ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
MINI_APP_URL: str = os.getenv("MINI_APP_URL", "https://your-domain.com/webapp/")

# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///halol_crypto.db")
SQLITE_PATH: str = os.getenv("SQLITE_PATH", "halol_crypto.db")

# ──────────────────────────────────────────────
# APIs (free / public)
# ──────────────────────────────────────────────
BINANCE_BASE_URL: str = "https://api.binance.com/api/v3"
COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"

# ──────────────────────────────────────────────
# Supported Halal Spot Coins
# ──────────────────────────────────────────────
HALAL_COINS: list[str] = [
    "BTC", "ETH", "BNB", "SOL", "XRP",
    "ADA", "DOGE", "LINK", "TON", "AVAX",
    "DOT", "MATIC", "ATOM", "LTC", "UNI",
    "NEAR", "ICP", "FIL", "APT", "ARB",
    "OP",  "INJ",  "SUI", "TIA", "SEI",
    "WLD", "PEPE", "SHIB","FLOKI","BONK",
]

BINANCE_SYMBOLS: dict[str, str] = {coin: f"{coin}USDT" for coin in HALAL_COINS}

COINGECKO_IDS: dict[str, str] = {
    "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
    "SOL": "solana", "XRP": "ripple", "ADA": "cardano",
    "DOGE": "dogecoin", "LINK": "chainlink", "TON": "the-open-network",
    "AVAX": "avalanche-2", "DOT": "polkadot", "MATIC": "matic-network",
    "ATOM": "cosmos", "LTC": "litecoin", "UNI": "uniswap",
    "NEAR": "near", "ICP": "internet-computer", "FIL": "filecoin",
    "APT": "aptos", "ARB": "arbitrum", "OP": "optimism",
    "INJ": "injective-protocol", "SUI": "sui", "TIA": "celestia",
    "SEI": "sei-network", "WLD": "worldcoin-wld", "PEPE": "pepe",
    "SHIB": "shiba-inu", "FLOKI": "floki", "BONK": "bonk",
}

# ──────────────────────────────────────────────
# Scanner / Cache
# ──────────────────────────────────────────────
SCAN_INTERVAL_SECONDS: int = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))   # 5 min
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "60"))             # 1 min
KLINE_LIMIT: int = 200          # candles per request
DEFAULT_TIMEFRAME: str = "1h"   # default analysis timeframe

# ──────────────────────────────────────────────
# Signal thresholds
# ──────────────────────────────────────────────
STRONG_BUY_THRESHOLD: int = 75
BUY_THRESHOLD: int = 55
PROFIT_ZONE_THRESHOLD: int = 80   # score above this AND extended = profit zone

# ──────────────────────────────────────────────
# Risk / trade plan defaults
# ──────────────────────────────────────────────
DEFAULT_STOP_LOSS_PCT: float = 0.035    # 3.5 %
TP1_MULTIPLIER: float = 1.5             # 1 : 1.5
TP2_MULTIPLIER: float = 2.5             # 1 : 2.5
TP3_MULTIPLIER: float = 4.0             # 1 : 4.0

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", "halol_crypto.log")

# ──────────────────────────────────────────────
# App meta
# ──────────────────────────────────────────────
APP_NAME: str = "Halol Crypto AI"
APP_VERSION: str = "1.0.0"
