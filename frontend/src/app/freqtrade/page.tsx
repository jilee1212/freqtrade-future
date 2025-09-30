"use client"

import { useState, useEffect } from "react"
import { Navbar } from "@/components/layout/navbar"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ExternalLink, RefreshCw } from "lucide-react"

export default function FreqtradePage() {
  const [iframeKey, setIframeKey] = useState(0)
  const freqtradeUrl = process.env.NEXT_PUBLIC_FREQTRADE_URL || "http://localhost:8080"

  const handleRefresh = () => {
    setIframeKey(prev => prev + 1)
  }

  const handleOpenNewTab = () => {
    window.open(freqtradeUrl, '_blank')
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">FreqUI Dashboard</h1>
            <p className="text-muted-foreground">
              Official Freqtrade Web Interface
            </p>
          </div>
          
          <div className="flex gap-2">
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={handleOpenNewTab} variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Open in New Tab
            </Button>
          </div>
        </div>

        <Card className="overflow-hidden">
          <iframe
            key={iframeKey}
            src={freqtradeUrl}
            className="w-full h-[calc(100vh-220px)] border-0"
            title="Freqtrade UI"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
          />
        </Card>
      </main>
    </div>
  )
}
