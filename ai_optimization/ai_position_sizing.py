#!/usr/bin/env python3
"""
AI-Driven Position Sizing System
Phase 9: Advanced position sizing using machine learning

Features:
- Kelly Criterion optimization
- Volatility-adjusted sizing
- Correlation-based sizing
- Risk-parity allocation
- Dynamic sizing based on confidence
- Portfolio optimization
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
from scipy.optimize import minimize, differential_evolution
import warnings
warnings.filterwarnings('ignore')

# ML and Statistics
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score

# Portfolio optimization
import cvxpy as cp

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

@dataclass
class PositionSizeRecommendation:
    """Position size recommendation structure"""
    symbol: str
    recommended_size: float
    confidence: float
    risk_score: float
    kelly_fraction: float
    volatility_adjustment: float
    correlation_adjustment: float
    max_size_limit: float
    reasoning: List[str]

@dataclass
class PortfolioMetrics:
    """Portfolio risk metrics"""
    total_exposure: float
    risk_budget_used: float
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    max_drawdown_estimate: float
    diversification_ratio: float

class KellyCriterionCalculator:
    """Calculate optimal position size using Kelly Criterion"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False

    def calculate_kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly fraction for given parameters"""
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0

        # Kelly formula: f = (bp - q) / b
        # where: b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
        b = avg_win / abs(avg_loss)
        p = win_rate
        q = 1 - win_rate

        kelly_fraction = (b * p - q) / b

        # Apply conservative scaling (typically 25-50% of full Kelly)
        conservative_kelly = kelly_fraction * 0.25

        return max(0.0, min(conservative_kelly, 0.1))  # Cap at 10% of portfolio

    def train_kelly_predictor(self, historical_data: pd.DataFrame) -> float:
        """Train ML model to predict optimal Kelly fraction"""
        if len(historical_data) < 100:
            return 0.0

        # Prepare features
        features = self._extract_kelly_features(historical_data)

        # Calculate rolling Kelly fractions as targets
        targets = self._calculate_rolling_kelly(historical_data)

        if len(features) != len(targets) or len(features) < 50:
            return 0.0

        # Scale features
        X_scaled = self.scaler.fit_transform(features)

        # Time series split
        tscv = TimeSeriesSplit(n_splits=3)
        scores = []

        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )

        for train_idx, val_idx in tscv.split(X_scaled):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = targets[train_idx], targets[val_idx]

            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_val)
            score = r2_score(y_val, y_pred)
            scores.append(score)

        # Final training on full dataset
        self.model.fit(X_scaled, targets)
        self.is_trained = True

        return np.mean(scores)

    def _extract_kelly_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features for Kelly prediction"""
        features = []

        # Price features
        returns = df['Close'].pct_change().fillna(0)
        features.append(returns.rolling(20).mean().fillna(0))  # Momentum
        features.append(returns.rolling(20).std().fillna(0))   # Volatility

        # Win rate features
        positive_returns = (returns > 0).rolling(20).sum() / 20
        features.append(positive_returns.fillna(0.5))

        # Average win/loss
        wins = returns[returns > 0].rolling(20).mean().fillna(0)
        losses = returns[returns < 0].rolling(20).mean().fillna(0)
        features.extend([wins, abs(losses)])

        # Technical indicators
        if 'RSI' in df.columns:
            features.append(df['RSI'].fillna(50) / 100)
        else:
            features.append(pd.Series(0.5, index=df.index))

        # Volume features
        if 'Volume' in df.columns:
            volume_ma = df['Volume'].rolling(20).mean()
            volume_ratio = (df['Volume'] / volume_ma).fillna(1)
            features.append(volume_ratio)
        else:
            features.append(pd.Series(1.0, index=df.index))

        # Market regime features
        sma_20 = df['Close'].rolling(20).mean()
        trend_strength = ((df['Close'] - sma_20) / sma_20).fillna(0)
        features.append(trend_strength)

        return np.column_stack(features)

    def _calculate_rolling_kelly(self, df: pd.DataFrame, window: int = 50) -> np.ndarray:
        """Calculate rolling Kelly fractions"""
        returns = df['Close'].pct_change().fillna(0)
        kelly_fractions = []

        for i in range(len(returns)):
            if i < window:
                kelly_fractions.append(0.02)  # Default small size
                continue

            window_returns = returns.iloc[i-window:i]

            # Calculate win rate and avg win/loss
            wins = window_returns[window_returns > 0]
            losses = window_returns[window_returns < 0]

            if len(wins) == 0 or len(losses) == 0:
                kelly_fractions.append(0.02)
                continue

            win_rate = len(wins) / len(window_returns)
            avg_win = wins.mean()
            avg_loss = losses.mean()

            kelly = self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
            kelly_fractions.append(kelly)

        return np.array(kelly_fractions)

    def predict_kelly_fraction(self, features: np.ndarray) -> float:
        """Predict Kelly fraction using trained model"""
        if not self.is_trained:
            return 0.02  # Default conservative size

        features_scaled = self.scaler.transform(features.reshape(1, -1))
        predicted_kelly = self.model.predict(features_scaled)[0]

        return max(0.001, min(predicted_kelly, 0.1))  # Bounds checking

