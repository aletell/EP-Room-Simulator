"""
Event-driven interface for simulation lifecycle.

This module provides the SimulationEventHandler class which allows registering
callbacks for various simulation events.
"""

import logging
from typing import Callable, Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of supported event types."""
    START = "start"
    TIMESTEP = "timestep"
    COMPLETE = "complete"
    ERROR = "error"
    STATE_CHANGE = "state_change"
    PAUSE = "pause"
    RESUME = "resume"


class SimulationEventHandler:
    """
    Event-driven interface for simulation lifecycle.
    
    Allows registering callbacks that are triggered at specific points
    during simulation execution.
    
    Example:
        handler = SimulationEventHandler()
        
        @handler.on_timestep
        def check_temperature(timestep, state):
            if state['temperature'] > 26:
                print("Temperature too high!")
                
        handler.attach(sim_id)
    """
    
    def __init__(self):
        """Initialize event handler with empty callback lists."""
        self._callbacks: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self._state_change_callbacks: Dict[str, List[Callable]] = {}
        
    def on_start(self, callback: Callable[[str], None]) -> Callable:
        """
        Register callback for simulation start.
        
        The callback receives the simulation ID as argument.
        
        Args:
            callback: Function to call when simulation starts
            
        Returns:
            The callback function (for use as decorator)
            
        Example:
            @handler.on_start
            def simulation_started(sim_id):
                print(f"Simulation {sim_id} started")
        """
        self._callbacks[EventType.START].append(callback)
        return callback
        
    def on_timestep(self, callback: Callable[[int, Dict[str, Any]], None]) -> Callable:
        """
        Register callback for each timestep.
        
        The callback receives the timestep number and current state dictionary.
        
        Args:
            callback: Function to call at each timestep
            
        Returns:
            The callback function (for use as decorator)
            
        Example:
            @handler.on_timestep
            def check_conditions(timestep, state):
                temp = state.get('temperature', 0)
                if temp > 26:
                    print(f"High temperature at timestep {timestep}")
        """
        self._callbacks[EventType.TIMESTEP].append(callback)
        return callback
        
    def on_complete(self, callback: Callable[[Dict[str, Any]], None]) -> Callable:
        """
        Register callback for simulation completion.
        
        The callback receives the final results dictionary.
        
        Args:
            callback: Function to call when simulation completes
            
        Returns:
            The callback function (for use as decorator)
            
        Example:
            @handler.on_complete
            def save_results(results):
                results.to_csv('output.csv')
        """
        self._callbacks[EventType.COMPLETE].append(callback)
        return callback
        
    def on_error(self, callback: Callable[[Exception], None]) -> Callable:
        """
        Register callback for errors.
        
        The callback receives the exception that occurred.
        
        Args:
            callback: Function to call when an error occurs
            
        Returns:
            The callback function (for use as decorator)
            
        Example:
            @handler.on_error
            def handle_error(error):
                print(f"Simulation failed: {error}")
                send_notification(error)
        """
        self._callbacks[EventType.ERROR].append(callback)
        return callback
        
    def on_state_change(self, variable_name: str, 
                       callback: Callable[[str, Any, Any], None]) -> Callable:
        """
        Register callback for specific variable changes.
        
        The callback receives variable name, old value, and new value.
        
        Args:
            variable_name: Name of the variable to watch
            callback: Function to call when variable changes
            
        Returns:
            The callback function (for use as decorator)
            
        Example:
            @handler.on_state_change('zone_temperature')
            def temperature_changed(var_name, old_val, new_val):
                print(f"Temperature: {old_val} -> {new_val}")
        """
        if variable_name not in self._state_change_callbacks:
            self._state_change_callbacks[variable_name] = []
            
        self._state_change_callbacks[variable_name].append(callback)
        return callback
        
    def on_pause(self, callback: Callable[[str], None]) -> Callable:
        """
        Register callback for simulation pause.
        
        Args:
            callback: Function to call when simulation is paused
            
        Returns:
            The callback function (for use as decorator)
        """
        self._callbacks[EventType.PAUSE].append(callback)
        return callback
        
    def on_resume(self, callback: Callable[[str], None]) -> Callable:
        """
        Register callback for simulation resume.
        
        Args:
            callback: Function to call when simulation resumes
            
        Returns:
            The callback function (for use as decorator)
        """
        self._callbacks[EventType.RESUME].append(callback)
        return callback
        
    def trigger(self, event_type: EventType, *args, **kwargs) -> None:
        """
        Trigger all callbacks for a specific event type.
        
        Args:
            event_type: Type of event to trigger
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
        """
        callbacks = self._callbacks.get(event_type, [])
        
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in event callback: {e}", exc_info=True)
                
    def trigger_state_change(self, variable_name: str, old_value: Any, new_value: Any) -> None:
        """
        Trigger callbacks for a specific variable change.
        
        Args:
            variable_name: Name of the variable that changed
            old_value: Previous value
            new_value: New value
        """
        callbacks = self._state_change_callbacks.get(variable_name, [])
        
        for callback in callbacks:
            try:
                callback(variable_name, old_value, new_value)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}", exc_info=True)
                
    def clear_callbacks(self, event_type: Optional[EventType] = None) -> None:
        """
        Clear registered callbacks.
        
        Args:
            event_type: Specific event type to clear, or None to clear all
        """
        if event_type:
            self._callbacks[event_type] = []
        else:
            for event_type in EventType:
                self._callbacks[event_type] = []
            self._state_change_callbacks = {}
            
    def attach(self, sim_id: str) -> None:
        """
        Attach event handler to a simulation.
        
        Note: This requires backend support for event-driven simulation.
        Currently this is a placeholder for future implementation.
        
        Args:
            sim_id: Simulation identifier
        """
        logger.warning(f"Event handler attachment not yet fully implemented")
        logger.info(f"Event handler ready for simulation {sim_id}")
        
    def detach(self, sim_id: str) -> None:
        """
        Detach event handler from a simulation.
        
        Args:
            sim_id: Simulation identifier
        """
        logger.info(f"Event handler detached from simulation {sim_id}")


class EventMonitor:
    """
    Helper class for monitoring simulation events.
    
    Provides convenience methods for common monitoring patterns.
    """
    
    def __init__(self, handler: SimulationEventHandler):
        """
        Initialize event monitor.
        
        Args:
            handler: SimulationEventHandler to monitor
        """
        self.handler = handler
        self.event_log: List[Dict[str, Any]] = []
        
    def log_all_events(self) -> None:
        """Enable logging of all events."""
        
        @self.handler.on_start
        def log_start(sim_id):
            self.event_log.append({
                'type': 'start',
                'sim_id': sim_id,
                'timestamp': self._get_timestamp()
            })
            
        @self.handler.on_complete
        def log_complete(results):
            self.event_log.append({
                'type': 'complete',
                'timestamp': self._get_timestamp()
            })
            
        @self.handler.on_error
        def log_error(error):
            self.event_log.append({
                'type': 'error',
                'error': str(error),
                'timestamp': self._get_timestamp()
            })
            
    def get_event_log(self) -> List[Dict[str, Any]]:
        """
        Get the event log.
        
        Returns:
            List of event dictionaries
        """
        return self.event_log.copy()
        
    def clear_event_log(self) -> None:
        """Clear the event log."""
        self.event_log = []
        
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp as ISO format string."""
        from datetime import datetime
        return datetime.now().isoformat()
