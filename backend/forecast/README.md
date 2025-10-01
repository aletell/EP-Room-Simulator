# Occupancy Forecasting Module

This module provides machine learning-based occupancy forecasting capabilities for the EP-Room-Simulator.

## Overview

The forecasting module allows you to:
- Train models on historical occupancy data
- Generate future occupancy predictions
- Evaluate model performance
- Create forecasts with confidence intervals
- Save and load trained models

## Quick Start

### Basic Usage

```python
from backend.forecast import OccupancyForecaster
import pandas as pd

# Load historical data
historical_data = pd.read_csv('occupancy_history.csv')

# Create and train forecaster
forecaster = OccupancyForecaster(model_type='linear')
forecaster.train(historical_data)

# Generate forecast
forecast = forecaster.predict(
    start_date='2024-02-01',
    end_date='2024-02-29',
    interval='15min'
)

# Save forecast
forecast.to_csv('february_forecast.csv', index=False)
```

## Supported Models

### 1. Simple Pattern Model (`model_type='simple'`)
- **How it works**: Learns average occupancy patterns by hour and day of week
- **Best for**: Regular, predictable schedules
- **Pros**: Fast, interpretable, no external dependencies
- **Cons**: Cannot capture complex patterns or trends

### 2. Hourly Average Model (`model_type='average'`)
- **How it works**: Uses average occupancy for each hour, regardless of day
- **Best for**: Very consistent daily patterns
- **Pros**: Very fast, minimal data requirements
- **Cons**: Ignores day-of-week variations

### 3. Linear Regression Model (`model_type='linear'`)
- **How it works**: Linear regression with temporal features
- **Best for**: Patterns with multiple influencing factors
- **Pros**: Handles multiple features, provides feature importance
- **Cons**: Assumes linear relationships
- **Requirements**: scikit-learn

### Future Models (Planned)

#### LSTM Model (`model_type='lstm'`)
- **How it works**: Long Short-Term Memory neural network
- **Best for**: Complex temporal dependencies
- **Requirements**: TensorFlow/Keras

#### Prophet Model (`model_type='prophet'`)
- **How it works**: Facebook's Prophet forecasting library
- **Best for**: Seasonal patterns and holidays
- **Requirements**: prophet library

## Data Format

### Input Data Requirements

Your historical data should be a pandas DataFrame with at least these columns:

```python
# Required columns:
- timestamp: datetime or string in 'YYYY-MM-DD HH:MM:SS' format
- occupancy: numeric, number of occupants

# Example:
   timestamp              occupancy
0  2024-01-01 00:00:00    0
1  2024-01-01 00:15:00    0
2  2024-01-01 08:00:00    5
3  2024-01-01 09:00:00    15
```

### Output Format

Forecasts are returned as pandas DataFrames:

```python
# Basic forecast:
   timestamp              occupancy
0  2024-02-01 00:00:00    0.2
1  2024-02-01 00:15:00    0.1
2  2024-02-01 08:00:00    5.3

# Forecast with confidence intervals:
   timestamp              occupancy  lower_bound  upper_bound
0  2024-02-01 00:00:00    0.2        0.0          1.5
1  2024-02-01 00:15:00    0.1        0.0          1.3
```

## API Reference

### OccupancyForecaster

Main forecasting class.

#### Methods

##### `__init__(model_type='simple')`
Initialize forecaster with specified model type.

```python
forecaster = OccupancyForecaster(model_type='linear')
```

##### `train(historical_data, features=None)`
Train the forecasting model.

```python
forecaster.train(historical_data)
```

**Parameters:**
- `historical_data`: DataFrame with 'timestamp' and 'occupancy' columns
- `features`: Optional list of additional feature columns

##### `predict(start_date, end_date, interval='15min')`
Generate occupancy forecast.

```python
forecast = forecaster.predict(
    start_date='2024-02-01',
    end_date='2024-02-29',
    interval='15min'
)
```

**Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `interval`: Time interval ('15min', '30min', '1H', etc.)

**Returns:** DataFrame with predicted occupancy

##### `predict_with_confidence(start_date, end_date, interval='15min')`
Generate forecast with confidence intervals.

```python
forecast = forecaster.predict_with_confidence(
    start_date='2024-02-01',
    end_date='2024-02-29'
)
```

**Returns:** DataFrame with 'occupancy', 'lower_bound', 'upper_bound'

##### `evaluate(test_data)`
Evaluate model performance on test data.

```python
metrics = forecaster.evaluate(test_data)
print(f"RMSE: {metrics['rmse']:.2f}")
print(f"MAE: {metrics['mae']:.2f}")
```

**Returns:** Dictionary with metrics (RMSE, MAE, R², etc.)

