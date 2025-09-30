"use client"

import { useEffect, useRef } from 'react'
import { createChart, ColorType } from 'lightweight-charts'

interface CandlestickChartProps {
  symbol?: string
  height?: number
}

export function CandlestickChart({
  symbol = 'BTC/USDT',
  height = 500
}: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)

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
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
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

    // Generate demo candlestick data
    const now = Math.floor(Date.now() / 1000)
    let basePrice = 45000
    const demoCandles = []

    for (let i = 0; i < 100; i++) {
      const time = now - (99 - i) * 300 // 5-minute candles
      const open = basePrice + (Math.random() - 0.5) * 100
      const close = open + (Math.random() - 0.5) * 200
      const high = Math.max(open, close) + Math.random() * 100
      const low = Math.min(open, close) - Math.random() * 100

      const date = new Date(time * 1000)
      demoCandles.push({
        time: date.toISOString().split('T')[0] + ' ' + date.toTimeString().split(' ')[0].substring(0, 5),
        open,
        high,
        low,
        close,
      })

      basePrice = close
    }

    candlestickSeries.setData(demoCandles)

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [height])

  return (
    <div className="relative w-full">
      <div className="absolute top-4 left-4 z-10 bg-card/80 backdrop-blur-sm px-3 py-2 rounded-lg border border-border">
        <div className="text-sm font-semibold text-foreground">{symbol}</div>
      </div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  )
}