"use client"

import { useState } from "react"
import { Navbar } from "@/components/layout/navbar"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { formatCurrency, formatPercent } from "@/lib/utils"
import {
  TrendingUp,
  Play,
  Pause,
  Settings,
  BarChart3,
  CheckCircle2,
  XCircle
} from "lucide-react"

interface Strategy {
  id: string
  name: string
  description: string
  status: "active" | "inactive" | "testing"
  winRate: number
  totalTrades: number
  profitFactor: number
  avgProfit: number
  maxDrawdown: number
  pairs: string[]
}

const demoStrategies: Strategy[] = [
  {
    id: "1",
    name: "EMA Crossover",
    description: "Exponential moving average crossover strategy with volume confirmation",
    status: "active",
    winRate: 68.5,
    totalTrades: 245,
    profitFactor: 2.34,
    avgProfit: 1.2,
    maxDrawdown: -8.5,
    pairs: ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
  },
  {
    id: "2",
    name: "RSI Divergence",
    description: "Identifies divergence between price and RSI for potential reversals",
    status: "active",
    winRate: 72.3,
    totalTrades: 189,
    profitFactor: 2.87,
    avgProfit: 1.8,
    maxDrawdown: -6.2,
    pairs: ["BTC/USDT", "ETH/USDT"]
  },
  {
    id: "3",
    name: "Bollinger Breakout",
    description: "Trades breakouts from Bollinger Bands with volume surge",
    status: "testing",
    winRate: 65.0,
    totalTrades: 78,
    profitFactor: 1.95,
    avgProfit: 0.9,
    maxDrawdown: -12.1,
    pairs: ["BNB/USDT", "ADA/USDT"]
  },
  {
    id: "4",
    name: "MACD Momentum",
    description: "MACD histogram momentum strategy for trending markets",
    status: "inactive",
    winRate: 61.2,
    totalTrades: 312,
    profitFactor: 1.76,
    avgProfit: 0.7,
    maxDrawdown: -15.3,
    pairs: ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
  },
]

