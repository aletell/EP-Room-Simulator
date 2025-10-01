"""
Fluent configuration builder for simulations.

This module provides the SimulationConfig class which allows building
simulation configurations using a fluent API pattern.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from .exceptions import InvalidParameterError

logger = logging.getLogger(__name__)


class SimulationConfig:
    """
    Fluent API for building simulation configurations.
    
    Example:
        config = (SimulationConfig()
            .with_idf_file('models/office.idf')
            .with_epw_file('weather/chicago.epw')
            .with_room_dimensions(5.0, 6.0, 3.0)
            .build())
    """
    
    def __init__(self):
        """Initialize empty configuration."""
        self._config: Dict[str, Any] = {}
        
    def with_idf_file(self, filepath: str) -> 'SimulationConfig':
        """
        Set IDF file path.
        
        Args:
            filepath: Path to IDF file
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If file doesn't exist
        """
        import os
        if not os.path.exists(filepath):
            raise InvalidParameterError(f"IDF file not found: {filepath}")
            
        self._config['idf_file'] = filepath
        return self
        
    def with_epw_file(self, filepath: str) -> 'SimulationConfig':
        """
        Set EPW file path.
        
        Args:
            filepath: Path to EPW file
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If file doesn't exist
        """
        import os
        if not os.path.exists(filepath):
            raise InvalidParameterError(f"EPW file not found: {filepath}")
            
        self._config['epw_file'] = filepath
        return self
        
    def with_room_dimensions(self, width: float, length: float, height: float) -> 'SimulationConfig':
        """
        Set room dimensions.
        
        Args:
            width: Room width in meters
            length: Room length in meters
            height: Room height in meters
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If dimensions are invalid
        """
        if width <= 0 or length <= 0 or height <= 0:
            raise InvalidParameterError("Room dimensions must be positive")
            
        self._config['room_dimensions'] = {
            'width': width,
            'length': length,
            'height': height
        }
        return self
        
    def with_occupancy_schedule(self, schedule_data: Any) -> 'SimulationConfig':
        """
        Set occupancy schedule.
        
        Args:
            schedule_data: Path to CSV file or DataFrame with occupancy data
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If schedule data is invalid
        """
        import pandas as pd
        
        if isinstance(schedule_data, str):
            # Assume it's a file path
            import os
            if not os.path.exists(schedule_data):
                raise InvalidParameterError(f"Occupancy file not found: {schedule_data}")
        elif not isinstance(schedule_data, pd.DataFrame):
            raise InvalidParameterError("schedule_data must be a file path or DataFrame")
            
        self._config['occupancy_schedule'] = schedule_data
        return self
        
    def with_forecasted_occupancy(self, forecast_data: Any) -> 'SimulationConfig':
        """
        Set forecasted occupancy schedule.
        
        Args:
            forecast_data: DataFrame with forecasted occupancy
            
        Returns:
            Self for method chaining
        """
        import pandas as pd
        
        if not isinstance(forecast_data, pd.DataFrame):
            raise InvalidParameterError("forecast_data must be a DataFrame")
            
        self._config['occupancy_schedule'] = forecast_data
        self._config['is_forecast'] = True
        return self
        
    def with_simulation_period(self, start_date: Any, end_date: Any) -> 'SimulationConfig':
        """
        Set simulation period.
        
        Args:
            start_date: Start date (string 'YYYY-MM-DD' or date object)
            end_date: End date (string 'YYYY-MM-DD' or date object)
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If dates are invalid
        """
        # Convert to date objects if strings
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                raise InvalidParameterError(f"Invalid start date format: {start_date}")
                
        if isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                raise InvalidParameterError(f"Invalid end date format: {end_date}")
                
        if start_date >= end_date:
            raise InvalidParameterError("Start date must be before end date")
            
        self._config['simulation_period'] = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        return self
        
    def with_timestep(self, minutes: int) -> 'SimulationConfig':
        """
        Set timestep in minutes.
        
        Args:
            minutes: Timestep duration (must divide evenly into 60)
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If timestep is invalid
        """
        if minutes <= 0:
            raise InvalidParameterError("Timestep must be positive")
            
        if 60 % minutes != 0:
            raise InvalidParameterError("Timestep must divide evenly into 60 minutes")
            
        self._config['timestep'] = minutes
        return self
        
    def with_infiltration_rate(self, rate: float) -> 'SimulationConfig':
        """
        Set infiltration rate.
        
        Args:
            rate: Infiltration rate (m³/s)
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If rate is invalid
        """
        if rate < 0:
            raise InvalidParameterError("Infiltration rate must be non-negative")
            
        self._config['infiltration_rate'] = rate
        return self
        
    def with_orientation(self, degrees: float) -> 'SimulationConfig':
        """
        Set building orientation.
        
        Args:
            degrees: Orientation in degrees (0-360)
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If orientation is invalid
        """
        if degrees < 0 or degrees >= 360:
            raise InvalidParameterError("Orientation must be between 0 and 360 degrees")
            
        self._config['orientation'] = degrees
        return self
        
    def with_zone_name(self, zone_name: str) -> 'SimulationConfig':
        """
        Set zone name for the simulation.
        
        Args:
            zone_name: Name of the zone
            
        Returns:
            Self for method chaining
        """
        if not zone_name:
            raise InvalidParameterError("Zone name cannot be empty")
            
        self._config['zone_name'] = zone_name
        return self
        
    def with_max_occupants(self, count: int) -> 'SimulationConfig':
        """
        Set maximum number of occupants.
        
        Args:
            count: Maximum occupant count
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If count is invalid
        """
        if count < 0:
            raise InvalidParameterError("Maximum occupant count must be non-negative")
            
        self._config['max_occupants'] = count
        return self
        
    def with_co2_generation_rate(self, rate: float) -> 'SimulationConfig':
        """
        Set CO2 generation rate per person.
        
        Args:
            rate: CO2 generation rate (m³/s per person)
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If rate is invalid
        """
        if rate < 0:
            raise InvalidParameterError("CO2 generation rate must be non-negative")
            
        self._config['co2_generation_rate'] = rate
        return self
        
    def with_activity_level(self, level: float) -> 'SimulationConfig':
        """
        Set occupant activity level.
        
        Args:
            level: Activity level in W/person
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidParameterError: If level is invalid
        """
        if level < 0:
            raise InvalidParameterError("Activity level must be non-negative")
            
        self._config['activity_level'] = level
        return self
        
    def with_custom_parameter(self, name: str, value: Any) -> 'SimulationConfig':
        """
        Set a custom parameter.
        
        Args:
            name: Parameter name
            value: Parameter value
            
        Returns:
            Self for method chaining
        """
        if 'custom_parameters' not in self._config:
            self._config['custom_parameters'] = {}
            
        self._config['custom_parameters'][name] = value
        return self
        
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            InvalidParameterError: If configuration is invalid
        """
        # Check required fields
        if 'idf_file' not in self._config:
            raise InvalidParameterError("IDF file is required")
            
        if 'epw_file' not in self._config:
            raise InvalidParameterError("EPW file is required")
            
        # Validate that files still exist
        import os
        if not os.path.exists(self._config['idf_file']):
            raise InvalidParameterError(f"IDF file not found: {self._config['idf_file']}")
            
        if not os.path.exists(self._config['epw_file']):
            raise InvalidParameterError(f"EPW file not found: {self._config['epw_file']}")
            
        return True
        
    def build(self) -> Dict[str, Any]:
        """
        Build and validate configuration.
        
        Returns:
            Configuration dictionary
            
        Raises:
            InvalidParameterError: If configuration is invalid
        """
        self.validate()
        logger.info("Built simulation configuration")
        return self._config.copy()
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary without validation.
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy()
