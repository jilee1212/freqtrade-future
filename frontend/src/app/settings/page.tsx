"use client"

import { Navbar } from "@/components/layout/navbar"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Settings, Bell, Shield, Database, Users } from "lucide-react"

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Manage your bot configuration and preferences
          </p>
        </div>

        <Tabs defaultValue="general" className="space-y-6">
          <TabsList>
            <TabsTrigger value="general" className="gap-2">
              <Settings className="h-4 w-4" />
              General
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2">
              <Bell className="h-4 w-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="api" className="gap-2">
              <Database className="h-4 w-4" />
              API Keys
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-2">
              <Shield className="h-4 w-4" />
              Security
            </TabsTrigger>
          </TabsList>

          {/* General Settings */}
          <TabsContent value="general">
            <Card className="p-6 space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-4">General Settings</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="botName">Bot Name</Label>
                  <Input
                    id="botName"
                    defaultValue="Freqtrade Future"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="exchange">Exchange</Label>
                  <Select defaultValue="binance">
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="binance">Binance Futures</SelectItem>
                      <SelectItem value="bybit">Bybit</SelectItem>
                      <SelectItem value="okx">OKX</SelectItem>
                      <SelectItem value="bitget">Bitget</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="timeframe">Default Timeframe</Label>
                  <Select defaultValue="5m">
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1m">1 minute</SelectItem>
                      <SelectItem value="5m">5 minutes</SelectItem>
                      <SelectItem value="15m">15 minutes</SelectItem>
                      <SelectItem value="1h">1 hour</SelectItem>
                      <SelectItem value="4h">4 hours</SelectItem>
                      <SelectItem value="1d">1 day</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Dry Run Mode</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Test strategies without real money
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Auto Start</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Start bot automatically on system restart
                    </p>
                  </div>
                  <Switch />
                </div>
              </div>

              <Button className="w-full">Save Changes</Button>
            </Card>
          </TabsContent>

          {/* Notifications */}
          <TabsContent value="notifications">
            <Card className="p-6 space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-4">Notification Preferences</h2>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Trade Notifications</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Get notified when trades are opened or closed
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Profit Alerts</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Alert when profit threshold is reached
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Loss Alerts</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Alert when loss threshold is reached
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Strategy Alerts</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Notifications about strategy performance
                    </p>
                  </div>
                  <Switch />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>System Alerts</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Bot errors and system status updates
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div>
                  <Label htmlFor="telegram">Telegram Bot Token</Label>
                  <Input
                    id="telegram"
                    placeholder="Enter your Telegram bot token"
                    className="mt-2"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    Optional: Get notifications via Telegram
                  </p>
                </div>

                <div>
                  <Label htmlFor="discord">Discord Webhook URL</Label>
                  <Input
                    id="discord"
                    placeholder="Enter Discord webhook URL"
                    className="mt-2"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    Optional: Get notifications via Discord
                  </p>
                </div>
              </div>

              <Button className="w-full">Save Preferences</Button>
            </Card>
          </TabsContent>

          {/* API Keys */}
          <TabsContent value="api">
            <Card className="p-6 space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-4">Exchange API Configuration</h2>
                <p className="text-sm text-muted-foreground">
                  Configure your exchange API credentials. Never share these keys.
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="apiKey">API Key</Label>
                  <Input
                    id="apiKey"
                    type="password"
                    placeholder="••••••••••••••••"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="apiSecret">API Secret</Label>
                  <Input
                    id="apiSecret"
                    type="password"
                    placeholder="••••••••••••••••"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="apiPassphrase">API Passphrase (if required)</Label>
                  <Input
                    id="apiPassphrase"
                    type="password"
                    placeholder="••••••••••••••••"
                    className="mt-2"
                  />
                </div>

                <div className="p-4 bg-yellow-600/10 border border-yellow-600/20 rounded-lg">
                  <p className="text-sm font-medium">⚠️ Security Notice</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Make sure to enable IP whitelist on your exchange and only grant
                    necessary permissions (read + trade, no withdraw).
                  </p>
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">
                  Test Connection
                </Button>
                <Button className="flex-1">Save API Keys</Button>
              </div>
            </Card>
          </TabsContent>

          {/* Security */}
          <TabsContent value="security">
            <Card className="p-6 space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-4">Security Settings</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="currentPassword">Current Password</Label>
                  <Input
                    id="currentPassword"
                    type="password"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="newPassword">New Password</Label>
                  <Input
                    id="newPassword"
                    type="password"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    className="mt-2"
                  />
                </div>

                <div className="flex items-center justify-between pt-4">
                  <div>
                    <Label>Two-Factor Authentication (2FA)</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Add an extra layer of security to your account
                    </p>
                  </div>
                  <Switch />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Session Timeout</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Auto logout after inactivity
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div>
                  <Label htmlFor="ipWhitelist">IP Whitelist</Label>
                  <Textarea
                    id="ipWhitelist"
                    placeholder="Enter IP addresses (one per line)"
                    className="mt-2"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    Restrict access to specific IP addresses
                  </p>
                </div>
              </div>

              <Button className="w-full">Update Security Settings</Button>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}