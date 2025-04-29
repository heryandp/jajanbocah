"use client";
import { useState } from "react";
import dynamic from "next/dynamic";

const INDICATORS = [
  { label: "RSI", value: "rsi", params: [{ name: "upper", label: "Upper", default: 70 }, { name: "lower", label: "Lower", default: 30 }, { name: "period", label: "Period", default: 14 }] },
  { label: "MACD", value: "macd", params: [] },
  { label: "Moving Average", value: "ma", params: [{ name: "period", label: "Period", default: 14 }] },
  { label: "Bollinger Bands", value: "bb", params: [{ name: "period", label: "Period", default: 20 }] },
  { label: "Stochastic", value: "stoch", params: [{ name: "k", label: "%K", default: 14 }, { name: "d", label: "%D", default: 3 }] },
  { label: "CCI", value: "cci", params: [{ name: "period", label: "Period", default: 20 }] },
  { label: "ATR", value: "atr", params: [{ name: "period", label: "Period", default: 14 }] },
  { label: "ADX", value: "adx", params: [{ name: "period", label: "Period", default: 14 }] },
  { label: "Volume", value: "volume", params: [] },
];
const TIMEFRAMES = [
  { label: "M1", value: "1m" },
  { label: "M5", value: "5m" },
  { label: "M15", value: "15m" },
  { label: "M30", value: "30m" },
  { label: "H1", value: "1h" },
  { label: "H4", value: "4h" },
  { label: "D1", value: "1d" },
  { label: "W1", value: "1w" },
  { label: "1 Bulan", value: "1mo" },
  { label: "3 Bulan", value: "3mo" },
  { label: "6 Bulan", value: "6mo" },
  { label: "12 Bulan", value: "12mo" },
];

const PAIRS = [
  { label: "GOLD", value: "GOLD" },
  { label: "BTCUSD", value: "BTC-USD" },
  { label: "EURUSD", value: "EURUSD=X" },
  { label: "AAPL", value: "AAPL" },
  { label: "TSLA", value: "TSLA" },
  { label: "GOOG", value: "GOOG" },
  { label: "AMZN", value: "AMZN" },
];

type IndicatorParam = { [key: string]: number };
type IndicatorSelection = { value: string; params: IndicatorParam };

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

type SignalResult = {
  indicators: IndicatorResult;
  close: number;
  signal?: string;
  error?: string;
  ohlc?: { time: number; close: number }[];
};

const Chart = dynamic(() => import("./SignalChart"), { ssr: false });

