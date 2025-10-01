"""
Data preprocessing module for occupancy forecasting.

This module provides utilities for cleaning, transforming, and preparing
occupancy data for machine learning models.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Preprocesses occupancy data for machine learning.
    
    Provides methods for cleaning, feature extraction, normalization,
    and sequence creation for time series forecasting.
    """
    
    def __init__(self):
        """Initialize preprocessor."""
        self.scaler = None
        self.feature_columns = None
        
    def clean_data(self, data: pd.DataFrame, 
                   occupancy_col: str = 'occupancy') -> pd.DataFrame:
        """
        Clean occupancy data by handling missing values and outliers.
        
        Args:
            data: DataFrame with occupancy data
            occupancy_col: Name of occupancy column
            
        Returns:
            Cleaned DataFrame
        """
        df = data.copy()
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        # Handle missing values
        if occupancy_col in df.columns:
            # Fill missing occupancy with 0 (assuming room is empty)
            df[occupancy_col] = df[occupancy_col].fillna(0)
            
            # Remove negative values
            df.loc[df[occupancy_col] < 0, occupancy_col] = 0
            
            # Handle outliers using IQR method
            Q1 = df[occupancy_col].quantile(0.25)
            Q3 = df[occupancy_col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Cap outliers
            df.loc[df[occupancy_col] < lower_bound, occupancy_col] = lower_bound
            df.loc[df[occupancy_col] > upper_bound, occupancy_col] = upper_bound
            
        logger.info(f"Cleaned data: {len(df)} records")
        return df
        
    def extract_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract temporal features from timestamps.
        
        Features extracted:
        - Hour of day (0-23)
        - Day of week (0-6, Monday=0)
        - Week of year (1-52)
        - Month (1-12)
        - Is weekend (binary)
        - Is holiday (binary, requires holidays package)
        - Season (0-3: winter, spring, summer, fall)
        
        Args:
            data: DataFrame with 'timestamp' column
            
        Returns:
            DataFrame with added temporal features
        """
        df = data.copy()
        
        if 'timestamp' not in df.columns:
            raise ValueError("DataFrame must have 'timestamp' column")
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Basic temporal features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['week_of_year'] = df['timestamp'].dt.isocalendar().week
        df['month'] = df['timestamp'].dt.month
        df['day_of_month'] = df['timestamp'].dt.day
        
        # Derived features
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Season (Northern hemisphere)
        df['season'] = df['month'].apply(self._get_season)
        
        # Cyclical encoding for periodic features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Try to add holiday information
        try:
            import holidays
            us_holidays = holidays.US(years=df['timestamp'].dt.year.unique())
            df['is_holiday'] = df['timestamp'].dt.date.apply(
                lambda x: 1 if x in us_holidays else 0
            )
        except ImportError:
            logger.warning("holidays package not installed, skipping holiday features")
            df['is_holiday'] = 0
            
        logger.info(f"Extracted temporal features for {len(df)} records")
        return df
        
    @staticmethod
    def _get_season(month: int) -> int:
        """
        Get season from month (Northern hemisphere).
        
        Args:
            month: Month number (1-12)
            
        Returns:
            Season: 0=winter, 1=spring, 2=summer, 3=fall
        """
        if month in [12, 1, 2]:
            return 0  # Winter
        elif month in [3, 4, 5]:
            return 1  # Spring
        elif month in [6, 7, 8]:
            return 2  # Summer
        else:
            return 3  # Fall
            
    def add_lag_features(self, data: pd.DataFrame, 
                        target_col: str = 'occupancy',
                        lag_periods: List[int] = None) -> pd.DataFrame:
        """
        Add lagged values of the target variable as features.
        
        Args:
            data: DataFrame with time series data
            target_col: Name of target column
            lag_periods: List of lag periods to create (default: [1, 2, 3, 24])
            
        Returns:
            DataFrame with lag features
        """
        if lag_periods is None:
            lag_periods = [1, 2, 3, 24]  # Default lags
            
        df = data.copy()
        
        for lag in lag_periods:
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
            
        # Add rolling statistics
        for window in [6, 12, 24]:  # 6, 12, 24 hour windows
            df[f'{target_col}_rolling_mean_{window}'] = (
                df[target_col].rolling(window=window, min_periods=1).mean()
            )
            df[f'{target_col}_rolling_std_{window}'] = (
                df[target_col].rolling(window=window, min_periods=1).std()
            )
            
        # Drop rows with NaN in lag features (from initial lags)
        df = df.dropna()
        
        logger.info(f"Added lag features: {lag_periods}")
        return df
        
    def normalize(self, data: pd.DataFrame, 
                 feature_columns: List[str]) -> pd.DataFrame:
        """
        Normalize features using StandardScaler.
        
        Args:
            data: DataFrame with features
            feature_columns: List of columns to normalize
            
        Returns:
            DataFrame with normalized features
        """
        from sklearn.preprocessing import StandardScaler
        
        df = data.copy()
        
        if self.scaler is None:
            self.scaler = StandardScaler()
            df[feature_columns] = self.scaler.fit_transform(df[feature_columns])
            self.feature_columns = feature_columns
        else:
            df[feature_columns] = self.scaler.transform(df[feature_columns])
            
        logger.info(f"Normalized {len(feature_columns)} features")
        return df
        
    def inverse_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Inverse normalize features.
        
        Args:
            data: DataFrame with normalized features
            
        Returns:
            DataFrame with original scale features
        """
        if self.scaler is None or self.feature_columns is None:
            raise ValueError("Must call normalize() before inverse_transform()")
            
        df = data.copy()
        df[self.feature_columns] = self.scaler.inverse_transform(
            df[self.feature_columns]
        )
        return df
        
    def create_sequences(self, data: pd.DataFrame,
                        target_col: str = 'occupancy',
                        feature_cols: List[str] = None,
                        sequence_length: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create input sequences for LSTM models.
        
        Args:
            data: DataFrame with time series data
            target_col: Name of target column
            feature_cols: List of feature columns to use
            sequence_length: Length of input sequences
            
        Returns:
            Tuple of (X, y) arrays for training
        """
        df = data.copy()
        
        if feature_cols is None:
            # Use all numeric columns except target
            feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns
                          if col != target_col]
            
        X_sequences = []
        y_sequences = []
        
        for i in range(len(df) - sequence_length):
            # Input sequence
            X_sequences.append(df[feature_cols].iloc[i:i+sequence_length].values)
            # Target value (next timestep)
            y_sequences.append(df[target_col].iloc[i+sequence_length])
            
        X = np.array(X_sequences)
        y = np.array(y_sequences)
        
        logger.info(f"Created {len(X)} sequences of length {sequence_length}")
        return X, y
        
    def train_test_split(self, data: pd.DataFrame,
                        test_size: float = 0.2,
                        shuffle: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into train and test sets.
        
        Args:
            data: DataFrame to split
            test_size: Fraction of data for test set
            shuffle: Whether to shuffle data (not recommended for time series)
            
        Returns:
            Tuple of (train_df, test_df)
        """
        if shuffle:
            data = data.sample(frac=1).reset_index(drop=True)
            
        split_idx = int(len(data) * (1 - test_size))
        train_df = data.iloc[:split_idx].copy()
        test_df = data.iloc[split_idx:].copy()
        
        logger.info(f"Split: {len(train_df)} train, {len(test_df)} test")
        return train_df, test_df
        
    def prepare_for_training(self, data: pd.DataFrame,
                            target_col: str = 'occupancy',
                            test_size: float = 0.2) -> dict:
        """
        Complete preprocessing pipeline for training.
        
        Args:
            data: Raw DataFrame with occupancy data
            target_col: Name of target column
            test_size: Fraction for test set
            
        Returns:
            Dictionary with prepared data
        """
        # Clean data
        df = self.clean_data(data, target_col)
        
        # Extract features
        df = self.extract_temporal_features(df)
        
        # Add lag features
        df = self.add_lag_features(df, target_col)
        
        # Split data
        train_df, test_df = self.train_test_split(df, test_size)
        
        # Get feature columns (exclude timestamp and target)
        feature_cols = [col for col in df.columns 
                       if col not in ['timestamp', target_col]]
        
        # Normalize
        train_df = self.normalize(train_df, feature_cols)
        test_df = self.normalize(test_df, feature_cols)
        
        return {
            'train': train_df,
            'test': test_df,
            'feature_columns': feature_cols,
            'target_column': target_col
        }
