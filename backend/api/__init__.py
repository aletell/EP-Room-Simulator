"""
EP-Room-Simulator Python API

This package provides a programmatic interface for controlling simulations,
inspecting states, and overriding variables at runtime.

Main classes:
    - SimulationAPI: Main API client for simulation control
    - StateManager: Interface for state inspection and modification
    - SimulationConfig: Fluent configuration builder
    - SimulationEventHandler: Event-driven simulation control
    - MultiZoneManager: Multi-zone simulation management
    - SimulationMonitor: Real-time simulation monitoring
    - AdaptiveController: Adaptive control for dynamic optimization
    - EnergyPlusRuntime: Direct EnergyPlus Python API integration
"""

from .simulation_api import SimulationAPI
from .state_manager import StateManager
from .config_builder import SimulationConfig
from .event_hooks import SimulationEventHandler
from .multi_zone_manager import MultiZoneManager, MultiZoneStateManager
from .realtime_monitor import SimulationMonitor, AdaptiveController, LiveDashboard
from .exceptions import (
    SimulationAPIError,
    SimulationNotFoundError,
    InvalidStateError,
    InvalidParameterError,
    SimulationExecutionError
)

# Optional: EnergyPlus Python API integration
try:
    from .energyplus_runtime import (
        EnergyPlusRuntime,
        WindowController,
        HVACController,
        create_runtime_controller
    )
    ENERGYPLUS_RUNTIME_AVAILABLE = True
except ImportError:
    ENERGYPLUS_RUNTIME_AVAILABLE = False
    EnergyPlusRuntime = None
    WindowController = None
    HVACController = None
    create_runtime_controller = None

__version__ = '0.3.0'
__all__ = [
    'SimulationAPI',
    'StateManager',
    'SimulationConfig',
    'SimulationEventHandler',
    'MultiZoneManager',
    'MultiZoneStateManager',
    'SimulationMonitor',
    'AdaptiveController',
    'LiveDashboard',
    'SimulationAPIError',
    'SimulationNotFoundError',
    'InvalidStateError',
    'InvalidParameterError',
    'SimulationExecutionError',
    'ENERGYPLUS_RUNTIME_AVAILABLE'
]

# Add runtime classes if available
if ENERGYPLUS_RUNTIME_AVAILABLE:
    __all__.extend([
        'EnergyPlusRuntime',
        'WindowController',
        'HVACController',
        'create_runtime_controller'
    ])