class VolatilityAdjuster:
    """Adjust position size based on volatility"""

    def __init__(self, target_volatility: float = 0.15):
        self.target_volatility = target_volatility

    def calculate_volatility_adjustment(self, current_volatility: float,
                                      lookback_volatility: float) -> float:
        """Calculate volatility adjustment factor"""
        if current_volatility <= 0 or lookback_volatility <= 0:
            return 1.0

        # Adjustment based on current vs historical volatility
        vol_ratio = current_volatility / lookback_volatility

        # Scale position size inversely with volatility
        adjustment = 1.0 / vol_ratio

        # Apply bounds
        return max(0.5, min(adjustment, 2.0))

    def calculate_volatility_target_sizing(self, current_volatility: float) -> float:
        """Calculate position size to achieve target volatility"""
        if current_volatility <= 0:
            return 0.02

        # Size to achieve target portfolio volatility
        target_size = self.target_volatility / current_volatility

        return max(0.001, min(target_size, 0.2))  # Bounds: 0.1% to 20%

class CorrelationAnalyzer:
    """Analyze correlations for position sizing"""

    def __init__(self):
        self.correlation_matrix = None

    def calculate_correlation_adjustment(self, symbol: str,
                                       existing_positions: Dict[str, float],
                                       correlation_matrix: pd.DataFrame) -> float:
        """Calculate position size adjustment based on correlations"""
        if symbol not in correlation_matrix.index or not existing_positions:
            return 1.0

        # Calculate weighted average correlation with existing positions
        total_weight = 0
        weighted_correlation = 0

        for existing_symbol, position_size in existing_positions.items():
            if existing_symbol in correlation_matrix.columns:
                correlation = correlation_matrix.loc[symbol, existing_symbol]
                weighted_correlation += correlation * position_size
                total_weight += position_size

        if total_weight == 0:
            return 1.0

        avg_correlation = weighted_correlation / total_weight

        # Reduce size for highly correlated positions
        if avg_correlation > 0.7:
            adjustment = 0.5
        elif avg_correlation > 0.5:
            adjustment = 0.7
        elif avg_correlation > 0.3:
            adjustment = 0.9
        else:
            adjustment = 1.0

        return adjustment

