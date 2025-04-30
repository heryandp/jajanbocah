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

  function uniqueAsc<T extends { time: string }>(arr: T[]): T[] {
    const seen = new Set();
    return arr
      .sort((a, b) => a.time.localeCompare(b.time))
      .filter(item => {
        if (seen.has(item.time)) return false;
        seen.add(item.time);
        return true;
      });
  }

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
    let mainSeries;
    if (ohlc[0].open !== undefined && ohlc[0].high !== undefined && ohlc[0].low !== undefined) {
      mainSeries = chart.addCandlestickSeries();
      mainSeries.setData(
        uniqueAsc(
          ohlc
            .filter(d => typeof d.open === 'number' && typeof d.high === 'number' && typeof d.low === 'number' && typeof d.close === 'number')
            .map(d => ({
              time: toChartTime(d.time),
              open: d.open!,
              high: d.high!,
              low: d.low!,
              close: d.close
            }))
        )
      );
    } else {
      mainSeries = chart.addLineSeries({ color: '#f59e42', lineWidth: 2 });
      mainSeries.setData(uniqueAsc(ohlc.map(d => ({ time: toChartTime(d.time), value: d.close }))));
    }
    // Volume
    if (ohlc[0].volume !== undefined) {
      const volumeSeries = chart.addHistogramSeries({ color: '#60a5fa', priceFormat: { type: 'volume' }, priceScaleId: 'vol' });
      volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.7, bottom: 0 } });
      volumeSeries.setData(uniqueAsc(ohlc.map(d => ({ time: toChartTime(d.time), value: d.volume ?? 0 }))));
    }
    // MA, RSI, MACD jika ada
    if (indicators?.maArr && Array.isArray(indicators.maArr)) {
      const maSeries = chart.addLineSeries({ color: '#fbbf24', lineWidth: 1 });
      maSeries.setData(uniqueAsc(indicators.maArr.map(d => ({ time: toChartTime(d.time), value: d.value }))));
    }
    if (indicators?.rsiArr && Array.isArray(indicators.rsiArr)) {
      const rsiSeries = chart.addLineSeries({ color: '#38bdf8', lineWidth: 1 });
      rsiSeries.setData(uniqueAsc(indicators.rsiArr.map(d => ({ time: toChartTime(d.time), value: d.value }))));
    }
    if (indicators?.macdArr && Array.isArray(indicators.macdArr)) {
      const macdSeries = chart.addLineSeries({ color: '#a78bfa', lineWidth: 1 });
      macdSeries.setData(uniqueAsc(indicators.macdArr.map(d => ({ time: toChartTime(d.time), value: d.value }))));
    }
    // Icon signal di titik terakhir
    if (signal && ohlc.length > 0) {
      const last = ohlc[ohlc.length - 1];
      const marker = {
        time: toChartTime(last.time),
        position: signal === "BUY" ? "belowBar" as const : "aboveBar" as const,
        color: signal === "BUY" ? "#22c55e" : "#ef4444",
        shape: signal === "BUY" ? "arrowUp" as const : "arrowDown" as const,
        text: signal,
      };
      mainSeries.setMarkers([marker]);
    }
    // Responsive
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [ohlc, signal, indicators]);

  return <>
    <div ref={chartContainerRef} style={{ width: '100%', height: 400 }} />
    <button
      onClick={() => {
        if (chartRef.current) {
          const screenshot = chartRef.current.takeScreenshot();
          let dataUrl = '';
          if (typeof screenshot === 'string') {
            dataUrl = screenshot;
          } else if (screenshot instanceof HTMLCanvasElement) {
            dataUrl = screenshot.toDataURL();
          }
          if (dataUrl) {
            const a = document.createElement('a');
            a.href = dataUrl;
            a.download = 'chart.png';
            a.click();
          }
        }
      }}
      className="mt-2 px-4 py-2 bg-yellow-500 text-white rounded"
    >
      Download Chart
    </button>
  </>;
} 