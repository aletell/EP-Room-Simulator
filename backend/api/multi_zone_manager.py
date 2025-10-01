"""
Multi-zone simulation management.

This module provides support for managing simulations with multiple zones
and multiple IDF files, enabling complex building simulations.
"""

import logging
from typing import Dict, Any, List, Optional
import requests

from .exceptions import (
    SimulationAPIError,
    InvalidParameterError
)
from .simulation_api import SimulationAPI

logger = logging.getLogger(__name__)


class Zone:
    """Represents a single zone in a multi-zone simulation."""
    
    def __init__(self, zone_id: str, zone_name: str, idf_file: str):
        """
        Initialize a zone.
        
        Args:
            zone_id: Unique identifier for the zone
            zone_name: Human-readable zone name
            idf_file: Path to IDF file for this zone
        """
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.idf_file = idf_file
        self.parameters = {}
        self.connections = []  # Adjacent zones
        
    def set_parameter(self, parameter: str, value: Any) -> None:
        """Set a parameter for this zone."""
        self.parameters[parameter] = value
        
    def connect_to(self, other_zone: 'Zone', connection_type: str = 'airflow') -> None:
        """
        Create a connection to another zone.
        
        Args:
            other_zone: Zone to connect to
            connection_type: Type of connection ('airflow', 'thermal', etc.)
        """
        self.connections.append({
            'zone': other_zone.zone_id,
            'type': connection_type
        })


class MultiZoneManager:
    """
    Manages multi-zone simulations with multiple IDF files.
    
    This class enables complex building simulations with:
    - Multiple zones from different IDF files
    - Inter-zone air flow and thermal connections
    - Coordinated parameter control across zones
    - Aggregated results collection
    
    Example:
        manager = MultiZoneManager(api)
        
        # Add zones
        zone1 = manager.add_zone('office_1', 'Office Room 1', 'office.idf')
        zone2 = manager.add_zone('office_2', 'Office Room 2', 'office.idf')
        zone3 = manager.add_zone('corridor', 'Corridor', 'corridor.idf')
        
        # Define connections
        manager.connect_zones(zone1, zone3, airflow_rate=0.5)
        manager.connect_zones(zone2, zone3, airflow_rate=0.5)
        
        # Create and run simulation
        sim = manager.create_simulation('Multi-Zone Office Building')
        sim.start()
    """
    
    def __init__(self, api: SimulationAPI):
        """
        Initialize multi-zone manager.
        
        Args:
            api: SimulationAPI instance for backend communication
        """
        self.api = api
        self.zones: Dict[str, Zone] = {}
        self.zone_connections: List[Dict[str, Any]] = []
        
    def add_zone(self, zone_id: str, zone_name: str, idf_file: str) -> Zone:
        """
        Add a zone to the multi-zone simulation.
        
        Args:
            zone_id: Unique identifier for the zone
            zone_name: Human-readable zone name
            idf_file: Path to IDF file for this zone
            
        Returns:
            Zone object
            
        Raises:
            InvalidParameterError: If zone_id already exists
        """
        if zone_id in self.zones:
            raise InvalidParameterError(f"Zone {zone_id} already exists")
            
        zone = Zone(zone_id, zone_name, idf_file)
        self.zones[zone_id] = zone
        logger.info(f"Added zone {zone_id} ({zone_name}) from {idf_file}")
        return zone
        
    def remove_zone(self, zone_id: str) -> None:
        """
        Remove a zone from the simulation.
        
        Args:
            zone_id: Identifier of zone to remove
        """
        if zone_id in self.zones:
            del self.zones[zone_id]
            # Remove connections involving this zone
            self.zone_connections = [
                conn for conn in self.zone_connections
                if conn['from_zone'] != zone_id and conn['to_zone'] != zone_id
            ]
            logger.info(f"Removed zone {zone_id}")
        
    def connect_zones(self, from_zone: str, to_zone: str,
                     connection_type: str = 'airflow',
                     airflow_rate: Optional[float] = None,
                     thermal_conductance: Optional[float] = None) -> None:
        """
        Connect two zones for air flow or thermal exchange.
        
        Args:
            from_zone: Source zone ID
            to_zone: Destination zone ID
            connection_type: Type of connection ('airflow', 'thermal', 'both')
            airflow_rate: Air flow rate in m³/s (for airflow connections)
            thermal_conductance: Thermal conductance in W/K (for thermal connections)
            
        Raises:
            InvalidParameterError: If zones don't exist
        """
        if from_zone not in self.zones:
            raise InvalidParameterError(f"Zone {from_zone} not found")
        if to_zone not in self.zones:
            raise InvalidParameterError(f"Zone {to_zone} not found")
            
        connection = {
            'from_zone': from_zone,
            'to_zone': to_zone,
            'type': connection_type,
            'airflow_rate': airflow_rate,
            'thermal_conductance': thermal_conductance
        }
        
        self.zone_connections.append(connection)
        logger.info(f"Connected {from_zone} to {to_zone} ({connection_type})")
        
    def set_zone_parameter(self, zone_id: str, parameter: str, value: Any) -> None:
        """
        Set a parameter for a specific zone.
        
        Args:
            zone_id: Zone identifier
            parameter: Parameter name
            value: Parameter value
        """
        if zone_id not in self.zones:
            raise InvalidParameterError(f"Zone {zone_id} not found")
            
        self.zones[zone_id].set_parameter(parameter, value)
        logger.info(f"Set {parameter}={value} for zone {zone_id}")
        
    def set_all_zones_parameter(self, parameter: str, value: Any) -> None:
        """
        Set a parameter for all zones.
        
        Args:
            parameter: Parameter name
            value: Parameter value
        """
        for zone in self.zones.values():
            zone.set_parameter(parameter, value)
        logger.info(f"Set {parameter}={value} for all zones")
        
    def get_zone_list(self) -> List[str]:
        """
        Get list of all zone IDs.
        
        Returns:
            List of zone IDs
        """
        return list(self.zones.keys())
        
    def get_zone_info(self, zone_id: str) -> Dict[str, Any]:
        """
        Get information about a specific zone.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            Dictionary with zone information
        """
        if zone_id not in self.zones:
            raise InvalidParameterError(f"Zone {zone_id} not found")
            
        zone = self.zones[zone_id]
        return {
            'zone_id': zone.zone_id,
            'zone_name': zone.zone_name,
            'idf_file': zone.idf_file,
            'parameters': zone.parameters.copy(),
            'connections': zone.connections.copy()
        }
        
    def create_simulation(self, name: str, description: Optional[str] = None) -> Any:
        """
        Create a multi-zone simulation.
        
        This method creates a simulation that includes all configured zones
        and their connections.
        
        Args:
            name: Simulation name
            description: Optional description
            
        Returns:
            Simulation object
            
        Raises:
            SimulationAPIError: If simulation creation fails
        """
        if not self.zones:
            raise InvalidParameterError("No zones defined. Add at least one zone.")
            
        # Create simulation via API
        sim = self.api.create_simulation(name, description)
        
        # TODO: Upload zone configurations and connections to backend
        # This requires backend support for multi-zone simulations
        logger.warning("Multi-zone simulation creation requires backend support")
        logger.info(f"Created multi-zone simulation with {len(self.zones)} zones")
        
        return sim
        
    def export_configuration(self) -> Dict[str, Any]:
        """
        Export the multi-zone configuration.
        
        Returns:
            Dictionary with complete configuration
        """
        return {
            'zones': {
                zone_id: {
                    'name': zone.zone_name,
                    'idf_file': zone.idf_file,
                    'parameters': zone.parameters
                }
                for zone_id, zone in self.zones.items()
            },
            'connections': self.zone_connections
        }
        
    def import_configuration(self, config: Dict[str, Any]) -> None:
        """
        Import a multi-zone configuration.
        
        Args:
            config: Configuration dictionary from export_configuration
        """
        # Clear existing configuration
        self.zones.clear()
        self.zone_connections.clear()
        
        # Import zones
        for zone_id, zone_data in config.get('zones', {}).items():
            zone = self.add_zone(
                zone_id,
                zone_data['name'],
                zone_data['idf_file']
            )
            for param, value in zone_data.get('parameters', {}).items():
                zone.set_parameter(param, value)
                
        # Import connections
        self.zone_connections = config.get('connections', [])
        
        logger.info(f"Imported configuration with {len(self.zones)} zones")


