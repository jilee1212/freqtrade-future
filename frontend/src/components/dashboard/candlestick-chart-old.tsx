"use client"

import { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData, HistogramData } from 'lightweight-charts'

interface CandlestickChartProps {
  symbol?: string
  data?: CandlestickData[]
  volumeData?: HistogramData[]
  height?: number
}

export function CandlestickChart({
  symbol = 'BTC/USDT',
  data,
  volumeData,
  height = 500
}: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      width: chartContainerRef.current.clientWidth,
      height,
      rightPriceScale: {
        borderColor: '#334155',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
      },
    })

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    const volumeSeries = chart.addHistogramSeries({
      color: '#3b82f6',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries
    volumeSeriesRef.current = volumeSeries

    // Generate demo data if none provided
    const generateDemoData = () => {
      const demoCandles: CandlestickData[] = []
      const demoVolume: HistogramData[] = []
      let basePrice = 45000

      for (let i = 0; i < 100; i++) {
        const time = (Date.now() / 1000 - (99 - i) * 300) as any // 5-minute candles
        const open = basePrice + (Math.random() - 0.5) * 100
        const close = open + (Math.random() - 0.5) * 200
        const high = Math.max(open, close) + Math.random() * 100
        const low = Math.min(open, close) - Math.random() * 100

        demoCandles.push({ time, open, high, low, close })
        demoVolume.push({
          time,
          value: Math.random() * 1000,
          color: close > open ? '#22c55e33' : '#ef444433',
        })

        basePrice = close
      }

      return { candles: demoCandles, volume: demoVolume }
    }

    const { candles, volume } = generateDemoData()
    candlestickSeries.setData(data || candles)
    volumeSeries.setData(volumeData || volume)

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, volumeData, height])

  return (
    <div className="relative w-full">
      <div className="absolute top-4 left-4 z-10 bg-card/80 backdrop-blur-sm px-3 py-2 rounded-lg border border-border">
        <div className="text-sm font-semibold text-foreground">{symbol}</div>
      </div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  )
}