class RiskParityOptimizer:
    """Risk parity portfolio optimization"""

    def __init__(self):
        self.covariance_matrix = None

    def calculate_risk_parity_weights(self, symbols: List[str],
                                    returns_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate risk parity weights"""
        if len(symbols) < 2 or len(returns_data) < 30:
            # Equal weights if insufficient data
            equal_weight = 1.0 / len(symbols)
            return {symbol: equal_weight for symbol in symbols}

        # Calculate covariance matrix
        symbol_returns = returns_data[symbols].dropna()
        cov_matrix = symbol_returns.cov().values

        # Risk parity optimization
        n_assets = len(symbols)

        def risk_parity_objective(weights):
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            contrib = weights * marginal_contrib
            target_contrib = portfolio_vol / n_assets
            return np.sum((contrib - target_contrib) ** 2)

        # Constraints
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0.01, 0.5) for _ in range(n_assets))  # Min 1%, max 50%

        # Initial guess
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        try:
            result = minimize(
                risk_parity_objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )

            if result.success:
                weights = result.x
                return dict(zip(symbols, weights))
        except:
            pass

        # Fallback to equal weights
        equal_weight = 1.0 / len(symbols)
        return {symbol: equal_weight for symbol in symbols}

class AIPositionSizer:
    """Main AI-driven position sizing system"""

    def __init__(self, max_portfolio_risk: float = 0.02):
        self.kelly_calculator = KellyCriterionCalculator()
        self.volatility_adjuster = VolatilityAdjuster()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.risk_parity_optimizer = RiskParityOptimizer()

        self.max_portfolio_risk = max_portfolio_risk
        self.max_single_position = 0.05  # 5% max per position
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('AIPositionSizer')
        logger.setLevel(logging.INFO)

        log_dir = os.path.join(project_root, 'ai_optimization', 'models')
        os.makedirs(log_dir, exist_ok=True)

        handler = logging.FileHandler(
            os.path.join(log_dir, 'position_sizing.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def train_models(self, market_data: pd.DataFrame) -> Dict[str, float]:
        """Train position sizing models"""
        self.logger.info("Training position sizing models...")

        results = {}

        # Train Kelly predictor
        kelly_score = self.kelly_calculator.train_kelly_predictor(market_data)
        results['kelly_r2_score'] = kelly_score

        self.logger.info(f"Kelly predictor R2 score: {kelly_score:.3f}")

        return results

    def calculate_position_size(self,
                              symbol: str,
                              market_data: pd.DataFrame,
                              existing_positions: Dict[str, float] = None,
                              strategy_confidence: float = 0.7,
                              correlation_matrix: pd.DataFrame = None) -> PositionSizeRecommendation:
        """Calculate optimal position size for a symbol"""

        existing_positions = existing_positions or {}
        reasoning = []

        # 1. Kelly Criterion sizing
        if self.kelly_calculator.is_trained and len(market_data) >= 50:
            features = self.kelly_calculator._extract_kelly_features(market_data)
            kelly_fraction = self.kelly_calculator.predict_kelly_fraction(features[-1])
        else:
            # Fallback Kelly calculation
            returns = market_data['Close'].pct_change().dropna()
            if len(returns) >= 20:
                wins = returns[returns > 0]
                losses = returns[returns < 0]

                if len(wins) > 0 and len(losses) > 0:
                    win_rate = len(wins) / len(returns)
                    avg_win = wins.mean()
                    avg_loss = losses.mean()
                    kelly_fraction = self.kelly_calculator.calculate_kelly_fraction(
                        win_rate, avg_win, avg_loss
                    )
                else:
                    kelly_fraction = 0.02
            else:
                kelly_fraction = 0.02

        reasoning.append(f"Kelly fraction: {kelly_fraction:.3f}")

        # 2. Volatility adjustment
        returns = market_data['Close'].pct_change().dropna()
        if len(returns) >= 20:
            current_vol = returns.tail(20).std() * np.sqrt(252)  # Annualized
            historical_vol = returns.std() * np.sqrt(252)

            vol_adjustment = self.volatility_adjuster.calculate_volatility_adjustment(
                current_vol, historical_vol
            )

            vol_target_size = self.volatility_adjuster.calculate_volatility_target_sizing(
                current_vol
            )
        else:
            vol_adjustment = 1.0
            vol_target_size = 0.02
            current_vol = 0.2

        reasoning.append(f"Volatility adjustment: {vol_adjustment:.3f}")
        reasoning.append(f"Volatility target size: {vol_target_size:.3f}")

        # 3. Correlation adjustment
        correlation_adjustment = 1.0
        if correlation_matrix is not None:
            correlation_adjustment = self.correlation_analyzer.calculate_correlation_adjustment(
                symbol, existing_positions, correlation_matrix
            )
            reasoning.append(f"Correlation adjustment: {correlation_adjustment:.3f}")

        # 4. Confidence adjustment
        confidence_adjustment = strategy_confidence
        reasoning.append(f"Strategy confidence: {confidence_adjustment:.3f}")

        # 5. Calculate composite size
        base_size = kelly_fraction
        adjusted_size = (base_size *
                        vol_adjustment *
                        correlation_adjustment *
                        confidence_adjustment)

        # Take minimum of different sizing methods
        final_size = min(adjusted_size, vol_target_size)

        # Apply portfolio and position limits
        current_portfolio_exposure = sum(existing_positions.values())
        remaining_budget = self.max_portfolio_risk - current_portfolio_exposure

        final_size = min(final_size, remaining_budget, self.max_single_position)
        final_size = max(final_size, 0.0)

        reasoning.append(f"Portfolio exposure: {current_portfolio_exposure:.3f}")
        reasoning.append(f"Remaining budget: {remaining_budget:.3f}")

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            final_size, current_vol, correlation_adjustment, existing_positions
        )

        # Calculate confidence based on data quality and model agreement
        confidence = self._calculate_sizing_confidence(
            market_data, kelly_fraction, vol_adjustment, strategy_confidence
        )

        return PositionSizeRecommendation(
            symbol=symbol,
            recommended_size=final_size,
            confidence=confidence,
            risk_score=risk_score,
            kelly_fraction=kelly_fraction,
            volatility_adjustment=vol_adjustment,
            correlation_adjustment=correlation_adjustment,
            max_size_limit=min(remaining_budget, self.max_single_position),
            reasoning=reasoning
        )

    def optimize_portfolio_allocation(self,
                                    symbols: List[str],
                                    market_data_dict: Dict[str, pd.DataFrame],
                                    total_capital: float = 1.0) -> Dict[str, float]:
        """Optimize allocation across multiple symbols"""
        self.logger.info(f"Optimizing portfolio allocation for {len(symbols)} symbols")

        if len(symbols) <= 1:
            return {symbols[0]: total_capital} if symbols else {}

        # Calculate individual position sizes
        individual_sizes = {}
        for symbol in symbols:
            if symbol in market_data_dict:
                rec = self.calculate_position_size(symbol, market_data_dict[symbol])
                individual_sizes[symbol] = rec.recommended_size

        # Risk parity optimization if we have sufficient data
        try:
            # Combine returns data
            returns_dict = {}
            for symbol in symbols:
                if symbol in market_data_dict:
                    returns = market_data_dict[symbol]['Close'].pct_change().dropna()
                    returns_dict[symbol] = returns

            if len(returns_dict) >= 2:
                # Align all return series
                returns_df = pd.DataFrame(returns_dict).dropna()

                if len(returns_df) >= 30:
                    risk_parity_weights = self.risk_parity_optimizer.calculate_risk_parity_weights(
                        symbols, returns_df
                    )

                    # Blend individual sizes with risk parity
                    blended_allocation = {}
                    for symbol in symbols:
                        individual_weight = individual_sizes.get(symbol, 0)
                        risk_parity_weight = risk_parity_weights.get(symbol, 0)

                        # 70% individual sizing, 30% risk parity
                        blended_weight = 0.7 * individual_weight + 0.3 * risk_parity_weight
                        blended_allocation[symbol] = blended_weight

                    # Normalize to total capital
                    total_weight = sum(blended_allocation.values())
                    if total_weight > 0:
                        for symbol in blended_allocation:
                            blended_allocation[symbol] = (
                                blended_allocation[symbol] / total_weight * total_capital
                            )

                    return blended_allocation
        except Exception as e:
            self.logger.warning(f"Risk parity optimization failed: {e}")

        # Fallback: normalize individual sizes
        total_individual = sum(individual_sizes.values())
        if total_individual > 0:
            normalized_allocation = {}
            for symbol, size in individual_sizes.items():
                normalized_allocation[symbol] = (size / total_individual) * total_capital
            return normalized_allocation

        # Final fallback: equal weights
        equal_weight = total_capital / len(symbols)
        return {symbol: equal_weight for symbol in symbols}

    def _calculate_risk_score(self, position_size: float, volatility: float,
                            correlation_adj: float, existing_positions: Dict) -> float:
        """Calculate risk score for position (0-100)"""
        # Size component
        size_risk = (position_size / self.max_single_position) * 40

        # Volatility component
        vol_risk = min(volatility / 0.5, 1.0) * 30  # Normalize to 50% vol

        # Correlation component
        corr_risk = (1 - correlation_adj) * 20  # High correlation = high risk

        # Portfolio concentration component
        portfolio_exposure = sum(existing_positions.values())
        concentration_risk = (portfolio_exposure / self.max_portfolio_risk) * 10

        total_risk = size_risk + vol_risk + corr_risk + concentration_risk
        return min(total_risk, 100)

    def _calculate_sizing_confidence(self, market_data: pd.DataFrame,
                                   kelly_fraction: float, vol_adjustment: float,
                                   strategy_confidence: float) -> float:
        """Calculate confidence in sizing recommendation"""
        # Data quality
        data_quality = min(len(market_data) / 100, 1.0) * 0.3

        # Model agreement (how close different methods are)
        methods_agreement = 1.0 - abs(kelly_fraction - (0.02 * vol_adjustment)) / 0.05
        methods_agreement = max(0, min(methods_agreement, 1.0)) * 0.3

        # Strategy confidence
        strategy_component = strategy_confidence * 0.4

        total_confidence = data_quality + methods_agreement + strategy_component
        return max(0.1, min(total_confidence, 1.0))

    def calculate_portfolio_metrics(self, positions: Dict[str, float],
                                  market_data_dict: Dict[str, pd.DataFrame]) -> PortfolioMetrics:
        """Calculate portfolio-level metrics"""
        if not positions:
            return PortfolioMetrics(0, 0, 0, 0, 0, 0, 1.0)

        # Total exposure
        total_exposure = sum(positions.values())

        # Risk budget utilization
        risk_budget_used = total_exposure / self.max_portfolio_risk * 100

        # Calculate portfolio returns for metrics
        portfolio_returns = []
        for symbol, weight in positions.items():
            if symbol in market_data_dict:
                returns = market_data_dict[symbol]['Close'].pct_change().dropna()
                if len(returns) > 0:
                    weighted_returns = returns * weight
                    portfolio_returns.append(weighted_returns)

        if portfolio_returns:
            # Align and sum returns
            portfolio_df = pd.concat(portfolio_returns, axis=1).fillna(0)
            total_returns = portfolio_df.sum(axis=1)

            expected_return = total_returns.mean() * 252  # Annualized
            expected_volatility = total_returns.std() * np.sqrt(252)

            sharpe_ratio = expected_return / expected_volatility if expected_volatility > 0 else 0

            # Estimate max drawdown
            cumulative = (1 + total_returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown_estimate = drawdown.min()

            # Diversification ratio
            individual_vols = []
            for symbol, weight in positions.items():
                if symbol in market_data_dict:
                    returns = market_data_dict[symbol]['Close'].pct_change().dropna()
                    vol = returns.std() * np.sqrt(252)
                    individual_vols.append(weight * vol)

            weighted_avg_vol = sum(individual_vols)
            diversification_ratio = weighted_avg_vol / expected_volatility if expected_volatility > 0 else 1.0

        else:
            expected_return = 0
            expected_volatility = 0
            sharpe_ratio = 0
            max_drawdown_estimate = 0
            diversification_ratio = 1.0

        return PortfolioMetrics(
            total_exposure=total_exposure,
            risk_budget_used=risk_budget_used,
            expected_return=expected_return,
            expected_volatility=expected_volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_estimate=max_drawdown_estimate,
            diversification_ratio=diversification_ratio
        )

def main():
    """Main position sizing demo"""
    print("=" * 60)
    print("AI-DRIVEN POSITION SIZING SYSTEM")
    print("Phase 9: Advanced Position Sizing")
    print("=" * 60)

    # Initialize position sizer
    position_sizer = AIPositionSizer(max_portfolio_risk=0.05)

    # Generate synthetic market data
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    market_data_dict = {}

    np.random.seed(42)

    for symbol in symbols:
        dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='1H')

        # Different base prices and volatilities
        if 'BTC' in symbol:
            base_price, base_vol = 50000, 0.03
        elif 'ETH' in symbol:
            base_price, base_vol = 3000, 0.04
        else:  # SOL
            base_price, base_vol = 100, 0.06

        price = base_price
        prices = [price]

        for _ in range(len(dates) - 1):
            change = np.random.normal(0, base_vol)
            price = price * (1 + change)
            prices.append(price)

        market_data_dict[symbol] = pd.DataFrame({
            'Close': prices,
            'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'Open': prices,
            'Volume': np.random.randint(1000000, 5000000, len(prices))
        }, index=dates)

    # Train models
    print("Training position sizing models...")
    training_results = {}
    for symbol, data in market_data_dict.items():
        results = position_sizer.train_models(data)
        training_results[symbol] = results
        print(f"{symbol} Kelly R2: {results['kelly_r2_score']:.3f}")

    # Test individual position sizing
    print("\nCalculating individual position sizes...")
    existing_positions = {'BTC/USDT': 0.02}  # 2% already allocated

    for symbol in ['ETH/USDT', 'SOL/USDT']:
        recommendation = position_sizer.calculate_position_size(
            symbol=symbol,
            market_data=market_data_dict[symbol],
            existing_positions=existing_positions,
            strategy_confidence=0.8
        )

        print(f"\n{symbol} Position Sizing:")
        print(f"  Recommended Size: {recommendation.recommended_size:.3f} ({recommendation.recommended_size*100:.1f}%)")
        print(f"  Confidence: {recommendation.confidence:.3f}")
        print(f"  Risk Score: {recommendation.risk_score:.1f}/100")
        print(f"  Kelly Fraction: {recommendation.kelly_fraction:.3f}")
        print(f"  Volatility Adj: {recommendation.volatility_adjustment:.3f}")
        print(f"  Correlation Adj: {recommendation.correlation_adjustment:.3f}")
        print(f"  Reasoning: {'; '.join(recommendation.reasoning[:3])}")

    # Test portfolio optimization
    print("\nOptimizing portfolio allocation...")
    optimized_allocation = position_sizer.optimize_portfolio_allocation(
        symbols=symbols,
        market_data_dict=market_data_dict,
        total_capital=0.05  # 5% of total capital
    )

    print("Optimized Portfolio Allocation:")
    for symbol, allocation in optimized_allocation.items():
        print(f"  {symbol}: {allocation:.3f} ({allocation*100:.1f}%)")

    # Calculate portfolio metrics
    print("\nPortfolio Metrics:")
    metrics = position_sizer.calculate_portfolio_metrics(
        optimized_allocation, market_data_dict
    )

    print(f"  Total Exposure: {metrics.total_exposure:.3f} ({metrics.total_exposure*100:.1f}%)")
    print(f"  Risk Budget Used: {metrics.risk_budget_used:.1f}%")
    print(f"  Expected Return: {metrics.expected_return:.1f}% (annual)")
    print(f"  Expected Volatility: {metrics.expected_volatility:.1f}% (annual)")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"  Max Drawdown Est: {metrics.max_drawdown_estimate:.1%}")
    print(f"  Diversification Ratio: {metrics.diversification_ratio:.2f}")

if __name__ == '__main__':
    main()