##### `save_model(filepath)`
Save trained model to disk.

```python
forecaster.save_model('models/my_forecaster.pkl')
```

##### `load_model(filepath)`
Load trained model from disk.

```python
forecaster = OccupancyForecaster()
forecaster.load_model('models/my_forecaster.pkl')
```

### DataPreprocessor

Data preprocessing utilities.

```python
from backend.forecast import DataPreprocessor

preprocessor = DataPreprocessor()

# Clean data
clean_data = preprocessor.clean_data(raw_data)

# Extract temporal features
data_with_features = preprocessor.extract_temporal_features(clean_data)

# Add lag features
data_with_lags = preprocessor.add_lag_features(data_with_features)
```

## Examples

### Example 1: Train and Forecast

```python
import pandas as pd
from backend.forecast import OccupancyForecaster

# Load data
data = pd.read_csv('historical_occupancy.csv')

# Train model
forecaster = OccupancyForecaster(model_type='linear')
forecaster.train(data)

# Generate forecast
forecast = forecaster.predict('2024-02-01', '2024-02-07')

# Save results
forecast.to_csv('weekly_forecast.csv', index=False)
```

### Example 2: Model Comparison

```python
from backend.forecast import OccupancyForecaster

# Train multiple models
models = {
    'simple': OccupancyForecaster('simple'),
    'average': OccupancyForecaster('average'),
    'linear': OccupancyForecaster('linear')
}

for name, model in models.items():
    model.train(training_data)
    metrics = model.evaluate(test_data)
    print(f"{name}: RMSE = {metrics['rmse']:.2f}")
```

### Example 3: Use Forecast in Simulation

```python
from backend.forecast import OccupancyForecaster
from backend.api import SimulationAPI, SimulationConfig

# Generate forecast
forecaster = OccupancyForecaster()
forecaster.load_model('models/trained_model.pkl')
forecast = forecaster.predict('2024-02-01', '2024-02-29')

# Save forecast as occupancy file
forecast.to_csv('occupancy_forecast.csv', index=False)

# Use in simulation
api = SimulationAPI()
config = (SimulationConfig()
    .with_idf_file('models/office.idf')
    .with_epw_file('weather/chicago.epw')
    .with_occupancy_schedule('occupancy_forecast.csv')
    .build())

sim = api.create_simulation('Forecast-based Simulation')
sim.configure(config)
sim.start()
```

## Model Selection Guide

Choose a model based on your data and requirements:

| Scenario | Recommended Model |
|----------|------------------|
| Regular office hours, consistent schedule | Simple Pattern |
| Limited historical data | Hourly Average |
| Multiple influencing factors | Linear Regression |
| Complex patterns with trends | LSTM (planned) |
| Strong seasonal effects, holidays | Prophet (planned) |

## Performance Tips

1. **Training Data**: Provide at least 1 month of historical data for reliable patterns
2. **Data Quality**: Clean data with `DataPreprocessor` before training
3. **Interval**: Use 15-minute intervals for good balance of detail and efficiency
4. **Model Selection**: Start with simple models and increase complexity if needed
5. **Validation**: Always evaluate on held-out test data

## Troubleshooting

### Poor Forecast Accuracy
- **Check data quality**: Ensure no missing values or outliers
- **Increase training data**: More historical data improves patterns
- **Try different model**: Some patterns require more complex models
- **Verify time alignment**: Ensure timestamps are correctly formatted

### Memory Issues
- **Reduce forecast period**: Generate forecasts for shorter periods
- **Increase interval**: Use 30min or 1H instead of 15min
- **Downsample training data**: Use representative subset

### Import Errors
```python
ModuleNotFoundError: No module named 'sklearn'
```
**Solution:** Install required dependencies:
```bash
pip install scikit-learn pandas numpy
```

## Integration with Simulation

The forecast module integrates seamlessly with the simulation API:

1. **Generate Forecast**: Create occupancy predictions
2. **Save as CSV**: Export in the required format
3. **Use in Simulation**: Load as occupancy schedule

See `examples/example_04_occupancy_forecasting.py` for a complete workflow.

## Future Enhancements

Planned features:
- LSTM and Prophet model implementations
- Automatic model selection based on data
- Online learning for model updates
- Multi-zone forecasting
- External factors integration (weather, events)
- Real-time forecast adjustments

## Contributing

To contribute new models:
1. Add model implementation to `models/` directory
2. Update `OccupancyForecaster.SUPPORTED_MODELS`
3. Implement `_train_<model>()` and `_predict_<model>()` methods
4. Add tests and documentation
5. Submit pull request

## License

This module is part of the EP-Room-Simulator project and follows the same license.