class MultiZoneStateManager:
    """
    State manager for multi-zone simulations.
    
    Provides methods to inspect and modify state across multiple zones.
    """
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        """
        Initialize multi-zone state manager.
        
        Args:
            base_url: Backend API base URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def get_all_zones_temperature(self, sim_id: str) -> Dict[str, float]:
        """
        Get temperature for all zones.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            Dictionary mapping zone IDs to temperatures
        """
        # Placeholder for backend implementation
        logger.warning("Multi-zone state inspection requires backend support")
        return {}
        
    def get_zone_variable(self, sim_id: str, zone_id: str, 
                         variable_name: str) -> Any:
        """
        Get a variable value for a specific zone.
        
        Args:
            sim_id: Simulation identifier
            zone_id: Zone identifier
            variable_name: Variable name
            
        Returns:
            Variable value
        """
        # Placeholder for backend implementation
        logger.warning("Zone-specific variable inspection requires backend support")
        return None
        
    def set_zone_variable(self, sim_id: str, zone_id: str,
                         variable_name: str, value: Any) -> None:
        """
        Set a variable value for a specific zone.
        
        Args:
            sim_id: Simulation identifier
            zone_id: Zone identifier
            variable_name: Variable name
            value: New value
        """
        # Placeholder for backend implementation
        logger.warning("Zone-specific variable modification requires backend support")
        
    def get_inter_zone_flow(self, sim_id: str, from_zone: str, 
                           to_zone: str) -> Dict[str, float]:
        """
        Get inter-zone air flow and heat transfer rates.
        
        Args:
            sim_id: Simulation identifier
            from_zone: Source zone ID
            to_zone: Destination zone ID
            
        Returns:
            Dictionary with flow rates and heat transfer
        """
        # Placeholder for backend implementation
        logger.warning("Inter-zone flow monitoring requires backend support")
        return {
            'airflow_rate': 0.0,
            'heat_transfer_rate': 0.0
        }
