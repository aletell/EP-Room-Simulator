"""
Example 4: Occupancy Forecasting

This example demonstrates how to use the occupancy forecasting module
to predict future occupancy patterns.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from forecast import OccupancyForecaster, DataPreprocessor


def generate_sample_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Generate sample occupancy data for demonstration.
    
    Simulates a typical office occupancy pattern with:
    - High occupancy during work hours (9 AM - 5 PM)
    - Low/zero occupancy outside work hours
    - Lower occupancy on weekends
    - Some random variation
    """
    print("Generating sample occupancy data...")
    
    timestamps = pd.date_range(start=start_date, end=end_date, freq='15min')
    data = []
    
    for ts in timestamps:
        hour = ts.hour
        day_of_week = ts.dayofweek
        
        # Base occupancy pattern
        if day_of_week < 5:  # Weekday
            if 9 <= hour < 17:  # Work hours
                base_occupancy = 15 + 5 * np.sin((hour - 9) * np.pi / 8)
            elif 7 <= hour < 9:  # Morning arrival
                base_occupancy = (hour - 7) * 7.5
            elif 17 <= hour < 19:  # Evening departure
                base_occupancy = (19 - hour) * 7.5
            else:
                base_occupancy = 0
        else:  # Weekend
            if 10 <= hour < 14:  # Minimal weekend activity
                base_occupancy = 2 + np.random.random() * 2
            else:
                base_occupancy = 0
                
        # Add random variation
        occupancy = max(0, base_occupancy + np.random.normal(0, 2))
        
        data.append({
            'timestamp': ts,
            'occupancy': round(occupancy, 1)
        })
        
    df = pd.DataFrame(data)
    print(f"Generated {len(df)} data points")
    return df


def main():
    """Run occupancy forecasting example."""
    
    print("EP-Room-Simulator - Occupancy Forecasting Example")
    print("=" * 60)
    
    # Generate sample historical data (1 month)
    print("\n1. Preparing historical data...")
    historical_start = '2024-01-01'
    historical_end = '2024-01-31'
    historical_data = generate_sample_data(historical_start, historical_end)
    print(f"   ✓ Historical data: {len(historical_data)} records")
    
    # Save sample data
    historical_data.to_csv('sample_occupancy_data.csv', index=False)
    print("   ✓ Saved to sample_occupancy_data.csv")
    
    # Show sample statistics
    print(f"\n   Statistics:")
    print(f"   - Average occupancy: {historical_data['occupancy'].mean():.1f}")
    print(f"   - Max occupancy: {historical_data['occupancy'].max():.1f}")
    print(f"   - Std deviation: {historical_data['occupancy'].std():.1f}")
    
    # Train forecasting model
    print("\n2. Training forecasting models...")
    
    models = {
        'Simple Pattern': OccupancyForecaster(model_type='simple'),
        'Hourly Average': OccupancyForecaster(model_type='average'),
        'Linear Regression': OccupancyForecaster(model_type='linear')
    }
    
    for name, forecaster in models.items():
        forecaster.train(historical_data)
        print(f"   ✓ Trained {name} model")
        
    # Generate forecast for next week
    print("\n3. Generating forecasts...")
    forecast_start = '2024-02-01'
    forecast_end = '2024-02-07'
    
    forecasts = {}
    for name, forecaster in models.items():
        forecast = forecaster.predict(forecast_start, forecast_end, interval='15min')
        forecasts[name] = forecast
        print(f"   ✓ Generated forecast with {name}: {len(forecast)} data points")
        
    # Generate forecast with confidence intervals
    print("\n4. Generating forecast with confidence intervals...")
    best_model = models['Linear Regression']
    forecast_with_conf = best_model.predict_with_confidence(
        forecast_start, forecast_end, interval='15min'
    )
    print(f"   ✓ Generated forecast with confidence bounds")
    
    # Save forecasts
    print("\n5. Saving forecasts...")
    for name, forecast in forecasts.items():
        filename = f"forecast_{name.replace(' ', '_').lower()}.csv"
        forecast.to_csv(filename, index=False)
        print(f"   ✓ Saved {filename}")
        
    forecast_with_conf.to_csv('forecast_with_confidence.csv', index=False)
    print("   ✓ Saved forecast_with_confidence.csv")
    
    # Evaluate models on test data
    print("\n6. Evaluating models...")
    test_start = '2024-01-25'
    test_end = '2024-01-31'
    test_data = historical_data[
        (historical_data['timestamp'] >= test_start) &
        (historical_data['timestamp'] <= test_end)
    ].copy()
    
    print(f"\n   Test data: {len(test_data)} records")
    print("   " + "-" * 50)
    
    for name, forecaster in models.items():
        metrics = forecaster.evaluate(test_data)
        print(f"\n   {name}:")
        print(f"   - RMSE: {metrics['rmse']:.2f} persons")
        print(f"   - MAE:  {metrics['mae']:.2f} persons")
        print(f"   - R²:   {metrics['r2_score']:.3f}")
        
    # Save model
    print("\n7. Saving trained model...")
    best_model.save_model('models/occupancy_forecaster.pkl')
    print("   ✓ Model saved to models/occupancy_forecaster.pkl")
    
    # Display summary
    print("\n" + "=" * 60)
    print("Occupancy forecasting example completed!")
    print("\nGenerated files:")
    print("  - sample_occupancy_data.csv")
    print("  - forecast_simple_pattern.csv")
    print("  - forecast_hourly_average.csv")
    print("  - forecast_linear_regression.csv")
    print("  - forecast_with_confidence.csv")
    print("  - models/occupancy_forecaster.pkl")
    
    # Show sample forecast
    print("\nSample forecast (first 24 hours):")
    print(forecast_with_conf[['timestamp', 'occupancy', 'lower_bound', 'upper_bound']].head(24*4).to_string(index=False))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
