#!/usr/bin/env python3
"""
Automated Strategy Selector AI System
Phase 9: Dynamic strategy selection based on market conditions

Features:
- Market regime detection
- Strategy performance tracking
- Dynamic strategy switching
- Multi-factor strategy scoring
- Adaptive strategy allocation
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum

# ML and Statistics
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import scipy.stats as stats

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class MarketRegime(Enum):
    """Market regime classifications"""
    BULLISH_TRENDING = "bullish_trending"
    BEARISH_TRENDING = "bearish_trending"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    RANGING = "ranging"
    BREAKOUT = "breakout"

@dataclass
class StrategyInfo:
    """Strategy information structure"""
    name: str
    type: str  # trend, mean_reversion, momentum, etc.
    optimal_conditions: List[MarketRegime]
    risk_level: str  # low, medium, high
    min_volatility: float
    max_volatility: float
    min_volume: float
    performance_metrics: Dict[str, float]
    last_updated: datetime

@dataclass
class StrategyPerformance:
    """Strategy performance tracking"""
    strategy_name: str
    market_regime: MarketRegime
    total_trades: int
    win_rate: float
    avg_profit: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    period_start: datetime
    period_end: datetime

class MarketRegimeDetector:
    """Detect current market regime"""

    def __init__(self):
        self.classifier = None
        self.scaler = StandardScaler()
        self.is_trained = False

    def extract_market_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features for market regime classification"""
        features = []

        # Price momentum features
        returns = df['Close'].pct_change().fillna(0)
        for period in [5, 10, 20]:
            momentum = df['Close'].pct_change(period).fillna(0)
            features.append(momentum.iloc[-1])

        # Volatility features
        for period in [10, 20, 30]:
            volatility = returns.rolling(period).std().fillna(0)
            features.append(volatility.iloc[-1])

        # Trend strength
        sma_20 = df['Close'].rolling(20).mean()
        sma_50 = df['Close'].rolling(50).mean()
        trend_strength = ((sma_20 - sma_50) / sma_50).fillna(0)
        features.append(trend_strength.iloc[-1])

        # Volume analysis
        volume_sma = df['Volume'].rolling(20).mean()
        volume_ratio = (df['Volume'] / volume_sma).fillna(1)
        features.append(volume_ratio.iloc[-1])

        # Price position relative to moving averages
        price_vs_sma20 = ((df['Close'] - sma_20) / sma_20).fillna(0)
        price_vs_sma50 = ((df['Close'] - sma_50) / sma_50).fillna(0)
        features.extend([price_vs_sma20.iloc[-1], price_vs_sma50.iloc[-1]])

        # Support/Resistance analysis
        recent_high = df['High'].rolling(20).max()
        recent_low = df['Low'].rolling(20).min()
        price_range = (recent_high - recent_low) / df['Close']
        features.append(price_range.fillna(0).iloc[-1])

        # ADX-like trend strength
        high_low_range = (df['High'] - df['Low']).rolling(14).mean()
        trend_strength_adx = high_low_range / df['Close']
        features.append(trend_strength_adx.fillna(0).iloc[-1])

        return np.array(features)

    def create_regime_labels(self, df: pd.DataFrame) -> List[MarketRegime]:
        """Create regime labels for training data"""
        labels = []

        returns = df['Close'].pct_change().fillna(0)
        volatility = returns.rolling(20).std()

        for i in range(len(df)):
            if i < 50:  # Need sufficient history
                labels.append(MarketRegime.RANGING)
                continue

            # Get recent data
            recent_returns = returns.iloc[i-20:i]
            recent_vol = volatility.iloc[i]
            recent_momentum = df['Close'].iloc[i] / df['Close'].iloc[i-20] - 1

            # Classify regime
            if recent_vol > volatility.quantile(0.8):
                if abs(recent_momentum) > 0.05:
                    labels.append(MarketRegime.BREAKOUT)
                else:
                    labels.append(MarketRegime.HIGH_VOLATILITY)
            elif recent_vol < volatility.quantile(0.2):
                labels.append(MarketRegime.LOW_VOLATILITY)
            elif recent_momentum > 0.03:
                labels.append(MarketRegime.BULLISH_TRENDING)
            elif recent_momentum < -0.03:
                labels.append(MarketRegime.BEARISH_TRENDING)
            else:
                labels.append(MarketRegime.RANGING)

        return labels

    def train_classifier(self, df: pd.DataFrame) -> float:
        """Train market regime classifier"""
        if len(df) < 100:
            return 0.0

        # Create features and labels
        features_list = []
        labels = self.create_regime_labels(df)

        for i in range(50, len(df)):  # Start from index 50 to have sufficient history
            feature_subset = df.iloc[i-49:i+1]  # 50 periods of data
            features = self.extract_market_features(feature_subset)
            features_list.append(features)

        if len(features_list) < 50:
            return 0.0

        X = np.array(features_list)
        y = [label.value for label in labels[50:]]  # Align with features

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train classifier
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        self.classifier.fit(X_train, y_train)

        # Evaluate
        y_pred = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        self.is_trained = True
        return accuracy

    def predict_regime(self, df: pd.DataFrame) -> Tuple[MarketRegime, float]:
        """Predict current market regime"""
        if not self.is_trained or len(df) < 50:
            return MarketRegime.RANGING, 0.0

        features = self.extract_market_features(df.tail(50))
        features_scaled = self.scaler.transform(features.reshape(1, -1))

        prediction = self.classifier.predict(features_scaled)[0]
        probabilities = self.classifier.predict_proba(features_scaled)[0]
        confidence = max(probabilities)

        return MarketRegime(prediction), confidence

