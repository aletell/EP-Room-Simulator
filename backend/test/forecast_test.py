"""
Unit tests for the occupancy forecasting module.

Tests OccupancyForecaster and DataPreprocessor functionality.
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from forecast.occupancy_forecaster import OccupancyForecaster
from forecast.data_preprocessor import DataPreprocessor


class TestDataPreprocessor(unittest.TestCase):
    """Test cases for DataPreprocessor."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample data
        timestamps = pd.date_range(start='2024-01-01', end='2024-01-07', freq='1H')
        self.sample_data = pd.DataFrame({
            'timestamp': timestamps,
            'occupancy': np.random.randint(0, 20, size=len(timestamps))
        })
        self.preprocessor = DataPreprocessor()
    
    def test_clean_data(self):
        """Test data cleaning."""
        # Add some problematic data
        dirty_data = self.sample_data.copy()
        dirty_data.loc[0, 'occupancy'] = np.nan
        dirty_data.loc[1, 'occupancy'] = -5
        
        cleaned = self.preprocessor.clean_data(dirty_data)
        
        # Check that NaN was filled
        self.assertFalse(cleaned['occupancy'].isna().any())
        
        # Check that negative values were removed
        self.assertTrue((cleaned['occupancy'] >= 0).all())
    
    def test_extract_temporal_features(self):
        """Test temporal feature extraction."""
        featured_data = self.preprocessor.extract_temporal_features(self.sample_data)
        
        # Check that features were added
        expected_features = ['hour', 'day_of_week', 'month', 'is_weekend', 
                           'season', 'hour_sin', 'hour_cos']
        for feature in expected_features:
            self.assertIn(feature, featured_data.columns)
        
        # Check value ranges
        self.assertTrue((featured_data['hour'] >= 0).all())
        self.assertTrue((featured_data['hour'] <= 23).all())
        self.assertTrue((featured_data['day_of_week'] >= 0).all())
        self.assertTrue((featured_data['day_of_week'] <= 6).all())
        self.assertTrue(featured_data['is_weekend'].isin([0, 1]).all())
    
    def test_add_lag_features(self):
        """Test lag feature creation."""
        lagged_data = self.preprocessor.add_lag_features(
            self.sample_data, 
            lag_periods=[1, 2]
        )
        
        # Check that lag columns were created
        self.assertIn('occupancy_lag_1', lagged_data.columns)
        self.assertIn('occupancy_lag_2', lagged_data.columns)
        
        # Check that data was shifted correctly
        self.assertTrue(len(lagged_data) < len(self.sample_data))  # NaNs dropped
    
    def test_train_test_split(self):
        """Test data splitting."""
        train, test = self.preprocessor.train_test_split(
            self.sample_data, 
            test_size=0.2
        )
        
        # Check sizes
        total_size = len(train) + len(test)
        self.assertEqual(total_size, len(self.sample_data))
        
        # Check that test is approximately 20%
        test_ratio = len(test) / len(self.sample_data)
        self.assertAlmostEqual(test_ratio, 0.2, places=1)


