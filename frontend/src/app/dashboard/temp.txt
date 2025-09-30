"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Settings,
  Bell
} from "lucide-react"
import { formatCurrency, formatPercent } from "@/lib/utils"

interface DashboardData {
  balance: number
  balanceChange: number
  pnl: number
  pnlPercent: number
  winRate: number
  openTrades: number
  todayTrades: number
  status: string
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData>({
    balance: 10450.23,
    balanceChange: 2.3,
    pnl: 234.56,
    pnlPercent: 2.3,
    winRate: 68.5,
    openTrades: 2,
    todayTrades: 8,
    status: "running"
  })
  const [lastUpdate, setLastUpdate] = useState(new Date())

  // Simulated real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => ({
        ...prev,
        pnl: prev.pnl + (Math.random() - 0.5) * 10,
        balance: prev.balance + (Math.random() - 0.5) * 10,
      }))
      setLastUpdate(new Date())
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold">Trading Dashboard</h1>
              <Badge variant={data.status === "running" ? "default" : "secondary"}>
                <div className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse" />
                {data.status.toUpperCase()}
              </Badge>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                Last update: {lastUpdate.toLocaleTimeString()}
              </span>
              <Button size="icon" variant="ghost">
                <Bell className="h-4 w-4" />
              </Button>
              <Button size="icon" variant="ghost">
                <Settings className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="outline" className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Balance Card */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Total Balance</p>
                <p className="text-3xl font-bold">{formatCurrency(data.balance)}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <DollarSign className="h-6 w-6 text-primary" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              {data.balanceChange >= 0 ? (
                <ArrowUpRight className="h-4 w-4 text-green-600" />
              ) : (
                <ArrowDownRight className="h-4 w-4 text-red-600" />
              )}
              <span className={data.balanceChange >= 0 ? "text-green-600" : "text-red-600"}>
                {formatPercent(data.balanceChange)}
              </span>
              <span className="text-sm text-muted-foreground">vs yesterday</span>
            </div>
          </Card>

          {/* P&L Card */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Today's P&L</p>
                <p className={`text-3xl font-bold ${data.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(data.pnl)}
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                {data.pnl >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-green-600" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-600" />
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={data.pnlPercent >= 0 ? "text-green-600" : "text-red-600"}>
                {formatPercent(data.pnlPercent)}
              </span>
              <span className="text-sm text-muted-foreground">return</span>
            </div>
          </Card>

          {/* Win Rate Card */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Win Rate</p>
                <p className="text-3xl font-bold">{data.winRate}%</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-primary" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-green-600 border-green-600">
                Excellent
              </Badge>
              <span className="text-sm text-muted-foreground">
                {Math.round(data.winRate * data.todayTrades / 100)}/{data.todayTrades} wins
              </span>
            </div>
          </Card>

          {/* Open Trades Card */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Open Positions</p>
                <p className="text-3xl font-bold">{data.openTrades}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Activity className="h-6 w-6 text-primary" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-blue-600 border-blue-600">
                Active
              </Badge>
              <span className="text-sm text-muted-foreground">
                {data.todayTrades} trades today
              </span>
            </div>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart Section */}
          <Card className="lg:col-span-2 p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Equity Curve</h2>
              <div className="flex gap-2">
                <Button size="sm" variant="outline">1D</Button>
                <Button size="sm" variant="outline">1W</Button>
                <Button size="sm" variant="default">1M</Button>
                <Button size="sm" variant="outline">ALL</Button>
              </div>
            </div>
            <div className="h-[400px] flex items-center justify-center bg-muted/50 rounded-lg">
              <div className="text-center space-y-2">
                <BarChart3 className="h-16 w-16 text-muted-foreground mx-auto" />
                <p className="text-sm text-muted-foreground">
                  Chart will be integrated with TradingView Lightweight Charts
                </p>
              </div>
            </div>
          </Card>

          {/* Quick Actions */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6">Quick Actions</h2>
            <div className="space-y-3">
              <Button className="w-full justify-start" variant="outline">
                <Activity className="mr-2 h-4 w-4" />
                View All Trades
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <BarChart3 className="mr-2 h-4 w-4" />
                Strategy Manager
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <TrendingUp className="mr-2 h-4 w-4" />
                Risk Monitor
              </Button>
              <Separator className="my-4" />
              <a
                href={process.env.NEXT_PUBLIC_FREQTRADE_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="block"
              >
                <Button className="w-full" variant="default">
                  Open FreqUI
                  <ArrowUpRight className="ml-2 h-4 w-4" />
                </Button>
              </a>
            </div>
          </Card>
        </div>

        {/* Open Positions */}
        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Open Positions</h2>
            <Button size="sm" variant="outline">View All</Button>
          </div>

          <div className="space-y-4">
            {/* Position 1 - SHORT */}
            <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors border-l-4 border-l-red-500">
              <div className="flex items-center gap-4">
                <div>
                  <p className="font-semibold">BTC/USDT</p>
                  <p className="text-sm text-muted-foreground">Perpetual Futures</p>
                </div>
                <Badge variant="destructive">SHORT</Badge>
              </div>

              <div className="text-right">
                <p className="font-semibold">Entry: $67,234</p>
                <p className="text-sm text-muted-foreground">5x Leverage</p>
              </div>

              <div className="text-right">
                <p className="font-semibold text-green-600">+$45.23</p>
                <p className="text-sm text-green-600">+0.67%</p>
              </div>

              <Button size="sm" variant="outline">Close</Button>
            </div>

            {/* Position 2 - LONG */}
            <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors border-l-4 border-l-green-500">
              <div className="flex items-center gap-4">
                <div>
                  <p className="font-semibold">ETH/USDT</p>
                  <p className="text-sm text-muted-foreground">Perpetual Futures</p>
                </div>
                <Badge className="bg-green-600">LONG</Badge>
              </div>

              <div className="text-right">
                <p className="font-semibold">Entry: $3,456</p>
                <p className="text-sm text-muted-foreground">3x Leverage</p>
              </div>

              <div className="text-right">
                <p className="font-semibold text-red-600">-$12.45</p>
                <p className="text-sm text-red-600">-0.36%</p>
              </div>

              <Button size="sm" variant="outline">Close</Button>
            </div>
          </div>
        </Card>

        {/* Recent Trades */}
        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Recent Trades</h2>
            <Button size="sm" variant="outline">View All</Button>
          </div>

          <div className="space-y-2">
            {[
              { pair: "BTC/USDT", profit: 2.3, time: "2 mins ago", win: true },
              { pair: "ETH/USDT", profit: -1.2, time: "5 mins ago", win: false },
              { pair: "SOL/USDT", profit: 4.5, time: "10 mins ago", win: true },
              { pair: "BNB/USDT", profit: 1.8, time: "15 mins ago", win: true },
            ].map((trade, i) => (
              <div key={i} className="flex items-center justify-between py-3 border-b last:border-0">
                <div>
                  <p className="font-medium">{trade.pair}</p>
                  <p className="text-sm text-muted-foreground">{trade.time}</p>
                </div>
                <div className="text-right flex items-center gap-4">
                  <div>
                    <p className={`font-semibold ${trade.win ? 'text-green-600' : 'text-red-600'}`}>
                      {trade.win ? '+' : ''}{trade.profit}%
                    </p>
                  </div>
                  <span className="text-2xl">{trade.win ? '✅' : '❌'}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </main>
    </div>
  )
}