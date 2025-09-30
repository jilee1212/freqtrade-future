"use client"

import { useState } from "react"
import { Navbar } from "@/components/layout/navbar"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatCurrency, formatPercent } from "@/lib/utils"
import { TrendingUp, TrendingDown, Download, Filter } from "lucide-react"

interface Trade {
  id: string
  pair: string
  side: "long" | "short"
  entryPrice: number
  exitPrice?: number
  amount: number
  leverage: number
  pnl: number
  pnlPercent: number
  openDate: string
  closeDate?: string
  status: "open" | "closed"
}

const demoTrades: Trade[] = [
  {
    id: "1",
    pair: "BTC/USDT",
    side: "long",
    entryPrice: 67234,
    exitPrice: 68100,
    amount: 0.5,
    leverage: 10,
    pnl: 433,
    pnlPercent: 12.87,
    openDate: "2025-09-30 14:23:10",
    closeDate: "2025-09-30 15:45:22",
    status: "closed"
  },
  {
    id: "2",
    pair: "ETH/USDT",
    side: "short",
    entryPrice: 3456,
    amount: 2,
    leverage: 5,
    pnl: -12.45,
    pnlPercent: -0.36,
    openDate: "2025-09-30 13:10:05",
    status: "open"
  },
  {
    id: "3",
    pair: "SOL/USDT",
    side: "long",
    entryPrice: 145.2,
    exitPrice: 152.8,
    amount: 10,
    leverage: 3,
    pnl: 228,
    pnlPercent: 15.70,
    openDate: "2025-09-30 11:05:33",
    closeDate: "2025-09-30 12:30:15",
    status: "closed"
  },
  {
    id: "4",
    pair: "BNB/USDT",
    side: "long",
    entryPrice: 612.5,
    amount: 3,
    leverage: 5,
    pnl: 45.23,
    pnlPercent: 2.46,
    openDate: "2025-09-30 15:20:00",
    status: "open"
  },
]

export default function TradesPage() {
  const [activeTab, setActiveTab] = useState("all")

  const openTrades = demoTrades.filter(t => t.status === "open")
  const closedTrades = demoTrades.filter(t => t.status === "closed")

  const TradeTable = ({ trades }: { trades: Trade[] }) => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Pair</TableHead>
          <TableHead>Side</TableHead>
          <TableHead>Entry</TableHead>
          <TableHead>Exit</TableHead>
          <TableHead>Amount</TableHead>
          <TableHead>Leverage</TableHead>
          <TableHead>P&L</TableHead>
          <TableHead>Open Date</TableHead>
          <TableHead>Close Date</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {trades.map((trade) => (
          <TableRow key={trade.id}>
            <TableCell className="font-medium">{trade.pair}</TableCell>
            <TableCell>
              <Badge
                variant={trade.side === "long" ? "default" : "destructive"}
                className={trade.side === "long" ? "bg-green-600" : ""}
              >
                {trade.side.toUpperCase()}
              </Badge>
            </TableCell>
            <TableCell>{formatCurrency(trade.entryPrice)}</TableCell>
            <TableCell>
              {trade.exitPrice ? formatCurrency(trade.exitPrice) : "-"}
            </TableCell>
            <TableCell>{trade.amount}</TableCell>
            <TableCell>{trade.leverage}x</TableCell>
            <TableCell>
              <div className="flex items-center gap-2">
                {trade.pnl >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
                <span className={trade.pnl >= 0 ? "text-green-600" : "text-red-600"}>
                  {formatCurrency(trade.pnl)}
                </span>
                <span className={`text-sm ${trade.pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                  ({formatPercent(trade.pnlPercent)})
                </span>
              </div>
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {trade.openDate}
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {trade.closeDate || "-"}
            </TableCell>
            <TableCell>
              <Badge variant={trade.status === "open" ? "default" : "secondary"}>
                {trade.status}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Trade History</h1>
            <p className="text-muted-foreground mt-1">
              View and analyze all your trading activity
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2">
              <Filter className="h-4 w-4" />
              Filter
            </Button>
            <Button className="gap-2">
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="p-6">
            <p className="text-sm text-muted-foreground">Total Trades</p>
            <p className="text-3xl font-bold mt-2">{demoTrades.length}</p>
            <p className="text-sm text-muted-foreground mt-1">All time</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-muted-foreground">Open Positions</p>
            <p className="text-3xl font-bold mt-2">{openTrades.length}</p>
            <p className="text-sm text-blue-600 mt-1">Active now</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-muted-foreground">Closed Trades</p>
            <p className="text-3xl font-bold mt-2">{closedTrades.length}</p>
            <p className="text-sm text-muted-foreground mt-1">Completed</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-muted-foreground">Total P&L</p>
            <p className="text-3xl font-bold mt-2 text-green-600">
              {formatCurrency(693.78)}
            </p>
            <p className="text-sm text-green-600 mt-1">+10.32%</p>
          </Card>
        </div>

        {/* Trades Table */}
        <Card className="p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="all">All Trades ({demoTrades.length})</TabsTrigger>
              <TabsTrigger value="open">Open ({openTrades.length})</TabsTrigger>
              <TabsTrigger value="closed">Closed ({closedTrades.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-6">
              <TradeTable trades={demoTrades} />
            </TabsContent>

            <TabsContent value="open" className="mt-6">
              <TradeTable trades={openTrades} />
            </TabsContent>

            <TabsContent value="closed" className="mt-6">
              <TradeTable trades={closedTrades} />
            </TabsContent>
          </Tabs>
        </Card>
      </main>
    </div>
  )
}