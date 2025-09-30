"use client"

import { Navbar } from "@/components/layout/navbar"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { formatCurrency, formatPercent } from "@/lib/utils"
import {
  Shield,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  Activity,
  Bell
} from "lucide-react"

interface RiskMetric {
  label: string
  value: number
  max: number
  status: "safe" | "warning" | "danger"
  description: string
}

const riskMetrics: RiskMetric[] = [
  {
    label: "Portfolio Risk",
    value: 35,
    max: 100,
    status: "safe",
    description: "Overall exposure as percentage of total capital"
  },
  {
    label: "Max Drawdown",
    value: 12.5,
    max: 25,
    status: "warning",
    description: "Largest peak-to-trough decline"
  },
  {
    label: "Leverage Usage",
    value: 8.2,
    max: 10,
    status: "danger",
    description: "Current average leverage across positions"
  },
  {
    label: "Position Concentration",
    value: 42,
    max: 100,
    status: "warning",
    description: "Percentage in largest position"
  }
]

export default function RiskPage() {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "safe":
        return "text-green-600"
      case "warning":
        return "text-yellow-600"
      case "danger":
        return "text-red-600"
      default:
        return "text-gray-600"
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case "safe":
        return "bg-green-600"
      case "warning":
        return "bg-yellow-600"
      case "danger":
        return "bg-red-600"
      default:
        return "bg-gray-600"
    }
  }

  const RiskGauge = ({ metric }: { metric: RiskMetric }) => {
    const percentage = (metric.value / metric.max) * 100

    return (
      <Card className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-semibold">{metric.label}</h3>
            <p className="text-sm text-muted-foreground mt-1">{metric.description}</p>
          </div>
          <Badge
            variant="outline"
            className={`${getStatusColor(metric.status)} border-current`}
          >
            {metric.status.toUpperCase()}
          </Badge>
        </div>

        {/* Gauge */}
        <div className="space-y-3">
          <div className="flex items-end gap-2">
            <span className={`text-4xl font-bold ${getStatusColor(metric.status)}`}>
              {metric.value}
            </span>
            <span className="text-2xl text-muted-foreground mb-1">/ {metric.max}</span>
          </div>

          {/* Progress Bar */}
          <div className="relative h-4 bg-muted rounded-full overflow-hidden">
            <div
              className={`absolute left-0 top-0 h-full ${getStatusBg(metric.status)} transition-all duration-500`}
              style={{ width: `${percentage}%` }}
            />
          </div>

          <div className="flex justify-between text-sm text-muted-foreground">
            <span>0</span>
            <span>{percentage.toFixed(1)}%</span>
            <span>{metric.max}</span>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Risk Monitor</h1>
            <p className="text-muted-foreground mt-1">
              Track and manage your portfolio risk in real-time
            </p>
          </div>
          <Button className="gap-2">
            <Bell className="h-4 w-4" />
            Configure Alerts
          </Button>
        </div>

        {/* Overall Risk Status */}
        <Card className="p-6 bg-gradient-to-r from-primary/10 to-purple-600/10 border-primary/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-green-600/20 flex items-center justify-center">
                <Shield className="h-8 w-8 text-green-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">Overall Risk: Moderate</h2>
                <p className="text-muted-foreground mt-1">
                  Your portfolio is within acceptable risk parameters
                </p>
              </div>
            </div>
            <Badge className="bg-green-600 text-white px-4 py-2 text-lg">
              Safe
            </Badge>
          </div>
        </Card>

        {/* Risk Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {riskMetrics.map((metric) => (
            <RiskGauge key={metric.label} metric={metric} />
          ))}
        </div>

        {/* Additional Risk Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-3">
              <DollarSign className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Account Balance</h3>
            </div>
            <p className="text-3xl font-bold">{formatCurrency(10450.23)}</p>
            <p className="text-sm text-green-600 mt-1">+2.3% this week</p>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-3 mb-3">
              <Activity className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Open Positions</h3>
            </div>
            <p className="text-3xl font-bold">4</p>
            <p className="text-sm text-muted-foreground mt-1">
              {formatCurrency(3500)} total value
            </p>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-3 mb-3">
              <TrendingUp className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Profit Today</h3>
            </div>
            <p className="text-3xl font-bold text-green-600">
              {formatCurrency(234.56)}
            </p>
            <p className="text-sm text-green-600 mt-1">+2.24%</p>
          </Card>
        </div>

        {/* Risk Alerts */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <h2 className="text-xl font-semibold">Recent Alerts</h2>
          </div>

          <div className="space-y-3">
            <div className="flex items-start gap-3 p-4 border border-yellow-600/20 bg-yellow-600/5 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <p className="font-medium">High Leverage Warning</p>
                <p className="text-sm text-muted-foreground mt-1">
                  BTC/USDT position using 10x leverage - consider reducing exposure
                </p>
                <p className="text-xs text-muted-foreground mt-2">2 hours ago</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 border border-blue-600/20 bg-blue-600/5 rounded-lg">
              <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <p className="font-medium">Stop Loss Triggered</p>
                <p className="text-sm text-muted-foreground mt-1">
                  ETH/USDT position closed at stop loss level - loss minimized to -0.8%
                </p>
                <p className="text-xs text-muted-foreground mt-2">5 hours ago</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 border border-green-600/20 bg-green-600/5 rounded-lg">
              <Shield className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium">Risk Parameters Normal</p>
                <p className="text-sm text-muted-foreground mt-1">
                  All risk metrics are within acceptable ranges
                </p>
                <p className="text-xs text-muted-foreground mt-2">1 day ago</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Risk Management Tips */}
        <Card className="p-6 bg-muted/50">
          <h2 className="text-xl font-semibold mb-4">Risk Management Tips</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium mb-2">✓ Always use stop losses</h3>
              <p className="text-sm text-muted-foreground">
                Protect your capital by setting stop losses on every trade
              </p>
            </div>
            <div>
              <h3 className="font-medium mb-2">✓ Diversify your positions</h3>
              <p className="text-sm text-muted-foreground">
                Don't put all your capital in one asset or strategy
              </p>
            </div>
            <div>
              <h3 className="font-medium mb-2">✓ Limit leverage usage</h3>
              <p className="text-sm text-muted-foreground">
                Higher leverage increases both profits and losses
              </p>
            </div>
            <div>
              <h3 className="font-medium mb-2">✓ Monitor drawdown</h3>
              <p className="text-sm text-muted-foreground">
                Keep track of your peak-to-trough losses
              </p>
            </div>
          </div>
        </Card>
      </main>
    </div>
  )
}