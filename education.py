"""
education.py - Offline educational content for Halol Crypto AI.
No external APIs required. All content is embedded.
"""

from typing import Optional

# ──────────────────────────────────────────────
# Lesson data
# ──────────────────────────────────────────────

LESSONS: dict[str, dict[str, str]] = {

    # ── Crypto Basics ─────────────────────────

    "what_is_bitcoin": {
        "title": "₿ What is Bitcoin?",
        "content": (
            "Bitcoin (BTC) is the world's first decentralised digital currency, "
            "created in 2009 by an anonymous entity known as Satoshi Nakamoto.\n\n"
            "🔑 *Key Facts:*\n"
            "• Fixed supply of 21 million BTC — no inflation by design\n"
            "• Transactions are verified by a global network of computers (miners)\n"
            "• No central bank or government controls it\n"
            "• You are your own bank — full financial sovereignty\n"
            "• Considered digital gold — a store of value\n\n"
            "📌 *Why Halal?*\n"
            "Spot Bitcoin trading involves actual ownership of an asset — no riba (interest), "
            "no leverage, no uncertainty beyond normal market risk.\n\n"
            "💡 *Tip:* Never invest more than you can afford to lose."
        ),
    },

    "what_is_blockchain": {
        "title": "⛓ What is Blockchain?",
        "content": (
            "A blockchain is a distributed digital ledger that records transactions "
            "across thousands of computers simultaneously.\n\n"
            "🔑 *Key Concepts:*\n"
            "• *Block* — a batch of transactions bundled together\n"
            "• *Chain* — each block links to the previous one cryptographically\n"
            "• *Decentralised* — no single point of failure or control\n"
            "• *Immutable* — once recorded, data cannot be altered\n"
            "• *Transparent* — anyone can verify transactions\n\n"
            "🔐 *How it stays secure:*\n"
            "Changing one block would require re-mining every subsequent block — "
            "computationally impossible on large networks.\n\n"
            "🌍 *Real-world use:*\n"
            "Finance, supply chains, healthcare records, digital identity, voting, NFTs."
        ),
    },

    "what_is_spot_trading": {
        "title": "🛒 What is Spot Trading?",
        "content": (
            "Spot trading means buying and selling an actual asset at the current market price — "
            "with immediate settlement.\n\n"
            "✅ *Why Spot Trading is Halal:*\n"
            "• You own the actual asset (BTC, ETH, etc.)\n"
            "• No borrowing, no leverage, no riba\n"
            "• Real value exchange — buyer gets crypto, seller gets money\n"
            "• Risk is limited to your invested capital only\n\n"
            "❌ *What to Avoid (Haram):*\n"
            "• Futures trading — speculating on price without owning the asset\n"
            "• Margin trading — borrowing funds (riba)\n"
            "• Short selling — profiting from falling prices using borrowed assets\n\n"
            "💡 *Example:* You buy 0.01 BTC at $50,000 = $500 investment.\n"
            "You now *own* 0.01 BTC. If it rises to $60,000, your 0.01 BTC = $600.\n"
            "Profit: $100. This is halal spot trading!"
        ),
    },

    # ── Indicators ────────────────────────────

    "what_is_rsi": {
        "title": "📊 What is RSI?",
        "content": (
            "RSI (Relative Strength Index) measures the speed and magnitude of price changes "
            "to identify overbought or oversold conditions.\n\n"
            "📏 *Scale: 0 to 100*\n"
            "• Below 30 → Oversold (potential buy opportunity)\n"
            "• 30 – 50 → Bearish / recovering zone\n"
            "• 50 – 70 → Bullish / neutral zone\n"
            "• Above 70 → Overbought (caution, consider taking profits)\n\n"
            "🔍 *How to read RSI:*\n"
            "• RSI crossing above 50 from below = momentum turning bullish\n"
            "• RSI diverging from price = potential reversal signal\n"
            "• RSI at 30 + price at support = strong buy zone\n\n"
            "⚙️ *Default Period:* 14 candles\n\n"
            "💡 *Pro Tip:* RSI works best when combined with trend indicators like EMA."
        ),
    },

    "what_is_macd": {
        "title": "📈 What is MACD?",
        "content": (
            "MACD (Moving Average Convergence Divergence) tracks the relationship between "
            "two EMAs to show trend direction and momentum.\n\n"
            "🔑 *Components:*\n"
            "• *MACD Line* — EMA(12) minus EMA(26)\n"
            "• *Signal Line* — EMA(9) of the MACD line\n"
            "• *Histogram* — MACD line minus signal line\n\n"
            "📖 *Reading MACD:*\n"
            "• MACD crosses above signal line → Bullish crossover (buy signal)\n"
            "• MACD crosses below signal line → Bearish crossover (exit signal)\n"
            "• Histogram growing above zero → momentum increasing\n"
            "• MACD above zero line → uptrend\n\n"
            "🔍 *MACD Divergence:*\n"
            "• Price makes new low but MACD doesn't → bullish divergence (reversal signal)\n\n"
            "💡 *Best used with:* RSI, Volume, EMA for confirmation."
        ),
    },

    "what_is_ema": {
        "title": "📉 What is EMA?",
        "content": (
            "EMA (Exponential Moving Average) is a moving average that gives more weight "
            "to recent price data, making it more responsive to new information.\n\n"
            "🔑 *Key EMAs used in Halol Crypto AI:*\n"
            "• *EMA 20* — Short-term trend (last ~20 candles)\n"
            "• *EMA 50* — Medium-term trend\n"
            "• *EMA 200* — Long-term trend (the most important)\n\n"
            "📖 *Trading Rules:*\n"
            "• Price above EMA200 → long-term uptrend ✅\n"
            "• EMA20 crosses above EMA50 → Golden Cross (bullish)\n"
            "• EMA20 crosses below EMA50 → Death Cross (bearish, wait)\n"
            "• Price bounces off EMA → dynamic support/resistance\n\n"
            "💡 *Pro Tip:* When EMA20 > EMA50 > EMA200 and price is above all three — "
            "that is the ideal accumulation zone for spot buying."
        ),
    },

    "what_is_atr": {
        "title": "📐 What is ATR?",
        "content": (
            "ATR (Average True Range) measures market volatility — "
            "how much a price typically moves in a given period.\n\n"
            "🔑 *Why ATR matters:*\n"
            "• High ATR → high volatility, wider stop losses needed\n"
            "• Low ATR → calm market, tighter stops acceptable\n"
            "• ATR does NOT indicate direction — only movement size\n\n"
            "🎯 *Using ATR for Stop Loss:*\n"
            "• Stop Loss = Entry Price − (ATR × 1.5)\n"
            "• This ensures stop is placed beyond normal market noise\n\n"
            "📊 *Example:*\n"
            "BTC price = $50,000 | ATR = $800\n"
            "Stop Loss = $50,000 − ($800 × 1.5) = $48,800\n\n"
            "💡 *Rule:* Never set a stop tighter than 1× ATR."
        ),
    },

    "what_is_adx": {
        "title": "💪 What is ADX?",
        "content": (
            "ADX (Average Directional Index) measures trend STRENGTH — "
            "not direction, just how strong the current trend is.\n\n"
            "📏 *ADX Scale:*\n"
            "• Below 20 → Weak trend / sideways market\n"
            "• 20 – 25 → Developing trend\n"
            "• 25 – 40 → Strong trend ✅\n"
            "• Above 40 → Very strong trend\n"
            "• Above 60 → Extreme trend (rare)\n\n"
            "🔑 *Key Insight:*\n"
            "• ADX does NOT tell you if trend is up or down\n"
            "• Use ADX with EMAs: ADX > 25 + EMA trend up = strong buy setup\n"
            "• ADX below 20 = avoid trend-following strategies\n\n"
            "💡 *Best Use:* Filter out weak signals by only trading when ADX > 25."
        ),
    },

    "what_is_bollinger_bands": {
        "title": "📊 What are Bollinger Bands?",
        "content": (
            "Bollinger Bands are volatility bands placed above and below a moving average, "
            "adapting to market conditions automatically.\n\n"
            "🔑 *Three Lines:*\n"
            "• *Upper Band* — SMA + 2 standard deviations\n"
            "• *Middle Band* — 20-period SMA\n"
            "• *Lower Band* — SMA − 2 standard deviations\n\n"
            "📖 *Reading Bollinger Bands:*\n"
            "• Price touches lower band → potentially oversold, watch for bounce\n"
            "• Price touches upper band → potentially overbought\n"
            "• *Band squeeze* (bands narrow) → low volatility, big move incoming\n"
            "• Price walking upper band → strong uptrend\n\n"
            "🎯 *Halol Strategy:*\n"
            "Buy near the lower band when RSI < 40 AND price is above support.\n\n"
            "💡 *Pro Tip:* Bollinger Bands alone are not enough. Combine with RSI + Volume."
        ),
    },

    "what_is_support": {
        "title": "🛡 What is Support?",
        "content": (
            "Support is a price level where buying pressure historically exceeded selling pressure, "
            "causing the price to bounce upward.\n\n"
            "🔑 *Key Concepts:*\n"
            "• Support acts like a floor — price tends to bounce off it\n"
            "• The more times a level is tested, the stronger it becomes\n"
            "• Once support breaks, it often becomes resistance\n\n"
            "📊 *Types of Support:*\n"
            "• *Historical Support* — previous swing lows\n"
            "• *Dynamic Support* — EMA lines acting as support\n"
            "• *Psychological Support* — round numbers ($50,000, $100,000)\n"
            "• *Volume Support* — areas with very high historical volume\n\n"
            "🎯 *Trading Rule:*\n"
            "Buy near support with a stop loss just below it.\n"
            "The closer to support, the better the risk-reward ratio.\n\n"
            "💡 *Tip:* Wait for a confirmation candle before entering at support."
        ),
    },

    "what_is_resistance": {
        "title": "🔴 What is Resistance?",
        "content": (
            "Resistance is a price level where selling pressure historically exceeded buying pressure, "
            "causing the price to reverse downward.\n\n"
            "🔑 *Key Concepts:*\n"
            "• Resistance acts like a ceiling — price struggles to break above it\n"
            "• Once resistance is broken, it often becomes new support\n"
            "• This concept is called 'role reversal'\n\n"
            "📊 *Trading at Resistance:*\n"
            "• When price approaches resistance → consider taking partial profits\n"
            "• When price breaks above resistance with high volume → strong buy\n"
            "• Watch for fakeouts (brief break then reversal)\n\n"
            "🎯 *Breakout Strategy:*\n"
            "1. Wait for clean close above resistance\n"
            "2. Look for retest of breakout level\n"
            "3. Enter on confirmed retest with high volume\n\n"
            "💡 *Tip:* The higher the timeframe, the more significant the resistance level."
        ),
    },

    # ── Smart Money Concepts ──────────────────

    "what_is_order_block": {
        "title": "📦 What is an Order Block?",
        "content": (
            "An Order Block is a price area where large institutional traders (smart money) "
            "placed massive buy or sell orders, causing strong directional moves.\n\n"
            "🔑 *Bullish Order Block:*\n"
            "• Last bearish candle before a strong bullish move\n"
            "• Price often returns to this zone to 'fill' remaining orders\n"
            "• When price revisits the zone → potential strong buy entry\n\n"
            "📖 *How to Identify:*\n"
            "1. Find a strong bullish impulse move\n"
            "2. Look at the last bearish candle before that move\n"
            "3. The body of that candle is the order block\n\n"
            "✅ *Confirmation:*\n"
            "• Price enters the order block zone\n"
            "• RSI shows oversold\n"
            "• Volume increases on entry\n\n"
            "💡 *Key Insight:* Banks and institutions place orders in blocks, not at single prices."
        ),
    },

    "what_is_fvg": {
        "title": "📊 What is a Fair Value Gap (FVG)?",
        "content": (
            "A Fair Value Gap (FVG) is a price imbalance created when price moves so quickly "
            "that no trading occurs between two candles, leaving a 'gap' in market structure.\n\n"
            "🔑 *How FVG Forms:*\n"
            "• Candle 1 high and Candle 3 low don't overlap\n"
            "• The space between them = Fair Value Gap\n"
            "• Price tends to revisit this zone to fill the imbalance\n\n"
            "✅ *Bullish FVG Setup:*\n"
            "1. Price creates a bullish FVG (gap above)\n"
            "2. Price pulls back into the FVG zone\n"
            "3. RSI shows oversold / Order Block present\n"
            "4. Enter long with stop below the FVG\n\n"
            "🎯 *Target:* Price typically moves to close the FVG fully.\n\n"
            "💡 *Halol Tip:* FVGs near key support levels = highest probability entries."
        ),
    },

    "what_is_bos": {
        "title": "💥 What is Break of Structure (BOS)?",
        "content": (
            "A Break of Structure (BOS) occurs when price breaks a previous significant swing high "
            "(in an uptrend) or swing low (in a downtrend), confirming trend continuation.\n\n"
            "🔑 *Bullish BOS:*\n"
            "• Price makes a new Higher High above the previous swing high\n"
            "• Confirms the uptrend is intact and continuing\n"
            "• Signal to look for buy entries on pullback\n\n"
            "📖 *BOS vs CHoCH:*\n"
            "• BOS = trend continuation (same direction)\n"
            "• CHoCH = trend reversal (direction change)\n\n"
            "🎯 *Trading BOS:*\n"
            "1. Identify swing highs and lows\n"
            "2. Wait for price to break above last swing high\n"
            "3. Look for pullback to previous resistance (now support)\n"
            "4. Enter with stop below the pullback low\n\n"
            "💡 *Key Rule:* BOS on higher timeframes (4H, Daily) = stronger signal."
        ),
    },

    "what_is_choch": {
        "title": "🔄 What is Change of Character (CHoCH)?",
        "content": (
            "A Change of Character (CHoCH) is the first sign that a trend is reversing. "
            "It signals a shift in market structure from bearish to bullish (or vice versa).\n\n"
            "🔑 *Bullish CHoCH:*\n"
            "• In a downtrend, price breaks above the last swing high\n"
            "• This is the FIRST sign that selling pressure is weakening\n"
            "• Not confirmed reversal — but strong early warning\n\n"
            "📖 *CHoCH vs BOS:*\n"
            "• CHoCH = against the current trend (reversal signal)\n"
            "• BOS = with the current trend (continuation signal)\n\n"
            "🎯 *Trading CHoCH:*\n"
            "• Do NOT enter immediately on CHoCH\n"
            "• Wait for a BOS confirmation after CHoCH\n"
            "• CHoCH + BOS = high confidence reversal entry\n\n"
            "💡 *Smart Money Flow:* Institutions distribute at highs → CHoCH → accumulate at lows → BOS up."
        ),
    },

    "what_is_liquidity_sweep": {
        "title": "💧 What is a Liquidity Sweep?",
        "content": (
            "A Liquidity Sweep occurs when price temporarily breaks through a key level "
            "(equal highs or lows where stop losses cluster) to fill large institutional orders, "
            "then reverses sharply.\n\n"
            "🔑 *Low Sweep (Bullish):*\n"
            "• Price dips below obvious support / equal lows\n"
            "• Stop losses of retail traders are triggered\n"
            "• Institutions buy the triggered stops cheaply\n"
            "• Price reverses sharply upward\n\n"
            "🎯 *Trading a Liquidity Sweep:*\n"
            "1. Identify key support level (equal lows)\n"
            "2. Wait for price to sweep below (wick down)\n"
            "3. Watch for strong bullish candle close above support\n"
            "4. Enter long with stop below the sweep wick\n\n"
            "⚠️ *Warning:* Not every sweep reverses — always wait for close confirmation.\n\n"
            "💡 *Smart Money Reality:* Big players need liquidity to fill orders. Retail stops = liquidity."
        ),
    },

    "what_is_breakout_retest": {
        "title": "🚀 What is Breakout Retest?",
        "content": (
            "A Breakout Retest occurs when price breaks above a key resistance level, "
            "then pulls back to test the broken resistance as new support before continuing higher.\n\n"
            "🔑 *Breakout Retest Stages:*\n"
            "1. *Consolidation* — price builds energy near resistance\n"
            "2. *Breakout* — strong candle closes above resistance\n"
            "3. *Retest* — price pulls back to the broken level\n"
            "4. *Bounce* — price bounces off old resistance (now support)\n"
            "5. *Continuation* — price moves to new highs\n\n"
            "✅ *High Probability Setup:*\n"
            "• Volume increases on breakout\n"
            "• Retest shows decreasing volume\n"
            "• Bounce shows increasing volume\n"
            "• RSI stays above 50 during retest\n\n"
            "💡 *Best Risk:Reward:* Enter on retest, stop below retest level, target = 2× breakout range."
        ),
    },

    # ── Risk Management ───────────────────────

    "what_is_stop_loss": {
        "title": "🛑 What is Stop Loss?",
        "content": (
            "A Stop Loss is a pre-set order that automatically sells your position if price "
            "falls to a specified level, limiting your maximum loss.\n\n"
            "🔑 *Why Stop Loss is Essential:*\n"
            "• Protects capital from catastrophic losses\n"
            "• Removes emotion from trading decisions\n"
            "• Allows you to sleep without watching the screen\n"
            "• Professional traders ALWAYS use stop losses\n\n"
            "📊 *How to Set Stop Loss:*\n"
            "• ATR Method: Entry − (1.5 × ATR)\n"
            "• Structure Method: Below key support level\n"
            "• Percentage Method: 3-5% below entry\n\n"
            "🚫 *NEVER:*\n"
            "• Move stop loss further away when losing\n"
            "• Trade without a stop loss\n"
            "• Risk more than 2% of capital per trade\n\n"
            "💡 *Islamic Perspective:* Using stop losses is good risk management (hikmah), not gambling."
        ),
    },

    "what_is_take_profit": {
        "title": "🎯 What is Take Profit?",
        "content": (
            "Take Profit (TP) is a pre-set order to automatically sell a portion (or all) of "
            "your position when price reaches a target level, locking in gains.\n\n"
            "🔑 *Multi-Level Take Profit Strategy:*\n"
            "• *TP1* — First target (1.5:1 reward:risk)\n"
            "  → Sell 30-40% of position, move stop to breakeven\n"
            "• *TP2* — Second target (2.5:1 reward:risk)\n"
            "  → Sell another 30-40% of position\n"
            "• *TP3* — Final target (4:1 reward:risk)\n"
            "  → Sell remaining position\n\n"
            "✅ *Benefits of Multi-TP:*\n"
            "• Locks in profit early\n"
            "• Reduces psychological pressure\n"
            "• Allows remaining position to run with free money\n\n"
            "💡 *Halol Rule:* Always set TP before entering. Don't change TP out of greed."
        ),
    },

    "what_is_risk_reward": {
        "title": "⚖️ What is Risk:Reward Ratio?",
        "content": (
            "Risk:Reward (R:R) Ratio compares how much you risk to how much you can gain, "
            "helping you decide if a trade is mathematically worth taking.\n\n"
            "📊 *Calculation:*\n"
            "R:R = (Target Price − Entry) ÷ (Entry − Stop Loss)\n\n"
            "✅ *Example:*\n"
            "• Entry: $100\n"
            "• Stop Loss: $95 → Risk = $5\n"
            "• Take Profit: $115 → Reward = $15\n"
            "• R:R = $15 / $5 = 1:3 ✅ (excellent)\n\n"
            "📏 *Minimum Acceptable R:R:*\n"
            "• Below 1:1.5 → Avoid the trade\n"
            "• 1:2 → Acceptable\n"
            "• 1:3 or higher → Excellent ✅\n\n"
            "💡 *Key Insight:* With 1:2 R:R, you only need to win 34% of trades to be profitable.\n"
            "With 1:3 R:R, you only need to win 25% of trades!"
        ),
    },

    "what_is_position_sizing": {
        "title": "💰 What is Position Sizing?",
        "content": (
            "Position Sizing determines how much capital to allocate to a single trade, "
            "ensuring one loss never devastates your portfolio.\n\n"
            "🔑 *The 2% Rule:*\n"
            "Never risk more than 2% of total portfolio on a single trade.\n\n"
            "📊 *Calculation:*\n"
            "Position Size = (Portfolio × Risk%) ÷ (Entry − Stop Loss)\n\n"
            "✅ *Example:*\n"
            "• Portfolio: $10,000\n"
            "• Risk: 2% = $200\n"
            "• Entry: $100 | Stop Loss: $95 → Distance = $5\n"
            "• Position Size = $200 ÷ $5 = 40 units\n\n"
            "🏦 *Portfolio Allocation for Spot:*\n"
            "• 40-50% in BTC/ETH (safer)\n"
            "• 30-40% in top altcoins\n"
            "• 10-20% in higher-risk opportunities\n"
            "• Always keep 20% in cash/stablecoin\n\n"
            "💡 *Rule:* A 50% loss requires a 100% gain to recover. Protect your capital first."
        ),
    },

    # ── Technical Analysis ────────────────────

    "candlestick_patterns": {
        "title": "🕯 Candlestick Patterns Guide",
        "content": (
            "Candlestick patterns are visual signals formed by one or more candles that "
            "indicate potential price reversals or continuations.\n\n"
            "🟢 *Bullish Reversal Patterns:*\n"
            "• *Hammer* — small body, long lower wick, at support → buyers rejected lower prices\n"
            "• *Bullish Engulfing* — large green candle completely engulfs previous red candle\n"
            "• *Morning Star* — 3-candle pattern: red + small doji + large green\n"
            "• *Inverted Hammer* — long upper wick at bottom → buyers testing higher prices\n"
            "• *Dragonfly Doji* — opens and closes at high, long lower wick\n\n"
            "⚡ *Continuation Patterns:*\n"
            "• *Three White Soldiers* — 3 consecutive green candles = strong uptrend\n"
            "• *Rising Three Methods* — brief consolidation within uptrend then continuation\n\n"
            "⚠️ *Bearish Warning Patterns (consider taking profits):*\n"
            "• *Shooting Star* — long upper wick after uptrend\n"
            "• *Bearish Engulfing* — large red candle engulfs green\n"
            "• *Evening Star* — green + doji + red\n\n"
            "💡 *Rule:* Never trade a pattern in isolation. Confirm with RSI, volume, and structure."
        ),
    },

    "risk_management_overview": {
        "title": "⚠️ Risk Management Overview",
        "content": (
            "Risk Management is the most important skill in trading — more important than any indicator.\n\n"
            "🏛 *The 5 Golden Rules:*\n\n"
            "1️⃣ *Never risk more than 2% per trade*\n"
            "   → Even 10 losses in a row = only 18% drawdown\n\n"
            "2️⃣ *Always use a stop loss*\n"
            "   → No exceptions. Ever.\n\n"
            "3️⃣ *Minimum 1:2 Risk:Reward*\n"
            "   → Every trade must have a target 2× your risk\n\n"
            "4️⃣ *Diversify across multiple coins*\n"
            "   → Never put all capital in one trade\n\n"
            "5️⃣ *Keep 20% in cash*\n"
            "   → Always have dry powder for opportunities\n\n"
            "🧠 *Psychology Rules:*\n"
            "• Never chase FOMO (fear of missing out)\n"
            "• Don't revenge trade after a loss\n"
            "• Follow your plan, not your emotions\n"
            "• Take breaks after 3 consecutive losses\n\n"
            "💡 *Islamic Principle:* Tawakkul — do your best analysis, set your plan, then accept the outcome."
        ),
    },

    "faq": {
        "title": "❓ Frequently Asked Questions",
        "content": (
            "🔶 *Is crypto trading halal?*\n"
            "Spot trading (buying and owning actual assets) is generally considered permissible "
            "by many Islamic scholars. Futures, margin, and leveraged trading are generally considered "
            "haram due to riba and excessive gharar (uncertainty).\n\n"
            "🔶 *Why no sell signals?*\n"
            "We focus on spot buying opportunities. In halal spot investing, you hold until "
            "your TP is reached. No shorting or selling borrowed assets.\n\n"
            "🔶 *How accurate are the signals?*\n"
            "Signals are based on technical analysis — not financial advice. "
            "Past patterns do not guarantee future results. Always do your own research.\n\n"
            "🔶 *Which coins are supported?*\n"
            "30 halal spot coins including BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK, TON and more.\n\n"
            "🔶 *How often are signals updated?*\n"
            "Every 5 minutes by the background scanner.\n\n"
            "🔶 *Is this financial advice?*\n"
            "No. This is educational and analytical software only. "
            "Never invest more than you can afford to lose.\n\n"
            "🔶 *How do I add a coin to my watchlist?*\n"
            "Go to ⭐ Watchlist → Add Coin → Select from the list."
        ),
    },
}

