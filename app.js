/**
 * app.js — Halol Crypto AI Telegram Mini App
 * Mobile-first, dark mode, full crypto dashboard.
 * HALAL SPOT ONLY — no sell/short signals.
 */

'use strict';

// ══════════════════════════════════════════════
// Telegram WebApp init
// ══════════════════════════════════════════════
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  if (tg.setHeaderColor) tg.setHeaderColor('#0a0e1a');
  if (tg.setBackgroundColor) tg.setBackgroundColor('#0a0e1a');
}

// ══════════════════════════════════════════════
// Constants
// ══════════════════════════════════════════════
const BINANCE_TICKER_URL  = 'https://api.binance.com/api/v3/ticker/24hr';
const BINANCE_KLINES_URL  = 'https://api.binance.com/api/v3/klines';

const HALAL_COINS = [
  'BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK','TON','AVAX',
  'DOT','MATIC','ATOM','LTC','UNI','NEAR','ICP','FIL','APT','ARB',
  'OP','INJ','SUI','TIA','SEI','WLD','PEPE','SHIB','FLOKI','BONK',
];

const COIN_EMOJI = {
  BTC:'₿', ETH:'⟠', BNB:'🔶', SOL:'◎', XRP:'💧',
  ADA:'🌊', DOGE:'🐕', LINK:'🔗', TON:'💎', AVAX:'🔺',
  DOT:'⚫', MATIC:'🟣', ATOM:'⚛', LTC:'🥈', UNI:'🦄',
  NEAR:'🌐', ICP:'♾', FIL:'📂', APT:'🍎', ARB:'🔵',
  OP:'🔴', INJ:'💉', SUI:'🌊', TIA:'🌌', SEI:'🔷',
  WLD:'🌍', PEPE:'🐸', SHIB:'🐕', FLOKI:'🐕', BONK:'🐶',
};

// ══════════════════════════════════════════════
// State
// ══════════════════════════════════════════════
const state = {
  currentPage: 'home',
  previousPage: null,
  watchlist: JSON.parse(localStorage.getItem('halol_watchlist') || '[]'),
  signalCache: JSON.parse(localStorage.getItem('halol_signals') || '{}'),
  timeframe: localStorage.getItem('halol_tf') || '1h',
  currentDetailSymbol: null,
  eduPreviousPage: null,
};

// ══════════════════════════════════════════════
// Navigation
// ══════════════════════════════════════════════
function switchPage(pageId) {
  const pages = document.querySelectorAll('.page');
  pages.forEach(p => p.classList.remove('active'));
  const target = document.getElementById(`page-${pageId}`);
  if (target) target.classList.add('active');

  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(n => n.classList.remove('active'));
  const navItem = document.querySelector(`[data-page="${pageId}"]`);
  if (navItem) navItem.classList.add('active');

  state.previousPage = state.currentPage;
  state.currentPage = pageId;

  // Trigger page-specific init
  if (pageId === 'home')      initHomePage();
  if (pageId === 'signals')   initSignalsPage();
  if (pageId === 'watchlist') initWatchlistPage();
  if (pageId === 'market')    loadMarketData();
  if (pageId === 'settings')  initSettings();
}

// Nav buttons
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => switchPage(btn.dataset.page));
});

// ══════════════════════════════════════════════
// Utility
// ══════════════════════════════════════════════
function formatPrice(p) {
  if (!p) return '—';
  if (p >= 1000) return '$' + p.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
  if (p >= 1)    return '$' + p.toFixed(4);
  return '$' + p.toFixed(6);
}

