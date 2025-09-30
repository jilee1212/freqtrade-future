"use client"

import { useEffect, useRef, useState } from 'react'
import { wsClient } from '@/lib/websocket'

interface UseWebSocketOptions {
  url?: string
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: any) => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const optionsRef = useRef(options)

  useEffect(() => {
    optionsRef.current = options
  }, [options])

  useEffect(() => {
    const url = optionsRef.current.url || process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:5000'

    const handleConnect = () => {
      setIsConnected(true)
      optionsRef.current.onConnect?.()
    }

    const handleDisconnect = () => {
      setIsConnected(false)
      optionsRef.current.onDisconnect?.()
    }

    const handleError = (error: any) => {
      optionsRef.current.onError?.(error)
    }

    // Connect to WebSocket
    wsClient.connect(url)
    wsClient.on('connect', handleConnect)
    wsClient.on('disconnect', handleDisconnect)
    wsClient.on('error', handleError)

    // Update initial connection state
    setIsConnected(wsClient.isConnected())

    return () => {
      wsClient.off('connect', handleConnect)
      wsClient.off('disconnect', handleDisconnect)
      wsClient.off('error', handleError)
    }
  }, [])

  const subscribe = (event: string, callback: (...args: any[]) => void) => {
    wsClient.on(event, callback)
    return () => wsClient.off(event, callback)
  }

  const emit = (event: string, ...args: any[]) => {
    wsClient.emit(event, ...args)
  }

  return {
    isConnected,
    subscribe,
    emit,
  }
}