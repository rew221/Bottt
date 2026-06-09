# 🌙 Halol Crypto AI

> **Production-ready Telegram Bot + Mini App for halal spot crypto investing.**
> No futures. No shorts. No leverage. Pure spot analysis.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🟢 Halal Signals | Strong Buy / Buy / Wait / Profit Zone — no sell/short signals |
| 📊 Technical Indicators | EMA20/50/200, RSI, MACD, ATR, ADX, Bollinger Bands, Volume |
| 🏦 Smart Money Concepts | Order Blocks, FVG, BOS, CHoCH, Liquidity Sweep, Breakout Retest |
| 📋 Trade Plans | Entry, Stop Loss, TP1/2/3, R:R Ratio per signal |
| ⭐ Watchlist | Add/remove coins with custom alerts |
| 🚀 Mini App | Full Telegram Mini App with dark mode crypto dashboard |
| 🎓 Academy | 20+ built-in lessons — no paid AI API required |
| 🔔 Alerts | Push notifications for Strong Buy, Breakouts, Sweeps |

---

## 📁 Project Structure

```
halol_crypto_ai/
├── bot.py              # Main Telegram bot — all menus & handlers
├── scanner.py          # Background coin scanner & alert dispatcher
├── signals.py          # Signal scoring engine (0–100%)
├── indicators.py       # Pure Python technical analysis
├── education.py        # Built-in lesson content
├── database.py         # SQLite database layer
├── config.py           # All configuration constants
├── utils.py            # API helpers, formatting, caching
├── requirements.txt    # Python dependencies
├── Dockerfile          # Production Docker image
├── .env.example        # Environment variable template
└── webapp/             # Telegram Mini App
    ├── index.html      # App shell with all page templates
    ├── style.css       # Dark mode crypto UI styles
    └── app.js          # Client-side TA + all page logic
```

---

## 🚀 Quick Start (Local)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/halol-crypto-ai.git
cd halol-crypto-ai/halol_crypto_ai
cp .env.example .env
nano .env   # Fill in TELEGRAM_BOT_TOKEN and MINI_APP_URL
```

### 2. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the bot

```bash
python bot.py
```

The bot starts in **polling mode** if `TELEGRAM_WEBHOOK_URL` is not set.

### 4. Serve the Mini App locally (optional)

```bash
cd webapp
python3 -m http.server 8000
# Open ngrok or similar to get HTTPS URL
```

---

## 🚂 Railway Deployment

1. **Create a new Railway project** at [railway.app](https://railway.app)
2. **Connect your GitHub repo**
3. **Set environment variables** in Railway → Variables:
   ```
   TELEGRAM_BOT_TOKEN  = your_bot_token
   TELEGRAM_WEBHOOK_URL = https://your-app.up.railway.app
   MINI_APP_URL        = https://your-app.up.railway.app/webapp/
   PORT                = 8080
   ```
4. Railway auto-detects the `Dockerfile` and deploys.
5. **Static files**: Add a `railway.json` or configure Nginx to serve `webapp/` at `/webapp/`.

---

## 🎨 Render Deployment

1. **Create a new Web Service** at [render.com](https://render.com)
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python bot.py`
4. **Environment Variables**:
   ```
   TELEGRAM_BOT_TOKEN  = your_bot_token
   TELEGRAM_WEBHOOK_URL = https://your-service.onrender.com
   MINI_APP_URL        = https://your-service.onrender.com/webapp/
   PORT                = 10000
   ```
5. For the Mini App, create a separate **Static Site** pointing to `webapp/`.

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t halol-crypto-ai .

# Run with environment file
docker run -d \
  --name halol-crypto \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  halol-crypto-ai
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | From @BotFather |
| `MINI_APP_URL` | ✅ | — | HTTPS URL to serve `webapp/` |
| `TELEGRAM_WEBHOOK_URL` | ❌ | — | Leave empty for polling mode |
| `PORT` | ❌ | 8080 | Webhook server port |
| `SQLITE_PATH` | ❌ | halol_crypto.db | Database file path |
| `SCAN_INTERVAL_SECONDS` | ❌ | 300 | Scan interval in seconds |
| `LOG_LEVEL` | ❌ | INFO | DEBUG/INFO/WARNING/ERROR |

---

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Launch bot with full menu |
| `/menu` | Return to main menu |

All navigation is button-based — no typing required.

---

## 📊 Supported Halal Coins (30)

BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK, TON, AVAX, DOT, MATIC, ATOM, LTC, UNI, NEAR, ICP, FIL, APT, ARB, OP, INJ, SUI, TIA, SEI, WLD, PEPE, SHIB, FLOKI, BONK

---

## ⚠️ Disclaimer

> This software is for **educational and informational purposes only**. It is not financial advice. Cryptocurrency trading involves significant risk. Never invest more than you can afford to lose. Always do your own research (DYOR). The developers are not responsible for any financial losses.

---

## 🤝 Halal Principles

- ✅ Spot trading only (owning actual assets)
- ✅ No riba (no leveraged/margin recommendations)
- ✅ No futures or short selling
- ✅ Risk management tools included
- ✅ Educational content on halal vs haram trading

---

*Made with ❤️ for the Muslim crypto community*
