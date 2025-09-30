"use client"

import { useEffect, useRef } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi, LineData } from 'lightweight-charts'

interface EquityChartProps {
  data?: LineData[]
  height?: number
}

export function EquityChart({ data, height = 400 }: EquityChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null)

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
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
      },
    })

    const lineSeries = chart.addLineSeries({
      color: '#22c55e',
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 6,
      lastValueVisible: true,
      priceLineVisible: true,
    })

    chartRef.current = chart
    seriesRef.current = lineSeries

    // Default demo data if no data provided
    const defaultData: LineData[] = Array.from({ length: 30 }, (_, i) => ({
      time: (Date.now() / 1000 - (29 - i) * 86400) as any,
      value: 10000 + Math.random() * 1000 * (i / 10),
    }))

    lineSeries.setData(data || defaultData)

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
  }, [data, height])

  return (
    <div className="relative w-full">
      <div ref={chartContainerRef} className="w-full" />
    </div>
  )
}