class StrategyPerformanceTracker:
    """Track strategy performance across different market regimes"""

    def __init__(self):
        self.performance_history = []
        self.strategy_scores = {}

    def add_performance_record(self, performance: StrategyPerformance):
        """Add performance record"""
        self.performance_history.append(performance)

    def calculate_strategy_scores(self) -> Dict[str, Dict[str, float]]:
        """Calculate strategy scores for each market regime"""
        scores = {}

        # Group by strategy and regime
        strategy_regime_data = {}
        for perf in self.performance_history:
            key = (perf.strategy_name, perf.market_regime)
            if key not in strategy_regime_data:
                strategy_regime_data[key] = []
            strategy_regime_data[key].append(perf)

        # Calculate scores
        for (strategy, regime), performances in strategy_regime_data.items():
            if strategy not in scores:
                scores[strategy] = {}

            # Aggregate performance metrics
            total_trades = sum(p.total_trades for p in performances)
            avg_win_rate = np.mean([p.win_rate for p in performances])
            avg_profit = np.mean([p.avg_profit for p in performances])
            max_drawdown = max([abs(p.max_drawdown) for p in performances])
            avg_sharpe = np.mean([p.sharpe_ratio for p in performances if p.sharpe_ratio])

            # Calculate composite score
            win_rate_score = avg_win_rate / 100  # Normalize to 0-1
            profit_score = max(0, min(avg_profit / 0.02, 1))  # Normalize to 2% target
            drawdown_penalty = max(0, 1 - (max_drawdown / 0.15))  # Penalty for >15% DD
            sharpe_score = max(0, min(avg_sharpe / 2.0, 1))  # Normalize to 2.0 target

            composite_score = (
                win_rate_score * 0.3 +
                profit_score * 0.3 +
                drawdown_penalty * 0.25 +
                sharpe_score * 0.15
            )

            scores[strategy][regime.value] = {
                'composite_score': composite_score,
                'win_rate': avg_win_rate,
                'avg_profit': avg_profit,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': avg_sharpe,
                'total_trades': total_trades
            }

        self.strategy_scores = scores
        return scores

    def get_best_strategy_for_regime(self, regime: MarketRegime,
                                   available_strategies: List[str]) -> Tuple[str, float]:
        """Get best strategy for specific market regime"""
        if not self.strategy_scores:
            self.calculate_strategy_scores()

        best_strategy = None
        best_score = 0.0

        for strategy in available_strategies:
            if strategy in self.strategy_scores:
                regime_scores = self.strategy_scores[strategy]
                if regime.value in regime_scores:
                    score = regime_scores[regime.value]['composite_score']
                    if score > best_score:
                        best_score = score
                        best_strategy = strategy

        return best_strategy or available_strategies[0], best_score

