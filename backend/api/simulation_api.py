"""
Main API class for programmatic simulation control.

This module provides the SimulationAPI class which serves as the primary
interface for creating, configuring, and controlling simulations.
"""

import json
import time
import logging
from typing import Optional, Dict, Any, List
import requests

from .exceptions import (
    SimulationAPIError,
    SimulationNotFoundError,
    InvalidStateError,
    SimulationExecutionError,
    ConnectionError as APIConnectionError
)

logger = logging.getLogger(__name__)


class Simulation:
    """
    Represents a single simulation instance with methods to control and query it.
    """
    
    def __init__(self, sim_id: str, api_client: 'SimulationAPI'):
        """
        Initialize a Simulation instance.
        
        Args:
            sim_id: Simulation identifier
            api_client: Reference to the API client
        """
        self.sim_id = sim_id
        self._api = api_client
        
    def configure(self, config: Dict[str, Any]) -> 'Simulation':
        """
        Apply configuration to the simulation.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Self for method chaining
        """
        # Apply IDF file if provided
        if 'idf_file' in config:
            self._api.set_idf_file(self.sim_id, config['idf_file'])
            
        # Apply EPW file if provided
        if 'epw_file' in config:
            self._api.set_epw_file(self.sim_id, config['epw_file'])
            
        # Apply room parameters if provided
        if 'room_dimensions' in config:
            self._api.set_room_dimensions(
                self.sim_id, 
                **config['room_dimensions']
            )
            
        # Apply occupancy if provided
        if 'occupancy_schedule' in config:
            self._api.set_occupancy_schedule(
                self.sim_id,
                config['occupancy_schedule']
            )
            
        return self
        
    def start(self, async_mode: bool = True) -> 'Simulation':
        """
        Start the simulation.
        
        Args:
            async_mode: If True, returns immediately; if False, waits for completion
            
        Returns:
            Self for method chaining
        """
        self._api.start_simulation(self.sim_id)
        
        if not async_mode:
            self.wait_for_completion()
            
        return self
        
    def wait_for_completion(self, timeout: Optional[int] = None, 
                          poll_interval: int = 5) -> 'Simulation':
        """
        Wait for simulation to complete.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            poll_interval: Time between status checks in seconds
            
        Returns:
            Self for method chaining
            
        Raises:
            SimulationExecutionError: If simulation fails
            TimeoutError: If timeout is reached
        """
        start_time = time.time()
        
        while True:
            status = self.get_status()
            state = status.get('status', 'unknown')
            
            if state == 'done':
                logger.info(f"Simulation {self.sim_id} completed successfully")
                return self
            elif state in ['failed', 'error']:
                raise SimulationExecutionError(
                    f"Simulation {self.sim_id} failed: {status.get('error', 'Unknown error')}"
                )
                
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Simulation {self.sim_id} did not complete within {timeout} seconds")
                
            time.sleep(poll_interval)
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get current simulation status.
        
        Returns:
            Dictionary with status information
        """
        return self._api.check_simulation(self.sim_id)
        
    def is_complete(self) -> bool:
        """
        Check if simulation is complete.
        
        Returns:
            True if simulation is done, False otherwise
        """
        status = self.get_status()
        return status.get('status') == 'done'
        
    def get_results(self, output_format: str = 'json') -> Any:
        """
        Retrieve simulation results.
        
        Args:
            output_format: Format for results ('json', 'dataframe', 'csv')
            
        Returns:
            Results in requested format
        """
        return self._api.get_results(self.sim_id, output_format)
        
    def stop(self) -> 'Simulation':
        """
        Stop a running simulation.
        
        Returns:
            Self for method chaining
        """
        # This would require backend support for stopping simulations
        logger.warning("Simulation stopping not yet implemented in backend")
        return self


class SimulationAPI:
    """
    Main API class for programmatic simulation control.
    
    This class provides methods to create, configure, and control simulations
    programmatically without using the web interface.
    """
    
    def __init__(self, base_url: str = 'http://localhost:5000', 
                 api_key: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the backend API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
            
        # Test connection
        try:
            response = self.session.get(f"{self.base_url}/simulation/overview")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise APIConnectionError(f"Failed to connect to backend at {self.base_url}: {e}")
            
    def create_simulation(self, name: str, description: Optional[str] = None) -> Simulation:
        """
        Create a new simulation and return a Simulation object.
        
        Args:
            name: Name for the simulation
            description: Optional description
            
        Returns:
            Simulation object
            
        Raises:
            SimulationAPIError: If creation fails
        """
        try:
            response = self.session.post(
                f"{self.base_url}/simulation",
                json={'name': name, 'description': description}
            )
            response.raise_for_status()
            data = response.json()
            sim_id = data.get('id')
            
            if not sim_id:
                raise SimulationAPIError("No simulation ID returned from server")
                
            logger.info(f"Created simulation {sim_id}")
            return Simulation(sim_id, self)
            
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to create simulation: {e}")
            
    def get_simulation(self, sim_id: str) -> Simulation:
        """
        Retrieve an existing simulation object by ID.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            Simulation object
            
        Raises:
            SimulationNotFoundError: If simulation doesn't exist
        """
        try:
            response = self.session.get(f"{self.base_url}/simulation/{sim_id}")
            response.raise_for_status()
            return Simulation(sim_id, self)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise SimulationNotFoundError(f"Simulation {sim_id} not found")
            raise SimulationAPIError(f"Failed to retrieve simulation: {e}")
            
    def list_simulations(self) -> List[Dict[str, Any]]:
        """
        List all simulations.
        
        Returns:
            List of simulation metadata dictionaries
        """
        try:
            response = self.session.get(f"{self.base_url}/simulation/overview")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to list simulations: {e}")
            
    def set_idf_file(self, sim_id: str, filepath: str) -> None:
        """
        Upload IDF file for a simulation.
        
        Args:
            sim_id: Simulation identifier
            filepath: Path to IDF file
            
        Raises:
            SimulationAPIError: If upload fails
        """
        import base64
        
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()
                encoded = base64.b64encode(file_content).decode('utf-8')
                
            response = self.session.put(
                f"{self.base_url}/simulation/{sim_id}/idf",
                json={'idf_base64': encoded}
            )
            response.raise_for_status()
            logger.info(f"Uploaded IDF file for simulation {sim_id}")
            
        except (IOError, requests.exceptions.RequestException) as e:
            raise SimulationAPIError(f"Failed to upload IDF file: {e}")
            
    def set_epw_file(self, sim_id: str, filepath: str) -> None:
        """
        Upload EPW file for a simulation.
        
        Args:
            sim_id: Simulation identifier
            filepath: Path to EPW file
            
        Raises:
            SimulationAPIError: If upload fails
        """
        import base64
        
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()
                encoded = base64.b64encode(file_content).decode('utf-8')
                
            response = self.session.put(
                f"{self.base_url}/simulation/{sim_id}/epw",
                json={'epw_base64': encoded}
            )
            response.raise_for_status()
            logger.info(f"Uploaded EPW file for simulation {sim_id}")
            
        except (IOError, requests.exceptions.RequestException) as e:
            raise SimulationAPIError(f"Failed to upload EPW file: {e}")
            
    def set_room_dimensions(self, sim_id: str, width: float, 
                          length: float, height: float) -> None:
        """
        Set room dimensions for a simulation.
        
        Args:
            sim_id: Simulation identifier
            width: Room width in meters
            length: Room length in meters
            height: Room height in meters
            
        Raises:
            InvalidParameterError: If dimensions are invalid
            SimulationAPIError: If update fails
        """
        if width <= 0 or length <= 0 or height <= 0:
            raise InvalidParameterError("Dimensions must be positive")
            
        # This would require a new endpoint in the backend
        logger.warning("Room dimension setting via API not yet implemented in backend")
        
    def set_occupancy_schedule(self, sim_id: str, schedule_data: Any) -> None:
        """
        Set occupancy schedule for a simulation.
        
        Args:
            sim_id: Simulation identifier
            schedule_data: Occupancy schedule (CSV file path or DataFrame)
            
        Raises:
            SimulationAPIError: If upload fails
        """
        import base64
        import pandas as pd
        
        try:
            # Handle different input types
            if isinstance(schedule_data, str):
                # Assume it's a file path
                with open(schedule_data, 'rb') as f:
                    file_content = f.read()
            elif isinstance(schedule_data, pd.DataFrame):
                # Convert DataFrame to CSV
                file_content = schedule_data.to_csv(index=False).encode('utf-8')
            else:
                raise InvalidParameterError("schedule_data must be a file path or DataFrame")
                
            encoded = base64.b64encode(file_content).decode('utf-8')
            
            response = self.session.put(
                f"{self.base_url}/simulation/{sim_id}/csv",
                json={'csv_base64': encoded}
            )
            response.raise_for_status()
            logger.info(f"Uploaded occupancy schedule for simulation {sim_id}")
            
        except (IOError, requests.exceptions.RequestException) as e:
            raise SimulationAPIError(f"Failed to upload occupancy schedule: {e}")
            
    def start_simulation(self, sim_id: str) -> None:
        """
        Start a simulation.
        
        Args:
            sim_id: Simulation identifier
            
        Raises:
            InvalidStateError: If simulation cannot be started
            SimulationAPIError: If start fails
        """
        try:
            response = self.session.post(f"{self.base_url}/simulation/{sim_id}/start")
            response.raise_for_status()
            logger.info(f"Started simulation {sim_id}")
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to start simulation: {e}")
            
    def check_simulation(self, sim_id: str) -> Dict[str, Any]:
        """
        Check simulation status.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            Status dictionary
        """
        try:
            response = self.session.get(f"{self.base_url}/simulation/{sim_id}/check")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to check simulation status: {e}")
            
    def get_results(self, sim_id: str, output_format: str = 'json') -> Any:
        """
        Retrieve simulation results.
        
        Args:
            sim_id: Simulation identifier
            output_format: Format for results ('json', 'dataframe', 'csv')
            
        Returns:
            Results in requested format
            
        Raises:
            SimulationAPIError: If retrieval fails
        """
        try:
            if output_format == 'csv':
                response = self.session.get(f"{self.base_url}/result/{sim_id}/csv")
            else:
                response = self.session.get(f"{self.base_url}/result/{sim_id}")
                
            response.raise_for_status()
            
            if output_format == 'json':
                return response.json()
            elif output_format == 'dataframe':
                import pandas as pd
                return pd.DataFrame(response.json())
            elif output_format == 'csv':
                return response.text
            else:
                raise InvalidParameterError(f"Unsupported output format: {output_format}")
                
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to retrieve results: {e}")
            
    def delete_simulation(self, sim_id: str) -> None:
        """
        Delete a simulation and its results.
        
        Args:
            sim_id: Simulation identifier
            
        Raises:
            SimulationAPIError: If deletion fails
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/simulation",
                json={'id': sim_id}
            )
            response.raise_for_status()
            logger.info(f"Deleted simulation {sim_id}")
        except requests.exceptions.RequestException as e:
            raise SimulationAPIError(f"Failed to delete simulation: {e}")
