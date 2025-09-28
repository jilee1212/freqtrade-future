#!/usr/bin/env python3
"""
Real-time Anomaly Detection System
Phase 9: Advanced anomaly detection for trading systems

Features:
- Statistical anomaly detection
- ML-based outlier detection
- Price action anomalies
- Volume anomalies
- Performance anomalies
- Real-time alerting
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from collections import deque
import threading
import time

# ML and Statistics
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import EllipticEnvelope
from sklearn.svm import OneClassSVM
import scipy.stats as stats

# Statistical tests
from scipy import signal
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.stats.diagnostic import acorr_ljungbox

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class StatisticalAnomalyDetector:
    """Statistical-based anomaly detection"""

    def __init__(self, window_size: int = 100, z_threshold: float = 3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.data_buffer = deque(maxlen=window_size)

    def detect_z_score_anomaly(self, value: float) -> Dict:
        """Detect anomalies using Z-score"""
        self.data_buffer.append(value)

        if len(self.data_buffer) < 10:
            return {'is_anomaly': False, 'score': 0.0, 'method': 'z_score'}

        data = np.array(self.data_buffer)
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return {'is_anomaly': False, 'score': 0.0, 'method': 'z_score'}

        z_score = abs((value - mean) / std)
        is_anomaly = z_score > self.z_threshold

        return {
            'is_anomaly': is_anomaly,
            'score': z_score,
            'threshold': self.z_threshold,
            'method': 'z_score',
            'mean': mean,
            'std': std
        }

    def detect_iqr_anomaly(self, value: float) -> Dict:
        """Detect anomalies using Interquartile Range"""
        self.data_buffer.append(value)

        if len(self.data_buffer) < 10:
            return {'is_anomaly': False, 'score': 0.0, 'method': 'iqr'}

        data = np.array(self.data_buffer)
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        is_anomaly = value < lower_bound or value > upper_bound

        # Calculate anomaly score
        if value < lower_bound:
            score = (lower_bound - value) / iqr
        elif value > upper_bound:
            score = (value - upper_bound) / iqr
        else:
            score = 0.0

        return {
            'is_anomaly': is_anomaly,
            'score': score,
            'method': 'iqr',
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'iqr': iqr
        }

    def detect_grubbs_anomaly(self, values: List[float]) -> Dict:
        """Detect anomalies using Grubbs test"""
        if len(values) < 3:
            return {'is_anomaly': False, 'score': 0.0, 'method': 'grubbs'}

        data = np.array(values)
        mean = np.mean(data)
        std = np.std(data)
        n = len(data)

        # Calculate Grubbs statistic for each point
        g_values = np.abs((data - mean) / std)
        max_g = np.max(g_values)

        # Critical value for Grubbs test (alpha = 0.05)
        from scipy.stats import t
        t_critical = t.ppf(1 - 0.05 / (2 * n), n - 2)
        g_critical = ((n - 1) / np.sqrt(n)) * np.sqrt(t_critical**2 / (n - 2 + t_critical**2))

        is_anomaly = max_g > g_critical
        anomaly_index = np.argmax(g_values) if is_anomaly else -1

        return {
            'is_anomaly': is_anomaly,
            'score': max_g,
            'critical_value': g_critical,
            'method': 'grubbs',
            'anomaly_index': anomaly_index,
            'anomaly_value': data[anomaly_index] if anomaly_index >= 0 else None
        }

class MLAnomalyDetector:
    """Machine learning-based anomaly detection"""

    def __init__(self):
        self.isolation_forest = None
        self.one_class_svm = None
        self.elliptic_envelope = None
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for ML anomaly detection"""
        features = []

        # Price features
        features.append(df['Close'].pct_change().fillna(0))
        features.append(df['High'].pct_change().fillna(0))
        features.append(df['Low'].pct_change().fillna(0))
        features.append(df['Volume'].pct_change().fillna(0))

        # Technical indicators
        if 'RSI' in df.columns:
            features.append(df['RSI'].fillna(50))
        if 'MACD' in df.columns:
            features.append(df['MACD'].fillna(0))

        # Volatility features
        returns = df['Close'].pct_change().fillna(0)
        features.append(returns.rolling(20).std().fillna(0))
        features.append(np.abs(returns))

        # Volume features
        features.append(df['Volume'].rolling(20).mean().fillna(0))

        return np.column_stack(features)

    def train_models(self, X: np.ndarray):
        """Train anomaly detection models"""
        if len(X) < 50:
            return False

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.isolation_forest.fit(X_scaled)

        # Train One-Class SVM
        self.one_class_svm = OneClassSVM(
            kernel='rbf',
            gamma='scale',
            nu=0.1
        )
        self.one_class_svm.fit(X_scaled)

        # Train Elliptic Envelope
        self.elliptic_envelope = EllipticEnvelope(
            contamination=0.1,
            random_state=42
        )
        self.elliptic_envelope.fit(X_scaled)

        self.is_trained = True
        return True

    def detect_anomaly(self, features: np.ndarray) -> Dict:
        """Detect anomalies using trained ML models"""
        if not self.is_trained:
            return {'error': 'Models not trained'}

        features_scaled = self.scaler.transform(features.reshape(1, -1))

        results = {}

        # Isolation Forest
        if_prediction = self.isolation_forest.predict(features_scaled)[0]
        if_score = self.isolation_forest.score_samples(features_scaled)[0]
        results['isolation_forest'] = {
            'is_anomaly': if_prediction == -1,
            'score': if_score
        }

        # One-Class SVM
        svm_prediction = self.one_class_svm.predict(features_scaled)[0]
        svm_score = self.one_class_svm.score_samples(features_scaled)[0]
        results['one_class_svm'] = {
            'is_anomaly': svm_prediction == -1,
            'score': svm_score
        }

        # Elliptic Envelope
        ee_prediction = self.elliptic_envelope.predict(features_scaled)[0]
        ee_score = self.elliptic_envelope.score_samples(features_scaled)[0]
        results['elliptic_envelope'] = {
            'is_anomaly': ee_prediction == -1,
            'score': ee_score
        }

        # Ensemble decision
        anomaly_votes = sum([
            results['isolation_forest']['is_anomaly'],
            results['one_class_svm']['is_anomaly'],
            results['elliptic_envelope']['is_anomaly']
        ])

        ensemble_decision = anomaly_votes >= 2

        return {
            'ensemble_decision': ensemble_decision,
            'anomaly_votes': anomaly_votes,
            'individual_results': results
        }

