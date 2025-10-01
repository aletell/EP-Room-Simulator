"""
EnergyPlus Python API wrapper for runtime control.

This module provides a high-level interface to the EnergyPlus Python API,
enabling runtime state inspection and dynamic parameter modification.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
import sys

logger = logging.getLogger(__name__)

# Check if EnergyPlus Python API is available
try:
    from pyenergyplus.api import EnergyPlusAPI
    ENERGYPLUS_API_AVAILABLE = True
except ImportError:
    ENERGYPLUS_API_AVAILABLE = False
    logger.warning("EnergyPlus Python API not available. Install with: pip install pyenergyplus")


class EnergyPlusRuntime:
    """
    Wrapper for EnergyPlus Python API providing runtime control capabilities.
    
    This class bridges the gap between eppy (IDF manipulation) and the
    EnergyPlus Python API (runtime control), enabling:
    - Real-time state inspection
    - Dynamic parameter modification
    - Custom control logic during simulation
    - Sensor/actuator management
    
    Example:
        runtime = EnergyPlusRuntime()
        
        # Define control logic
        @runtime.on_timestep
        def control_window(state):
            temp = runtime.get_sensor_value('zone_temperature')
            if temp > 26:
                runtime.set_actuator_value('window_opening', 1.0)
        
        # Run simulation with runtime control
        runtime.run_simulation('prepared.idf', 'weather.epw')
    """
    
    def __init__(self):
        """Initialize EnergyPlus runtime wrapper."""
        if not ENERGYPLUS_API_AVAILABLE:
            raise ImportError(
                "EnergyPlus Python API is required for runtime control. "
                "Install with: pip install pyenergyplus"
            )
            
        self.api = EnergyPlusAPI()
        self.state = None
        self.sensors: Dict[str, int] = {}
        self.actuators: Dict[str, int] = {}
        self.meters: Dict[str, int] = {}
        self.callbacks: Dict[str, List[Callable]] = {
            'begin_timestep': [],
            'end_timestep': [],
            'after_new_environment': [],
            'after_init_heat_balance': []
        }
        
    def register_sensor(self, name: str, variable_name: str, key_name: str) -> None:
        """
        Register a sensor for reading values during simulation.
        
        Args:
            name: Friendly name for the sensor
            variable_name: EnergyPlus variable name (e.g., "Zone Mean Air Temperature")
            key_name: Key name (e.g., zone name)
        """
        def setup_handle(state):
            handle = self.api.exchange.get_variable_handle(state, variable_name, key_name)
            if handle == -1:
                logger.warning(f"Sensor '{name}' not found: {variable_name} [{key_name}]")
            else:
                self.sensors[name] = handle
                logger.info(f"Registered sensor: {name}")
                
        self.callbacks['after_new_environment'].append(setup_handle)
        
    def register_actuator(self, name: str, component_type: str, 
                         control_type: str, key_name: str) -> None:
        """
        Register an actuator for modifying values during simulation.
        
        Args:
            name: Friendly name for the actuator
            component_type: Component type (e.g., "AirFlow Network Window/Door Opening")
            control_type: Control type (e.g., "Venting Opening Factor")
            key_name: Key name (e.g., window name)
        """
        def setup_handle(state):
            handle = self.api.exchange.get_actuator_handle(
                state, component_type, key_name, control_type
            )
            if handle == -1:
                logger.warning(f"Actuator '{name}' not found: {component_type} [{key_name}] {control_type}")
            else:
                self.actuators[name] = handle
                logger.info(f"Registered actuator: {name}")
                
        self.callbacks['after_new_environment'].append(setup_handle)
        
    def register_meter(self, name: str, meter_name: str) -> None:
        """
        Register a meter for reading energy consumption.
        
        Args:
            name: Friendly name for the meter
            meter_name: EnergyPlus meter name
        """
        def setup_handle(state):
            handle = self.api.exchange.get_meter_handle(state, meter_name)
            if handle == -1:
                logger.warning(f"Meter '{name}' not found: {meter_name}")
            else:
                self.meters[name] = handle
                logger.info(f"Registered meter: {name}")
                
        self.callbacks['after_new_environment'].append(setup_handle)
        
    def get_sensor_value(self, name: str) -> Optional[float]:
        """
        Get current value of a registered sensor.
        
        Args:
            name: Sensor name
            
        Returns:
            Sensor value or None if not available
        """
        handle = self.sensors.get(name)
        if handle is None or handle == -1:
            return None
        return self.api.exchange.get_variable_value(self.state, handle)
        
    def set_actuator_value(self, name: str, value: float) -> bool:
        """
        Set value of a registered actuator.
        
        Args:
            name: Actuator name
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        handle = self.actuators.get(name)
        if handle is None or handle == -1:
            return False
        self.api.exchange.set_actuator_value(self.state, handle, value)
        return True
        
    def get_meter_value(self, name: str) -> Optional[float]:
        """
        Get current value of a registered meter.
        
        Args:
            name: Meter name
            
        Returns:
            Meter value or None if not available
        """
        handle = self.meters.get(name)
        if handle is None or handle == -1:
            return None
        return self.api.exchange.get_meter_value(self.state, handle)
        
    def on_timestep(self, callback: Callable) -> None:
        """Register callback to run at each timestep."""
        self.callbacks['begin_timestep'].append(callback)
        
    def on_end_timestep(self, callback: Callable) -> None:
        """Register callback to run at end of each timestep."""
        self.callbacks['end_timestep'].append(callback)
        
    def run_simulation(self, idf_path: str, epw_path: str, 
                      output_dir: str = 'output') -> None:
        """
        Run simulation with registered sensors, actuators, and callbacks.
        
        Args:
            idf_path: Path to IDF file
            epw_path: Path to EPW weather file
            output_dir: Output directory for results
        """
        self.state = self.api.state_manager.new_state()
        
        # Register internal callbacks
        def after_new_env(state_arg):
            for cb in self.callbacks['after_new_environment']:
                cb(state_arg)
                
        def begin_timestep(state_arg):
            self.state = state_arg
            for cb in self.callbacks['begin_timestep']:
                try:
                    cb(state_arg)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
                    
        def end_timestep(state_arg):
            for cb in self.callbacks['end_timestep']:
                try:
                    cb(state_arg)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        # Register callbacks with EnergyPlus
        self.api.runtime.callback_after_new_environment_warmup_complete(
            self.state, after_new_env
        )
        self.api.runtime.callback_begin_zone_timestep_after_init_heat_balance(
            self.state, begin_timestep
        )
        self.api.runtime.callback_end_zone_timestep_after_zone_reporting(
            self.state, end_timestep
        )
        
        # Build command line arguments
        args = [
            '-w', epw_path,
            '-d', output_dir,
            idf_path
        ]
        
        logger.info(f"Running EnergyPlus simulation: {idf_path}")
        
        # Run simulation
        exit_code = self.api.runtime.run_energyplus(self.state, args)
        
        if exit_code == 0:
            logger.info("Simulation completed successfully")
        else:
            logger.error(f"Simulation failed with exit code {exit_code}")


