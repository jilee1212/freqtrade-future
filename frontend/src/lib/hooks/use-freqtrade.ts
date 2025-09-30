"use client"

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { backendEndpoints } from '@/lib/api'
import { useWebSocket } from './use-websocket'
import { useEffect } from 'react'

export function useFreqtradeStatus() {
  return useQuery({
    queryKey: ['freqtrade', 'status'],
    queryFn: async () => {
      const response = await backendEndpoints.status()
      return response.data
    },
  })
}

export function useFreqtradeBalance() {
  return useQuery({
    queryKey: ['freqtrade', 'balance'],
    queryFn: async () => {
      const response = await backendEndpoints.balance()
      return response.data
    },
  })
}

export function useFreqtradeTrades() {
  return useQuery({
    queryKey: ['freqtrade', 'trades'],
    queryFn: async () => {
      const response = await backendEndpoints.trades()
      return response.data
    },
  })
}

export function useFreqtradeProfit() {
  return useQuery({
    queryKey: ['freqtrade', 'profit'],
    queryFn: async () => {
      const response = await backendEndpoints.profit()
      return response.data
    },
  })
}

// Real-time updates via WebSocket
export function useFreqtradeRealtime() {
  const queryClient = useQueryClient()
  const { isConnected, subscribe } = useWebSocket()

  useEffect(() => {
    if (!isConnected) return

    // Subscribe to trade updates
    const unsubTrade = subscribe('trade_update', (data) => {
      queryClient.invalidateQueries({ queryKey: ['freqtrade', 'trades'] })
      queryClient.invalidateQueries({ queryKey: ['freqtrade', 'profit'] })
    })

    // Subscribe to balance updates
    const unsubBalance = subscribe('balance_update', (data) => {
      queryClient.invalidateQueries({ queryKey: ['freqtrade', 'balance'] })
    })

    // Subscribe to status updates
    const unsubStatus = subscribe('status_update', (data) => {
      queryClient.invalidateQueries({ queryKey: ['freqtrade', 'status'] })
    })

    return () => {
      unsubTrade()
      unsubBalance()
      unsubStatus()
    }
  }, [isConnected, subscribe, queryClient])

  return { isConnected }
}