function formatChange(pct) {
  const n = parseFloat(pct) || 0;
  return (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
}

function signalClass(signal) {
  if (!signal) return 'wait';
  if (signal.includes('Strong Buy')) return 'strong-buy';
  if (signal.includes('Buy'))        return 'buy';
  if (signal.includes('Profit'))     return 'profit';
  return 'wait';
}

function signalLabel(signal) {
  if (!signal) return 'Wait';
  if (signal.includes('Strong Buy')) return 'Strong Buy';
  if (signal.includes('Buy'))        return 'Buy';
  if (signal.includes('Profit'))     return 'Profit Zone';
  return 'Wait';
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

async function fetchJSON(url, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const fullUrl = qs ? `${url}?${qs}` : url;
  try {
    const res = await fetch(fullUrl, { signal: AbortSignal.timeout(10000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn('fetchJSON failed:', fullUrl, e.message);
    return null;
  }
}

// ══════════════════════════════════════════════
// Technical Analysis (client-side)
// ══════════════════════════════════════════════
const TA = {
  ema(prices, period) {
    if (prices.length < period) return new Array(prices.length).fill(null);
    const k = 2 / (period + 1);
    const res = new Array(period - 1).fill(null);
    let seed = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
    res.push(seed);
    for (let i = period; i < prices.length; i++) {
      seed = prices[i] * k + seed * (1 - k);
      res.push(seed);
    }
    return res;
  },

  rsi(prices, period = 14) {
    const res = new Array(period).fill(null);
    const changes = prices.slice(1).map((v, i) => v - prices[i]);
    if (changes.length < period) return new Array(prices.length).fill(null);
    let avgG = changes.slice(0, period).reduce((a, c) => a + Math.max(0, c), 0) / period;
    let avgL = changes.slice(0, period).reduce((a, c) => a + Math.abs(Math.min(0, c)), 0) / period;
    const rsiVal = (ag, al) => al === 0 ? 100 : 100 - (100 / (1 + ag / al));
    res.push(rsiVal(avgG, avgL));
    for (let i = period; i < changes.length; i++) {
      avgG = (avgG * (period - 1) + Math.max(0, changes[i])) / period;
      avgL = (avgL * (period - 1) + Math.abs(Math.min(0, changes[i]))) / period;
      res.push(rsiVal(avgG, avgL));
    }
    return res;
  },

  last(arr) { return arr.slice().reverse().find(v => v != null) ?? 0; },

  supportResistance(highs, lows, lookback = 50) {
    const h = highs.slice(-lookback);
    const l = lows.slice(-lookback);
    return { support: Math.min(...l), resistance: Math.max(...h) };
  },

  volumeRatio(volumes, period = 20) {
    if (volumes.length < period) return 1;
    const avg = volumes.slice(-period).reduce((a, b) => a + b, 0) / period;
    return avg > 0 ? volumes[volumes.length - 1] / avg : 1;
  },

  score(data) {
    const { opens, highs, lows, closes, volumes } = data;
    if (closes.length < 50) return null;

    let score = 0, max = 0;
    const bullish = [], caution = [];
    const current = closes[closes.length - 1];

    // EMA
    const e20  = TA.last(TA.ema(closes, 20));
    const e50  = TA.last(TA.ema(closes, 50));
    const e200 = closes.length >= 200 ? TA.last(TA.ema(closes, 200)) : null;

    if (e20 && e50) {
      max += 10;
      if (e20 > e50) { score += 10; bullish.push('EMA20 > EMA50'); }
      else caution.push('EMA20 < EMA50');
    }
    if (e50 && e200) {
      max += 10;
      if (e50 > e200) { score += 10; bullish.push('EMA50 > EMA200 (golden zone)'); }
    }
    if (e20 && current > e20) { max += 5; score += 5; bullish.push('Price above EMA20'); }

    // RSI
    const rsiVal = TA.last(TA.rsi(closes));
    max += 15;
    if (rsiVal >= 30 && rsiVal < 40) { score += 15; bullish.push(`RSI ${rsiVal.toFixed(1)} (oversold recovery)`); }
    else if (rsiVal < 30) { score += 12; bullish.push(`RSI ${rsiVal.toFixed(1)} (deeply oversold)`); }
    else if (rsiVal >= 40 && rsiVal <= 60) { score += 10; }
    else if (rsiVal > 70) caution.push(`RSI ${rsiVal.toFixed(1)} (overbought)`);

    // Volume
    const relVol = TA.volumeRatio(volumes);
    max += 10;
    if (relVol >= 2)      { score += 10; bullish.push(`Volume spike ${relVol.toFixed(1)}x`); }
    else if (relVol >= 1.3) { score += 6; bullish.push(`Above avg volume ${relVol.toFixed(1)}x`); }

    // Support
    const sr = TA.supportResistance(highs, lows, closes);
    max += 10;
    const distSup = (current - sr.support) / current;
    if (distSup > 0 && distSup < 0.04) { score += 10; bullish.push(`Near support ${formatPrice(sr.support)}`); }
    else if (distSup > 0 && distSup < 0.08) score += 5;

    // SMC simple checks
    const prev20H = Math.max(...highs.slice(-20, -2));
    const prev20L = Math.min(...lows.slice(-20, -2));
    max += 15;
    if (lows[lows.length - 1] < prev20L && closes[closes.length - 1] > prev20L) {
      score += 8; bullish.push('Liquidity sweep (low sweep)');
    }
    if (closes[closes.length - 1] > prev20H) {
      score += 7; bullish.push('Breakout above recent highs');
    }

    const finalScore = Math.round(Math.min(100, Math.max(0, (score / max) * 100)));
    const extended = e200 && current > e200 * 1.1;

    let signal;
    if (extended && finalScore >= 80) signal = '💰 Profit Taking Zone';
    else if (finalScore >= 75) signal = '🟢 Strong Buy';
    else if (finalScore >= 55) signal = '🟢 Buy';
    else signal = '🟡 Wait';

    const trend = (e20 && e50 && e200 && current > e200 && e50 > e200) ? 'Strong Uptrend'
                : (e20 && e50 && current > e50) ? 'Uptrend'
                : (e20 && e50 && current < e50) ? 'Downtrend'
                : 'Sideways';

    // Trade plan
    const slDist = Math.max(current * 0.035, current * 0.02);
    const sl = current - slDist;
    const tp1 = current + slDist * 1.5;
    const tp2 = current + slDist * 2.5;
    const tp3 = current + slDist * 4.0;

    return {
      score: finalScore,
      signal,
      trend,
      momentum: rsiVal > 60 ? 'Strong' : rsiVal > 50 ? 'Moderate' : rsiVal < 40 ? 'Weak' : 'Neutral',
      risk: finalScore >= 70 ? 'Low-Medium' : 'Medium',
      confidence: finalScore,
      rsi: rsiVal.toFixed(1),
      ema20: e20?.toFixed(4),
      ema50: e50?.toFixed(4),
      ema200: e200?.toFixed(4),
      relVolume: relVol.toFixed(2),
      support: sr.support,
      resistance: sr.resistance,
      bullish,
      caution,
      price: current,
      tradePlan: {
        entry: formatPrice(current),
        sl: formatPrice(sl),
        tp1: formatPrice(tp1),
        tp2: formatPrice(tp2),
        tp3: formatPrice(tp3),
        rr: '1:2.5',
      },
    };
  }
};

// ══════════════════════════════════════════════
// Data fetching
// ══════════════════════════════════════════════
async function fetchKlines(symbol, interval = '1h', limit = 200) {
  const data = await fetchJSON(BINANCE_KLINES_URL, {
    symbol: `${symbol}USDT`, interval, limit,
  });
  if (!data) return null;
  return {
    opens:   data.map(k => parseFloat(k[1])),
    highs:   data.map(k => parseFloat(k[2])),
    lows:    data.map(k => parseFloat(k[3])),
    closes:  data.map(k => parseFloat(k[4])),
    volumes: data.map(k => parseFloat(k[5])),
  };
}

async function fetchTicker(symbol) {
  return fetchJSON(BINANCE_TICKER_URL, { symbol: `${symbol}USDT` });
}

async function fetchMultipleTickers(symbols) {
  const results = await Promise.allSettled(symbols.map(s => fetchTicker(s)));
  return results.map((r, i) => {
    if (r.status === 'fulfilled' && r.value) {
      return {
        symbol: symbols[i],
        price: parseFloat(r.value.lastPrice),
        change: parseFloat(r.value.priceChangePercent),
        volume: parseFloat(r.value.quoteVolume),
      };
    }
    return { symbol: symbols[i], price: 0, change: 0, volume: 0 };
  });
}

// ══════════════════════════════════════════════
// HOME PAGE
// ══════════════════════════════════════════════
async function initHomePage() {
  loadSentimentCard();
  loadTopSignals();
}

async function loadSentimentCard() {
  try {
    const [btc, eth] = await Promise.all([fetchTicker('BTC'), fetchTicker('ETH')]);
    if (btc) {
      document.getElementById('btcPrice').textContent = formatPrice(parseFloat(btc.lastPrice));
      const chgEl = document.getElementById('btcChange');
      const chg = parseFloat(btc.priceChangePercent);
      chgEl.textContent = formatChange(chg);
      chgEl.className = 'sentiment-chg ' + (chg >= 0 ? 'positive' : 'negative');
    }
    if (eth) {
      document.getElementById('ethPrice').textContent = formatPrice(parseFloat(eth.lastPrice));
      const chgEl = document.getElementById('ethChange');
      const chg = parseFloat(eth.priceChangePercent);
      chgEl.textContent = formatChange(chg);
      chgEl.className = 'sentiment-chg ' + (chg >= 0 ? 'positive' : 'negative');
    }
    // Sentiment from cache
    const cached = Object.values(state.signalCache);
    if (cached.length > 0) {
      const buys = cached.filter(s => s.signal?.includes('Buy')).length;
      const ratio = buys / cached.length;
      const badge = document.getElementById('sentimentBadge');
      badge.textContent = ratio > 0.5 ? 'Bullish' : ratio < 0.35 ? 'Bearish' : 'Neutral';
      badge.className = 'sentiment-badge ' + (ratio > 0.5 ? 'bullish' : ratio < 0.35 ? 'bearish' : 'neutral');
    }
  } catch(e) { console.warn('Sentiment load error', e); }
}

async function loadTopSignals() {
  const grid = document.getElementById('topSignalsGrid');
  // Use cache first
  const cached = Object.entries(state.signalCache)
    .map(([sym, sig]) => ({ symbol: sym, ...sig }))
    .sort((a, b) => (b.score || 0) - (a.score || 0))
    .slice(0, 6);

  if (cached.length > 0) {
    renderTopSignalsGrid(cached);
    return;
  }

  // Quick fetch top 6
  const top6 = ['BTC','ETH','BNB','SOL','XRP','ADA'];
  const promises = top6.map(sym => fetchKlines(sym, state.timeframe, 100).then(data => {
    if (!data) return null;
    const sig = TA.score(data);
    if (!sig) return null;
    sig.symbol = sym;
    sig.price = data.closes[data.closes.length - 1];
    state.signalCache[sym] = sig;
    return sig;
  }));
  const results = (await Promise.all(promises)).filter(Boolean);
  localStorage.setItem('halol_signals', JSON.stringify(state.signalCache));
  renderTopSignalsGrid(results.sort((a, b) => b.score - a.score));
}

function renderTopSignalsGrid(signals) {
  const grid = document.getElementById('topSignalsGrid');
  if (!signals.length) {
    grid.innerHTML = '<p style="color:var(--text-muted);font-size:13px;grid-column:1/-1;text-align:center;padding:16px">No signal data yet</p>';
    return;
  }
  grid.innerHTML = signals.slice(0, 6).map(sig => {
    const cls = signalClass(sig.signal);
    const lbl = signalLabel(sig.signal);
    const emoji = COIN_EMOJI[sig.symbol] || '🪙';
    return `
      <div class="signal-mini-card ${cls}" onclick="showSignalDetail('${sig.symbol}')">
        <span class="signal-mini-symbol">${emoji} ${sig.symbol}</span>
        <span class="signal-mini-score ${cls}">${sig.score}%</span>
        <span class="signal-mini-label">${lbl}</span>
      </div>
    `;
  }).join('');
}

// ══════════════════════════════════════════════
// SIGNALS PAGE
// ══════════════════════════════════════════════
function initSignalsPage() {
  renderCoinsGrid(HALAL_COINS);
  // Background: fetch cached signals for display
  updateCoinGridFromCache();
}

function filterCoins(query) {
  const q = query.trim().toUpperCase();
  const filtered = q ? HALAL_COINS.filter(c => c.includes(q)) : HALAL_COINS;
  renderCoinsGrid(filtered);
}

function renderCoinsGrid(coins) {
  const grid = document.getElementById('coinsGrid');
  if (!coins.length) {
    grid.innerHTML = '<p style="color:var(--text-muted);font-size:13px;text-align:center;padding:20px;grid-column:1/-1">No coins found</p>';
    return;
  }
  grid.innerHTML = coins.map(sym => {
    const sig = state.signalCache[sym];
    const emoji = COIN_EMOJI[sym] || '🪙';
    const cls = sig ? signalClass(sig.signal) : '';
    const lbl = sig ? signalLabel(sig.signal) : '';
    const score = sig ? `${sig.score}%` : '—';
    return `
      <div class="coin-card" onclick="showSignalDetail('${sym}')">
        <span class="coin-emoji">${emoji}</span>
        <span class="coin-symbol">${sym}</span>
        <span class="coin-score">${score}</span>
        ${lbl ? `<span class="coin-signal ${cls}">${lbl}</span>` : ''}
      </div>
    `;
  }).join('');
}

async function updateCoinGridFromCache() {
  // Load a few coins in background
  const batch = HALAL_COINS.slice(0, 15);
  for (const sym of batch) {
    if (state.signalCache[sym]) continue;
    try {
      const klines = await fetchKlines(sym, state.timeframe, 100);
      if (klines) {
        const sig = TA.score(klines);
        if (sig) {
          sig.symbol = sym;
          sig.price = klines.closes[klines.closes.length - 1];
          state.signalCache[sym] = sig;
        }
      }
    } catch(e) {}
    await new Promise(r => setTimeout(r, 200));
  }
  localStorage.setItem('halol_signals', JSON.stringify(state.signalCache));
  if (state.currentPage === 'signals') {
    const q = document.getElementById('signalSearch')?.value || '';
    filterCoins(q);
  }
  if (state.currentPage === 'home') renderTopSignalsGrid(
    Object.entries(state.signalCache)
      .map(([sym, sig]) => ({ symbol: sym, ...sig }))
      .sort((a, b) => (b.score||0) - (a.score||0))
      .slice(0, 6)
  );
}

// ══════════════════════════════════════════════
// SIGNAL DETAIL
// ══════════════════════════════════════════════
async function showSignalDetail(symbol) {
  state.currentDetailSymbol = symbol;
  const emoji = COIN_EMOJI[symbol] || '🪙';

  // Show detail page
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-signal-detail').classList.add('active');
  document.getElementById('detailTitle').textContent = `${emoji} ${symbol}`;

  const wlBtn = document.getElementById('detailWatchlistBtn');
  wlBtn.textContent = state.watchlist.includes(symbol) ? '⭐' : '☆';

  const content = document.getElementById('signalDetailContent');
  content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Analysing ' + symbol + '...</p></div>';

  try {
    let sig = state.signalCache[symbol];
    if (!sig) {
      const klines = await fetchKlines(symbol, state.timeframe);
      if (klines) {
        sig = TA.score(klines);
        if (sig) {
          sig.symbol = symbol;
          sig.price = klines.closes[klines.closes.length - 1];
          state.signalCache[symbol] = sig;
          localStorage.setItem('halol_signals', JSON.stringify(state.signalCache));
        }
      }
    }

    // Get live price
    const ticker = await fetchTicker(symbol);
    const livePrice = ticker ? parseFloat(ticker.lastPrice) : sig?.price || 0;
    const change24h = ticker ? parseFloat(ticker.priceChangePercent) : 0;

    if (!sig) {
      content.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">⚠️</span>
          <p>Could not load signal</p>
          <small>Binance may be temporarily unavailable</small>
          <button class="btn-primary" onclick="showSignalDetail('${symbol}')">Retry</button>
        </div>`;
      return;
    }

    const cls = signalClass(sig.signal);
    const lbl = signalLabel(sig.signal);
    const pct = change24h;

    content.innerHTML = `
      <!-- Score overview -->
      <div class="signal-detail-score">
        <div class="score-circle">
          <span class="score-number" style="color:${cls==='strong-buy'?'#22c55e':cls==='buy'?'#10b981':cls==='profit'?'#f59e0b':'#f59e0b'}">${sig.score}</span>
          <span class="score-label">Score</span>
        </div>
        <span class="score-signal">${sig.signal}</span>
        <div style="width:100%">
          <div class="score-bar-container">
            <div class="score-bar ${cls}" style="width:${sig.score}%"></div>
          </div>
        </div>
        <div style="font-size:13px;color:var(--text-secondary);text-align:center">
          ${formatPrice(livePrice)}
          <span style="color:${pct>=0?'#10b981':'#ef4444'};margin-left:8px">${formatChange(pct)}</span>
        </div>
      </div>

      <!-- Metrics -->
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Trend</div>
          <div class="metric-value">${sig.trend}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Momentum</div>
          <div class="metric-value">${sig.momentum}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">RSI</div>
          <div class="metric-value">${sig.rsi}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Confidence</div>
          <div class="metric-value">${sig.confidence}%</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Risk</div>
          <div class="metric-value">${sig.risk}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Rel. Volume</div>
          <div class="metric-value">${sig.relVolume}x</div>
        </div>
      </div>

      <!-- Trade Plan -->
      <div class="trade-plan-card">
        <div class="trade-plan-title">📋 Trade Plan</div>
        <div class="trade-plan-row">
          <span class="tp-label">🟢 Entry</span>
          <span class="tp-value entry">${sig.tradePlan.entry}</span>
        </div>
        <div class="trade-plan-row">
          <span class="tp-label">🛑 Stop Loss</span>
          <span class="tp-value sl">${sig.tradePlan.sl}</span>
        </div>
        <div class="trade-plan-row">
          <span class="tp-label">🎯 TP1</span>
          <span class="tp-value tp1">${sig.tradePlan.tp1}</span>
        </div>
        <div class="trade-plan-row">
          <span class="tp-label">🎯 TP2</span>
          <span class="tp-value tp2">${sig.tradePlan.tp2}</span>
        </div>
        <div class="trade-plan-row">
          <span class="tp-label">🎯 TP3</span>
          <span class="tp-value tp3">${sig.tradePlan.tp3}</span>
        </div>
        <div class="trade-plan-row">
          <span class="tp-label">⚖️ R:R Ratio</span>
          <span class="tp-value">${sig.tradePlan.rr}</span>
        </div>
      </div>

      <!-- Key Levels -->
      <div class="card">
        <div class="trade-plan-title">📐 Key Levels</div>
        <div class="trade-plan-row">
          <span class="tp-label">🛡 Support</span>
          <span class="tp-value">${formatPrice(sig.support)}</span>
        </div>
        <div class="trade-plan-row">
          <span class="tp-label">🔴 Resistance</span>
          <span class="tp-value">${formatPrice(sig.resistance)}</span>
        </div>
        ${sig.ema20 ? `<div class="trade-plan-row"><span class="tp-label">EMA20</span><span class="tp-value">${formatPrice(parseFloat(sig.ema20))}</span></div>` : ''}
        ${sig.ema50 ? `<div class="trade-plan-row"><span class="tp-label">EMA50</span><span class="tp-value">${formatPrice(parseFloat(sig.ema50))}</span></div>` : ''}
        ${sig.ema200 ? `<div class="trade-plan-row"><span class="tp-label">EMA200</span><span class="tp-value">${formatPrice(parseFloat(sig.ema200))}</span></div>` : ''}
      </div>

      <!-- Bullish Factors -->
      ${sig.bullish?.length ? `
      <div class="factors-card">
        <div class="factors-title">💪 Bullish Factors</div>
        ${sig.bullish.map(f => `<div class="factor-item">${f}</div>`).join('')}
      </div>` : ''}

      <!-- Caution -->
      ${sig.caution?.length ? `
      <div class="factors-card" style="border-color:rgba(245,158,11,0.2)">
        <div class="factors-title" style="color:var(--wait-color)">⚠️ Caution</div>
        ${sig.caution.map(f => `<div class="factor-item" style="color:var(--wait-color)">${f}</div>`).join('')}
      </div>` : ''}

      <!-- Disclaimer -->
      <p style="font-size:11px;color:var(--text-muted);text-align:center;padding:8px 0">
        Educational analysis only. Always manage your risk. HALAL SPOT ONLY.
      </p>
    `;
  } catch(e) {
    console.error('Signal detail error:', e);
    content.innerHTML = '<div class="empty-state"><span class="empty-icon">❌</span><p>Error loading signal</p><button class="btn-primary" onclick="showSignalDetail(\'' + symbol + '\')">Retry</button></div>';
  }
}

function closeSignalDetail() {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const prev = state.previousPage || 'signals';
  document.getElementById(`page-${prev}`).classList.add('active');
  const navItem = document.querySelector(`[data-page="${prev}"]`);
  if (navItem) { document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active')); navItem.classList.add('active'); }
}

function toggleWatchlistFromDetail() {
  const sym = state.currentDetailSymbol;
  if (!sym) return;
  if (state.watchlist.includes(sym)) {
    state.watchlist = state.watchlist.filter(s => s !== sym);
    document.getElementById('detailWatchlistBtn').textContent = '☆';
    showToast(`${sym} removed from watchlist`);
  } else {
    state.watchlist.push(sym);
    document.getElementById('detailWatchlistBtn').textContent = '⭐';
    showToast(`${sym} added to watchlist`);
  }
  localStorage.setItem('halol_watchlist', JSON.stringify(state.watchlist));
}

// ══════════════════════════════════════════════
// WATCHLIST PAGE
// ══════════════════════════════════════════════
function initWatchlistPage() {
  const emptyEl = document.getElementById('watchlistEmpty');
  const itemsEl = document.getElementById('watchlistItems');
  if (!state.watchlist.length) {
    emptyEl.style.display = 'flex';
    itemsEl.innerHTML = '';
    return;
  }
  emptyEl.style.display = 'none';
  itemsEl.innerHTML = state.watchlist.map(sym => {
    const sig = state.signalCache[sym];
    const emoji = COIN_EMOJI[sym] || '🪙';
    const price = sig ? formatPrice(sig.price) : '—';
    const score = sig ? `${sig.score}%` : '—';
    const cls = sig ? signalClass(sig.signal) : '';
    return `
      <div class="watchlist-coin-row" onclick="showSignalDetail('${sym}')">
        <span class="coin-emoji" style="font-size:22px">${emoji}</span>
        <span class="wl-symbol">${sym}</span>
        <span class="wl-price">${price}</span>
        <span class="wl-score" style="color:${cls==='strong-buy'?'#22c55e':cls==='buy'?'#10b981':'#f59e0b'}">${score}</span>
        <button class="wl-remove" onclick="event.stopPropagation();removeFromWatchlist('${sym}')">✕</button>
      </div>
    `;
  }).join('');
}

function removeFromWatchlist(sym) {
  state.watchlist = state.watchlist.filter(s => s !== sym);
  localStorage.setItem('halol_watchlist', JSON.stringify(state.watchlist));
  showToast(`${sym} removed from watchlist`);
  initWatchlistPage();
}

// ══════════════════════════════════════════════
// EDUCATION PAGE
// ══════════════════════════════════════════════
const LESSONS = {
  crypto_basics: {
    title: '📚 Crypto Basics',
    lessons: [
      { id: 'bitcoin',   title: '₿ What is Bitcoin?',       content: `Bitcoin (BTC) is the world's first decentralised digital currency, created in 2009 by Satoshi Nakamoto.\n\n🔑 Key Facts:\n• Fixed supply of 21 million BTC — no inflation\n• Verified by global network of miners\n• No central bank controls it\n• You own the asset — full financial sovereignty\n\n📌 Why Halal?\nSpot Bitcoin trading involves actual ownership. No riba (interest), no leverage.\n\n💡 Tip: Never invest more than you can afford to lose.` },
      { id: 'blockchain', title: '⛓ What is Blockchain?',    content: `A blockchain is a distributed ledger recording transactions across thousands of computers.\n\n🔑 Key Concepts:\n• Block — a batch of transactions\n• Chain — each block links cryptographically to the previous\n• Decentralised — no single point of failure\n• Immutable — recorded data cannot be altered\n• Transparent — anyone can verify transactions\n\n🔐 Security: Changing one block would require re-mining every subsequent block — computationally impossible.` },
      { id: 'spot',       title: '🛒 What is Spot Trading?',  content: `Spot trading means buying and selling actual assets at the current market price — with immediate settlement.\n\n✅ Why Spot Trading is Halal:\n• You own the actual asset\n• No borrowing, no leverage, no riba\n• Real value exchange\n• Risk limited to invested capital\n\n❌ What to Avoid (Haram):\n• Futures trading — no actual ownership\n• Margin trading — borrowing = riba\n• Short selling — profiting from borrowed assets\n\n💡 Example: You buy 0.01 BTC at $50,000 = $500. You OWN 0.01 BTC. If it rises to $60,000 → $600. Profit = $100. This is halal spot trading!` },
    ]
  },
  indicators: {
    title: '📊 Indicators',
    lessons: [
      { id: 'rsi',     title: '📊 RSI',              content: `RSI (Relative Strength Index) measures the speed of price changes to identify overbought/oversold conditions.\n\n📏 Scale: 0 to 100\n• Below 30 → Oversold (potential buy opportunity) ✅\n• 30–50 → Bearish / recovering\n• 50–70 → Bullish / neutral ✅\n• Above 70 → Overbought (consider taking profits) ⚠️\n\n🔍 How to read:\n• RSI crossing above 50 from below = momentum turning bullish\n• RSI at 30 + price at support = strong buy zone\n\n⚙️ Default period: 14 candles` },
      { id: 'macd',    title: '📈 MACD',             content: `MACD (Moving Average Convergence Divergence) tracks relationship between two EMAs.\n\n🔑 Components:\n• MACD Line — EMA(12) minus EMA(26)\n• Signal Line — EMA(9) of MACD line\n• Histogram — MACD line minus signal line\n\n📖 Reading:\n• MACD crosses above signal → Bullish crossover ✅\n• Histogram growing above zero → momentum increasing\n• MACD above zero line → uptrend\n\n💡 Best combined with RSI, Volume, EMA.` },
      { id: 'ema',     title: '📉 EMA',              content: `EMA (Exponential Moving Average) gives more weight to recent price data.\n\n🔑 Key EMAs:\n• EMA 20 — Short-term trend\n• EMA 50 — Medium-term trend\n• EMA 200 — Long-term trend (most important)\n\n📖 Rules:\n• Price above EMA200 → long-term uptrend ✅\n• EMA20 crosses above EMA50 → Golden Cross (bullish)\n• EMA bounce → dynamic support/resistance\n\n💡 When EMA20 > EMA50 > EMA200 and price above all three — ideal spot accumulation zone!` },
      { id: 'atr',     title: '📐 ATR',              content: `ATR (Average True Range) measures market volatility.\n\n🔑 Usage:\n• High ATR → high volatility, wider stops needed\n• Low ATR → calm market, tighter stops\n• Does NOT indicate direction — only movement size\n\n🎯 Stop Loss:\n• Stop Loss = Entry − (ATR × 1.5)\n• Ensures stop is beyond normal noise\n\n📊 Example:\nBTC = $50,000 | ATR = $800\nStop Loss = $50,000 − $1,200 = $48,800\n\n💡 Rule: Never set a stop tighter than 1× ATR.` },
      { id: 'adx',     title: '💪 ADX',              content: `ADX (Average Directional Index) measures trend STRENGTH — not direction.\n\n📏 Scale:\n• Below 20 → Weak trend / sideways\n• 20–25 → Developing trend\n• 25–40 → Strong trend ✅\n• Above 40 → Very strong trend\n\n🔑 Key Insight:\n• ADX doesn't tell you if trend is up or down\n• Use with EMAs: ADX > 25 + EMA trend up = strong buy setup\n\n💡 Filter weak signals: only trade when ADX > 25.` },
      { id: 'bb',      title: '📊 Bollinger Bands',  content: `Bollinger Bands are volatility bands above and below a moving average.\n\n🔑 Three Lines:\n• Upper Band — SMA + 2 standard deviations\n• Middle Band — 20-period SMA\n• Lower Band — SMA − 2 standard deviations\n\n📖 Reading:\n• Price touches lower band → potentially oversold, watch for bounce\n• Band squeeze → big move incoming\n• Price walking upper band → strong uptrend\n\n🎯 Strategy: Buy near lower band when RSI < 40 AND price above support.` },
    ]
  },
  candlestick: {
    title: '🕯 Candlestick Patterns',
    lessons: [
      { id: 'candles', title: '🕯 Candlestick Patterns Guide', content: `Candlestick patterns are visual signals formed by candles indicating potential reversals or continuations.\n\n🟢 Bullish Reversal Patterns:\n• Hammer — small body, long lower wick at support\n• Bullish Engulfing — large green candle engulfs red\n• Morning Star — red + small doji + large green\n• Inverted Hammer — long upper wick at bottom\n• Dragonfly Doji — opens and closes at high\n\n⚡ Continuation Patterns:\n• Three White Soldiers — 3 consecutive green candles\n• Rising Three Methods — brief consolidation then continuation\n\n⚠️ Bearish Warnings (take profits):\n• Shooting Star — long upper wick after uptrend\n• Bearish Engulfing — large red engulfs green\n• Evening Star — green + doji + red\n\n💡 Rule: Never trade a pattern in isolation. Confirm with RSI, volume, structure.` },
    ]
  },
  smc: {
    title: '🏦 Smart Money Concepts',
    lessons: [
      { id: 'ob',    title: '📦 Order Block',         content: `An Order Block is a price area where large institutional traders placed massive orders, causing strong directional moves.\n\n🔑 Bullish Order Block:\n• Last bearish candle before a strong bullish move\n• Price often returns to this zone to fill remaining orders\n• When price revisits → potential strong buy entry\n\n📖 How to Identify:\n1. Find a strong bullish impulse move\n2. Look at the last bearish candle before that move\n3. The body of that candle = the order block\n\n✅ Confirmation:\n• RSI shows oversold\n• Volume increases on entry\n\n💡 Banks place orders in blocks, not at single prices.` },
      { id: 'fvg',   title: '📊 Fair Value Gap',      content: `A Fair Value Gap (FVG) is a price imbalance where price moves so quickly that no trading occurs between two candles.\n\n🔑 How FVG Forms:\n• Candle 1 high and Candle 3 low don't overlap\n• The space between them = FVG\n• Price tends to revisit this zone\n\n✅ Bullish FVG Setup:\n1. Price creates bullish FVG\n2. Price pulls back into the FVG\n3. RSI oversold / Order Block present\n4. Enter long with stop below FVG\n\n💡 FVGs near key support = highest probability entries.` },
      { id: 'bos',   title: '💥 Break of Structure',  content: `A Break of Structure (BOS) confirms trend continuation when price breaks a previous swing high (uptrend) or low (downtrend).\n\n🔑 Bullish BOS:\n• Price makes new Higher High above previous swing high\n• Confirms uptrend is intact\n• Signal to look for buy entries on pullback\n\n📖 BOS vs CHoCH:\n• BOS = trend continuation (same direction)\n• CHoCH = trend reversal (direction change)\n\n💡 BOS on 4H/Daily timeframe = stronger signal.` },
      { id: 'choch', title: '🔄 Change of Character', content: `A Change of Character (CHoCH) is the first sign of trend reversal.\n\n🔑 Bullish CHoCH:\n• In a downtrend, price breaks above the last swing high\n• First sign that selling pressure is weakening\n• Not confirmed reversal — strong early warning\n\n🎯 Trading CHoCH:\n• Do NOT enter immediately on CHoCH\n• Wait for BOS confirmation after CHoCH\n• CHoCH + BOS = high confidence reversal entry\n\n💡 Smart Money: Distribute at highs → CHoCH → Accumulate at lows → BOS up.` },
      { id: 'liq',   title: '💧 Liquidity Sweep',     content: `A Liquidity Sweep occurs when price temporarily breaks through a key level to fill large institutional orders, then reverses sharply.\n\n🔑 Low Sweep (Bullish):\n• Price dips below obvious support/equal lows\n• Stop losses of retail traders triggered\n• Institutions buy the triggered stops cheaply\n• Price reverses sharply upward\n\n🎯 Trading:\n1. Identify key support level (equal lows)\n2. Wait for price to sweep below (wick down)\n3. Wait for strong bullish candle close above support\n4. Enter with stop below sweep wick\n\n💡 Big players need liquidity. Retail stops = their liquidity.` },
      { id: 'br',    title: '🚀 Breakout Retest',     content: `Breakout Retest: price breaks above resistance, pulls back to test the broken level as new support, then continues higher.\n\n🔑 Stages:\n1. Consolidation — price builds energy near resistance\n2. Breakout — strong candle closes above resistance\n3. Retest — price pulls back to broken level\n4. Bounce — price bounces off old resistance (now support)\n5. Continuation — price moves to new highs\n\n✅ High Probability Setup:\n• Volume increases on breakout\n• Retest shows decreasing volume\n• Bounce shows increasing volume\n• RSI stays above 50 during retest\n\n💡 Best Risk:Reward: Enter on retest, stop below retest level.` },
    ]
  },
  risk_management: {
    title: '⚠️ Risk Management',
    lessons: [
      { id: 'sl',     title: '🛑 Stop Loss',          content: `A Stop Loss is a pre-set order that automatically sells if price falls to a specified level, limiting maximum loss.\n\n🔑 Why Essential:\n• Protects capital from catastrophic losses\n• Removes emotion from decisions\n• Professional traders ALWAYS use stop losses\n\n📊 How to Set:\n• ATR Method: Entry − (1.5 × ATR)\n• Structure Method: Below key support\n• Percentage Method: 3–5% below entry\n\n🚫 NEVER:\n• Move stop loss further away when losing\n• Trade without a stop loss\n• Risk more than 2% of capital per trade` },
      { id: 'tp',     title: '🎯 Take Profit',        content: `Take Profit (TP) automatically sells when price reaches your target, locking in gains.\n\n🔑 Multi-Level Strategy:\n• TP1 — 1.5:1 reward:risk → Sell 30–40%, move stop to breakeven\n• TP2 — 2.5:1 reward:risk → Sell another 30–40%\n• TP3 — 4:1 reward:risk → Sell remaining position\n\n✅ Benefits:\n• Locks in profit early\n• Reduces psychological pressure\n• Allows remaining position to run free\n\n💡 Halol Rule: Always set TP before entering.` },
      { id: 'rr',     title: '⚖️ Risk:Reward Ratio',  content: `Risk:Reward (R:R) compares how much you risk to how much you can gain.\n\n📊 Calculation:\nR:R = (Target − Entry) ÷ (Entry − Stop Loss)\n\n✅ Example:\n• Entry: $100 | Stop: $95 | Target: $115\n• Risk: $5 | Reward: $15 | R:R = 1:3 ✅\n\n📏 Minimum acceptable:\n• Below 1:1.5 → Avoid\n• 1:2 → Acceptable\n• 1:3 or higher → Excellent ✅\n\n💡 With 1:2 R:R, you only need to win 34% of trades to be profitable!` },
      { id: 'ps',     title: '💰 Position Sizing',    content: `Position Sizing determines how much capital to allocate per trade.\n\n🔑 The 2% Rule:\nNever risk more than 2% of portfolio on a single trade.\n\n📊 Calculation:\nPosition Size = (Portfolio × 2%) ÷ (Entry − Stop Loss)\n\n✅ Example:\n• Portfolio: $10,000 | Risk: 2% = $200\n• Entry: $100 | Stop: $95 → Distance = $5\n• Position Size = $200 ÷ $5 = 40 units\n\n🏦 Portfolio Allocation:\n• 40–50% in BTC/ETH (safer)\n• 30–40% in top altcoins\n• 10–20% in opportunities\n• Always keep 20% in cash\n\n💡 A 50% loss requires 100% gain to recover. Protect capital first!` },
      { id: 'overview', title: '⚠️ Risk Management Overview', content: `Risk Management is the most important skill in trading.\n\n🏛 The 5 Golden Rules:\n\n1️⃣ Never risk more than 2% per trade\n   → Even 10 losses = only 18% drawdown\n\n2️⃣ Always use a stop loss\n   → No exceptions. Ever.\n\n3️⃣ Minimum 1:2 Risk:Reward\n   → Every trade target = 2× your risk\n\n4️⃣ Diversify across multiple coins\n   → Never put all capital in one trade\n\n5️⃣ Keep 20% in cash\n   → Always have dry powder\n\n🧠 Psychology:\n• Never chase FOMO\n• Don't revenge trade\n• Follow your plan, not emotions\n\n💡 Islamic: Tawakkul — do best analysis, set plan, accept outcome.` },
    ]
  },
  faq: {
    title: '❓ FAQ',
    lessons: [
      { id: 'faq', title: '❓ Frequently Asked Questions', content: `🔶 Is crypto trading halal?\nSpot trading (buying/owning actual assets) is generally considered permissible. Futures, margin, leveraged trading are generally haram (riba, excessive gharar).\n\n🔶 Why no sell signals?\nWe focus on spot buying. In halal spot investing, you hold until TP is reached.\n\n🔶 How accurate are the signals?\nBased on technical analysis — not financial advice. Past patterns don't guarantee future results. Always do your own research.\n\n🔶 Which coins are supported?\n30 halal spot coins: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK, TON and more.\n\n🔶 How often are signals updated?\nEvery 5 minutes by the background scanner.\n\n🔶 Is this financial advice?\nNo. Educational and analytical software only. Never invest more than you can afford to lose.` },
    ]
  },
};

let currentEduCategory = null;
let currentLessonId = null;

function showEduCategory(cat) {
  currentEduCategory = cat;
  const category = LESSONS[cat];
  if (!category) return;

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-edu-category').classList.add('active');
  document.getElementById('eduCategoryTitle').textContent = category.title;

  const content = document.getElementById('eduCategoryContent');
  content.innerHTML = `<div class="lesson-list">
    ${category.lessons.map(l => `
      <button class="lesson-btn" onclick="showLesson('${cat}', '${l.id}')">
        ${l.title}
        <span class="lesson-chevron">›</span>
      </button>
    `).join('')}
  </div>`;
}

function showLesson(cat, lessonId) {
  const category = LESSONS[cat];
  if (!category) return;
  const lesson = category.lessons.find(l => l.id === lessonId);
  if (!lesson) return;
  currentLessonId = lessonId;

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-lesson').classList.add('active');
  document.getElementById('lessonTitle').textContent = lesson.title;

  document.getElementById('lessonBackBtn').onclick = () => showEduCategory(cat);

  const content = document.getElementById('lessonContent');
  const formatted = lesson.content
    .replace(/\*([^*]+)\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
  content.innerHTML = `<div class="lesson-body">${formatted}</div>`;
}

function closeLessonPage() {
  if (currentEduCategory) {
    showEduCategory(currentEduCategory);
  } else {
    switchPage('education');
  }
}

// ══════════════════════════════════════════════
// MARKET PAGE
// ══════════════════════════════════════════════
async function loadMarketData() {
  const content = document.getElementById('marketContent');
  content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading market data...</p></div>';

  try {
    const top = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK','TON','AVAX'];
    const tickers = await fetchMultipleTickers(top);

    const valid = tickers.filter(t => t.price > 0);
    const gainers = [...valid].sort((a, b) => b.change - a.change).slice(0, 5);
    const losers  = [...valid].sort((a, b) => a.change - b.change).slice(0, 5);
    const byVol   = [...valid].sort((a, b) => b.volume - a.volume).slice(0, 5);
    const btc = valid.find(t => t.symbol === 'BTC');
    const eth = valid.find(t => t.symbol === 'ETH');
    const bulls = valid.filter(t => t.change > 0).length;
    const sentiment = bulls >= 6 ? '🟢 Bullish' : bulls <= 3 ? '🔴 Bearish' : '🟡 Neutral';

    function row(t) {
      const cls = t.change >= 0 ? 'pos' : 'neg';
      return `<div class="market-row">
        <span class="market-symbol">${COIN_EMOJI[t.symbol]||'🪙'} ${t.symbol}</span>
        <span class="market-price">${formatPrice(t.price)}</span>
        <span class="market-chg ${cls}">${formatChange(t.change)}</span>
      </div>`;
    }

    content.innerHTML = `
      <div class="card">
        <div class="market-section-title">📡 Market Sentiment: ${sentiment}</div>
        <div class="trade-plan-row">
          <span class="tp-label">₿ BTC</span>
          <span class="tp-value">${btc ? formatPrice(btc.price) : '—'}</span>
          <span style="font-size:13px;color:${btc&&btc.change>=0?'#10b981':'#ef4444'}">${btc ? formatChange(btc.change) : ''}</span>
        </div>
        <div class="trade-plan-row">
          <span class="tp-label">⟠ ETH</span>
          <span class="tp-value">${eth ? formatPrice(eth.price) : '—'}</span>
          <span style="font-size:13px;color:${eth&&eth.change>=0?'#10b981':'#ef4444'}">${eth ? formatChange(eth.change) : ''}</span>
        </div>
      </div>
      <div class="card">
        <div class="market-section-title">📈 Top Gainers</div>
        ${gainers.map(row).join('')}
      </div>
      <div class="card">
        <div class="market-section-title">📉 Top Losers</div>
        ${losers.map(row).join('')}
      </div>
      <div class="card">
        <div class="market-section-title">💹 Volume Leaders</div>
        ${byVol.map(t => `
          <div class="market-row">
            <span class="market-symbol">${COIN_EMOJI[t.symbol]||'🪙'} ${t.symbol}</span>
            <span class="market-price">${formatPrice(t.price)}</span>
            <span class="market-chg" style="color:var(--text-secondary)">${t.volume > 1e9 ? '$'+(t.volume/1e9).toFixed(2)+'B' : '$'+(t.volume/1e6).toFixed(0)+'M'}</span>
          </div>
        `).join('')}
      </div>
      <p style="font-size:11px;color:var(--text-muted);text-align:center">Last updated: ${new Date().toLocaleTimeString()}</p>
    `;
  } catch(e) {
    console.error('Market data error:', e);
    content.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">⚠️</span>
        <p>Could not load market data</p>
        <button class="btn-primary" onclick="loadMarketData()">Retry</button>
      </div>`;
  }
}

// ══════════════════════════════════════════════
// SETTINGS PAGE
// ══════════════════════════════════════════════
function initSettings() {
  // Restore timeframe
  document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tf === state.timeframe);
  });
}

function selectTimeframe(btn) {
  document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.timeframe = btn.dataset.tf;
  localStorage.setItem('halol_tf', state.timeframe);
  // Clear signal cache so next analysis uses new timeframe
  state.signalCache = {};
  localStorage.setItem('halol_signals', '{}');
  showToast(`Timeframe set to ${state.timeframe.toUpperCase()}`);
}

// ══════════════════════════════════════════════
// Init
// ══════════════════════════════════════════════
function init() {
  switchPage('home');
  // Load signals in background
  setTimeout(updateCoinGridFromCache, 1000);
}

init();