export default function Home() {
  const [pair, setPair] = useState("GOLD");
  const [timeframe, setTimeframe] = useState("15m");
  const [selectedIndicators, setSelectedIndicators] = useState<IndicatorSelection[]>(
    INDICATORS.map((ind) => ({ value: ind.value, params: Object.fromEntries(ind.params.map(p => [p.name, p.default])) }))
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SignalResult | null>(null);
  const [showIndicator, setShowIndicator] = useState<{[key:string]:boolean}>({});

  const handleIndicatorChange = (value: string) => {
    setSelectedIndicators((prev) =>
      prev.some((v) => v.value === value)
        ? prev.filter((v) => v.value !== value)
        : [...prev, { value, params: Object.fromEntries(INDICATORS.find(i => i.value === value)?.params.map(p => [p.name, p.default]) || []) }]
    );
  };

  const handleParamChange = (indValue: string, param: string, val: number) => {
    setSelectedIndicators((prev) =>
      prev.map((v) =>
        v.value === indValue ? { ...v, params: { ...v.params, [param]: val } } : v
      )
    );
  };

  const handleShowIndicator = (ind: string) => {
    setShowIndicator((prev) => ({ ...prev, [ind]: !prev[ind] }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    const res = await fetch("/api/signal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: pair,
        timeframe,
        indicators: selectedIndicators,
      }),
    });
    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  return (
    <div className="max-w-xl mx-auto py-10 px-4">
      <h1 className="text-2xl font-bold mb-4">Signal Trading</h1>
      <p className="mb-4 text-sm text-gray-600 dark:text-gray-300">Signal <b>WAIT</b> artinya: <span className="text-yellow-600">Tunggu, jangan lakukan apapun sampai ada signal BUY/SELL.</span></p>
      <form onSubmit={handleSubmit} className="space-y-4 bg-white dark:bg-gray-900 p-6 rounded shadow">
        <div>
          <label className="block font-medium mb-1">Pair</label>
          <select
            className="w-full border rounded p-2 bg-white dark:bg-gray-800 shadow focus:outline-none focus:ring-2 focus:ring-yellow-400"
            value={pair}
            onChange={(e) => setPair(e.target.value)}
          >
            {PAIRS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block font-medium mb-1">Timeframe</label>
          <select
            className="w-full border rounded p-2 bg-white dark:bg-gray-800 shadow focus:outline-none focus:ring-2 focus:ring-yellow-400"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
          >
            {TIMEFRAMES.map((tf) => (
              <option key={tf.value} value={tf.value}>
                {tf.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block font-medium mb-1">Indikator</label>
          <div className="flex flex-col gap-3">
            {INDICATORS.map((ind) => {
              const selected = selectedIndicators.find((v) => v.value === ind.value);
              return (
                <div key={ind.value} className="flex flex-col gap-1 border p-2 rounded bg-gray-50 dark:bg-gray-900">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={!!selected}
                      onChange={() => handleIndicatorChange(ind.value)}
                    />
                    <span>{ind.label}</span>
                    <button type="button" className="ml-auto text-xs text-yellow-600 underline" onClick={() => handleShowIndicator(ind.value)}>
                      {showIndicator[ind.value] ? "Hide" : "Show"} Param
                    </button>
                  </div>
                  {selected && ind.params.length > 0 && showIndicator[ind.value] && (
                    <div className="flex flex-wrap gap-2 mt-1">
                      {ind.params.map((p) => (
                        <label key={p.name} className="flex items-center gap-1 text-xs">
                          {p.label}:
                          <input
                            type="number"
                            className="border rounded px-1 py-0.5 w-16"
                            value={selected.params[p.name]}
                            onChange={(e) => handleParamChange(ind.value, p.name, Number(e.target.value))}
                          />
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        <button
          type="submit"
          className="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded"
          disabled={loading}
        >
          {loading ? "Loading..." : "Generate Signal"}
        </button>
      </form>
      {result && (
        <div className="mt-8 bg-gray-100 dark:bg-gray-800 p-4 rounded">
          <h2 className="text-lg font-semibold mb-2">Hasil Signal</h2>
          <div className="mb-2">Signal: <span className="font-bold text-xl">{result.signal}</span></div>
          {result.signal === "WAIT" && (
            <div className="mb-2 p-2 bg-yellow-100 text-yellow-800 rounded">Tunggu, jangan lakukan apapun.</div>
          )}
          {result.signal === "BUY" && (
            <div className="mb-2 p-2 bg-green-100 text-green-800 rounded">Segera lakukan <b>BUY</b> sesuai signal!</div>
          )}
          {result.signal === "SELL" && (
            <div className="mb-2 p-2 bg-red-100 text-red-800 rounded">Segera lakukan <b>SELL</b> sesuai signal!</div>
          )}
          <div>
            <h3 className="font-semibold">Indikator:</h3>
            <ul className="list-disc ml-5">
              {Object.entries(result.indicators || {}).map(([key, val]) => (
                <li key={key}>
                  {key.toUpperCase()}: {typeof val === "object" ? JSON.stringify(val) : val}
                </li>
              ))}
            </ul>
          </div>
          {result.ohlc && (
            <div className="mt-6">
              <Chart ohlc={result.ohlc} signal={result.signal} indicators={{ rsiArr: result.indicators.rsiArr, maArr: result.indicators.maArr, macdArr: result.indicators.macdArr }} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
