#!/usr/bin/env python3
"""
Multi-Exchange Support and Arbitrage System
Phase 9: Advanced multi-exchange trading and arbitrage detection

Features:
- Multi-exchange connectivity
- Cross-exchange arbitrage detection
- Liquidity aggregation
- Exchange performance monitoring
- Smart order routing
"""

import os
import sys
import json
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import time

# Exchange connectors
import ccxt
import ccxt.async_support as ccxt_async

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

@dataclass
class ExchangeInfo:
    """Exchange information structure"""
    name: str
    enabled: bool
    api_key: str
    api_secret: str
    sandbox: bool
    fees: Dict[str, float]
    min_trade_amount: float
    max_leverage: float
    supported_pairs: List[str]

@dataclass
class OrderBookData:
    """Order book data structure"""
    exchange: str
    symbol: str
    timestamp: datetime
    bids: List[Tuple[float, float]]  # [(price, amount), ...]
    asks: List[Tuple[float, float]]
    bid_price: float
    ask_price: float
    spread: float
    spread_pct: float

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity structure"""
    buy_exchange: str
    sell_exchange: str
    symbol: str
    buy_price: float
    sell_price: float
    profit_pct: float
    max_volume: float
    timestamp: datetime
    confidence: float

class ExchangeConnector:
    """Individual exchange connector"""

    def __init__(self, exchange_info: ExchangeInfo):
        self.info = exchange_info
        self.exchange = None
        self.async_exchange = None
        self.is_connected = False
        self.last_error = None

        self._setup_exchange()

    def _setup_exchange(self):
        """Setup exchange connection"""
        try:
            # Synchronous exchange
            exchange_class = getattr(ccxt, self.info.name.lower())
            self.exchange = exchange_class({
                'apiKey': self.info.api_key,
                'secret': self.info.api_secret,
                'sandbox': self.info.sandbox,
                'enableRateLimit': True,
            })

            # Asynchronous exchange
            async_exchange_class = getattr(ccxt_async, self.info.name.lower())
            self.async_exchange = async_exchange_class({
                'apiKey': self.info.api_key,
                'secret': self.info.api_secret,
                'sandbox': self.info.sandbox,
                'enableRateLimit': True,
            })

            self.is_connected = True

        except Exception as e:
            self.last_error = str(e)
            self.is_connected = False

    async def get_order_book(self, symbol: str, limit: int = 10) -> Optional[OrderBookData]:
        """Get order book data"""
        if not self.is_connected:
            return None

        try:
            order_book = await self.async_exchange.fetch_order_book(symbol, limit)

            bids = order_book['bids'][:limit] if order_book['bids'] else []
            asks = order_book['asks'][:limit] if order_book['asks'] else []

            if not bids or not asks:
                return None

            bid_price = bids[0][0]
            ask_price = asks[0][0]
            spread = ask_price - bid_price
            spread_pct = (spread / bid_price) * 100

            return OrderBookData(
                exchange=self.info.name,
                symbol=symbol,
                timestamp=datetime.fromtimestamp(order_book['timestamp'] / 1000),
                bids=bids,
                asks=asks,
                bid_price=bid_price,
                ask_price=ask_price,
                spread=spread,
                spread_pct=spread_pct
            )

        except Exception as e:
            self.last_error = str(e)
            return None

    async def get_balance(self) -> Optional[Dict]:
        """Get account balance"""
        if not self.is_connected:
            return None

        try:
            balance = await self.async_exchange.fetch_balance()
            return balance
        except Exception as e:
            self.last_error = str(e)
            return None

    async def place_order(self, symbol: str, order_type: str, side: str,
                         amount: float, price: float = None) -> Optional[Dict]:
        """Place order on exchange"""
        if not self.is_connected:
            return None

        try:
            order = await self.async_exchange.create_order(
                symbol, order_type, side, amount, price
            )
            return order
        except Exception as e:
            self.last_error = str(e)
            return None

    def close(self):
        """Close exchange connection"""
        if self.async_exchange:
            asyncio.create_task(self.async_exchange.close())

class ArbitrageDetector:
    """Cross-exchange arbitrage detection"""

    def __init__(self, min_profit_pct: float = 0.5):
        self.min_profit_pct = min_profit_pct
        self.opportunities = []
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('ArbitrageDetector')
        logger.setLevel(logging.INFO)

        log_dir = os.path.join(project_root, 'ai_optimization', 'models')
        os.makedirs(log_dir, exist_ok=True)

        handler = logging.FileHandler(
            os.path.join(log_dir, 'arbitrage.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def detect_arbitrage(self, order_books: List[OrderBookData]) -> List[ArbitrageOpportunity]:
        """Detect arbitrage opportunities between exchanges"""
        opportunities = []

        if len(order_books) < 2:
            return opportunities

        # Group by symbol
        symbol_books = {}
        for book in order_books:
            if book.symbol not in symbol_books:
                symbol_books[book.symbol] = []
            symbol_books[book.symbol].append(book)

        # Find arbitrage opportunities for each symbol
        for symbol, books in symbol_books.items():
            if len(books) < 2:
                continue

            # Compare all pairs of exchanges
            for i in range(len(books)):
                for j in range(i + 1, len(books)):
                    book1, book2 = books[i], books[j]

                    # Check if we can buy on book1 and sell on book2
                    opp1 = self._check_arbitrage_pair(book1, book2)
                    if opp1:
                        opportunities.append(opp1)

                    # Check if we can buy on book2 and sell on book1
                    opp2 = self._check_arbitrage_pair(book2, book1)
                    if opp2:
                        opportunities.append(opp2)

        # Sort by profit percentage
        opportunities.sort(key=lambda x: x.profit_pct, reverse=True)

        # Log opportunities
        if opportunities:
            self.logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            for opp in opportunities[:5]:  # Log top 5
                self.logger.info(f"  {opp.symbol}: Buy {opp.buy_exchange} @ {opp.buy_price:.2f}, "
                               f"Sell {opp.sell_exchange} @ {opp.sell_price:.2f}, "
                               f"Profit: {opp.profit_pct:.2f}%")

        return opportunities

    def _check_arbitrage_pair(self, buy_book: OrderBookData,
                             sell_book: OrderBookData) -> Optional[ArbitrageOpportunity]:
        """Check arbitrage between two order books"""
        # Buy at ask price on buy_book, sell at bid price on sell_book
        buy_price = buy_book.ask_price
        sell_price = sell_book.bid_price

        if sell_price <= buy_price:
            return None

        profit_pct = ((sell_price - buy_price) / buy_price) * 100

        if profit_pct < self.min_profit_pct:
            return None

        # Calculate maximum volume (limited by smallest order book depth)
        buy_volume = buy_book.asks[0][1] if buy_book.asks else 0
        sell_volume = sell_book.bids[0][1] if sell_book.bids else 0
        max_volume = min(buy_volume, sell_volume)

        # Calculate confidence based on order book depth and spreads
        confidence = self._calculate_confidence(buy_book, sell_book, profit_pct)

        return ArbitrageOpportunity(
            buy_exchange=buy_book.exchange,
            sell_exchange=sell_book.exchange,
            symbol=buy_book.symbol,
            buy_price=buy_price,
            sell_price=sell_price,
            profit_pct=profit_pct,
            max_volume=max_volume,
            timestamp=datetime.now(),
            confidence=confidence
        )

    def _calculate_confidence(self, buy_book: OrderBookData,
                            sell_book: OrderBookData, profit_pct: float) -> float:
        """Calculate confidence score for arbitrage opportunity"""
        # Base confidence from profit margin
        profit_confidence = min(profit_pct / 2.0, 1.0)  # Max 1.0 at 2% profit

        # Reduce confidence for wide spreads
        avg_spread = (buy_book.spread_pct + sell_book.spread_pct) / 2
        spread_penalty = max(0, avg_spread - 0.1) * 2  # Penalty for spreads > 0.1%
        spread_confidence = max(0, 1.0 - spread_penalty)

        # Order book depth confidence
        depth_confidence = min(
            len(buy_book.asks) / 10,
            len(sell_book.bids) / 10,
            1.0
        )

        # Combined confidence
        confidence = (profit_confidence * 0.5 +
                     spread_confidence * 0.3 +
                     depth_confidence * 0.2)

        return max(0, min(confidence, 1.0))

class LiquidityAggregator:
    """Aggregate liquidity across multiple exchanges"""

    def __init__(self):
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('LiquidityAggregator')
        logger.setLevel(logging.INFO)

        log_dir = os.path.join(project_root, 'ai_optimization', 'models')
        os.makedirs(log_dir, exist_ok=True)

        handler = logging.FileHandler(
            os.path.join(log_dir, 'liquidity.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def aggregate_order_books(self, order_books: List[OrderBookData]) -> Dict:
        """Aggregate order books from multiple exchanges"""
        if not order_books:
            return {}

        # Group by symbol
        symbol_books = {}
        for book in order_books:
            if book.symbol not in symbol_books:
                symbol_books[book.symbol] = []
            symbol_books[book.symbol].append(book)

        aggregated = {}

        for symbol, books in symbol_books.items():
            # Aggregate bids and asks
            all_bids = []
            all_asks = []

            for book in books:
                # Add exchange info to each order
                for price, amount in book.bids:
                    all_bids.append((price, amount, book.exchange))
                for price, amount in book.asks:
                    all_asks.append((price, amount, book.exchange))

            # Sort bids (highest first) and asks (lowest first)
            all_bids.sort(key=lambda x: x[0], reverse=True)
            all_asks.sort(key=lambda x: x[0])

            # Calculate aggregate metrics
            best_bid = all_bids[0][0] if all_bids else 0
            best_ask = all_asks[0][0] if all_asks else 0
            spread = best_ask - best_bid if best_bid and best_ask else 0
            spread_pct = (spread / best_bid * 100) if best_bid else 0

            # Calculate total liquidity
            total_bid_volume = sum(bid[1] for bid in all_bids)
            total_ask_volume = sum(ask[1] for ask in all_asks)

            aggregated[symbol] = {
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread': spread,
                'spread_pct': spread_pct,
                'total_bid_volume': total_bid_volume,
                'total_ask_volume': total_ask_volume,
                'bid_depth': len(all_bids),
                'ask_depth': len(all_asks),
                'exchanges': len(books),
                'bids': all_bids[:20],  # Top 20 bids
                'asks': all_asks[:20]   # Top 20 asks
            }

        return aggregated

    def find_best_execution(self, symbol: str, side: str, amount: float,
                          order_books: List[OrderBookData]) -> Dict:
        """Find best execution strategy across exchanges"""
        symbol_books = [book for book in order_books if book.symbol == symbol]

        if not symbol_books:
            return {'error': 'No order books found for symbol'}

        execution_plan = []
        remaining_amount = amount

        if side == 'buy':
            # Sort by ask price (lowest first)
            sorted_books = sorted(symbol_books, key=lambda x: x.ask_price)

            for book in sorted_books:
                if remaining_amount <= 0:
                    break

                available_amount = sum(ask[1] for ask in book.asks)
                execution_amount = min(remaining_amount, available_amount)

                if execution_amount > 0:
                    # Calculate weighted average price
                    total_cost = 0
                    temp_amount = execution_amount

                    for ask_price, ask_amount in book.asks:
                        if temp_amount <= 0:
                            break

                        use_amount = min(temp_amount, ask_amount)
                        total_cost += use_amount * ask_price
                        temp_amount -= use_amount

                    avg_price = total_cost / execution_amount

                    execution_plan.append({
                        'exchange': book.exchange,
                        'amount': execution_amount,
                        'price': avg_price,
                        'cost': total_cost
                    })

                    remaining_amount -= execution_amount

        else:  # sell
            # Sort by bid price (highest first)
            sorted_books = sorted(symbol_books, key=lambda x: x.bid_price, reverse=True)

            for book in sorted_books:
                if remaining_amount <= 0:
                    break

                available_amount = sum(bid[1] for bid in book.bids)
                execution_amount = min(remaining_amount, available_amount)

                if execution_amount > 0:
                    # Calculate weighted average price
                    total_value = 0
                    temp_amount = execution_amount

                    for bid_price, bid_amount in book.bids:
                        if temp_amount <= 0:
                            break

                        use_amount = min(temp_amount, bid_amount)
                        total_value += use_amount * bid_price
                        temp_amount -= use_amount

                    avg_price = total_value / execution_amount

                    execution_plan.append({
                        'exchange': book.exchange,
                        'amount': execution_amount,
                        'price': avg_price,
                        'value': total_value
                    })

                    remaining_amount -= execution_amount

        # Calculate execution summary
        total_executed = amount - remaining_amount
        execution_rate = (total_executed / amount * 100) if amount > 0 else 0

        if side == 'buy':
            total_cost = sum(plan['cost'] for plan in execution_plan)
            avg_execution_price = total_cost / total_executed if total_executed > 0 else 0
        else:
            total_value = sum(plan['value'] for plan in execution_plan)
            avg_execution_price = total_value / total_executed if total_executed > 0 else 0

        return {
            'symbol': symbol,
            'side': side,
            'requested_amount': amount,
            'executed_amount': total_executed,
            'execution_rate': execution_rate,
            'avg_price': avg_execution_price,
            'execution_plan': execution_plan,
            'exchanges_used': len(execution_plan)
        }

class MultiExchangeManager:
    """Main multi-exchange management system"""

    def __init__(self):
        self.exchanges = {}
        self.arbitrage_detector = ArbitrageDetector()
        self.liquidity_aggregator = LiquidityAggregator()
        self.logger = self._setup_logging()

        self.is_monitoring = False
        self.monitoring_symbols = ['BTC/USDT', 'ETH/USDT']

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('MultiExchangeManager')
        logger.setLevel(logging.INFO)

        log_dir = os.path.join(project_root, 'ai_optimization', 'models')
        os.makedirs(log_dir, exist_ok=True)

        handler = logging.FileHandler(
            os.path.join(log_dir, 'multi_exchange.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def add_exchange(self, exchange_info: ExchangeInfo):
        """Add exchange to the system"""
        self.logger.info(f"Adding exchange: {exchange_info.name}")

        connector = ExchangeConnector(exchange_info)
        if connector.is_connected:
            self.exchanges[exchange_info.name] = connector
            self.logger.info(f"Successfully connected to {exchange_info.name}")
        else:
            self.logger.error(f"Failed to connect to {exchange_info.name}: {connector.last_error}")

    async def get_all_order_books(self, symbols: List[str]) -> List[OrderBookData]:
        """Get order books from all exchanges"""
        tasks = []

        for exchange_name, connector in self.exchanges.items():
            for symbol in symbols:
                task = connector.get_order_book(symbol)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        order_books = []
        for result in results:
            if isinstance(result, OrderBookData):
                order_books.append(result)

        return order_books

    async def monitor_arbitrage(self, callback=None):
        """Monitor arbitrage opportunities"""
        self.is_monitoring = True
        self.logger.info("Starting arbitrage monitoring...")

        while self.is_monitoring:
            try:
                # Get order books
                order_books = await self.get_all_order_books(self.monitoring_symbols)

                # Detect arbitrage
                opportunities = self.arbitrage_detector.detect_arbitrage(order_books)

                # Aggregate liquidity
                aggregated = self.liquidity_aggregator.aggregate_order_books(order_books)

                # Call callback with results
                if callback and (opportunities or aggregated):
                    callback({
                        'timestamp': datetime.now(),
                        'arbitrage_opportunities': opportunities,
                        'aggregated_liquidity': aggregated,
                        'active_exchanges': len(self.exchanges)
                    })

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)

    def stop_monitoring(self):
        """Stop arbitrage monitoring"""
        self.is_monitoring = False
        self.logger.info("Stopped arbitrage monitoring")

    def get_exchange_status(self) -> Dict:
        """Get status of all exchanges"""
        status = {}

        for name, connector in self.exchanges.items():
            status[name] = {
                'connected': connector.is_connected,
                'last_error': connector.last_error,
                'name': connector.info.name,
                'sandbox': connector.info.sandbox
            }

        return status

    def close_all_connections(self):
        """Close all exchange connections"""
        for connector in self.exchanges.values():
            connector.close()

def main():
    """Main multi-exchange demo"""
    print("=" * 60)
    print("MULTI-EXCHANGE ARBITRAGE SYSTEM")
    print("Phase 9: Advanced Multi-Exchange Trading")
    print("=" * 60)

    # Initialize manager
    manager = MultiExchangeManager()

    # Demo exchange configurations (sandbox mode)
    exchanges = [
        ExchangeInfo(
            name='binance',
            enabled=True,
            api_key='demo_key',
            api_secret='demo_secret',
            sandbox=True,
            fees={'maker': 0.001, 'taker': 0.001},
            min_trade_amount=0.001,
            max_leverage=125,
            supported_pairs=['BTC/USDT', 'ETH/USDT']
        ),
        ExchangeInfo(
            name='okx',
            enabled=True,
            api_key='demo_key',
            api_secret='demo_secret',
            sandbox=True,
            fees={'maker': 0.0008, 'taker': 0.001},
            min_trade_amount=0.001,
            max_leverage=100,
            supported_pairs=['BTC/USDT', 'ETH/USDT']
        )
    ]

    # Add exchanges
    for exchange_info in exchanges:
        manager.add_exchange(exchange_info)

    # Check status
    print("\nExchange Status:")
    status = manager.get_exchange_status()
    for name, info in status.items():
        print(f"  {name}: {'Connected' if info['connected'] else 'Disconnected'}")

    # Demo arbitrage detection with synthetic data
    print("\nGenerating synthetic order book data for demo...")

    # Create synthetic order books
    order_books = []

    # Binance order book
    order_books.append(OrderBookData(
        exchange='binance',
        symbol='BTC/USDT',
        timestamp=datetime.now(),
        bids=[(50000, 1.0), (49990, 2.0), (49980, 1.5)],
        asks=[(50010, 1.5), (50020, 2.0), (50030, 1.0)],
        bid_price=50000,
        ask_price=50010,
        spread=10,
        spread_pct=0.02
    ))

    # OKX order book (with arbitrage opportunity)
    order_books.append(OrderBookData(
        exchange='okx',
        symbol='BTC/USDT',
        timestamp=datetime.now(),
        bids=[(50050, 1.0), (50040, 2.0), (50030, 1.5)],
        asks=[(50060, 1.5), (50070, 2.0), (50080, 1.0)],
        bid_price=50050,
        ask_price=50060,
        spread=10,
        spread_pct=0.02
    ))

    # Detect arbitrage
    opportunities = manager.arbitrage_detector.detect_arbitrage(order_books)

    print(f"\nArbitrage Opportunities Found: {len(opportunities)}")
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. {opp.symbol}")
        print(f"   Buy: {opp.buy_exchange} @ ${opp.buy_price:.2f}")
        print(f"   Sell: {opp.sell_exchange} @ ${opp.sell_price:.2f}")
        print(f"   Profit: {opp.profit_pct:.2f}%")
        print(f"   Confidence: {opp.confidence:.2f}")

    # Aggregate liquidity
    aggregated = manager.liquidity_aggregator.aggregate_order_books(order_books)

    print(f"\nAggregated Liquidity:")
    for symbol, data in aggregated.items():
        print(f"{symbol}:")
        print(f"  Best Bid: ${data['best_bid']:.2f}")
        print(f"  Best Ask: ${data['best_ask']:.2f}")
        print(f"  Spread: {data['spread_pct']:.3f}%")
        print(f"  Total Volume: {data['total_bid_volume']:.2f} / {data['total_ask_volume']:.2f}")
        print(f"  Exchanges: {data['exchanges']}")

    # Test execution planning
    execution = manager.liquidity_aggregator.find_best_execution(
        'BTC/USDT', 'buy', 2.0, order_books
    )

    print(f"\nBest Execution Plan (Buy 2.0 BTC):")
    print(f"Executed: {execution['executed_amount']:.2f} BTC ({execution['execution_rate']:.1f}%)")
    print(f"Average Price: ${execution['avg_price']:.2f}")
    print(f"Exchanges Used: {execution['exchanges_used']}")

    for i, plan in enumerate(execution['execution_plan'], 1):
        print(f"  {i}. {plan['exchange']}: {plan['amount']:.2f} BTC @ ${plan['price']:.2f}")

    # Cleanup
    manager.close_all_connections()

if __name__ == '__main__':
    main()