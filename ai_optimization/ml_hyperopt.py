#!/usr/bin/env python3
"""
ML-Based Hyperparameter Optimization System
Phase 9: Advanced AI-driven strategy optimization

Features:
- Bayesian optimization with Optuna
- Multi-objective optimization (profit + risk)
- Dynamic parameter bounds adjustment
- Cross-validation backtesting
- Performance prediction models
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

# ML and Optimization
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class MLHyperOptimizer:
    """ML-based hyperparameter optimization system"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(project_root, 'user_data', 'config_futures.json')
        self.results_dir = os.path.join(project_root, 'ai_optimization', 'results')
        os.makedirs(self.results_dir, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logging()

        # ML models for performance prediction
        self.performance_model = None
        self.risk_model = None
        self.scaler = StandardScaler()

        # Optimization history
        self.optimization_history = []

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('MLHyperOptimizer')
        logger.setLevel(logging.INFO)

        handler = logging.FileHandler(
            os.path.join(self.results_dir, 'ml_optimization.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def load_historical_data(self) -> pd.DataFrame:
        """Load historical backtest results for ML training"""
        data_file = os.path.join(self.results_dir, 'optimization_history.json')

        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                history = json.load(f)
            return pd.DataFrame(history)
        else:
            return pd.DataFrame()

    def save_optimization_result(self, params: Dict, metrics: Dict):
        """Save optimization result to history"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'parameters': params,
            'metrics': metrics
        }

        self.optimization_history.append(result)

        # Save to file
        data_file = os.path.join(self.results_dir, 'optimization_history.json')
        with open(data_file, 'w') as f:
            json.dump(self.optimization_history, f, indent=2)

    def extract_features(self, params: Dict) -> np.ndarray:
        """Extract features from hyperparameters for ML models"""
        features = []

        # RSI parameters
        features.extend([
            params.get('rsi_period', 14),
            params.get('rsi_oversold', 30),
            params.get('rsi_overbought', 70)
        ])

        # Bollinger Bands parameters
        features.extend([
            params.get('bb_period', 20),
            params.get('bb_std', 2.0)
        ])

        # Position sizing parameters
        features.extend([
            params.get('max_leverage', 5.0),
            params.get('risk_per_trade', 0.02),
            params.get('stop_loss_pct', 0.05)
        ])

        # Trading parameters
        features.extend([
            params.get('min_volume', 1000000),
            params.get('profit_target_pct', 0.02)
        ])

        return np.array(features)

    def train_performance_models(self, df: pd.DataFrame):
        """Train ML models to predict strategy performance"""
        if df.empty:
            self.logger.warning("No historical data available for model training")
            return

        self.logger.info("Training performance prediction models...")

        # Prepare features and targets
        features = []
        profit_targets = []
        risk_targets = []

        for _, row in df.iterrows():
            feature_vector = self.extract_features(row['parameters'])
            features.append(feature_vector)

            metrics = row['metrics']
            profit_targets.append(metrics.get('total_profit', 0))
            risk_targets.append(metrics.get('max_drawdown', 0))

        if len(features) < 10:
            self.logger.warning("Insufficient data for model training (need at least 10 samples)")
            return

        features = np.array(features)
        profit_targets = np.array(profit_targets)
        risk_targets = np.array(risk_targets)

        # Scale features
        features_scaled = self.scaler.fit_transform(features)

        # Train performance model (profit prediction)
        self.performance_model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        self.performance_model.fit(features_scaled, profit_targets)

        # Train risk model (drawdown prediction)
        self.risk_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        self.risk_model.fit(features_scaled, risk_targets)

        # Evaluate models
        tscv = TimeSeriesSplit(n_splits=3)

        profit_scores = []
        risk_scores = []

        for train_idx, test_idx in tscv.split(features_scaled):
            # Profit model evaluation
            self.performance_model.fit(features_scaled[train_idx], profit_targets[train_idx])
            profit_pred = self.performance_model.predict(features_scaled[test_idx])
            profit_scores.append(r2_score(profit_targets[test_idx], profit_pred))

            # Risk model evaluation
            self.risk_model.fit(features_scaled[train_idx], risk_targets[train_idx])
            risk_pred = self.risk_model.predict(features_scaled[test_idx])
            risk_scores.append(r2_score(risk_targets[test_idx], risk_pred))

        self.logger.info(f"Performance model R2: {np.mean(profit_scores):.3f}")
        self.logger.info(f"Risk model R2: {np.mean(risk_scores):.3f}")

    def predict_performance(self, params: Dict) -> Tuple[float, float]:
        """Predict strategy performance using ML models"""
        if self.performance_model is None or self.risk_model is None:
            return 0.0, 0.0

        features = self.extract_features(params).reshape(1, -1)
        features_scaled = self.scaler.transform(features)

        predicted_profit = self.performance_model.predict(features_scaled)[0]
        predicted_risk = self.risk_model.predict(features_scaled)[0]

        return predicted_profit, predicted_risk

    def run_backtest(self, params: Dict) -> Dict:
        """Run backtest with given parameters"""
        self.logger.info(f"Running backtest with parameters: {params}")

        try:
            # Create temporary strategy file with parameters
            strategy_content = self._generate_strategy_code(params)
            strategy_file = os.path.join(self.results_dir, 'temp_strategy.py')

            with open(strategy_file, 'w') as f:
                f.write(strategy_content)

            # Run freqtrade backtest
            cmd = [
                'freqtrade', 'backtesting',
                '--config', self.config_path,
                '--strategy', 'temp_strategy',
                '--timerange', '20240901-20241201',  # Last 3 months
                '--export', 'trades',
                '--export-filename', os.path.join(self.results_dir, 'temp_backtest.json')
            ]

            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Parse backtest results
                return self._parse_backtest_results()
            else:
                self.logger.error(f"Backtest failed: {result.stderr}")
                return {'total_profit': -1000, 'max_drawdown': 100, 'win_rate': 0}

        except Exception as e:
            self.logger.error(f"Backtest error: {e}")
            return {'total_profit': -1000, 'max_drawdown': 100, 'win_rate': 0}

    def _generate_strategy_code(self, params: Dict) -> str:
        """Generate strategy code with given parameters"""
        return f'''
import talib.abstract as ta
from freqtrade.strategy import IStrategy, merge_informative_pair
from pandas import DataFrame
import numpy as np

class TempStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '5m'

    # Parameters from optimization
    rsi_period = {params.get('rsi_period', 14)}
    rsi_oversold = {params.get('rsi_oversold', 30)}
    rsi_overbought = {params.get('rsi_overbought', 70)}
    bb_period = {params.get('bb_period', 20)}
    bb_std = {params.get('bb_std', 2.0)}

    stop_loss = -{params.get('stop_loss_pct', 0.05)}
    roi = {{"0": {params.get('profit_target_pct', 0.02)}}}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=int(self.rsi_period))

        # Bollinger Bands
        bollinger = ta.BBANDS(dataframe, timeperiod=int(self.bb_period), nbdevup=self.bb_std, nbdevdn=self.bb_std)
        dataframe['bb_lower'] = bollinger['lowerband']
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_middle'] = bollinger['middleband']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['rsi'] < self.rsi_oversold) &
            (dataframe['close'] < dataframe['bb_lower']) &
            (dataframe['volume'] > {params.get('min_volume', 1000000)}),
            'enter_short'
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['rsi'] > self.rsi_overbought) |
            (dataframe['close'] > dataframe['bb_middle']),
            'exit_short'
        ] = 1

        return dataframe
'''

    def _parse_backtest_results(self) -> Dict:
        """Parse backtest results from JSON file"""
        results_file = os.path.join(self.results_dir, 'temp_backtest.json')

        try:
            with open(results_file, 'r') as f:
                data = json.load(f)

            strategy_stats = data.get('strategy', {}).get('TempStrategy', {})

            return {
                'total_profit': strategy_stats.get('profit_total_abs', 0),
                'max_drawdown': abs(strategy_stats.get('max_drawdown', 0)) * 100,
                'win_rate': strategy_stats.get('wins', 0) / max(strategy_stats.get('total_trades', 1), 1) * 100,
                'profit_factor': strategy_stats.get('profit_factor', 0),
                'sharpe_ratio': strategy_stats.get('sharpe', 0),
                'total_trades': strategy_stats.get('total_trades', 0)
            }

        except Exception as e:
            self.logger.error(f"Error parsing results: {e}")
            return {'total_profit': -1000, 'max_drawdown': 100, 'win_rate': 0}

    def objective_function(self, trial: optuna.Trial) -> float:
        """Optuna objective function for multi-objective optimization"""

        # Define parameter search space
        params = {
            'rsi_period': trial.suggest_int('rsi_period', 10, 25),
            'rsi_oversold': trial.suggest_float('rsi_oversold', 20, 35),
            'rsi_overbought': trial.suggest_float('rsi_overbought', 65, 80),
            'bb_period': trial.suggest_int('bb_period', 15, 30),
            'bb_std': trial.suggest_float('bb_std', 1.5, 2.5),
            'stop_loss_pct': trial.suggest_float('stop_loss_pct', 0.02, 0.08),
            'profit_target_pct': trial.suggest_float('profit_target_pct', 0.01, 0.05),
            'min_volume': trial.suggest_int('min_volume', 500000, 2000000)
        }

        # Use ML prediction if models are available
        if self.performance_model is not None:
            predicted_profit, predicted_risk = self.predict_performance(params)

            # If prediction is very negative, skip expensive backtest
            if predicted_profit < -500:
                return -1000

        # Run actual backtest
        metrics = self.run_backtest(params)

        # Save result for future ML training
        self.save_optimization_result(params, metrics)

        # Multi-objective score: maximize profit, minimize risk
        profit_score = metrics['total_profit']
        risk_penalty = metrics['max_drawdown'] * 10  # Penalize high drawdown
        trade_bonus = min(metrics.get('total_trades', 0) * 2, 50)  # Bonus for active trading

        # Combined score
        score = profit_score - risk_penalty + trade_bonus

        self.logger.info(f"Trial result - Profit: {profit_score:.2f}, "
                        f"Drawdown: {metrics['max_drawdown']:.2f}%, "
                        f"Score: {score:.2f}")

        return score

    def optimize_strategy(self, n_trials: int = 100) -> Dict:
        """Run hyperparameter optimization"""
        self.logger.info(f"Starting ML-based optimization with {n_trials} trials")

        # Load historical data and train models
        historical_df = self.load_historical_data()
        if not historical_df.empty:
            self.train_performance_models(historical_df)

        # Create Optuna study
        sampler = TPESampler(seed=42)
        pruner = MedianPruner(n_startup_trials=10, n_warmup_steps=5)

        study = optuna.create_study(
            direction='maximize',
            sampler=sampler,
            pruner=pruner
        )

        # Run optimization
        study.optimize(self.objective_function, n_trials=n_trials, timeout=3600)

        # Get best results
        best_params = study.best_params
        best_value = study.best_value

        self.logger.info(f"Optimization completed!")
        self.logger.info(f"Best score: {best_value:.2f}")
        self.logger.info(f"Best parameters: {best_params}")

        # Final validation backtest
        final_metrics = self.run_backtest(best_params)

        # Save optimization summary
        optimization_summary = {
            'timestamp': datetime.now().isoformat(),
            'n_trials': n_trials,
            'best_score': best_value,
            'best_parameters': best_params,
            'final_metrics': final_metrics,
            'study_trials': len(study.trials)
        }

        summary_file = os.path.join(self.results_dir, 'latest_optimization.json')
        with open(summary_file, 'w') as f:
            json.dump(optimization_summary, f, indent=2)

        return optimization_summary

    def get_parameter_importance(self) -> Dict:
        """Analyze parameter importance using trained models"""
        if self.performance_model is None:
            return {}

        # Feature names
        feature_names = [
            'rsi_period', 'rsi_oversold', 'rsi_overbought',
            'bb_period', 'bb_std', 'max_leverage', 'risk_per_trade',
            'stop_loss_pct', 'min_volume', 'profit_target_pct'
        ]

        # Get feature importance from the model
        importance = self.performance_model.feature_importances_

        importance_dict = dict(zip(feature_names, importance))
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))

def main():
    """Main optimization runner"""
    print("=" * 60)
    print("FREQTRADE ML HYPERPARAMETER OPTIMIZATION")
    print("Phase 9: Advanced AI-driven Strategy Optimization")
    print("=" * 60)

    optimizer = MLHyperOptimizer()

    # Run optimization
    result = optimizer.optimize_strategy(n_trials=50)

    print("\nOptimization Results:")
    print(f"Best Score: {result['best_score']:.2f}")
    print(f"Best Parameters: {json.dumps(result['best_parameters'], indent=2)}")
    print(f"Final Metrics: {json.dumps(result['final_metrics'], indent=2)}")

    # Show parameter importance
    importance = optimizer.get_parameter_importance()
    if importance:
        print("\nParameter Importance:")
        for param, imp in importance.items():
            print(f"  {param}: {imp:.3f}")

if __name__ == '__main__':
    main()