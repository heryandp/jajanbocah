import { NextRequest, NextResponse } from "next/server";

// Tipe data OHLC
interface OHLC {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Helper fetch OHLC dari Yahoo Finance
async function fetchOHLC(symbol: string, interval: string, source: string = 'yahoo'): Promise<OHLC[]> {
  if (source === 'mt5') {
    // Fetch dari endpoint Flask lokal
    const tfMap: Record<string, string> = { '1m': 'M1', '5m': 'M5', '15m': 'M15', '30m': 'M30', '1h': 'H1', '4h': 'H4', '1d': 'D1', '1w': 'W1', '1mo': 'MN1' };
    const tf = tfMap[interval] || 'M1';
    const url = `http://localhost:5000/ohlc?symbol=${symbol}&tf=${tf}&n=200`;
    const res = await fetch(url);
    const data = await res.json();
    if (!Array.isArray(data)) throw new Error('MT5 API: Data not found');
    return data.map((d: { time: number; open: number; high: number; low: number; close: number; tick_volume?: number; volume?: number }) => ({
      time: d.time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
      volume: d.tick_volume || d.volume || 0,
    }));
  }
  // Yahoo Finance symbol mapping
  let yahooSymbol = symbol;
  if (symbol === 'GOLD' || symbol === 'XAUUSD') yahooSymbol = 'GC=F';
  if (symbol === 'BTCUSD' || symbol === 'BTC-USD') yahooSymbol = 'BTC-USD';
  // interval: 1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo
  const intervalMap: Record<string, string> = {
    '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '60m', '4h': '60m', '1d': '1d', '1w': '1wk', '1mo': '1mo', '3mo': '1mo', '6mo': '1mo', '12mo': '1mo'
  };
  const yfInterval = intervalMap[interval] || '15m';
  const range = yfInterval.endsWith('m') ? '5d' : '1y';
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${yahooSymbol}?interval=${yfInterval}&range=${range}`;
  const res = await fetch(url);
  const data = await res.json();
  if (!data.chart || !data.chart.result || !data.chart.result[0]) throw new Error('Yahoo Finance: Data not found');
  const result = data.chart.result[0];
  const ohlc = result.indicators.quote[0];
  const timestamps = result.timestamp;
  return timestamps.map((t: number, i: number) => ({
    time: t,
    open: ohlc.open[i],
    high: ohlc.high[i],
    low: ohlc.low[i],
    close: ohlc.close[i],
    volume: ohlc.volume[i],
  }));
}

// Simple indicator calculation (dummy, for demo)
function calcRSI(closes: number[], period = 14): number {
  let gains = 0, losses = 0;
  for (let i = closes.length - period; i < closes.length - 1; i++) {
    const diff = closes[i + 1] - closes[i];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }
  const rs = gains / (losses || 1);
  const rsi = 100 - 100 / (1 + rs);
  return Math.round(rsi * 10) / 10;
}
function calcMA(closes: number[], period = 14): number {
  const ma = closes.slice(-period).reduce((a, b) => a + b, 0) / period;
  return Math.round(ma * 100) / 100;
}
function calcMACD(closes: number[]): number {
  // EMA12 - EMA26
  function ema(period: number) {
    const k = 2 / (period + 1);
    let ema = closes[0];
    for (let i = 1; i < closes.length; i++) {
      ema = closes[i] * k + ema * (1 - k);
    }
    return ema;
  }
  const macd = ema(12) - ema(26);
  return Math.round(macd * 100) / 100;
}
function calcBB(closes: number[], period = 20): { upper: number; lower: number; basis: number } {
  const slice = closes.slice(-period);
  const ma = slice.reduce((a, b) => a + b, 0) / period;
  const std = Math.sqrt(slice.reduce((a, b) => a + Math.pow(b - ma, 2), 0) / period);
  return {
    upper: Math.round((ma + 2 * std) * 100) / 100,
    lower: Math.round((ma - 2 * std) * 100) / 100,
    basis: Math.round(ma * 100) / 100,
  };
}

type IndicatorResult = {
  rsi?: number;
  ma?: number;
  macd?: number;
  bb?: { upper: number; lower: number; basis: number };
  stoch?: { k: number; d: number };
  cci?: number;
  atr?: number;
  adx?: number;
  volume?: number;
  close?: number;
  rsiArr?: { time: number; value: number }[];
  maArr?: { time: number; value: number }[];
  macdArr?: { time: number; value: number }[];
};

type IndicatorSelection = { value: string; params: { [key: string]: number } };

// Tambahan indikator
function calcStoch(ohlc: OHLC[], kPeriod = 14, dPeriod = 3) {
  const closes = ohlc.map((c) => c.close);
  const lows = ohlc.map((c) => c.low);
  const highs = ohlc.map((c) => c.high);
  const n = closes.length;
  let k = 0;
  if (n >= kPeriod) {
    const low = Math.min(...lows.slice(-kPeriod));
    const high = Math.max(...highs.slice(-kPeriod));
    k = ((closes[n - 1] - low) / (high - low)) * 100;
  }
  let d = k;
  if (n >= kPeriod + dPeriod - 1) {
    const kArr = [];
    for (let i = n - dPeriod; i < n; i++) {
      const low = Math.min(...lows.slice(i - kPeriod + 1, i + 1));
      const high = Math.max(...highs.slice(i - kPeriod + 1, i + 1));
      kArr.push(((closes[i] - low) / (high - low)) * 100);
    }
    d = kArr.reduce((a, b) => a + b, 0) / dPeriod;
  }
  return { k: Math.round(k * 10) / 10, d: Math.round(d * 10) / 10 };
}
function calcCCI(ohlc: OHLC[], period = 20) {
  const tp = ohlc.map((c) => (c.high + c.low + c.close) / 3);
  const ma = tp.slice(-period).reduce((a, b) => a + b, 0) / period;
  const meanDev = tp.slice(-period).reduce((a, b) => a + Math.abs(b - ma), 0) / period;
  const cci = (tp[tp.length - 1] - ma) / (0.015 * meanDev);
  return Math.round(cci * 10) / 10;
}
function calcATR(ohlc: OHLC[], period = 14) {
  const trs = ohlc.slice(-period - 1).map((c, i, arr) => {
    if (i === 0) return 0;
    const prevClose = arr[i - 1].close;
    return Math.max(
      c.high - c.low,
      Math.abs(c.high - prevClose),
      Math.abs(c.low - prevClose)
    );
  });
  const atr = trs.slice(1).reduce((a, b) => a + b, 0) / period;
  return Math.round(atr * 100) / 100;
}
function calcADX(ohlc: OHLC[], period = 14) {
  // Sederhana, hanya nilai terakhir
  let trSum = 0, plusDM = 0, minusDM = 0;
  for (let i = ohlc.length - period; i < ohlc.length - 1; i++) {
    const upMove = ohlc[i + 1].high - ohlc[i].high;
    const downMove = ohlc[i].low - ohlc[i + 1].low;
    plusDM += upMove > downMove && upMove > 0 ? upMove : 0;
    minusDM += downMove > upMove && downMove > 0 ? downMove : 0;
    trSum += Math.max(
      ohlc[i + 1].high - ohlc[i + 1].low,
      Math.abs(ohlc[i + 1].high - ohlc[i].close),
      Math.abs(ohlc[i + 1].low - ohlc[i].close)
    );
  }
  const plusDI = 100 * (plusDM / trSum);
  const minusDI = 100 * (minusDM / trSum);
  const dx = 100 * Math.abs(plusDI - minusDI) / (plusDI + minusDI);
  return Math.round(dx * 10) / 10;
}

// ADVANCED SIGNAL GENERATOR
function generateSignalAdvanced(indicators: IndicatorResult, prevIndicators?: IndicatorResult): { signal: string; strength: number; reason: string[] } {
  let signal: string = "WAIT";
  let strength = 0;
  const reason: string[] = [];
  let conflict = false;

  // SMA/EMA crossover (pakai MA saja jika EMA tidak ada)
  if (indicators.ma !== undefined && prevIndicators?.ma !== undefined && indicators.close !== undefined && prevIndicators.close !== undefined) {
    // Crossover MA (misal: harga close cross MA)
    if (prevIndicators.close <= prevIndicators.ma && indicators.close > indicators.ma) {
      signal = "BUY";
      strength += 2;
      reason.push("Close crossed above MA");
    } else if (prevIndicators.close >= prevIndicators.ma && indicators.close < indicators.ma) {
      signal = "SELL";
      strength += 2;
      reason.push("Close crossed below MA");
    }
  }

  // RSI
  if (indicators.rsi !== undefined) {
    if (indicators.rsi < 30) {
      if (signal === "SELL") conflict = true;
      else signal = "BUY";
      strength += 1;
      reason.push(`RSI oversold (${indicators.rsi})`);
    } else if (indicators.rsi > 70) {
      if (signal === "BUY") conflict = true;
      else signal = "SELL";
      strength += 1;
      reason.push(`RSI overbought (${indicators.rsi})`);
    }
  }

  // Stochastic
  if (indicators.stoch) {
    if (indicators.stoch.k < 20 && indicators.stoch.k > indicators.stoch.d) {
      if (signal === "SELL") conflict = true;
      else signal = "BUY";
      strength += 1;
      reason.push(`Stoch oversold & K>D (${indicators.stoch.k}/${indicators.stoch.d})`);
    } else if (indicators.stoch.k > 80 && indicators.stoch.k < indicators.stoch.d) {
      if (signal === "BUY") conflict = true;
      else signal = "SELL";
      strength += 1;
      reason.push(`Stoch overbought & K<D (${indicators.stoch.k}/${indicators.stoch.d})`);
    }
  }

  // MACD
  if (indicators.macd !== undefined && prevIndicators?.macd !== undefined) {
    if (prevIndicators.macd <= 0 && indicators.macd > 0) {
      if (signal === "SELL") conflict = true;
      else signal = "BUY";
      strength += 2;
      reason.push("MACD crossed above 0");
    } else if (prevIndicators.macd >= 0 && indicators.macd < 0) {
      if (signal === "BUY") conflict = true;
      else signal = "SELL";
      strength += 2;
      reason.push("MACD crossed below 0");
    }
  }

  // Bollinger Bands
  if (indicators.bb && indicators.close !== undefined) {
    if (indicators.close < indicators.bb.lower) {
      if (signal === "SELL") conflict = true;
      else signal = "BUY";
      strength += 2;
      reason.push("Price below lower BB");
    } else if (indicators.close > indicators.bb.upper) {
      if (signal === "BUY") conflict = true;
      else signal = "SELL";
      strength += 2;
      reason.push("Price above upper BB");
    }
  }

  // ADX (trend strength)
  if (indicators.adx !== undefined && indicators.adx > 25) {
    strength += 1;
    reason.push(`Strong trend (ADX: ${indicators.adx})`);
  }

  // Momentum harga (persentase perubahan close)
  if (indicators.close !== undefined && prevIndicators?.close !== undefined) {
    const pct = ((indicators.close - prevIndicators.close) / prevIndicators.close) * 100;
    if (pct > 0.2) {
      if (signal === "SELL") strength -= 1;
      else strength += 1;
      reason.push(`Strong upward momentum (${pct.toFixed(2)}%)`);
    } else if (pct < -0.2) {
      if (signal === "BUY") strength -= 1;
      else strength += 1;
      reason.push(`Strong downward momentum (${pct.toFixed(2)}%)`);
    }
  }

  // Handle conflicting
  if (conflict) {
    signal = "WAIT";
    reason.push("Conflicting signals");
  }

  // Jika strength 0, tetap WAIT
  if (strength === 0) signal = "WAIT";

  return { signal, strength, reason };
}

export async function POST(req: NextRequest) {
  try {
    const { symbol, timeframe, indicators, source } = await req.json();
    const intervalMap: Record<string, string> = {
      "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m", "4h": "4h", "1d": "1d", "1w": "1wk", "1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "12mo": "12mo"
    };
    const interval = intervalMap[timeframe] || "15m";
    const ohlc: OHLC[] = await fetchOHLC(symbol, interval, source);
    const closes = ohlc.map((c) => c.close);
    const lastClose = closes[closes.length - 1];
    const prevCloses = closes.slice(0, -1);
    // Hitung indikator untuk candle terakhir dan sebelumnya
    const indicatorsNow: IndicatorResult = {};
    const indicatorsPrev: IndicatorResult = {};
    for (const ind of indicators) {
      if (ind.value === "rsi") {
        indicatorsNow.rsi = calcRSI(closes, ind.params.period ?? 14);
        indicatorsPrev.rsi = calcRSI(prevCloses, ind.params.period ?? 14);
      }
      if (ind.value === "ma") {
        indicatorsNow.ma = calcMA(closes, ind.params.period ?? 14);
        indicatorsPrev.ma = calcMA(prevCloses, ind.params.period ?? 14);
      }
      if (ind.value === "macd") {
        indicatorsNow.macd = calcMACD(closes);
        indicatorsPrev.macd = calcMACD(prevCloses);
      }
      if (ind.value === "bb") {
        indicatorsNow.bb = calcBB(closes, ind.params.period ?? 20);
        indicatorsPrev.bb = calcBB(prevCloses, ind.params.period ?? 20);
      }
      if (ind.value === "stoch") {
        indicatorsNow.stoch = calcStoch(ohlc, ind.params.k ?? 14, ind.params.d ?? 3);
        indicatorsPrev.stoch = calcStoch(ohlc.slice(0, -1), ind.params.k ?? 14, ind.params.d ?? 3);
      }
      if (ind.value === "cci") {
        indicatorsNow.cci = calcCCI(ohlc, ind.params.period ?? 20);
        indicatorsPrev.cci = calcCCI(ohlc.slice(0, -1), ind.params.period ?? 20);
      }
      if (ind.value === "atr") {
        indicatorsNow.atr = calcATR(ohlc, ind.params.period ?? 14);
        indicatorsPrev.atr = calcATR(ohlc.slice(0, -1), ind.params.period ?? 14);
      }
      if (ind.value === "adx") {
        indicatorsNow.adx = calcADX(ohlc, ind.params.period ?? 14);
        indicatorsPrev.adx = calcADX(ohlc.slice(0, -1), ind.params.period ?? 14);
      }
      if (ind.value === "volume") {
        indicatorsNow.volume = ohlc[ohlc.length - 1].volume;
        indicatorsPrev.volume = ohlc[ohlc.length - 2]?.volume;
      }
    }
    indicatorsNow.close = lastClose;
    indicatorsPrev.close = prevCloses[prevCloses.length - 1];

    // Gunakan signal advanced
    const adv = generateSignalAdvanced(indicatorsNow, indicatorsPrev);

    const result: { indicators: IndicatorResult; close: number; signal?: string; strength?: number; reason?: string[]; ohlc?: { time: number; close: number }[]; openPositionPrice?: number; tp?: number; sl?: number } = {
      indicators: indicatorsNow,
      close: lastClose,
      signal: adv.signal,
      strength: adv.strength,
      reason: adv.reason,
      ohlc: ohlc.map(({ time, close }) => ({ time, close })),
    };
    // Tambahkan posisi open buy/sell pada harga open candle terakhir jika signal BUY/SELL
    if (result.signal === 'BUY' || result.signal === 'SELL') {
      result.openPositionPrice = ohlc[ohlc.length - 1]?.open;
      // TP/SL sederhana berbasis ATR
      const atr = indicatorsNow.atr ?? 0;
      if (result.signal === 'BUY') {
        result.tp = result.openPositionPrice + 2 * atr;
        result.sl = result.openPositionPrice - atr;
      } else if (result.signal === 'SELL') {
        result.tp = result.openPositionPrice - 2 * atr;
        result.sl = result.openPositionPrice + atr;
      }
    }
    // Tambahkan array indikator untuk chart
    const rsiArr = [];
    const maArr = [];
    const macdArr = [];
    for (let i = 0; i < ohlc.length; i++) {
      if (indicators.some((ind: IndicatorSelection) => ind.value === "rsi")) {
        if (i >= 13) rsiArr.push({ time: ohlc[i].time, value: calcRSI(closes.slice(0, i + 1), indicators.find((ind: IndicatorSelection) => ind.value === "rsi")?.params?.period ?? 14) });
      }
      if (indicators.some((ind: IndicatorSelection) => ind.value === "ma")) {
        if (i >= 13) maArr.push({ time: ohlc[i].time, value: calcMA(closes.slice(0, i + 1), indicators.find((ind: IndicatorSelection) => ind.value === "ma")?.params?.period ?? 14) });
      }
      if (indicators.some((ind: IndicatorSelection) => ind.value === "macd")) {
        if (i >= 25) macdArr.push({ time: ohlc[i].time, value: calcMACD(closes.slice(0, i + 1)) });
      }
    }
    result.indicators.rsiArr = rsiArr;
    result.indicators.maArr = maArr;
    result.indicators.macdArr = macdArr;
    result.ohlc = ohlc
      .filter(bar => (
        typeof bar.open === 'number' &&
        typeof bar.high === 'number' &&
        typeof bar.low === 'number' &&
        typeof bar.close === 'number' &&
        !isNaN(bar.open) && !isNaN(bar.high) && !isNaN(bar.low) && !isNaN(bar.close)
      ))
      .map(({ time, open, high, low, close, volume }) => ({ time, open, high, low, close, volume }));
    return NextResponse.json(result);
  } catch (e: unknown) {
    let message = "Unknown error";
    if (typeof e === "object" && e !== null && "message" in e) {
      message = String((e as { message: string }).message);
    }
    return NextResponse.json({ error: message }, { status: 500 });
  }
} 