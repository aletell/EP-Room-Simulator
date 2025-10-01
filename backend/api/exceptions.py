"""
Custom exceptions for the EP-Room-Simulator API.
"""


class SimulationAPIError(Exception):
    """Base exception for all API errors."""
    pass


class SimulationNotFoundError(SimulationAPIError):
    """Raised when a simulation with the given ID is not found."""
    pass


class InvalidStateError(SimulationAPIError):
    """Raised when attempting an operation on a simulation in an invalid state."""
    pass


class InvalidParameterError(SimulationAPIError):
    """Raised when an invalid parameter value is provided."""
    pass


class SimulationExecutionError(SimulationAPIError):
    """Raised when a simulation execution fails."""
    pass


class ConnectionError(SimulationAPIError):
    """Raised when connection to the backend fails."""
    pass


class AuthenticationError(SimulationAPIError):
    """Raised when authentication fails."""
    pass
