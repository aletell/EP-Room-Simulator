"""
Main occupancy forecasting interface.

This module provides the OccupancyForecaster class which serves as the main
interface for occupancy prediction using various ML models.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import pickle
import os

from .data_preprocessor import DataPreprocessor

logger = logging.getLogger(__name__)


class OccupancyForecaster:
    """
    ML-based occupancy forecasting system.
    
    Supports multiple forecasting models and time horizons.
    Provides a unified interface for training, prediction, and evaluation.
    
    Example:
        forecaster = OccupancyForecaster(model_type='simple')
        forecaster.train(historical_data)
        forecast = forecaster.predict(start_date='2024-01-01', end_date='2024-01-31')
    """
    
    SUPPORTED_MODELS = ['simple', 'average', 'linear']
    
    def __init__(self, model_type: str = 'simple'):
        """
        Initialize forecaster with specified model.
        
        Args:
            model_type: Type of model ('simple', 'average', 'linear')
                       Note: Advanced models like 'lstm' and 'prophet' require
                       additional dependencies (tensorflow, prophet)
        """
        if model_type not in self.SUPPORTED_MODELS:
            logger.warning(f"Model type '{model_type}' not in basic supported models. "
                         f"Supported: {self.SUPPORTED_MODELS}")
            
        self.model_type = model_type
        self.model = None
        self.preprocessor = DataPreprocessor()
        self.trained = False
        self.training_data = None
        
    def train(self, historical_data: pd.DataFrame, 
             features: Optional[list] = None) -> None:
        """
        Train forecasting model on historical occupancy data.
        
        Args:
            historical_data: DataFrame with 'timestamp' and 'occupancy' columns
            features: Optional list of feature columns to use
        """
        if 'timestamp' not in historical_data.columns:
            raise ValueError("historical_data must have 'timestamp' column")
            
        if 'occupancy' not in historical_data.columns:
            raise ValueError("historical_data must have 'occupancy' column")
            
        logger.info(f"Training {self.model_type} model on {len(historical_data)} records")
        
        # Store training data for simple models
        self.training_data = historical_data.copy()
        self.training_data['timestamp'] = pd.to_datetime(self.training_data['timestamp'])
        
        if self.model_type == 'simple':
            self._train_simple_model()
        elif self.model_type == 'average':
            self._train_average_model()
        elif self.model_type == 'linear':
            self._train_linear_model()
        else:
            raise NotImplementedError(f"Model type '{self.model_type}' not yet implemented")
            
        self.trained = True
        logger.info("Model training completed")
        
    def _train_simple_model(self) -> None:
        """Train a simple pattern-based model."""
        # Extract patterns by hour of day and day of week
        df = self.training_data.copy()
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Calculate average occupancy for each hour and day combination
        patterns = df.groupby(['day_of_week', 'hour'])['occupancy'].mean().to_dict()
        self.model = {'patterns': patterns, 'type': 'simple'}
        
    def _train_average_model(self) -> None:
        """Train a simple average model."""
        df = self.training_data.copy()
        df['hour'] = df['timestamp'].dt.hour
        
        # Just use hourly averages regardless of day
        patterns = df.groupby('hour')['occupancy'].mean().to_dict()
        self.model = {'patterns': patterns, 'type': 'average'}
        
    def _train_linear_model(self) -> None:
        """Train a linear regression model."""
        from sklearn.linear_model import LinearRegression
        
        # Preprocess data
        df = self.preprocessor.clean_data(self.training_data)
        df = self.preprocessor.extract_temporal_features(df)
        
        # Select features
        feature_cols = ['hour', 'day_of_week', 'month', 'is_weekend', 
                       'hour_sin', 'hour_cos', 'day_sin', 'day_cos']
        
        X = df[feature_cols].values
        y = df['occupancy'].values
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        self.model = {
            'model': model,
            'type': 'linear',
            'features': feature_cols
        }
        
    def predict(self, start_date: str, end_date: str, 
                interval: str = '15min') -> pd.DataFrame:
        """
        Generate occupancy forecast for specified period.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Time interval ('15min', '30min', '1H', etc.)
            
        Returns:
            DataFrame with predicted occupancy at specified intervals
        """
        if not self.trained:
            raise ValueError("Model must be trained before prediction")
            
        logger.info(f"Generating forecast from {start_date} to {end_date}")
        
        # Create time range
        timestamps = pd.date_range(start=start_date, end=end_date, freq=interval)
        
        # Create DataFrame
        forecast_df = pd.DataFrame({'timestamp': timestamps})
        
        if self.model_type == 'simple':
            forecast_df['occupancy'] = self._predict_simple(forecast_df)
        elif self.model_type == 'average':
            forecast_df['occupancy'] = self._predict_average(forecast_df)
        elif self.model_type == 'linear':
            forecast_df['occupancy'] = self._predict_linear(forecast_df)
        else:
            raise NotImplementedError(f"Prediction for '{self.model_type}' not implemented")
            
        # Ensure non-negative occupancy
        forecast_df['occupancy'] = forecast_df['occupancy'].clip(lower=0)
        
        logger.info(f"Generated forecast with {len(forecast_df)} data points")
        return forecast_df
        
    def _predict_simple(self, df: pd.DataFrame) -> np.ndarray:
        """Predict using simple pattern model."""
        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        patterns = self.model['patterns']
        
        def get_prediction(row):
            key = (row['day_of_week'], row['hour'])
            return patterns.get(key, 0)
            
        return df.apply(get_prediction, axis=1).values
        
    def _predict_average(self, df: pd.DataFrame) -> np.ndarray:
        """Predict using average model."""
        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour
        
        patterns = self.model['patterns']
        
        def get_prediction(row):
            return patterns.get(row['hour'], 0)
            
        return df.apply(get_prediction, axis=1).values
        
    def _predict_linear(self, df: pd.DataFrame) -> np.ndarray:
        """Predict using linear model."""
        df = df.copy()
        df = self.preprocessor.extract_temporal_features(df)
        
        feature_cols = self.model['features']
        X = df[feature_cols].values
        
        model = self.model['model']
        return model.predict(X)
        
    def predict_with_confidence(self, start_date: str, end_date: str,
                                interval: str = '15min') -> pd.DataFrame:
        """
        Generate forecast with confidence intervals.
        
        Args:
            start_date: Start date
            end_date: End date
            interval: Time interval
            
        Returns:
            DataFrame with predicted occupancy, lower_bound, upper_bound
        """
        forecast = self.predict(start_date, end_date, interval)
        
        # Simple confidence interval based on training data variance
        if self.training_data is not None:
            std = self.training_data['occupancy'].std()
            forecast['lower_bound'] = (forecast['occupancy'] - 1.96 * std).clip(lower=0)
            forecast['upper_bound'] = forecast['occupancy'] + 1.96 * std
        else:
            # If no training data, use 20% margin
            forecast['lower_bound'] = (forecast['occupancy'] * 0.8).clip(lower=0)
            forecast['upper_bound'] = forecast['occupancy'] * 1.2
            
        return forecast
        
    def evaluate(self, test_data: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate model performance on test data.
        
        Args:
            test_data: DataFrame with 'timestamp' and 'occupancy' columns
            
        Returns:
            Dictionary with RMSE, MAE, and other metrics
        """
        if not self.trained:
            raise ValueError("Model must be trained before evaluation")
            
        # Generate predictions for test period
        start_date = test_data['timestamp'].min().strftime('%Y-%m-%d')
        end_date = test_data['timestamp'].max().strftime('%Y-%m-%d')
        
        # Determine interval from test data
        time_diff = test_data['timestamp'].diff().mode()[0]
        interval = f"{int(time_diff.total_seconds() / 60)}min"
        
        predictions = self.predict(start_date, end_date, interval)
        
        # Merge predictions with actual values
        test_data = test_data.copy()
        test_data['timestamp'] = pd.to_datetime(test_data['timestamp'])
        merged = pd.merge(
            predictions, 
            test_data[['timestamp', 'occupancy']], 
            on='timestamp',
            suffixes=('_pred', '_actual')
        )
        
        # Calculate metrics
        y_true = merged['occupancy_actual'].values
        y_pred = merged['occupancy_pred'].values
        
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2_score': r2_score(y_true, y_pred),
            'mean_error': np.mean(y_pred - y_true),
            'n_samples': len(merged)
        }
        
        logger.info(f"Evaluation metrics: RMSE={metrics['rmse']:.2f}, "
                   f"MAE={metrics['mae']:.2f}, R2={metrics['r2_score']:.3f}")
        
        return metrics
        
    def save_model(self, filepath: str) -> None:
        """
        Save trained model to disk.
        
        Args:
            filepath: Path to save model
        """
        if not self.trained:
            raise ValueError("Model must be trained before saving")
            
        model_data = {
            'model_type': self.model_type,
            'model': self.model,
            'preprocessor': self.preprocessor,
            'trained': self.trained
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
            
        logger.info(f"Model saved to {filepath}")
        
    def load_model(self, filepath: str) -> None:
        """
        Load trained model from disk.
        
        Args:
            filepath: Path to model file
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
            
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
            
        self.model_type = model_data['model_type']
        self.model = model_data['model']
        self.preprocessor = model_data['preprocessor']
        self.trained = model_data['trained']
        
        logger.info(f"Model loaded from {filepath}")
        
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance (for models that support it).
        
        Returns:
            Dictionary of feature names and importance scores, or None
        """
        if self.model_type == 'linear' and self.model:
            model = self.model['model']
            features = self.model['features']
            
            importance = dict(zip(features, np.abs(model.coef_)))
            # Normalize to sum to 1
            total = sum(importance.values())
            importance = {k: v/total for k, v in importance.items()}
            
            return importance
            
        return None
