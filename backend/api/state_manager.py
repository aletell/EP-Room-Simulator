"""
State management interface for inspecting and modifying simulation state.

This module provides the StateManager class which allows inspection and
modification of simulation state and variables during runtime.
"""

import logging
from typing import Dict, Any, Optional, List
import requests

from .exceptions import (
    SimulationAPIError,
    SimulationNotFoundError,
    InvalidStateError,
    InvalidParameterError
)

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages simulation state and provides methods to inspect and modify
    internal variables during simulation execution.
    
    Note: This requires backend support for state inspection and modification.
    Some features may not be available until backend endpoints are implemented.
    """
    
    def __init__(self, base_url: str = 'http://localhost:5000', api_key: Optional[str] = None):
        """
        Initialize state manager.
        
        Args:
            base_url: Base URL of the backend API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
            
    def get_current_timestep(self, sim_id: str) -> int:
        """
        Get current simulation timestep.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            Current timestep number
            
        Raises:
            SimulationNotFoundError: If simulation doesn't exist
            SimulationAPIError: If request fails
        """
        state = self._get_state(sim_id)
        return state.get('current_timestep', 0)
        
    def get_zone_temperature(self, sim_id: str, zone_name: str) -> float:
        """
        Get current temperature for a zone.
        
        Args:
            sim_id: Simulation identifier
            zone_name: Name of the zone
            
        Returns:
            Current temperature in Celsius
            
        Raises:
            SimulationNotFoundError: If simulation doesn't exist
            InvalidParameterError: If zone doesn't exist
            SimulationAPIError: If request fails
        """
        variables = self._get_variables(sim_id)
        temp_key = f"{zone_name}_temperature"
        
        if temp_key not in variables:
            raise InvalidParameterError(f"Zone {zone_name} not found")
            
        return variables[temp_key]
        
    def get_zone_humidity(self, sim_id: str, zone_name: str) -> float:
        """
        Get current relative humidity for a zone.
        
        Args:
            sim_id: Simulation identifier
            zone_name: Name of the zone
            
        Returns:
            Current relative humidity (0-100%)
        """
        variables = self._get_variables(sim_id)
        humidity_key = f"{zone_name}_humidity"
        
        if humidity_key not in variables:
            raise InvalidParameterError(f"Zone {zone_name} not found")
            
        return variables[humidity_key]
        
    def get_zone_co2(self, sim_id: str, zone_name: str) -> float:
        """
        Get current CO2 level for a zone.
        
        Args:
            sim_id: Simulation identifier
            zone_name: Name of the zone
            
        Returns:
            Current CO2 level in ppm
        """
        variables = self._get_variables(sim_id)
        co2_key = f"{zone_name}_co2"
        
        if co2_key not in variables:
            raise InvalidParameterError(f"Zone {zone_name} not found")
            
        return variables[co2_key]
        
    def set_occupancy(self, sim_id: str, zone_name: str, occupant_count: int) -> None:
        """
        Override occupancy count for a zone.
        
        Args:
            sim_id: Simulation identifier
            zone_name: Name of the zone
            occupant_count: Number of occupants
            
        Raises:
            InvalidParameterError: If parameters are invalid
            SimulationAPIError: If request fails
        """
        if occupant_count < 0:
            raise InvalidParameterError("Occupant count must be non-negative")
            
        self._set_variable(sim_id, f"{zone_name}_occupancy", occupant_count)
        logger.info(f"Set occupancy for {zone_name} to {occupant_count}")
        
    def set_window_state(self, sim_id: str, window_name: str, is_open: bool) -> None:
        """
        Override window open/closed state.
        
        Args:
            sim_id: Simulation identifier
            window_name: Name of the window
            is_open: True if window should be open, False if closed
            
        Raises:
            SimulationAPIError: If request fails
        """
        state_value = 1.0 if is_open else 0.0
        self._set_variable(sim_id, f"{window_name}_opening", state_value)
        logger.info(f"Set window {window_name} to {'open' if is_open else 'closed'}")
        
    def set_infiltration_rate(self, sim_id: str, zone_name: str, rate: float) -> None:
        """
        Override infiltration rate for a zone.
        
        Args:
            sim_id: Simulation identifier
            zone_name: Name of the zone
            rate: Infiltration rate (m³/s)
            
        Raises:
            InvalidParameterError: If rate is invalid
            SimulationAPIError: If request fails
        """
        if rate < 0:
            raise InvalidParameterError("Infiltration rate must be non-negative")
            
        self._set_variable(sim_id, f"{zone_name}_infiltration", rate)
        logger.info(f"Set infiltration rate for {zone_name} to {rate}")
        
    def get_all_variables(self, sim_id: str) -> Dict[str, Any]:
        """
        Get dictionary of all available variables and their current values.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            Dictionary mapping variable names to values
            
        Raises:
            SimulationNotFoundError: If simulation doesn't exist
            SimulationAPIError: If request fails
        """
        return self._get_variables(sim_id)
        
    def set_variable(self, sim_id: str, variable_name: str, value: Any) -> None:
        """
        Set any EnergyPlus variable by name.
        
        Args:
            sim_id: Simulation identifier
            variable_name: Name of the variable
            value: Value to set
            
        Raises:
            InvalidParameterError: If variable name is invalid
            SimulationAPIError: If request fails
        """
        self._set_variable(sim_id, variable_name, value)
        logger.info(f"Set variable {variable_name} to {value}")
        
    def get_variable(self, sim_id: str, variable_name: str) -> Any:
        """
        Get value of a specific variable.
        
        Args:
            sim_id: Simulation identifier
            variable_name: Name of the variable
            
        Returns:
            Variable value
            
        Raises:
            InvalidParameterError: If variable name is invalid
            SimulationAPIError: If request fails
        """
        variables = self._get_variables(sim_id)
        
        if variable_name not in variables:
            raise InvalidParameterError(f"Variable {variable_name} not found")
            
        return variables[variable_name]
        
    def list_zones(self, sim_id: str) -> List[str]:
        """
        List all zones in the simulation.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            List of zone names
        """
        state = self._get_state(sim_id)
        return state.get('zones', [])
        
    def _get_state(self, sim_id: str) -> Dict[str, Any]:
        """
        Internal method to get simulation state from backend.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            State dictionary
            
        Raises:
            SimulationNotFoundError: If simulation doesn't exist
            SimulationAPIError: If request fails
        """
        try:
            # This endpoint needs to be implemented in the backend
            response = self.session.get(f"{self.base_url}/simulation/{sim_id}/state")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise SimulationNotFoundError(f"Simulation {sim_id} not found")
            elif e.response.status_code == 501:
                # Not implemented yet
                logger.warning("State inspection endpoint not yet implemented in backend")
                return {}
            raise SimulationAPIError(f"Failed to get simulation state: {e}")
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to get simulation state: {e}")
            
    def _get_variables(self, sim_id: str) -> Dict[str, Any]:
        """
        Internal method to get all variables from backend.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            Dictionary of variables
            
        Raises:
            SimulationAPIError: If request fails
        """
        try:
            # This endpoint needs to be implemented in the backend
            response = self.session.get(f"{self.base_url}/simulation/{sim_id}/variables")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 501:
                # Not implemented yet
                logger.warning("Variable inspection endpoint not yet implemented in backend")
                return {}
            raise SimulationAPIError(f"Failed to get variables: {e}")
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to get variables: {e}")
            
    def _set_variable(self, sim_id: str, variable_name: str, value: Any) -> None:
        """
        Internal method to set a variable via backend.
        
        Args:
            sim_id: Simulation identifier
            variable_name: Name of the variable
            value: Value to set
            
        Raises:
            SimulationAPIError: If request fails
        """
        try:
            # This endpoint needs to be implemented in the backend
            response = self.session.post(
                f"{self.base_url}/simulation/{sim_id}/variables/{variable_name}",
                json={'value': value}
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 501:
                # Not implemented yet
                logger.warning("Variable modification endpoint not yet implemented in backend")
                logger.warning(f"Would set {variable_name} to {value} for simulation {sim_id}")
                return
            raise SimulationAPIError(f"Failed to set variable: {e}")
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to set variable: {e}")