class PriceAnomalyDetector:
    """Specialized price action anomaly detection"""

    def __init__(self):
        self.price_buffer = deque(maxlen=100)

    def detect_price_gap(self, current_price: float, previous_price: float, threshold: float = 0.02) -> Dict:
        """Detect significant price gaps"""
        if previous_price == 0:
            return {'is_anomaly': False, 'gap_size': 0.0}

        gap_size = abs(current_price - previous_price) / previous_price
        is_gap = gap_size > threshold

        return {
            'is_anomaly': is_gap,
            'gap_size': gap_size,
            'gap_direction': 'up' if current_price > previous_price else 'down',
            'threshold': threshold
        }

    def detect_price_spike(self, ohlc_data: Dict, threshold: float = 0.05) -> Dict:
        """Detect price spikes within a candle"""
        open_price = ohlc_data['Open']
        high_price = ohlc_data['High']
        low_price = ohlc_data['Low']
        close_price = ohlc_data['Close']

        # Calculate wick sizes
        upper_wick = (high_price - max(open_price, close_price)) / open_price
        lower_wick = (min(open_price, close_price) - low_price) / open_price
        body_size = abs(close_price - open_price) / open_price

        # Detect spikes
        is_upper_spike = upper_wick > threshold and upper_wick > body_size * 2
        is_lower_spike = lower_wick > threshold and lower_wick > body_size * 2

        return {
            'is_anomaly': is_upper_spike or is_lower_spike,
            'upper_spike': is_upper_spike,
            'lower_spike': is_lower_spike,
            'upper_wick_ratio': upper_wick,
            'lower_wick_ratio': lower_wick,
            'body_ratio': body_size
        }

    def detect_momentum_anomaly(self, prices: List[float], window: int = 20) -> Dict:
        """Detect momentum anomalies"""
        if len(prices) < window + 5:
            return {'is_anomaly': False, 'momentum_score': 0.0}

        # Calculate momentum
        recent_momentum = (prices[-1] - prices[-window]) / prices[-window]

        # Calculate historical momentum distribution
        momentum_history = []
        for i in range(window, len(prices) - 1):
            hist_momentum = (prices[i] - prices[i-window]) / prices[i-window]
            momentum_history.append(hist_momentum)

        if not momentum_history:
            return {'is_anomaly': False, 'momentum_score': 0.0}

        # Z-score of current momentum
        mean_momentum = np.mean(momentum_history)
        std_momentum = np.std(momentum_history)

        if std_momentum == 0:
            return {'is_anomaly': False, 'momentum_score': 0.0}

        momentum_z_score = abs((recent_momentum - mean_momentum) / std_momentum)
        is_anomaly = momentum_z_score > 2.5

        return {
            'is_anomaly': is_anomaly,
            'momentum_score': momentum_z_score,
            'recent_momentum': recent_momentum,
            'mean_momentum': mean_momentum,
            'momentum_direction': 'bullish' if recent_momentum > mean_momentum else 'bearish'
        }

