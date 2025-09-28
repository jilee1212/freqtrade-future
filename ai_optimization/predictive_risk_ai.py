#!/usr/bin/env python3
"""
Predictive Risk Management AI System
Phase 9: Advanced AI-driven risk prediction and management

Features:
- Volatility prediction models
- Drawdown forecasting
- Correlation analysis
- Portfolio risk optimization
- Real-time risk scoring
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import warnings
warnings.filterwarnings('ignore')

# ML and Statistics
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

# Statistical analysis
import scipy.stats as stats
from scipy.optimize import minimize
import arch  # GARCH models for volatility

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class VolatilityPredictor:
    """Volatility prediction using GARCH and ML models"""

    def __init__(self):
        self.garch_model = None
        self.ml_model = None
        self.scaler = StandardScaler()

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for volatility prediction"""
        features = df.copy()

        # Historical volatility features
        for window in [5, 10, 20, 30]:
            features[f'volatility_{window}'] = df['Close'].rolling(window).std()
            features[f'realized_vol_{window}'] = (df['Close'].pct_change().rolling(window).std() * np.sqrt(24))

        # Price-based features
        features['returns'] = df['Close'].pct_change()
        features['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
        features['abs_returns'] = np.abs(features['returns'])
        features['squared_returns'] = features['returns'] ** 2

        # Volume features
        features['volume_volatility'] = df['Volume'].rolling(20).std()
        features['price_volume_corr'] = features['returns'].rolling(20).corr(df['Volume'].pct_change())

        # Technical indicators
        features['atr'] = self._calculate_atr(df)
        features['bbands_width'] = self._calculate_bbands_width(df)

        return features.dropna()

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(period).mean()

    def _calculate_bbands_width(self, df: pd.DataFrame, period: int = 20, std: float = 2) -> pd.Series:
        """Calculate Bollinger Bands width"""
        sma = df['Close'].rolling(period).mean()
        rolling_std = df['Close'].rolling(period).std()
        upper_band = sma + (rolling_std * std)
        lower_band = sma - (rolling_std * std)
        return (upper_band - lower_band) / sma

    def train_garch_model(self, returns: pd.Series):
        """Train GARCH model for volatility prediction"""
        try:
            from arch import arch_model

            # Remove extreme outliers
            returns_clean = returns[np.abs(returns) < returns.std() * 5]

            # Fit GARCH(1,1) model
            self.garch_model = arch_model(
                returns_clean * 100,  # Scale for numerical stability
                vol='Garch',
                p=1, q=1,
                mean='Constant',
                dist='normal'
            )

            garch_fit = self.garch_model.fit(disp='off')
            return garch_fit

        except Exception as e:
            print(f"GARCH model training failed: {e}")
            return None

    def train_ml_model(self, features_df: pd.DataFrame, target_column: str = 'volatility_20'):
        """Train ML model for volatility prediction"""
        feature_columns = [col for col in features_df.columns
                          if col not in ['Close', 'Open', 'High', 'Low', 'Volume', target_column]]

        X = features_df[feature_columns].dropna()
        y = features_df[target_column].loc[X.index]

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Time series split for validation
        tscv = TimeSeriesSplit(n_splits=5)

        # Train XGBoost model
        self.ml_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )

        # Cross-validation
        cv_scores = []
        for train_idx, val_idx in tscv.split(X_scaled):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            self.ml_model.fit(X_train, y_train)
            y_pred = self.ml_model.predict(X_val)
            score = r2_score(y_val, y_pred)
            cv_scores.append(score)

        # Final training on full dataset
        self.ml_model.fit(X_scaled, y)

        return np.mean(cv_scores)

    def predict_volatility(self, features_df: pd.DataFrame, horizon: int = 5) -> Dict:
        """Predict future volatility"""
        if self.ml_model is None:
            return {'error': 'Model not trained'}

        feature_columns = [col for col in features_df.columns
                          if col not in ['Close', 'Open', 'High', 'Low', 'Volume']]

        X = features_df[feature_columns].tail(1)
        X_scaled = self.scaler.transform(X)

        # ML prediction
        ml_volatility = self.ml_model.predict(X_scaled)[0]

        # Current realized volatility
        current_vol = features_df['volatility_20'].iloc[-1]

        return {
            'ml_prediction': ml_volatility,
            'current_volatility': current_vol,
            'volatility_change': (ml_volatility - current_vol) / current_vol * 100,
            'volatility_regime': 'high' if ml_volatility > current_vol * 1.2 else 'normal'
        }