export default function StrategiesPage() {
  const [selectedStrategy, setSelectedStrategy] = useState(demoStrategies[0])

  const activeStrategies = demoStrategies.filter(s => s.status === "active")

  const handleToggleStrategy = (strategyId: string, enabled: boolean) => {
    console.log(`Strategy ${strategyId} ${enabled ? 'enabled' : 'disabled'}`)
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Strategy Manager</h1>
            <p className="text-muted-foreground mt-1">
              Configure and monitor your trading strategies
            </p>
          </div>
          <Button className="gap-2">
            <Settings className="h-4 w-4" />
            Configure
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="p-6">
            <p className="text-sm text-muted-foreground">Active Strategies</p>
            <p className="text-3xl font-bold mt-2">{activeStrategies.length}</p>
            <p className="text-sm text-green-600 mt-1">Running</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-muted-foreground">Avg Win Rate</p>
            <p className="text-3xl font-bold mt-2">68.7%</p>
            <p className="text-sm text-muted-foreground mt-1">Across all strategies</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-muted-foreground">Total Trades</p>
            <p className="text-3xl font-bold mt-2">824</p>
            <p className="text-sm text-muted-foreground mt-1">All time</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-muted-foreground">Avg Profit Factor</p>
            <p className="text-3xl font-bold mt-2 text-green-600">2.23</p>
            <p className="text-sm text-green-600 mt-1">Strong performance</p>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Strategy List */}
          <Card className="lg:col-span-1 p-6">
            <h2 className="text-xl font-semibold mb-4">Strategies</h2>
            <div className="space-y-3">
              {demoStrategies.map((strategy) => (
                <div
                  key={strategy.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedStrategy.id === strategy.id
                      ? "border-primary bg-primary/5"
                      : "hover:bg-muted/50"
                  }`}
                  onClick={() => setSelectedStrategy(strategy)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-semibold">{strategy.name}</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {strategy.totalTrades} trades
                      </p>
                    </div>
                    <Badge
                      variant={
                        strategy.status === "active"
                          ? "default"
                          : strategy.status === "testing"
                          ? "secondary"
                          : "outline"
                      }
                      className={strategy.status === "active" ? "bg-green-600" : ""}
                    >
                      {strategy.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{strategy.winRate}%</span>
                    <span className="text-sm text-muted-foreground">win rate</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Strategy Details */}
          <Card className="lg:col-span-2 p-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold">{selectedStrategy.name}</h2>
                <p className="text-muted-foreground mt-1">
                  {selectedStrategy.description}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={selectedStrategy.status === "active"}
                  onCheckedChange={(checked) =>
                    handleToggleStrategy(selectedStrategy.id, checked)
                  }
                />
                <Label>Enable</Label>
              </div>
            </div>

            <Tabs defaultValue="performance">
              <TabsList>
                <TabsTrigger value="performance">Performance</TabsTrigger>
                <TabsTrigger value="settings">Settings</TabsTrigger>
                <TabsTrigger value="backtest">Backtest</TabsTrigger>
              </TabsList>

              <TabsContent value="performance" className="mt-6 space-y-6">
                {/* Performance Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Win Rate</p>
                    <p className="text-2xl font-bold mt-1">
                      {selectedStrategy.winRate}%
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Profit Factor</p>
                    <p className="text-2xl font-bold mt-1 text-green-600">
                      {selectedStrategy.profitFactor}
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Avg Profit</p>
                    <p className="text-2xl font-bold mt-1">
                      {formatPercent(selectedStrategy.avgProfit)}
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground">Max Drawdown</p>
                    <p className="text-2xl font-bold mt-1 text-red-600">
                      {formatPercent(selectedStrategy.maxDrawdown)}
                    </p>
                  </div>
                </div>

                {/* Trading Pairs */}
                <div>
                  <h3 className="font-semibold mb-3">Active Pairs</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedStrategy.pairs.map((pair) => (
                      <Badge key={pair} variant="secondary">
                        {pair}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Recent Activity */}
                <div>
                  <h3 className="font-semibold mb-3">Recent Activity</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                        <div>
                          <p className="font-medium">BTC/USDT LONG</p>
                          <p className="text-sm text-muted-foreground">2 hours ago</p>
                        </div>
                      </div>
                      <span className="text-green-600 font-semibold">+2.4%</span>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <XCircle className="h-5 w-5 text-red-600" />
                        <div>
                          <p className="font-medium">ETH/USDT SHORT</p>
                          <p className="text-sm text-muted-foreground">5 hours ago</p>
                        </div>
                      </div>
                      <span className="text-red-600 font-semibold">-0.8%</span>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="settings" className="mt-6">
                <div className="space-y-4">
                  <div>
                    <Label>Risk per Trade</Label>
                    <Select defaultValue="1">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1% of balance</SelectItem>
                        <SelectItem value="2">2% of balance</SelectItem>
                        <SelectItem value="3">3% of balance</SelectItem>
                        <SelectItem value="5">5% of balance</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label>Max Open Trades</Label>
                    <Select defaultValue="3">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1</SelectItem>
                        <SelectItem value="2">2</SelectItem>
                        <SelectItem value="3">3</SelectItem>
                        <SelectItem value="5">5</SelectItem>
                        <SelectItem value="10">10</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Stop Loss</Label>
                    <Switch defaultChecked />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Take Profit</Label>
                    <Switch defaultChecked />
                  </div>

                  <Button className="w-full mt-4">Save Changes</Button>
                </div>
              </TabsContent>

              <TabsContent value="backtest" className="mt-6">
                <div className="text-center py-12">
                  <BarChart3 className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">
                    Backtesting results will be displayed here
                  </p>
                  <Button className="mt-4 gap-2">
                    <Play className="h-4 w-4" />
                    Run Backtest
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </Card>
        </div>
      </main>
    </div>
  )
}