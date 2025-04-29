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

// Helper fetch OHLC from Yahoo Finance
async function fetchOHLC(symbol: string, interval: string): Promise<OHLC[]> {
  // Yahoo Finance symbol for GOLD: "GC=F" (Gold Futures)
  const yahooSymbol = symbol === "GOLD" ? "GC=F" : symbol;
  // interval: 15m or 60m
  const range = interval === "15m" ? "1d" : "5d";
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${yahooSymbol}?interval=${interval}&range=${range}`;
  const res = await fetch(url);
  const data = await res.json();
  const result = data.chart.result[0];
  const ohlc = result.indicators.quote[0];
  const timestamps = result.timestamp;
  // Return array of {time, open, high, low, close, volume}
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

function generateSignal(indicators: IndicatorResult, rsiUpper = 70, rsiLower = 30): string {
  if (
    indicators.rsi !== undefined &&
    indicators.ma !== undefined &&
    indicators.close !== undefined
  ) {
    if (indicators.rsi < rsiLower && indicators.close < indicators.ma) return "BUY";
    if (indicators.rsi > rsiUpper && indicators.close > indicators.ma) return "SELL";
  }
  return "WAIT";
}

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

export async function POST(req: NextRequest) {
  try {
    const { symbol, timeframe, indicators } = await req.json();
    const intervalMap: Record<string, string> = {
      "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m", "4h": "4h", "1d": "1d", "1w": "1wk", "1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "12mo": "12mo"
    };
    const interval = intervalMap[timeframe] || "15m";
    const ohlc: OHLC[] = await fetchOHLC(symbol, interval);
    const closes = ohlc.map((c) => c.close);
    const lastClose = closes[closes.length - 1];
    const result: { indicators: IndicatorResult; close: number; signal?: string; ohlc?: { time: number; close: number }[] } = {
      indicators: {},
      close: lastClose,
      ohlc: ohlc.map(({ time, close }) => ({ time, close })),
    };
    for (const ind of indicators) {
      if (ind.value === "rsi") result.indicators.rsi = calcRSI(closes, ind.params.period ?? 14);
      if (ind.value === "ma") result.indicators.ma = calcMA(closes, ind.params.period ?? 14);
      if (ind.value === "macd") result.indicators.macd = calcMACD(closes);
      if (ind.value === "bb") result.indicators.bb = calcBB(closes, ind.params.period ?? 20);
      if (ind.value === "stoch") result.indicators.stoch = calcStoch(ohlc, ind.params.k ?? 14, ind.params.d ?? 3);
      if (ind.value === "cci") result.indicators.cci = calcCCI(ohlc, ind.params.period ?? 20);
      if (ind.value === "atr") result.indicators.atr = calcATR(ohlc, ind.params.period ?? 14);
      if (ind.value === "adx") result.indicators.adx = calcADX(ohlc, ind.params.period ?? 14);
      if (ind.value === "volume") result.indicators.volume = ohlc[ohlc.length - 1].volume;
    }
    result.indicators.close = lastClose;
    // Gunakan upper/lower RSI jika ada
    const rsiUpper = (indicators.find((i: IndicatorSelection) => i.value === "rsi")?.params?.upper) ?? 70;
    const rsiLower = (indicators.find((i: IndicatorSelection) => i.value === "rsi")?.params?.lower) ?? 30;
    result.signal = generateSignal({ ...result.indicators, close: lastClose }, rsiUpper, rsiLower);
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