class StrategySelector:
    """Main strategy selector system"""

    def __init__(self):
        self.regime_detector = MarketRegimeDetector()
        self.performance_tracker = StrategyPerformanceTracker()
        self.available_strategies = {}
        self.current_strategy = None
        self.logger = self._setup_logging()

        # Strategy switching parameters
        self.min_confidence_threshold = 0.7
        self.min_performance_difference = 0.1
        self.switch_cooldown_hours = 4

        self.last_switch_time = datetime.min

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('StrategySelector')
        logger.setLevel(logging.INFO)

        log_dir = os.path.join(project_root, 'ai_optimization', 'models')
        os.makedirs(log_dir, exist_ok=True)

        handler = logging.FileHandler(
            os.path.join(log_dir, 'strategy_selector.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def add_strategy(self, strategy_info: StrategyInfo):
        """Add strategy to available strategies"""
        self.available_strategies[strategy_info.name] = strategy_info
        self.logger.info(f"Added strategy: {strategy_info.name}")

    def train_regime_detector(self, market_data: pd.DataFrame) -> float:
        """Train market regime detection model"""
        self.logger.info("Training market regime detector...")
        accuracy = self.regime_detector.train_classifier(market_data)
        self.logger.info(f"Regime detector accuracy: {accuracy:.3f}")
        return accuracy

    def load_historical_performance(self, performance_data: List[Dict]):
        """Load historical strategy performance data"""
        self.logger.info("Loading historical performance data...")

        for data in performance_data:
            performance = StrategyPerformance(
                strategy_name=data['strategy_name'],
                market_regime=MarketRegime(data['market_regime']),
                total_trades=data['total_trades'],
                win_rate=data['win_rate'],
                avg_profit=data['avg_profit'],
                max_drawdown=data['max_drawdown'],
                sharpe_ratio=data.get('sharpe_ratio', 0.0),
                profit_factor=data.get('profit_factor', 1.0),
                period_start=datetime.fromisoformat(data['period_start']),
                period_end=datetime.fromisoformat(data['period_end'])
            )
            self.performance_tracker.add_performance_record(performance)

        # Calculate strategy scores
        self.performance_tracker.calculate_strategy_scores()
        self.logger.info(f"Loaded {len(performance_data)} performance records")

    def select_optimal_strategy(self, market_data: pd.DataFrame) -> Dict:
        """Select optimal strategy based on current market conditions"""
        # Detect current market regime
        if len(market_data) < 50:
            return {
                'error': 'Insufficient market data for regime detection',
                'recommended_strategy': list(self.available_strategies.keys())[0] if self.available_strategies else None
            }

        current_regime, confidence = self.regime_detector.predict_regime(market_data)

        self.logger.info(f"Detected market regime: {current_regime.value} (confidence: {confidence:.3f})")

        # Get available strategy names
        available_strategy_names = list(self.available_strategies.keys())

        if not available_strategy_names:
            return {'error': 'No strategies available'}

        # Get best strategy for current regime
        best_strategy, best_score = self.performance_tracker.get_best_strategy_for_regime(
            current_regime, available_strategy_names
        )

        # Check if strategy switch is recommended
        should_switch = self._should_switch_strategy(
            best_strategy, best_score, confidence
        )

        # Calculate market condition scores
        market_conditions = self._analyze_market_conditions(market_data)

        # Strategy recommendations with scores
        strategy_rankings = self._rank_all_strategies(current_regime, market_conditions)

        result = {
            'timestamp': datetime.now().isoformat(),
            'current_regime': current_regime.value,
            'regime_confidence': confidence,
            'recommended_strategy': best_strategy,
            'strategy_score': best_score,
            'current_strategy': self.current_strategy,
            'should_switch': should_switch,
            'switch_reason': self._get_switch_reason(best_strategy, best_score, confidence),
            'market_conditions': market_conditions,
            'strategy_rankings': strategy_rankings,
            'cooldown_remaining': self._get_cooldown_remaining()
        }

        # Update current strategy if switching
        if should_switch:
            self.current_strategy = best_strategy
            self.last_switch_time = datetime.now()
            self.logger.info(f"Strategy switch recommended: {best_strategy}")

        return result

    def _should_switch_strategy(self, recommended_strategy: str,
                              strategy_score: float, confidence: float) -> bool:
        """Determine if strategy switch is recommended"""
        # Check cooldown period
        if self._get_cooldown_remaining() > 0:
            return False

        # Check confidence threshold
        if confidence < self.min_confidence_threshold:
            return False

        # If no current strategy, switch to recommended
        if not self.current_strategy:
            return True

        # If recommended strategy is same as current, no switch needed
        if recommended_strategy == self.current_strategy:
            return False

        # Check performance difference threshold
        current_strategy_score = 0.0
        if self.current_strategy in self.performance_tracker.strategy_scores:
            current_regime = self.regime_detector.predict_regime(pd.DataFrame())[0]  # This is a simplified check
            regime_scores = self.performance_tracker.strategy_scores[self.current_strategy]
            if current_regime.value in regime_scores:
                current_strategy_score = regime_scores[current_regime.value]['composite_score']

        performance_improvement = strategy_score - current_strategy_score

        return performance_improvement > self.min_performance_difference

    def _get_switch_reason(self, recommended_strategy: str,
                          strategy_score: float, confidence: float) -> str:
        """Get reason for strategy switch recommendation"""
        if self._get_cooldown_remaining() > 0:
            return "Switch blocked by cooldown period"

        if confidence < self.min_confidence_threshold:
            return f"Low regime confidence ({confidence:.2f} < {self.min_confidence_threshold})"

        if not self.current_strategy:
            return "Initial strategy selection"

        if recommended_strategy == self.current_strategy:
            return "Current strategy is optimal"

        return f"Better strategy found (score improvement: {strategy_score:.3f})"

    def _get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in hours"""
        if self.last_switch_time == datetime.min:
            return 0.0

        elapsed = datetime.now() - self.last_switch_time
        elapsed_hours = elapsed.total_seconds() / 3600

        return max(0, self.switch_cooldown_hours - elapsed_hours)

    def _analyze_market_conditions(self, market_data: pd.DataFrame) -> Dict:
        """Analyze current market conditions"""
        if len(market_data) < 20:
            return {}

        recent_data = market_data.tail(20)

        # Volatility analysis
        returns = recent_data['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(24)  # Annualized

        # Volume analysis
        avg_volume = recent_data['Volume'].mean()
        volume_trend = recent_data['Volume'].iloc[-5:].mean() / recent_data['Volume'].iloc[-10:-5].mean()

        # Price momentum
        price_momentum = (recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[0] - 1) * 100

        # Trend strength
        sma_5 = recent_data['Close'].rolling(5).mean().iloc[-1]
        sma_20 = recent_data['Close'].rolling(20).mean().iloc[-1]
        trend_strength = (sma_5 - sma_20) / sma_20 * 100

        return {
            'volatility': volatility,
            'volatility_level': 'high' if volatility > 0.4 else 'normal' if volatility > 0.2 else 'low',
            'volume_trend': volume_trend,
            'volume_level': 'high' if volume_trend > 1.2 else 'normal' if volume_trend > 0.8 else 'low',
            'price_momentum': price_momentum,
            'momentum_direction': 'bullish' if price_momentum > 2 else 'bearish' if price_momentum < -2 else 'neutral',
            'trend_strength': trend_strength,
            'trend_direction': 'up' if trend_strength > 1 else 'down' if trend_strength < -1 else 'sideways'
        }

    def _rank_all_strategies(self, current_regime: MarketRegime,
                           market_conditions: Dict) -> List[Dict]:
        """Rank all available strategies"""
        rankings = []

        for strategy_name, strategy_info in self.available_strategies.items():
            # Base score from performance tracking
            base_score = 0.5  # Default score
            if strategy_name in self.performance_tracker.strategy_scores:
                regime_scores = self.performance_tracker.strategy_scores[strategy_name]
                if current_regime.value in regime_scores:
                    base_score = regime_scores[current_regime.value]['composite_score']

            # Adjust score based on strategy preferences and market conditions
            adjusted_score = base_score

            # Volatility adjustment
            if market_conditions.get('volatility_level') == 'high':
                if strategy_info.type in ['momentum', 'breakout']:
                    adjusted_score *= 1.1
                elif strategy_info.type == 'mean_reversion':
                    adjusted_score *= 0.9

            # Volume adjustment
            if market_conditions.get('volume_level') == 'high':
                if strategy_info.type in ['momentum', 'trend']:
                    adjusted_score *= 1.05

            # Regime preference adjustment
            if current_regime in strategy_info.optimal_conditions:
                adjusted_score *= 1.2

            rankings.append({
                'strategy': strategy_name,
                'base_score': base_score,
                'adjusted_score': adjusted_score,
                'strategy_type': strategy_info.type,
                'risk_level': strategy_info.risk_level
            })

        # Sort by adjusted score
        rankings.sort(key=lambda x: x['adjusted_score'], reverse=True)

        return rankings

def main():
    """Main strategy selector demo"""
    print("=" * 60)
    print("AUTOMATED STRATEGY SELECTOR AI")
    print("Phase 9: Dynamic Strategy Selection System")
    print("=" * 60)

    # Initialize selector
    selector = StrategySelector()

    # Add sample strategies
    strategies = [
        StrategyInfo(
            name="RossCameronRSI",
            type="mean_reversion",
            optimal_conditions=[MarketRegime.RANGING, MarketRegime.LOW_VOLATILITY],
            risk_level="medium",
            min_volatility=0.1,
            max_volatility=0.4,
            min_volume=1000000,
            performance_metrics={'sharpe': 1.2, 'max_dd': -0.08},
            last_updated=datetime.now()
        ),
        StrategyInfo(
            name="MomentumBreakout",
            type="momentum",
            optimal_conditions=[MarketRegime.BREAKOUT, MarketRegime.HIGH_VOLATILITY],
            risk_level="high",
            min_volatility=0.3,
            max_volatility=1.0,
            min_volume=2000000,
            performance_metrics={'sharpe': 1.5, 'max_dd': -0.12},
            last_updated=datetime.now()
        ),
        StrategyInfo(
            name="TrendFollowing",
            type="trend",
            optimal_conditions=[MarketRegime.BULLISH_TRENDING, MarketRegime.BEARISH_TRENDING],
            risk_level="medium",
            min_volatility=0.2,
            max_volatility=0.8,
            min_volume=1500000,
            performance_metrics={'sharpe': 1.1, 'max_dd': -0.10},
            last_updated=datetime.now()
        )
    ]

    for strategy in strategies:
        selector.add_strategy(strategy)

    # Generate synthetic market data
    dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='1H')
    np.random.seed(42)

    price = 50000
    prices = [price]
    volumes = []

    for i in range(len(dates) - 1):
        # Create different market regimes
        if i % 1000 < 200:  # Trending periods
            change = np.random.normal(0.001, 0.015)
        elif i % 1000 < 400:  # High volatility periods
            change = np.random.normal(0, 0.04)
        else:  # Normal/ranging periods
            change = np.random.normal(0, 0.02)

        price = price * (1 + change)
        prices.append(price)
        volumes.append(np.random.randint(1000000, 5000000))

    market_data = pd.DataFrame({
        'Close': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Open': prices,
        'Volume': volumes + [volumes[-1]]  # Match length
    }, index=dates)

    # Train regime detector
    print("Training regime detector...")
    accuracy = selector.train_regime_detector(market_data)
    print(f"Regime detector accuracy: {accuracy:.3f}")

    # Load synthetic performance data
    performance_data = [
        {
            'strategy_name': 'RossCameronRSI',
            'market_regime': 'ranging',
            'total_trades': 50,
            'win_rate': 65.0,
            'avg_profit': 0.015,
            'max_drawdown': -0.08,
            'sharpe_ratio': 1.2,
            'profit_factor': 1.4,
            'period_start': '2024-01-01T00:00:00',
            'period_end': '2024-03-01T00:00:00'
        },
        {
            'strategy_name': 'MomentumBreakout',
            'market_regime': 'breakout',
            'total_trades': 30,
            'win_rate': 70.0,
            'avg_profit': 0.025,
            'max_drawdown': -0.12,
            'sharpe_ratio': 1.5,
            'profit_factor': 1.8,
            'period_start': '2024-03-01T00:00:00',
            'period_end': '2024-06-01T00:00:00'
        },
        {
            'strategy_name': 'TrendFollowing',
            'market_regime': 'bullish_trending',
            'total_trades': 40,
            'win_rate': 60.0,
            'avg_profit': 0.018,
            'max_drawdown': -0.10,
            'sharpe_ratio': 1.1,
            'profit_factor': 1.3,
            'period_start': '2024-06-01T00:00:00',
            'period_end': '2024-09-01T00:00:00'
        }
    ]

    selector.load_historical_performance(performance_data)

    # Test strategy selection
    print("\nTesting strategy selection...")
    recent_data = market_data.tail(100)  # Use recent data for selection

    selection_result = selector.select_optimal_strategy(recent_data)

    print("\nStrategy Selection Results:")
    print(f"Current Regime: {selection_result['current_regime']}")
    print(f"Regime Confidence: {selection_result['regime_confidence']:.3f}")
    print(f"Recommended Strategy: {selection_result['recommended_strategy']}")
    print(f"Strategy Score: {selection_result['strategy_score']:.3f}")
    print(f"Should Switch: {selection_result['should_switch']}")
    print(f"Switch Reason: {selection_result['switch_reason']}")

    print(f"\nMarket Conditions:")
    conditions = selection_result['market_conditions']
    for key, value in conditions.items():
        print(f"  {key}: {value}")

    print(f"\nStrategy Rankings:")
    for i, ranking in enumerate(selection_result['strategy_rankings'], 1):
        print(f"  {i}. {ranking['strategy']} ({ranking['strategy_type']})")
        print(f"     Score: {ranking['adjusted_score']:.3f}, Risk: {ranking['risk_level']}")

if __name__ == '__main__':
    main()