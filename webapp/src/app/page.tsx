"use client";
import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import Select from "react-select";

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

const PAIRS_YAHOO = [
  { label: "GOLD", value: "GOLD" },
  { label: "BTCUSD", value: "BTC-USD" },
  { label: "EURUSD", value: "EURUSD=X" },
  { label: "AAPL", value: "AAPL" },
  { label: "TSLA", value: "TSLA" },
  { label: "GOOG", value: "GOOG" },
  { label: "AMZN", value: "AMZN" },
];

const SOURCES = [
  { label: 'MT5 Local (Realtime)', value: 'mt5' },
  { label: 'Yahoo Finance (Online)', value: 'yahoo' },
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
  openPositionPrice?: number;
  tp?: number;
  sl?: number;
};

const Chart = dynamic(() => import("./SignalChart"), { ssr: false });

const REFRESH_OPTIONS = [
  { label: "Manual", value: 0 },
  { label: "5 detik", value: 5000 },
  { label: "10 detik", value: 10000 },
  { label: "30 detik", value: 30000 },
];

export default function Home() {
  const [pair, setPair] = useState("GOLD");
  const [timeframe, setTimeframe] = useState("15m");
  const [selectedIndicators, setSelectedIndicators] = useState<IndicatorSelection[]>(
    INDICATORS.map((ind) => ({ value: ind.value, params: Object.fromEntries(ind.params.map(p => [p.name, p.default])) }))
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SignalResult | null>(null);
  const [showIndicator, setShowIndicator] = useState<{[key:string]:boolean}>({});
  const [source, setSource] = useState('yahoo');
  const [mt5Pairs, setMt5Pairs] = useState<{ label: string; value: string }[]>([]);
  const [refreshInterval, setRefreshInterval] = useState(0); // ms
  const [volume, setVolume] = useState(0.01);
  const [targetProfit, setTargetProfit] = useState(1);
  const [targetLoss, setTargetLoss] = useState(0.5);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (source === 'mt5') {
      fetch('http://localhost:5000/symbols')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setMt5Pairs(data.map((s: string) => ({ label: s, value: s })));
            setPair(data[0] || "");
          }
        })
        .catch(() => setMt5Pairs([]));
    }
  }, [source]);

  // Auto refresh logic
  const fetchSignal = async () => {
    setLoading(true);
    setResult(null);
    const res = await fetch("/api/signal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: pair,
        timeframe,
        indicators: selectedIndicators,
        source,
        volume,
        targetProfit,
        targetLoss,
      }),
    });
    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      fetchSignal(); // fetch langsung saat interval berubah
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(fetchSignal, refreshInterval);
      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
      };
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshInterval, pair, timeframe, selectedIndicators, source]);

  // Reset result saat ganti pair/timeframe/indikator/source
  useEffect(() => {
    setResult(null);
  }, [pair, timeframe, selectedIndicators, source]);

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
    fetchSignal();
  };

  const pairList = source === 'mt5' ? mt5Pairs : PAIRS_YAHOO;
  const pairOptions = pairList.map(p => ({ label: p.label, value: p.value }));
  const selectedPairOption = pairOptions.find(opt => opt.value === pair) || null;

  return (
    <div className="max-w-xl mx-auto py-10 px-4">
      <h1 className="text-2xl font-bold mb-4">Signal Trading</h1>
      <p className="mb-4 text-sm text-gray-600 dark:text-gray-300">Signal <b>WAIT</b> artinya: <span className="text-yellow-600">Tunggu, jangan lakukan apapun sampai ada signal BUY/SELL.</span></p>
      <form onSubmit={handleSubmit} className="space-y-4 bg-white dark:bg-gray-900 p-6 rounded shadow">
        <div>
          <label className="block font-medium mb-1">Sumber Data</label>
          <select
            className="w-full border rounded p-2 bg-white dark:bg-gray-800 shadow focus:outline-none focus:ring-2 focus:ring-yellow-400"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            {SOURCES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block font-medium mb-1">Pair</label>
          <Select
            className="react-select-container"
            classNamePrefix="react-select"
            options={pairOptions}
            value={selectedPairOption}
            onChange={opt => setPair(opt ? opt.value : "")}
            isSearchable
            placeholder="Pilih atau cari pair..."
            styles={{
              container: base => ({ ...base, width: '100%' }),
              menu: base => ({ ...base, zIndex: 20 }),
            }}
          />
        </div>
        <div className="flex gap-2">
          <div className="flex-1">
            <label className="block font-medium mb-1">Volume (lot)</label>
            <input
              type="number"
              min={0.01}
              step={0.01}
              className="w-full border rounded p-2 bg-white dark:bg-gray-800 shadow"
              value={volume}
              onChange={e => setVolume(Number(e.target.value))}
            />
          </div>
          <div className="flex-1">
            <label className="block font-medium mb-1">Target Profit (%)</label>
            <input
              type="number"
              min={0.1}
              step={0.1}
              className="w-full border rounded p-2 bg-white dark:bg-gray-800 shadow"
              value={targetProfit}
              onChange={e => setTargetProfit(Number(e.target.value))}
            />
          </div>
          <div className="flex-1">
            <label className="block font-medium mb-1">Target Loss (%)</label>
            <input
              type="number"
              min={0.1}
              step={0.1}
              className="w-full border rounded p-2 bg-white dark:bg-gray-800 shadow"
              value={targetLoss}
              onChange={e => setTargetLoss(Number(e.target.value))}
            />
          </div>
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
        <div>
          <label className="block font-medium mb-1">Auto Refresh</label>
          <select
            className="w-full border rounded p-2 bg-white dark:bg-gray-800 shadow focus:outline-none focus:ring-2 focus:ring-yellow-400"
            value={refreshInterval}
            onChange={e => setRefreshInterval(Number(e.target.value))}
          >
            {REFRESH_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
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
          <div className="mb-2">Volume: <span className="font-mono text-lg">{volume}</span> lot</div>
          <div className="mb-2">Target Profit: <span className="font-mono text-lg">{targetProfit}%</span> &nbsp;|&nbsp; Target Loss: <span className="font-mono text-lg">{targetLoss}%</span></div>
          <div className="mb-2">Signal: <span className="font-bold text-xl">{result.signal}</span></div>
          <div className="mb-2">Posisi: <span className={`font-bold text-xl ${result.signal === 'BUY' ? 'text-green-600' : result.signal === 'SELL' ? 'text-red-600' : 'text-yellow-600'}`}>{result.signal}</span></div>
          <div className="mb-2">Current Price: <span className="font-mono text-lg">{result.close}</span></div>
          {(result.signal === 'BUY' || result.signal === 'SELL') && result.openPositionPrice !== undefined && (
            <>
              <div className="mb-2">Open Position Price: <span className="font-mono text-lg">{result.openPositionPrice}</span></div>
              {result.tp !== undefined && <div className="mb-2">TP: <span className="font-mono text-lg text-green-600">{result.tp}</span></div>}
              {result.sl !== undefined && <div className="mb-2">SL: <span className="font-mono text-lg text-red-600">{result.sl}</span></div>}
            </>
          )}
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
              {['rsi', 'macd', 'ma', 'bb', 'stoch', 'cci', 'atr', 'adx', 'volume', 'close'].map(key => (
                (result.indicators as any)[key] !== undefined && (
                  <li key={key}>
                    {key.toUpperCase()}: {typeof (result.indicators as any)[key] === 'object' && !Array.isArray((result.indicators as any)[key]) ? JSON.stringify((result.indicators as any)[key]) : (result.indicators as any)[key]}
                  </li>
                )
              ))}
            </ul>
          </div>
          {result.ohlc && (
            <div className="mt-6">
              <Chart ohlc={result.ohlc} signal={result.signal} indicators={{ rsiArr: (result.indicators as any).rsiArr, maArr: (result.indicators as any).maArr, macdArr: (result.indicators as any).macdArr }} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
