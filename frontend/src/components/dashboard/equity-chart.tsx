"use client"

import { useEffect, useRef } from 'react'
import { createChart, ColorType } from 'lightweight-charts'

interface EquityChartProps {
  data?: Array<{ time: string; value: number }>
  height?: number
}

export function EquityChart({ data, height = 400 }: EquityChartProps) {
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

    const lineSeries = chart.addAreaSeries({
      lineColor: '#22c55e',
      topColor: '#22c55e33',
      bottomColor: '#22c55e00',
      lineWidth: 2,
    })

    // Generate demo data if none provided
    const now = Math.floor(Date.now() / 1000)
    const defaultData = Array.from({ length: 30 }, (_, i) => {
      const date = new Date((now - (29 - i) * 86400) * 1000)
      return {
        time: date.toISOString().split('T')[0],
        value: 10000 + Math.random() * 1000 + i * 30,
      }
    })

    lineSeries.setData(data || defaultData)

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
  }, [data, height])

  return (
    <div className="relative w-full">
      <div ref={chartContainerRef} className="w-full" />
    </div>
  )
}
