export interface Trade {
  id: string
  pair: string
  side: "long" | "short"
  entry_price: number
  current_price: number
  amount: number
  leverage: number
  pnl: number
  pnl_percent: number
  open_date: string
  is_open: boolean
}

export interface TradeHistory {
  id: string
  pair: string
  side: "long" | "short"
  entry_price: number
  exit_price: number
  profit: number
  profit_percent: number
  open_date: string
  close_date: string
  duration: number
}

export interface Balance {
  currency: string
  free: number
  used: number
  total: number
}

export interface Profit {
  profit_closed_coin: number
  profit_closed_percent: number
  profit_all_coin: number
  profit_all_percent: number
  trade_count: number
  first_trade_date: string
  latest_trade_date: string
  avg_duration: number
  best_pair: string
  best_rate: number
  winning_trades: number
  losing_trades: number
}

export interface BotStatus {
  state: "running" | "stopped" | "unknown"
  strategy: string
  strategy_version: string
  max_open_trades: number
  stake_amount: string
  dry_run: boolean
  dry_run_wallet: number
}