class VolumeAnomalyDetector:
    """Volume-based anomaly detection"""

    def __init__(self):
        self.volume_buffer = deque(maxlen=100)

    def detect_volume_spike(self, current_volume: float, threshold_multiplier: float = 3.0) -> Dict:
        """Detect volume spikes"""
        self.volume_buffer.append(current_volume)

        if len(self.volume_buffer) < 20:
            return {'is_anomaly': False, 'volume_ratio': 1.0}

        recent_volumes = list(self.volume_buffer)[:-1]  # Exclude current volume
        avg_volume = np.mean(recent_volumes)

        if avg_volume == 0:
            return {'is_anomaly': False, 'volume_ratio': 1.0}

        volume_ratio = current_volume / avg_volume
        is_spike = volume_ratio > threshold_multiplier

        return {
            'is_anomaly': is_spike,
            'volume_ratio': volume_ratio,
            'threshold': threshold_multiplier,
            'average_volume': avg_volume,
            'current_volume': current_volume
        }

    def detect_volume_drought(self, current_volume: float, threshold_ratio: float = 0.3) -> Dict:
        """Detect unusually low volume (volume drought)"""
        self.volume_buffer.append(current_volume)

        if len(self.volume_buffer) < 20:
            return {'is_anomaly': False, 'volume_ratio': 1.0}

        recent_volumes = list(self.volume_buffer)[:-1]
        avg_volume = np.mean(recent_volumes)

        if avg_volume == 0:
            return {'is_anomaly': False, 'volume_ratio': 1.0}

        volume_ratio = current_volume / avg_volume
        is_drought = volume_ratio < threshold_ratio

        return {
            'is_anomaly': is_drought,
            'volume_ratio': volume_ratio,
            'threshold': threshold_ratio,
            'average_volume': avg_volume,
            'current_volume': current_volume
        }