# ──────────────────────────────────────────────
# Category menus
# ──────────────────────────────────────────────

CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "crypto_basics": [
        ("₿ What is Bitcoin?",       "what_is_bitcoin"),
        ("⛓ What is Blockchain?",    "what_is_blockchain"),
        ("🛒 What is Spot Trading?",  "what_is_spot_trading"),
    ],
    "indicators": [
        ("📊 RSI",              "what_is_rsi"),
        ("📈 MACD",             "what_is_macd"),
        ("📉 EMA",              "what_is_ema"),
        ("📐 ATR",              "what_is_atr"),
        ("💪 ADX",              "what_is_adx"),
        ("📊 Bollinger Bands",  "what_is_bollinger_bands"),
        ("🛡 Support",          "what_is_support"),
        ("🔴 Resistance",       "what_is_resistance"),
    ],
    "smc": [
        ("📦 Order Block",        "what_is_order_block"),
        ("📊 Fair Value Gap",     "what_is_fvg"),
        ("💥 Break of Structure", "what_is_bos"),
        ("🔄 Change of Character","what_is_choch"),
        ("💧 Liquidity Sweep",    "what_is_liquidity_sweep"),
        ("🚀 Breakout Retest",    "what_is_breakout_retest"),
    ],
    "risk_management": [
        ("🛑 Stop Loss",         "what_is_stop_loss"),
        ("🎯 Take Profit",       "what_is_take_profit"),
        ("⚖️ Risk:Reward",       "what_is_risk_reward"),
        ("💰 Position Sizing",   "what_is_position_sizing"),
        ("⚠️ Risk Management Overview", "risk_management_overview"),
    ],
    "candlestick": [
        ("🕯 Candlestick Patterns", "candlestick_patterns"),
    ],
    "faq": [
        ("❓ FAQ", "faq"),
    ],
}


def get_lesson(key: str) -> Optional[dict]:
    return LESSONS.get(key)


def get_category_items(category: str) -> list[tuple[str, str]]:
    return CATEGORIES.get(category, [])