class DrawdownPredictor:
    """Maximum drawdown prediction system"""

    def __init__(self):
        self.model = None
        self.scaler = RobustScaler()

    def calculate_drawdown_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate features for drawdown prediction"""
        features = df.copy()

        # Price features
        features['returns'] = df['Close'].pct_change()
        features['cumulative_returns'] = (1 + features['returns']).cumprod()

        # Drawdown calculation
        rolling_max = features['cumulative_returns'].expanding().max()
        features['drawdown'] = (features['cumulative_returns'] - rolling_max) / rolling_max * 100

        # Drawdown features
        features['max_drawdown_5d'] = features['drawdown'].rolling(5).min()
        features['max_drawdown_20d'] = features['drawdown'].rolling(20).min()
        features['drawdown_duration'] = self._calculate_drawdown_duration(features['drawdown'])

        # Risk features
        features['downside_deviation'] = self._calculate_downside_deviation(features['returns'])
        features['negative_returns_pct'] = (features['returns'] < 0).rolling(20).sum() / 20

        # Volatility clustering
        features['volatility_regime'] = self._identify_volatility_regime(features['returns'])

        return features.dropna()

    def _calculate_drawdown_duration(self, drawdown_series: pd.Series) -> pd.Series:
        """Calculate drawdown duration"""
        duration = pd.Series(0, index=drawdown_series.index)
        current_duration = 0

        for i in range(1, len(drawdown_series)):
            if drawdown_series.iloc[i] < 0:
                current_duration += 1
            else:
                current_duration = 0
            duration.iloc[i] = current_duration

        return duration

    def _calculate_downside_deviation(self, returns: pd.Series, window: int = 20) -> pd.Series:
        """Calculate downside deviation"""
        negative_returns = returns.where(returns < 0, 0)
        return negative_returns.rolling(window).std()

    def _identify_volatility_regime(self, returns: pd.Series, window: int = 20) -> pd.Series:
        """Identify volatility regime"""
        volatility = returns.rolling(window).std()
        vol_mean = volatility.mean()
        vol_std = volatility.std()

        regime = pd.Series(0, index=returns.index)
        regime[volatility > vol_mean + vol_std] = 2  # High volatility
        regime[volatility < vol_mean - vol_std] = 1  # Low volatility

        return regime

    def train_model(self, features_df: pd.DataFrame) -> float:
        """Train drawdown prediction model"""
        # Target: future maximum drawdown over next 20 periods
        target = features_df['drawdown'].rolling(20).min().shift(-20)

        feature_columns = [
            'max_drawdown_5d', 'max_drawdown_20d', 'drawdown_duration',
            'downside_deviation', 'negative_returns_pct', 'volatility_regime'
        ]

        X = features_df[feature_columns].dropna()
        y = target.loc[X.index].dropna()

        # Align X and y
        common_index = X.index.intersection(y.index)
        X = X.loc[common_index]
        y = y.loc[common_index]

        if len(X) < 50:
            return 0.0

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )

        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=3)
        scores = []

        for train_idx, val_idx in tscv.split(X_scaled):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_val)
            score = r2_score(y_val, y_pred)
            scores.append(score)

        # Final training
        self.model.fit(X_scaled, y)

        return np.mean(scores)

    def predict_drawdown(self, features_df: pd.DataFrame) -> Dict:
        """Predict future maximum drawdown"""
        if self.model is None:
            return {'error': 'Model not trained'}

        feature_columns = [
            'max_drawdown_5d', 'max_drawdown_20d', 'drawdown_duration',
            'downside_deviation', 'negative_returns_pct', 'volatility_regime'
        ]

        X = features_df[feature_columns].tail(1)
        X_scaled = self.scaler.transform(X)

        predicted_drawdown = self.model.predict(X_scaled)[0]
        current_drawdown = features_df['drawdown'].iloc[-1]

        return {
            'predicted_max_drawdown': predicted_drawdown,
            'current_drawdown': current_drawdown,
            'risk_level': 'high' if predicted_drawdown < -10 else 'medium' if predicted_drawdown < -5 else 'low'
        }

class PredictiveRiskManager:
    """Main predictive risk management system"""

    def __init__(self):
        self.volatility_predictor = VolatilityPredictor()
        self.drawdown_predictor = DrawdownPredictor()
        self.logger = self._setup_logging()

        # Risk thresholds
        self.risk_thresholds = {
            'max_portfolio_risk': 0.02,  # 2% portfolio risk per trade
            'max_drawdown_threshold': -0.15,  # 15% max drawdown
            'volatility_threshold': 0.05,  # 5% daily volatility threshold
            'correlation_threshold': 0.7  # Max correlation between positions
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('PredictiveRiskManager')
        logger.setLevel(logging.INFO)

        log_dir = os.path.join(project_root, 'ai_optimization', 'models')
        os.makedirs(log_dir, exist_ok=True)

        handler = logging.FileHandler(
            os.path.join(log_dir, 'predictive_risk.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def train_models(self, market_data: pd.DataFrame) -> Dict:
        """Train all risk prediction models"""
        self.logger.info("Training predictive risk models...")

        results = {}

        # Train volatility predictor
        vol_features = self.volatility_predictor.prepare_features(market_data)
        vol_score = self.volatility_predictor.train_ml_model(vol_features)
        results['volatility_model_score'] = vol_score

        # Train GARCH model
        returns = market_data['Close'].pct_change().dropna()
        garch_fit = self.volatility_predictor.train_garch_model(returns)
        results['garch_model'] = garch_fit is not None

        # Train drawdown predictor
        dd_features = self.drawdown_predictor.calculate_drawdown_features(market_data)
        dd_score = self.drawdown_predictor.train_model(dd_features)
        results['drawdown_model_score'] = dd_score

        self.logger.info(f"Model training completed: {results}")
        return results

    def calculate_portfolio_risk(self, positions: List[Dict]) -> Dict:
        """Calculate comprehensive portfolio risk metrics"""
        if not positions:
            return {'total_risk': 0.0, 'max_single_risk': 0.0, 'diversification_ratio': 1.0}

        # Calculate individual position risks
        position_risks = []
        position_values = []

        for position in positions:
            size = position.get('size', 0)
            price = position.get('price', 0)
            stop_loss = position.get('stop_loss', 0)

            if stop_loss > 0:
                risk_per_unit = abs(price - stop_loss) / price
                position_risk = size * price * risk_per_unit
                position_risks.append(position_risk)
                position_values.append(size * price)

        if not position_risks:
            return {'total_risk': 0.0, 'max_single_risk': 0.0, 'diversification_ratio': 1.0}

        total_portfolio_value = sum(position_values)
        total_risk = sum(position_risks)
        max_single_risk = max(position_risks)

        # Diversification ratio
        equal_weight_risk = total_risk / len(position_risks)
        diversification_ratio = equal_weight_risk / (total_risk / len(position_risks)) if total_risk > 0 else 1.0

        return {
            'total_risk': total_risk,
            'total_risk_pct': total_risk / total_portfolio_value * 100 if total_portfolio_value > 0 else 0,
            'max_single_risk': max_single_risk,
            'max_single_risk_pct': max_single_risk / total_portfolio_value * 100 if total_portfolio_value > 0 else 0,
            'diversification_ratio': diversification_ratio,
            'position_count': len(positions)
        }

    def predict_portfolio_risk(self, market_data: pd.DataFrame, positions: List[Dict]) -> Dict:
        """Comprehensive portfolio risk prediction"""
        self.logger.info("Predicting portfolio risk...")

        # Current portfolio risk
        current_risk = self.calculate_portfolio_risk(positions)

        # Volatility prediction
        vol_features = self.volatility_predictor.prepare_features(market_data)
        volatility_pred = self.volatility_predictor.predict_volatility(vol_features)

        # Drawdown prediction
        dd_features = self.drawdown_predictor.calculate_drawdown_features(market_data)
        drawdown_pred = self.drawdown_predictor.predict_drawdown(dd_features)

        # Risk score calculation
        risk_score = self._calculate_risk_score(current_risk, volatility_pred, drawdown_pred)

        # Risk recommendations
        recommendations = self._generate_risk_recommendations(current_risk, volatility_pred, drawdown_pred)

        return {
            'timestamp': datetime.now().isoformat(),
            'current_portfolio_risk': current_risk,
            'volatility_prediction': volatility_pred,
            'drawdown_prediction': drawdown_pred,
            'overall_risk_score': risk_score,
            'risk_level': self._categorize_risk_level(risk_score),
            'recommendations': recommendations
        }

    def _calculate_risk_score(self, portfolio_risk: Dict, vol_pred: Dict, dd_pred: Dict) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0

        # Portfolio risk component (40% weight)
        portfolio_risk_pct = portfolio_risk.get('total_risk_pct', 0)
        risk_component = min(portfolio_risk_pct / self.risk_thresholds['max_portfolio_risk'] * 100, 100) * 0.4

        # Volatility component (30% weight)
        if 'volatility_change' in vol_pred:
            vol_change = vol_pred['volatility_change']
            vol_component = min(abs(vol_change) / 50 * 100, 100) * 0.3
        else:
            vol_component = 0

        # Drawdown component (30% weight)
        if 'predicted_max_drawdown' in dd_pred:
            predicted_dd = abs(dd_pred['predicted_max_drawdown'])
            dd_component = min(predicted_dd / abs(self.risk_thresholds['max_drawdown_threshold']) * 100, 100) * 0.3
        else:
            dd_component = 0

        score = risk_component + vol_component + dd_component
        return min(score, 100)

    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk level based on score"""
        if risk_score < 30:
            return 'LOW'
        elif risk_score < 60:
            return 'MEDIUM'
        elif risk_score < 80:
            return 'HIGH'
        else:
            return 'CRITICAL'

    def _generate_risk_recommendations(self, portfolio_risk: Dict, vol_pred: Dict, dd_pred: Dict) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []

        # Portfolio risk recommendations
        if portfolio_risk.get('total_risk_pct', 0) > 2:
            recommendations.append("Reduce position sizes to limit portfolio risk below 2%")

        if portfolio_risk.get('max_single_risk_pct', 0) > 1:
            recommendations.append("Reduce largest position size to limit single position risk")

        # Volatility recommendations
        if vol_pred.get('volatility_regime') == 'high':
            recommendations.append("High volatility predicted - consider tightening stop losses")

        # Drawdown recommendations
        if dd_pred.get('risk_level') == 'high':
            recommendations.append("High drawdown risk - consider reducing leverage or position count")

        # Diversification recommendations
        if portfolio_risk.get('position_count', 0) < 3:
            recommendations.append("Consider increasing diversification with more positions")

        if not recommendations:
            recommendations.append("Risk levels are within acceptable parameters")

        return recommendations