class TestOccupancyForecaster(unittest.TestCase):
    """Test cases for OccupancyForecaster."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample historical data with realistic pattern
        timestamps = pd.date_range(start='2024-01-01', end='2024-01-31', freq='1H')
        occupancy = []
        
        for ts in timestamps:
            hour = ts.hour
            day_of_week = ts.dayofweek
            
            # Simple pattern: high during work hours on weekdays
            if day_of_week < 5 and 9 <= hour < 17:
                occ = 15 + np.random.normal(0, 2)
            else:
                occ = np.random.normal(0, 1)
            
            occupancy.append(max(0, occ))
        
        self.historical_data = pd.DataFrame({
            'timestamp': timestamps,
            'occupancy': occupancy
        })
    
    def test_simple_model_training(self):
        """Test simple model training."""
        forecaster = OccupancyForecaster(model_type='simple')
        
        # Should not raise error
        forecaster.train(self.historical_data)
        
        self.assertTrue(forecaster.trained)
        self.assertIsNotNone(forecaster.model)
    
    def test_average_model_training(self):
        """Test average model training."""
        forecaster = OccupancyForecaster(model_type='average')
        forecaster.train(self.historical_data)
        
        self.assertTrue(forecaster.trained)
        self.assertIsNotNone(forecaster.model)
    
    def test_linear_model_training(self):
        """Test linear model training."""
        forecaster = OccupancyForecaster(model_type='linear')
        forecaster.train(self.historical_data)
        
        self.assertTrue(forecaster.trained)
        self.assertIsNotNone(forecaster.model)
    
    def test_prediction(self):
        """Test forecast generation."""
        forecaster = OccupancyForecaster(model_type='simple')
        forecaster.train(self.historical_data)
        
        # Generate forecast
        forecast = forecaster.predict(
            start_date='2024-02-01',
            end_date='2024-02-07',
            interval='1H'
        )
        
        # Check output format
        self.assertIsInstance(forecast, pd.DataFrame)
        self.assertIn('timestamp', forecast.columns)
        self.assertIn('occupancy', forecast.columns)
        
        # Check that all occupancy values are non-negative
        self.assertTrue((forecast['occupancy'] >= 0).all())
        
        # Check number of data points (7 days * 24 hours + 1)
        expected_points = 7 * 24 + 1
        self.assertEqual(len(forecast), expected_points)
    
    def test_prediction_without_training(self):
        """Test that prediction without training raises error."""
        forecaster = OccupancyForecaster(model_type='simple')
        
        with self.assertRaises(ValueError):
            forecaster.predict('2024-02-01', '2024-02-07')
    
    def test_prediction_with_confidence(self):
        """Test forecast with confidence intervals."""
        forecaster = OccupancyForecaster(model_type='simple')
        forecaster.train(self.historical_data)
        
        forecast = forecaster.predict_with_confidence(
            start_date='2024-02-01',
            end_date='2024-02-02',
            interval='1H'
        )
        
        # Check that confidence bounds exist
        self.assertIn('lower_bound', forecast.columns)
        self.assertIn('upper_bound', forecast.columns)
        
        # Check that bounds make sense
        self.assertTrue((forecast['lower_bound'] <= forecast['occupancy']).all())
        self.assertTrue((forecast['occupancy'] <= forecast['upper_bound']).all())
    
    def test_model_evaluation(self):
        """Test model evaluation on test data."""
        forecaster = OccupancyForecaster(model_type='simple')
        forecaster.train(self.historical_data)
        
        # Use last week as test data
        test_data = self.historical_data[self.historical_data['timestamp'] >= '2024-01-24'].copy()
        
        metrics = forecaster.evaluate(test_data)
        
        # Check that metrics are returned
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('r2_score', metrics)
        
        # Check that metrics are reasonable
        self.assertTrue(metrics['rmse'] >= 0)
        self.assertTrue(metrics['mae'] >= 0)
    
    def test_save_and_load_model(self):
        """Test model persistence."""
        forecaster = OccupancyForecaster(model_type='simple')
        forecaster.train(self.historical_data)
        
        # Save model
        model_path = 'tmp/test_forecaster.pkl'
        os.makedirs('tmp', exist_ok=True)
        forecaster.save_model(model_path)
        
        try:
            # Load model
            new_forecaster = OccupancyForecaster()
            new_forecaster.load_model(model_path)
            
            self.assertTrue(new_forecaster.trained)
            self.assertEqual(new_forecaster.model_type, 'simple')
            
            # Test that loaded model can predict
            forecast = new_forecaster.predict('2024-02-01', '2024-02-02')
            self.assertIsNotNone(forecast)
        finally:
            # Clean up
            if os.path.exists(model_path):
                os.remove(model_path)
    
    def test_different_intervals(self):
        """Test forecasting with different time intervals."""
        forecaster = OccupancyForecaster(model_type='simple')
        forecaster.train(self.historical_data)
        
        # Test different intervals
        intervals = ['15min', '30min', '1H']
        expected_points = {
            '15min': 24 * 4 + 1,  # 24 hours * 4 per hour + 1
            '30min': 24 * 2 + 1,  # 24 hours * 2 per hour + 1
            '1H': 24 + 1           # 24 hours + 1
        }
        
        for interval in intervals:
            forecast = forecaster.predict(
                start_date='2024-02-01',
                end_date='2024-02-01',
                interval=interval
            )
            self.assertEqual(len(forecast), expected_points[interval])


if __name__ == '__main__':
    unittest.main()