class WindowController:
    """
    Advanced window control using EnergyPlus Python API.
    
    Provides sophisticated window control strategies including:
    - Temperature-based control
    - Outdoor conditions consideration
    - Time-of-day scheduling
    - Occupancy-based control
    - Wind speed limits
    """
    
    def __init__(self, runtime: EnergyPlusRuntime):
        """
        Initialize window controller.
        
        Args:
            runtime: EnergyPlus runtime instance
        """
        self.runtime = runtime
        self.config = {
            'temp_threshold_high': 26.0,
            'temp_threshold_low': 20.0,
            'outdoor_temp_min': 10.0,
            'outdoor_temp_max': 28.0,
            'wind_speed_max': 10.0,
            'min_opening': 0.0,
            'max_opening': 1.0
        }
        
    def setup_sensors_actuators(self, zone_name: str, window_name: str) -> None:
        """
        Setup required sensors and actuators for window control.
        
        Args:
            zone_name: Name of the zone
            window_name: Name of the window
        """
        # Sensors
        self.runtime.register_sensor(
            'zone_temp',
            'Zone Mean Air Temperature',
            zone_name
        )
        self.runtime.register_sensor(
            'outdoor_temp',
            'Site Outdoor Air Drybulb Temperature',
            'Environment'
        )
        self.runtime.register_sensor(
            'wind_speed',
            'Site Wind Speed',
            'Environment'
        )
        self.runtime.register_sensor(
            'occupancy',
            'Zone People Occupant Count',
            zone_name
        )
        
        # Actuator
        self.runtime.register_actuator(
            'window_opening',
            'AirFlow Network Window/Door Opening',
            'Venting Opening Factor',
            window_name
        )
        
    def adaptive_control(self, state) -> None:
        """
        Implement adaptive window control logic.
        
        Args:
            state: EnergyPlus state object
        """
        # Get current conditions
        zone_temp = self.runtime.get_sensor_value('zone_temp')
        outdoor_temp = self.runtime.get_sensor_value('outdoor_temp')
        wind_speed = self.runtime.get_sensor_value('wind_speed')
        occupancy = self.runtime.get_sensor_value('occupancy')
        
        if None in [zone_temp, outdoor_temp, wind_speed]:
            return
            
        # Determine window opening
        opening = 0.0
        
        # Check outdoor conditions are suitable
        outdoor_suitable = (
            self.config['outdoor_temp_min'] < outdoor_temp < self.config['outdoor_temp_max']
            and wind_speed < self.config['wind_speed_max']
        )
        
        if not outdoor_suitable:
            opening = 0.0  # Close window if outdoor conditions unsuitable
        elif zone_temp > self.config['temp_threshold_high']:
            # Hot inside
            if outdoor_temp < zone_temp - 2:
                # Cooler outside -> open window
                opening = 1.0
        elif zone_temp < self.config['temp_threshold_low']:
            # Cold inside -> close window
            opening = 0.0
        else:
            # Comfortable range -> partial opening if conditions allow
            if outdoor_suitable and occupancy and occupancy > 0:
                opening = 0.3  # Small opening for fresh air
                
        # Apply limits
        opening = max(self.config['min_opening'], 
                     min(self.config['max_opening'], opening))
        
        # Set window opening
        self.runtime.set_actuator_value('window_opening', opening)