def main():
    """Main risk prediction runner"""
    print("=" * 60)
    print("PREDICTIVE RISK MANAGEMENT AI")
    print("Phase 9: Advanced Risk Prediction System")
    print("=" * 60)

    # Initialize risk manager
    risk_manager = PredictiveRiskManager()

    # Simulate market data (in production, fetch real data)
    dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='1H')
    np.random.seed(42)

    # Generate synthetic market data
    price = 50000
    prices = [price]

    for _ in range(len(dates) - 1):
        change = np.random.normal(0, 0.02)  # 2% hourly volatility
        price = price * (1 + change)
        prices.append(price)

    market_data = pd.DataFrame({
        'Close': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Open': prices,
        'Volume': np.random.randint(1000000, 5000000, len(prices))
    }, index=dates)

    # Train models
    print("Training risk prediction models...")
    training_results = risk_manager.train_models(market_data)
    print(f"Training results: {training_results}")

    # Simulate current positions
    positions = [
        {'size': 0.1, 'price': 48000, 'stop_loss': 46000, 'symbol': 'BTC/USDT'},
        {'size': 0.05, 'price': 3200, 'stop_loss': 3000, 'symbol': 'ETH/USDT'}
    ]

    # Predict portfolio risk
    print("\nPredicting portfolio risk...")
    risk_prediction = risk_manager.predict_portfolio_risk(market_data, positions)

    print("\nRisk Prediction Results:")
    print(json.dumps(risk_prediction, indent=2, default=str))

if __name__ == '__main__':
    main()