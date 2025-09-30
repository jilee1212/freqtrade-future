"use client"

import { useState, useEffect } from 'react'
import { freqtradeEndpoints } from '@/lib/api'

interface TradingData {
  balance: number
  balanceChange: number
  pnl: number
  pnlPercent: number
  winRate: number
  openTrades: number
  todayTrades: number
  status: string
  loading: boolean
  error: string | null
}

export function useTradingData() {
  const [data, setData] = useState<TradingData>({
    balance: 10450.23,
    balanceChange: 2.3,
    pnl: 234.56,
    pnlPercent: 2.3,
    winRate: 68.5,
    openTrades: 2,
    todayTrades: 8,
    status: "running",
    loading: true,
    error: null,
  })

  const fetchData = async () => {
    try {
      // Try to fetch real data from Freqtrade API
      const [statusRes, balanceRes, profitRes, tradesRes] = await Promise.allSettled([
        freqtradeEndpoints.status(),
        freqtradeEndpoints.balance(),
        freqtradeEndpoints.profit(),
        freqtradeEndpoints.trades(),
      ])

      // Process status
      if (statusRes.status === 'fulfilled' && statusRes.value.status === 'success') {
        const statusData = statusRes.value.data as any
        setData(prev => ({
          ...prev,
          status: statusData.state || 'unknown',
        }))
      }

      // Process balance
      if (balanceRes.status === 'fulfilled' && balanceRes.value.status === 'success') {
        const balanceData = balanceRes.value.data as any
        const total = balanceData.total || 0
        setData(prev => ({
          ...prev,
          balance: total,
        }))
      }

      // Process profit
      if (profitRes.status === 'fulfilled' && profitRes.value.status === 'success') {
        const profitData = profitRes.value.data as any
        setData(prev => ({
          ...prev,
          pnl: profitData.profit_closed_coin || 0,
          pnlPercent: profitData.profit_closed_percent || 0,
          todayTrades: profitData.trade_count || 0,
          winRate: profitData.winning_trades && profitData.trade_count
            ? (profitData.winning_trades / profitData.trade_count) * 100
            : 0,
        }))
      }

      // Process trades
      if (tradesRes.status === 'fulfilled' && tradesRes.value.status === 'success') {
        const tradesData = tradesRes.value.data as any[]
        const openTradesCount = tradesData.filter((t: any) => t.is_open).length
        setData(prev => ({
          ...prev,
          openTrades: openTradesCount,
        }))
      }

      setData(prev => ({ ...prev, loading: false, error: null }))
    } catch (error) {
      console.error('Error fetching trading data:', error)
      setData(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch data',
      }))
    }
  }

  useEffect(() => {
    fetchData()

    // Poll every 10 seconds
    const interval = setInterval(fetchData, 10000)

    return () => clearInterval(interval)
  }, [])

  return { data, refetch: fetchData }
}