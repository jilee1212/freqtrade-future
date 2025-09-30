import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowRight, TrendingUp, Shield, Zap, BarChart3, Bot, LineChart } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="flex flex-col items-center text-center space-y-8">
          <div className="inline-block rounded-lg bg-primary/10 px-4 py-2">
            <span className="text-sm font-medium text-primary">AI-Powered Trading</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            Freqtrade Future
          </h1>

          <p className="max-w-2xl text-xl text-muted-foreground">
            Professional-grade automated trading system for Binance Futures with
            AI-powered risk management and real-time monitoring
          </p>

          <div className="flex gap-4">
            <Link href="/dashboard">
              <Button size="lg" className="gap-2">
                Launch Dashboard <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href={process.env.NEXT_PUBLIC_FREQTRADE_URL} target="_blank" rel="noopener noreferrer">
              <Button size="lg" variant="outline">
                Open FreqUI
              </Button>
            </a>
          </div>

          {/* Status Indicator */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span>System Online • Server: 141.164.42.93</span>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="text-sm text-muted-foreground">Total Balance</div>
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            <div className="text-3xl font-bold mb-2">$10,450</div>
            <div className="text-sm text-green-600">+2.3% today</div>
          </Card>

          <Card className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="text-sm text-muted-foreground">Win Rate</div>
              <BarChart3 className="h-5 w-5 text-primary" />
            </div>
            <div className="text-3xl font-bold mb-2">68.5%</div>
            <div className="text-sm text-muted-foreground">68/100 trades</div>
          </Card>

          <Card className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="text-sm text-muted-foreground">Today's P&L</div>
              <LineChart className="h-5 w-5 text-primary" />
            </div>
            <div className="text-3xl font-bold mb-2 text-green-600">+$234</div>
            <div className="text-sm text-muted-foreground">+2.3% return</div>
          </Card>

          <Card className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="text-sm text-muted-foreground">Open Trades</div>
              <Bot className="h-5 w-5 text-primary" />
            </div>
            <div className="text-3xl font-bold mb-2">2</div>
            <div className="text-sm text-blue-600">Active positions</div>
          </Card>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Powerful Features</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Everything you need for professional cryptocurrency futures trading
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="p-6 hover:shadow-lg transition-all">
            <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Real-time Trading</h3>
            <p className="text-muted-foreground">
              Execute trades instantly with WebSocket-powered real-time data streaming
            </p>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-all">
            <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">AI Risk Management</h3>
            <p className="text-muted-foreground">
              Advanced AI algorithms monitor and manage portfolio risk in real-time
            </p>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-all">
            <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Bot className="h-6 w-6 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Multiple Strategies</h3>
            <p className="text-muted-foreground">
              Choose from proven strategies or create your own with backtesting
            </p>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16">
        <Card className="p-12 bg-gradient-to-r from-primary to-purple-600 text-white">
          <div className="max-w-2xl mx-auto text-center space-y-6">
            <h2 className="text-4xl font-bold">Ready to Start Trading?</h2>
            <p className="text-lg text-white/90">
              Access your trading dashboard and start monitoring your positions in real-time
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/dashboard">
                <Button size="lg" variant="secondary" className="gap-2">
                  Go to Dashboard <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </Card>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 mt-16 border-t">
        <div className="flex justify-between items-center text-sm text-muted-foreground">
          <div>Freqtrade Future v1.0.0</div>
          <div>Powered by Next.js & shadcn/ui</div>
        </div>
      </footer>
    </div>
  )
}
