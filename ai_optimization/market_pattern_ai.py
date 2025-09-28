#!/usr/bin/env python3
"""
Market Pattern Analysis AI System
Phase 9: Advanced pattern recognition and market regime detection

Features:
- Deep learning pattern recognition
- Market regime classification
- Trend prediction models
- Volume profile analysis
- Sentiment analysis integration
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

# Deep Learning
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# Technical Analysis
import talib
import yfinance as yf

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class MarketPatternDataset(Dataset):
    """PyTorch dataset for market pattern data"""

    def __init__(self, sequences, labels, sequence_length=60):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.LongTensor(labels)
        self.sequence_length = sequence_length

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

class LSTMPatternModel(nn.Module):
    """LSTM model for pattern recognition"""

    def __init__(self, input_size, hidden_size=128, num_layers=2, num_classes=3, dropout=0.2):
        super(LSTMPatternModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )

        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=8,
            dropout=dropout
        )

        # Classification layers
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc2 = nn.Linear(hidden_size // 2, num_classes)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(x)

        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)

        # Use last output
        out = attn_out[:, -1, :]

        # Classification
        out = self.dropout(out)
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)

        return out

class MarketPatternAI:
    """Advanced market pattern analysis system"""

    def __init__(self):
        self.model_dir = os.path.join(project_root, 'ai_optimization', 'models')
        os.makedirs(self.model_dir, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logging()

        # Models
        self.lstm_model = None
        self.regime_classifier = None
        self.scaler = MinMaxScaler()
        self.label_encoder = LabelEncoder()

        # Model parameters
        self.sequence_length = 60  # 60 periods for pattern recognition
        self.input_features = 15   # Number of technical indicators

        # Market regimes
        self.market_regimes = ['bullish', 'bearish', 'sideways']

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('MarketPatternAI')
        logger.setLevel(logging.INFO)

        handler = logging.FileHandler(
            os.path.join(self.model_dir, 'pattern_ai.log')
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def fetch_market_data(self, symbol: str = "BTC-USD", period: str = "1y") -> pd.DataFrame:
        """Fetch market data for analysis"""
        self.logger.info(f"Fetching market data for {symbol}")

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval="1h")

            if data.empty:
                raise ValueError(f"No data received for {symbol}")

            return data

        except Exception as e:
            self.logger.error(f"Error fetching data: {e}")
            return pd.DataFrame()

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        self.logger.info("Calculating technical indicators...")

        # Price-based indicators
        df['SMA_20'] = talib.SMA(df['Close'], timeperiod=20)
        df['EMA_12'] = talib.EMA(df['Close'], timeperiod=12)
        df['EMA_26'] = talib.EMA(df['Close'], timeperiod=26)

        # Momentum indicators
        df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
        df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['Close'])
        df['Stoch_K'], df['Stoch_D'] = talib.STOCH(df['High'], df['Low'], df['Close'])

        # Volatility indicators
        df['BB_upper'], df['BB_middle'], df['BB_lower'] = talib.BBANDS(df['Close'])
        df['ATR'] = talib.ATR(df['High'], df['Low'], df['Close'])

        # Volume indicators
        df['OBV'] = talib.OBV(df['Close'], df['Volume'])
        df['AD'] = talib.AD(df['High'], df['Low'], df['Close'], df['Volume'])

        # Price patterns
        df['DOJI'] = talib.CDLDOJI(df['Open'], df['High'], df['Low'], df['Close'])
        df['HAMMER'] = talib.CDLHAMMER(df['Open'], df['High'], df['Low'], df['Close'])

        # Custom indicators
        df['Price_Change'] = df['Close'].pct_change()
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

        return df.dropna()

    def create_market_regime_labels(self, df: pd.DataFrame) -> pd.Series:
        """Create market regime labels for supervised learning"""
        self.logger.info("Creating market regime labels...")

        # Calculate trend strength
        df['SMA_50'] = talib.SMA(df['Close'], timeperiod=50)
        df['Price_vs_SMA'] = (df['Close'] - df['SMA_50']) / df['SMA_50']

        # Calculate volatility
        df['Volatility'] = df['Close'].rolling(window=20).std()

        labels = []
        for i in range(len(df)):
            price_trend = df['Price_vs_SMA'].iloc[i]
            volatility = df['Volatility'].iloc[i]

            if price_trend > 0.02:  # Strong uptrend
                labels.append('bullish')
            elif price_trend < -0.02:  # Strong downtrend
                labels.append('bearish')
            else:  # Sideways/consolidation
                labels.append('sideways')

        return pd.Series(labels, index=df.index)

    def prepare_sequences(self, df: pd.DataFrame, labels: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM training"""
        self.logger.info("Preparing sequences for training...")

        # Select features
        feature_columns = [
            'SMA_20', 'EMA_12', 'EMA_26', 'RSI', 'MACD', 'MACD_signal',
            'Stoch_K', 'Stoch_D', 'BB_upper', 'BB_lower', 'ATR',
            'OBV', 'Price_Change', 'Volume_Ratio', 'Volatility'
        ]

        # Ensure all features exist
        available_features = [col for col in feature_columns if col in df.columns]
        self.logger.info(f"Using {len(available_features)} features: {available_features}")

        # Scale features
        feature_data = df[available_features].values
        scaled_data = self.scaler.fit_transform(feature_data)

        # Encode labels
        encoded_labels = self.label_encoder.fit_transform(labels)

        # Create sequences
        sequences = []
        sequence_labels = []

        for i in range(self.sequence_length, len(scaled_data)):
            sequences.append(scaled_data[i-self.sequence_length:i])
            sequence_labels.append(encoded_labels[i])

        return np.array(sequences), np.array(sequence_labels)

    def train_lstm_model(self, sequences: np.ndarray, labels: np.ndarray):
        """Train LSTM pattern recognition model"""
        self.logger.info("Training LSTM pattern recognition model...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            sequences, labels, test_size=0.2, random_state=42, stratify=labels
        )

        # Create datasets
        train_dataset = MarketPatternDataset(X_train, y_train, self.sequence_length)
        test_dataset = MarketPatternDataset(X_test, y_test, self.sequence_length)

        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

        # Initialize model
        self.lstm_model = LSTMPatternModel(
            input_size=self.input_features,
            hidden_size=128,
            num_layers=2,
            num_classes=len(self.market_regimes)
        )

        # Training setup
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.lstm_model.parameters(), lr=0.001)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10)

        # Training loop
        num_epochs = 100
        best_accuracy = 0.0

        for epoch in range(num_epochs):
            # Training phase
            self.lstm_model.train()
            train_loss = 0.0

            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.lstm_model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            # Validation phase
            self.lstm_model.eval()
            correct = 0
            total = 0

            with torch.no_grad():
                for batch_X, batch_y in test_loader:
                    outputs = self.lstm_model(batch_X)
                    _, predicted = torch.max(outputs.data, 1)
                    total += batch_y.size(0)
                    correct += (predicted == batch_y).sum().item()

            accuracy = 100 * correct / total
            avg_train_loss = train_loss / len(train_loader)

            scheduler.step(avg_train_loss)

            if epoch % 10 == 0:
                self.logger.info(f'Epoch {epoch}/{num_epochs}, '
                               f'Loss: {avg_train_loss:.4f}, '
                               f'Accuracy: {accuracy:.2f}%')

            # Save best model
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                self.save_model()

        self.logger.info(f"Training completed. Best accuracy: {best_accuracy:.2f}%")

    def train_regime_classifier(self, df: pd.DataFrame, labels: pd.Series):
        """Train market regime classifier"""
        self.logger.info("Training market regime classifier...")

        # Feature engineering for regime classification
        features = []
        feature_names = []

        # Price momentum features
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['Close'].pct_change(period)
            features.append(f'momentum_{period}')

        # Volatility features
        for period in [10, 20, 30]:
            df[f'volatility_{period}'] = df['Close'].rolling(period).std()
            features.append(f'volatility_{period}')

        # Volume features
        df['volume_sma'] = df['Volume'].rolling(20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma']
        features.extend(['volume_ratio'])

        # Technical indicators
        features.extend(['RSI', 'MACD', 'ATR'])

        # Prepare data
        feature_data = df[features].dropna()
        aligned_labels = labels.loc[feature_data.index]

        X_train, X_test, y_train, y_test = train_test_split(
            feature_data, aligned_labels, test_size=0.2, random_state=42
        )

        # Train Random Forest classifier
        self.regime_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        self.regime_classifier.fit(X_train, y_train)

        # Evaluate
        y_pred = self.regime_classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        self.logger.info(f"Regime classifier accuracy: {accuracy:.3f}")
        self.logger.info("Classification report:")
        self.logger.info(classification_report(y_test, y_pred))

        # Feature importance
        importance = dict(zip(features, self.regime_classifier.feature_importances_))
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)

        self.logger.info("Feature importance:")
        for feature, imp in sorted_importance[:10]:
            self.logger.info(f"  {feature}: {imp:.3f}")

    def predict_pattern(self, recent_data: pd.DataFrame) -> Dict:
        """Predict market pattern for recent data"""
        if self.lstm_model is None:
            return {'pattern': 'unknown', 'confidence': 0.0}

        # Prepare features
        feature_columns = [
            'SMA_20', 'EMA_12', 'EMA_26', 'RSI', 'MACD', 'MACD_signal',
            'Stoch_K', 'Stoch_D', 'BB_upper', 'BB_lower', 'ATR',
            'OBV', 'Price_Change', 'Volume_Ratio', 'Volatility'
        ]

        available_features = [col for col in feature_columns if col in recent_data.columns]
        feature_data = recent_data[available_features].tail(self.sequence_length).values

        if len(feature_data) < self.sequence_length:
            return {'pattern': 'insufficient_data', 'confidence': 0.0}

        # Scale and predict
        scaled_data = self.scaler.transform(feature_data)
        sequence = torch.FloatTensor(scaled_data).unsqueeze(0)

        self.lstm_model.eval()
        with torch.no_grad():
            output = self.lstm_model(sequence)
            probabilities = torch.softmax(output, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()

        predicted_regime = self.label_encoder.inverse_transform([predicted_class])[0]

        return {
            'pattern': predicted_regime,
            'confidence': confidence,
            'probabilities': {
                regime: prob.item() for regime, prob in
                zip(self.market_regimes, probabilities[0])
            }
        }

    def analyze_current_market(self, symbol: str = "BTC-USD") -> Dict:
        """Comprehensive current market analysis"""
        self.logger.info(f"Analyzing current market for {symbol}")

        # Fetch recent data
        df = self.fetch_market_data(symbol, period="3mo")
        if df.empty:
            return {'error': 'Unable to fetch market data'}

        # Calculate indicators
        df = self.calculate_technical_indicators(df)

        # Pattern prediction
        pattern_result = self.predict_pattern(df)

        # Recent price action analysis
        recent_close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        price_change = (recent_close - prev_close) / prev_close * 100

        # Volatility analysis
        volatility = df['Close'].tail(20).std()
        avg_volatility = df['Close'].rolling(50).std().mean()
        volatility_ratio = volatility / avg_volatility

        # Volume analysis
        recent_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].tail(20).mean()
        volume_ratio = recent_volume / avg_volume

        # Technical levels
        support_level = df['Close'].tail(50).min()
        resistance_level = df['Close'].tail(50).max()

        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'pattern_prediction': pattern_result,
            'price_analysis': {
                'current_price': recent_close,
                'price_change_pct': price_change,
                'support_level': support_level,
                'resistance_level': resistance_level
            },
            'volatility_analysis': {
                'current_volatility': volatility,
                'volatility_ratio': volatility_ratio,
                'volatility_state': 'high' if volatility_ratio > 1.2 else 'normal' if volatility_ratio > 0.8 else 'low'
            },
            'volume_analysis': {
                'current_volume': recent_volume,
                'volume_ratio': volume_ratio,
                'volume_state': 'high' if volume_ratio > 1.5 else 'normal' if volume_ratio > 0.7 else 'low'
            },
            'technical_indicators': {
                'rsi': df['RSI'].iloc[-1],
                'macd': df['MACD'].iloc[-1],
                'bb_position': (recent_close - df['BB_lower'].iloc[-1]) / (df['BB_upper'].iloc[-1] - df['BB_lower'].iloc[-1])
            }
        }

    def save_model(self):
        """Save trained models"""
        if self.lstm_model:
            torch.save(self.lstm_model.state_dict(),
                      os.path.join(self.model_dir, 'lstm_pattern_model.pth'))

        if self.regime_classifier:
            import joblib
            joblib.dump(self.regime_classifier,
                       os.path.join(self.model_dir, 'regime_classifier.pkl'))

        self.logger.info("Models saved successfully")

    def load_model(self):
        """Load trained models"""
        try:
            lstm_path = os.path.join(self.model_dir, 'lstm_pattern_model.pth')
            if os.path.exists(lstm_path):
                self.lstm_model = LSTMPatternModel(self.input_features)
                self.lstm_model.load_state_dict(torch.load(lstm_path))
                self.lstm_model.eval()

            import joblib
            classifier_path = os.path.join(self.model_dir, 'regime_classifier.pkl')
            if os.path.exists(classifier_path):
                self.regime_classifier = joblib.load(classifier_path)

            self.logger.info("Models loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False

def main():
    """Main training and analysis runner"""
    print("=" * 60)
    print("MARKET PATTERN ANALYSIS AI")
    print("Phase 9: Advanced Pattern Recognition System")
    print("=" * 60)

    ai = MarketPatternAI()

    # Try to load existing models
    if not ai.load_model():
        print("Training new models...")

        # Fetch training data
        df = ai.fetch_market_data("BTC-USD", period="2y")
        if df.empty:
            print("Error: Unable to fetch training data")
            return

        # Calculate indicators
        df = ai.calculate_technical_indicators(df)

        # Create labels
        labels = ai.create_market_regime_labels(df)

        # Train models
        sequences, seq_labels = ai.prepare_sequences(df, labels)
        ai.train_lstm_model(sequences, seq_labels)
        ai.train_regime_classifier(df, labels)

    # Analyze current market
    print("\nAnalyzing current market...")
    analysis = ai.analyze_current_market("BTC-USD")

    print("\nMarket Analysis Results:")
    print(json.dumps(analysis, indent=2, default=str))

if __name__ == '__main__':
    main()