class RealTimeAnomalyDetector:
    """Main real-time anomaly detection system"""

    def __init__(self):
        self.statistical_detector = StatisticalAnomalyDetector()
        self.ml_detector = MLAnomalyDetector()
        self.price_detector = PriceAnomalyDetector()
        self.volume_detector = VolumeAnomalyDetector()

        self.logger = self._setup_logging()
        self.alert_buffer = deque(maxlen=100)
        self.is_monitoring = False

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('AnomalyDetector')
        logger.setLevel(logging.INFO)

        log_dir = os.path.join(project_root, 'ai_optimization', 'models')
        os.makedirs(log_dir, exist_ok=True)

        handler = logging.FileHandler(
            os.path.join(log_dir, 'anomaly_detection.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def train_ml_models(self, historical_data: pd.DataFrame) -> bool:
        """Train ML anomaly detection models"""
        self.logger.info("Training ML anomaly detection models...")

        features = self.ml_detector.prepare_features(historical_data)
        success = self.ml_detector.train_models(features)

        if success:
            self.logger.info("ML models trained successfully")
        else:
            self.logger.warning("Failed to train ML models - insufficient data")

        return success

    def detect_anomalies(self, market_data: Dict) -> Dict:
        """Comprehensive anomaly detection"""
        timestamp = datetime.now()
        anomalies = {
            'timestamp': timestamp.isoformat(),
            'anomalies_detected': [],
            'risk_level': 'NORMAL'
        }

        # Price anomalies
        if 'price' in market_data:
            price = market_data['price']

            # Z-score anomaly
            z_result = self.statistical_detector.detect_z_score_anomaly(price)
            if z_result['is_anomaly']:
                anomalies['anomalies_detected'].append({
                    'type': 'price_z_score',
                    'severity': 'HIGH' if z_result['score'] > 4 else 'MEDIUM',
                    'details': z_result
                })

            # IQR anomaly
            iqr_result = self.statistical_detector.detect_iqr_anomaly(price)
            if iqr_result['is_anomaly']:
                anomalies['anomalies_detected'].append({
                    'type': 'price_iqr',
                    'severity': 'HIGH' if iqr_result['score'] > 3 else 'MEDIUM',
                    'details': iqr_result
                })

        # OHLC anomalies
        if all(key in market_data for key in ['Open', 'High', 'Low', 'Close']):
            ohlc_data = {k: market_data[k] for k in ['Open', 'High', 'Low', 'Close']}
            spike_result = self.price_detector.detect_price_spike(ohlc_data)

            if spike_result['is_anomaly']:
                anomalies['anomalies_detected'].append({
                    'type': 'price_spike',
                    'severity': 'HIGH',
                    'details': spike_result
                })

        # Volume anomalies
        if 'volume' in market_data:
            volume = market_data['volume']

            # Volume spike
            spike_result = self.volume_detector.detect_volume_spike(volume)
            if spike_result['is_anomaly']:
                anomalies['anomalies_detected'].append({
                    'type': 'volume_spike',
                    'severity': 'HIGH' if spike_result['volume_ratio'] > 5 else 'MEDIUM',
                    'details': spike_result
                })

            # Volume drought
            drought_result = self.volume_detector.detect_volume_drought(volume)
            if drought_result['is_anomaly']:
                anomalies['anomalies_detected'].append({
                    'type': 'volume_drought',
                    'severity': 'MEDIUM',
                    'details': drought_result
                })

        # ML-based anomalies (if models are trained)
        if self.ml_detector.is_trained and 'features' in market_data:
            ml_result = self.ml_detector.detect_anomaly(market_data['features'])
            if ml_result.get('ensemble_decision', False):
                anomalies['anomalies_detected'].append({
                    'type': 'ml_ensemble',
                    'severity': 'HIGH',
                    'details': ml_result
                })

        # Determine overall risk level
        if any(a['severity'] == 'HIGH' for a in anomalies['anomalies_detected']):
            anomalies['risk_level'] = 'HIGH'
        elif any(a['severity'] == 'MEDIUM' for a in anomalies['anomalies_detected']):
            anomalies['risk_level'] = 'MEDIUM'

        # Log anomalies
        if anomalies['anomalies_detected']:
            self.logger.warning(f"Anomalies detected: {len(anomalies['anomalies_detected'])} "
                              f"(Risk level: {anomalies['risk_level']})")

        return anomalies

    def start_monitoring(self, data_source_func, alert_callback=None):
        """Start real-time monitoring"""
        self.is_monitoring = True
        self.logger.info("Starting real-time anomaly monitoring...")

        def monitoring_loop():
            while self.is_monitoring:
                try:
                    # Get latest market data
                    market_data = data_source_func()

                    # Detect anomalies
                    anomalies = self.detect_anomalies(market_data)

                    # Send alerts if anomalies detected
                    if anomalies['anomalies_detected'] and alert_callback:
                        alert_callback(anomalies)

                    # Store in buffer
                    self.alert_buffer.append(anomalies)

                    time.sleep(1)  # Check every second

                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}")
                    time.sleep(5)

        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        self.logger.info("Stopped real-time anomaly monitoring")

    def get_anomaly_summary(self, hours: int = 24) -> Dict:
        """Get anomaly summary for the specified period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_anomalies = [
            alert for alert in self.alert_buffer
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]

        anomaly_types = {}
        risk_levels = {'HIGH': 0, 'MEDIUM': 0, 'NORMAL': 0}

        for alert in recent_anomalies:
            risk_levels[alert['risk_level']] += 1

            for anomaly in alert['anomalies_detected']:
                anomaly_type = anomaly['type']
                if anomaly_type not in anomaly_types:
                    anomaly_types[anomaly_type] = 0
                anomaly_types[anomaly_type] += 1

        return {
            'period_hours': hours,
            'total_alerts': len(recent_anomalies),
            'risk_level_distribution': risk_levels,
            'anomaly_type_distribution': anomaly_types,
            'latest_alert': recent_anomalies[-1] if recent_anomalies else None
        }

def main():
    """Main anomaly detection demo"""
    print("=" * 60)
    print("REAL-TIME ANOMALY DETECTION SYSTEM")
    print("Phase 9: Advanced Anomaly Detection")
    print("=" * 60)

    # Initialize detector
    detector = RealTimeAnomalyDetector()

    # Generate synthetic training data
    dates = pd.date_range(start='2024-01-01', end='2024-11-01', freq='1H')
    np.random.seed(42)

    # Normal market data
    prices = []
    price = 50000
    for i in range(len(dates)):
        # Add some anomalies randomly
        if np.random.random() < 0.01:  # 1% chance of anomaly
            change = np.random.normal(0, 0.1)  # Large price change
        else:
            change = np.random.normal(0, 0.02)  # Normal price change

        price = price * (1 + change)
        prices.append(price)

    training_data = pd.DataFrame({
        'Close': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Open': prices,
        'Volume': np.random.randint(1000000, 5000000, len(prices))
    }, index=dates)

    # Train models
    print("Training anomaly detection models...")
    success = detector.train_ml_models(training_data)
    print(f"Training {'successful' if success else 'failed'}")

    # Test anomaly detection with synthetic data
    print("\nTesting anomaly detection...")

    # Normal data point
    normal_data = {
        'price': 50000,
        'Open': 49900,
        'High': 50100,
        'Low': 49800,
        'Close': 50000,
        'volume': 2000000
    }

    normal_result = detector.detect_anomalies(normal_data)
    print(f"Normal data anomalies: {len(normal_result['anomalies_detected'])}")

    # Anomalous data point
    anomaly_data = {
        'price': 55000,  # 10% price jump
        'Open': 50000,
        'High': 55500,
        'Low': 49500,
        'Close': 55000,
        'volume': 10000000  # 5x volume spike
    }

    anomaly_result = detector.detect_anomalies(anomaly_data)
    print(f"Anomalous data anomalies: {len(anomaly_result['anomalies_detected'])}")
    print(f"Risk level: {anomaly_result['risk_level']}")

    # Display detected anomalies
    if anomaly_result['anomalies_detected']:
        print("\nDetected anomalies:")
        for i, anomaly in enumerate(anomaly_result['anomalies_detected'], 1):
            print(f"{i}. Type: {anomaly['type']}, Severity: {anomaly['severity']}")

if __name__ == '__main__':
    main()