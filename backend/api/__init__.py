"""
EP-Room-Simulator Python API

This package provides a programmatic interface for controlling simulations,
inspecting states, and overriding variables at runtime.

Main classes:
    - SimulationAPI: Main API client for simulation control
    - StateManager: Interface for state inspection and modification
    - SimulationConfig: Fluent configuration builder
    - SimulationEventHandler: Event-driven simulation control
"""

from .simulation_api import SimulationAPI
from .state_manager import StateManager
from .config_builder import SimulationConfig
from .event_hooks import SimulationEventHandler
from .exceptions import (
    SimulationAPIError,
    SimulationNotFoundError,
    InvalidStateError,
    InvalidParameterError,
    SimulationExecutionError
)

__version__ = '0.1.0'
__all__ = [
    'SimulationAPI',
    'StateManager',
    'SimulationConfig',
    'SimulationEventHandler',
    'SimulationAPIError',
    'SimulationNotFoundError',
    'InvalidStateError',
    'InvalidParameterError',
    'SimulationExecutionError'
]
