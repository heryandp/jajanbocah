"use client";
import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi } from "lightweight-charts";

export type OhlcPoint = { time: number; close: number; open?: number; high?: number; low?: number; volume?: number };
export type IndicatorArr = { time: number; value: number }[];
export type ChartIndicators = { rsiArr?: IndicatorArr; maArr?: IndicatorArr; macdArr?: IndicatorArr };

export default function SignalChart({ ohlc, signal, indicators }: { ohlc: OhlcPoint[]; signal?: string; indicators?: ChartIndicators }) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const toChartTime = (t: number) => {
    const d = new Date(t * 1000);
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  };

  useEffect(() => {
    if (!ohlc || ohlc.length === 0 || !chartContainerRef.current) return;
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: { background: { type: ColorType.Solid, color: '#18181b' }, textColor: '#e5e7eb' },
      grid: { vertLines: { color: '#27272a' }, horzLines: { color: '#27272a' } },
      timeScale: { timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderColor: '#888' },
    });
    chartRef.current = chart;
    // Candlestick
    if (ohlc[0].open !== undefined && ohlc[0].high !== undefined && ohlc[0].low !== undefined) {
      const candleSeries = chart.addCandlestickSeries();
      candleSeries.setData(
        ohlc
          .filter(d => typeof d.open === 'number' && typeof d.high === 'number' && typeof d.low === 'number' && typeof d.close === 'number')
          .map(d => ({
            time: toChartTime(d.time),
            open: d.open!,
            high: d.high!,
            low: d.low!,
            close: d.close
          }))
      );
    } else {
      // fallback line
      const lineSeries = chart.addLineSeries({ color: '#f59e42', lineWidth: 2 });
      lineSeries.setData(ohlc.map(d => ({ time: toChartTime(d.time), value: d.close })));
    }
    // Volume
    if (ohlc[0].volume !== undefined) {
      const volumeSeries = chart.addHistogramSeries({ color: '#60a5fa', priceFormat: { type: 'volume' }, priceScaleId: 'vol' });
      volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.7, bottom: 0 } });
      volumeSeries.setData(ohlc.map(d => ({ time: toChartTime(d.time), value: d.volume ?? 0 })));
    }
    // MA, RSI, MACD jika ada
    if (indicators?.maArr && Array.isArray(indicators.maArr)) {
      const maSeries = chart.addLineSeries({ color: '#fbbf24', lineWidth: 1 });
      maSeries.setData(indicators.maArr.map(d => ({ time: toChartTime(d.time), value: d.value })));
    }
    if (indicators?.rsiArr && Array.isArray(indicators.rsiArr)) {
      const rsiSeries = chart.addLineSeries({ color: '#38bdf8', lineWidth: 1 });
      rsiSeries.setData(indicators.rsiArr.map(d => ({ time: toChartTime(d.time), value: d.value })));
    }
    if (indicators?.macdArr && Array.isArray(indicators.macdArr)) {
      const macdSeries = chart.addLineSeries({ color: '#a78bfa', lineWidth: 1 });
      macdSeries.setData(indicators.macdArr.map(d => ({ time: toChartTime(d.time), value: d.value })));
    }
    // Icon signal di titik terakhir
    if (signal && ohlc.length > 0) {
      const last = ohlc[ohlc.length - 1];
      const marker = {
        time: toChartTime(last.time),
        position: signal === "BUY" ? "belowBar" : "aboveBar",
        color: signal === "BUY" ? "#22c55e" : "#ef4444",
        shape: signal === "BUY" ? "arrowUp" : "arrowDown",
        text: signal,
      };
      // marker hanya untuk candlestick/line utama
      if (ohlc[0].open !== undefined) {
        chart.serieses()[0].setMarkers([marker]);
      }
    }
    // Responsive
    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current?.clientWidth || 400 });
    };
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [ohlc, signal, indicators]);

  return <div ref={chartContainerRef} style={{ width: '100%', height: 400 }} />;
} 