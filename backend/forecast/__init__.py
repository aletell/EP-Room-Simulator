"""
Occupancy Forecasting Module

This package provides machine learning-based occupancy forecasting capabilities
for the EP-Room-Simulator.

Main classes:
    - OccupancyForecaster: Main forecasting interface
    - DataPreprocessor: Data preprocessing utilities
    - Various model implementations (LSTM, Prophet, etc.)
"""

from .occupancy_forecaster import OccupancyForecaster
from .data_preprocessor import DataPreprocessor

__version__ = '0.1.0'
__all__ = [
    'OccupancyForecaster',
    'DataPreprocessor'
]