class HVACController:
    """
    HVAC control using EnergyPlus Python API.
    
    Provides dynamic HVAC control including:
    - Setpoint optimization
    - Occupancy-based scheduling
    - Load-based control
    - Energy-efficient operation
    """
    
    def __init__(self, runtime: EnergyPlusRuntime):
        """
        Initialize HVAC controller.
        
        Args:
            runtime: EnergyPlus runtime instance
        """
        self.runtime = runtime
        self.config = {
            'occupied_heating_setpoint': 21.0,
            'occupied_cooling_setpoint': 24.0,
            'unoccupied_heating_setpoint': 18.0,
            'unoccupied_cooling_setpoint': 28.0,
            'occupancy_threshold': 0.5
        }
        
    def setup_sensors_actuators(self, zone_name: str) -> None:
        """
        Setup required sensors and actuators for HVAC control.
        
        Args:
            zone_name: Name of the zone
        """
        # Sensors
        self.runtime.register_sensor(
            'zone_temp',
            'Zone Mean Air Temperature',
            zone_name
        )
        self.runtime.register_sensor(
            'occupancy',
            'Zone People Occupant Count',
            zone_name
        )
        
        # Actuators
        self.runtime.register_actuator(
            'heating_setpoint',
            'Zone Temperature Control',
            'Heating Setpoint',
            zone_name
        )
        self.runtime.register_actuator(
            'cooling_setpoint',
            'Zone Temperature Control',
            'Cooling Setpoint',
            zone_name
        )
        
    def adaptive_control(self, state) -> None:
        """
        Implement adaptive HVAC control logic.
        
        Args:
            state: EnergyPlus state object
        """
        occupancy = self.runtime.get_sensor_value('occupancy')
        
        if occupancy is None:
            return
            
        # Determine if zone is occupied
        is_occupied = occupancy > self.config['occupancy_threshold']
        
        # Set appropriate setpoints
        if is_occupied:
            heating_sp = self.config['occupied_heating_setpoint']
            cooling_sp = self.config['occupied_cooling_setpoint']
        else:
            heating_sp = self.config['unoccupied_heating_setpoint']
            cooling_sp = self.config['unoccupied_cooling_setpoint']
            
        # Apply setpoints
        self.runtime.set_actuator_value('heating_setpoint', heating_sp)
        self.runtime.set_actuator_value('cooling_setpoint', cooling_sp)


def create_runtime_controller(idf_path: str, epw_path: str,
                              zone_name: str = 'ZONE_1',
                              window_name: str = 'WINDOW_1') -> EnergyPlusRuntime:
    """
    Create a configured runtime controller with window and HVAC control.
    
    Args:
        idf_path: Path to IDF file
        epw_path: Path to EPW file
        zone_name: Zone name for control
        window_name: Window name for control
        
    Returns:
        Configured EnergyPlusRuntime instance
        
    Example:
        runtime = create_runtime_controller('model.idf', 'weather.epw')
        runtime.run_simulation('model.idf', 'weather.epw')
    """
    runtime = EnergyPlusRuntime()
    
    # Setup window control
    window_ctrl = WindowController(runtime)
    window_ctrl.setup_sensors_actuators(zone_name, window_name)
    runtime.on_timestep(window_ctrl.adaptive_control)
    
    # Setup HVAC control
    hvac_ctrl = HVACController(runtime)
    hvac_ctrl.setup_sensors_actuators(zone_name)
    runtime.on_timestep(hvac_ctrl.adaptive_control)
    
    return runtime
