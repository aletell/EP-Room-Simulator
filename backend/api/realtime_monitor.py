"""
Real-time simulation monitoring and control.

This module provides capabilities for observing and modifying simulations
while they are running, enabling dynamic control and real-time optimization.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import requests

from .exceptions import (
    SimulationAPIError,
    SimulationNotFoundError,
    InvalidStateError
)

logger = logging.getLogger(__name__)


class SimulationMonitor:
    """
    Real-time monitoring of simulation execution.
    
    Provides continuous monitoring of simulation state with configurable
    callbacks for various events and thresholds.
    
    Example:
        monitor = SimulationMonitor(sim_id, base_url='http://localhost:5000')
        
        # Add threshold alert
        monitor.add_threshold_alert(
            'zone_temperature',
            operator='>',
            threshold=28.0,
            callback=lambda val: print(f"Temperature alert: {val}°C")
        )
        
        # Start monitoring
        monitor.start(interval=5)
        
        # Monitor runs in background
        time.sleep(300)
        
        # Stop monitoring
        monitor.stop()
    """
    
    def __init__(self, sim_id: str, base_url: str = 'http://localhost:5000'):
        """
        Initialize simulation monitor.
        
        Args:
            sim_id: Simulation identifier to monitor
            base_url: Backend API base URL
        """
        self.sim_id = sim_id
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []
        self.threshold_alerts: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback function to be called with each update.
        
        Args:
            callback: Function that receives state dictionary
        """
        self.callbacks.append(callback)
        
    def add_threshold_alert(self, variable: str, operator: str, 
                           threshold: float, callback: Callable) -> None:
        """
        Add a threshold-based alert.
        
        Args:
            variable: Variable name to monitor
            operator: Comparison operator ('>', '<', '>=', '<=', '==', '!=')
            threshold: Threshold value
            callback: Function to call when threshold is crossed
        """
        alert = {
            'variable': variable,
            'operator': operator,
            'threshold': threshold,
            'callback': callback,
            'triggered': False
        }
        self.threshold_alerts.append(alert)
        logger.info(f"Added threshold alert: {variable} {operator} {threshold}")
        
    def start(self, interval: int = 10) -> None:
        """
        Start monitoring in background thread.
        
        Args:
            interval: Polling interval in seconds
        """
        if self.running:
            logger.warning("Monitor already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started monitoring simulation {self.sim_id}")
        
    def stop(self) -> None:
        """Stop monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped monitoring")
        
    def _monitor_loop(self, interval: int) -> None:
        """Internal monitoring loop."""
        while self.running:
            try:
                # Get current state
                state = self._get_current_state()
                
                if state:
                    # Add timestamp
                    state['timestamp'] = datetime.now().isoformat()
                    
                    # Store in history
                    self.history.append(state)
                    if len(self.history) > self.max_history:
                        self.history.pop(0)
                    
                    # Call callbacks
                    for callback in self.callbacks:
                        try:
                            callback(state)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                    
                    # Check threshold alerts
                    self._check_threshold_alerts(state)
                    
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
            time.sleep(interval)
            
    def _get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get current simulation state from backend."""
        try:
            response = self.session.get(
                f"{self.base_url}/simulation/{self.sim_id}/state"
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 501:
                # Not implemented yet
                logger.debug("State endpoint not yet implemented")
                return None
        except Exception as e:
            logger.debug(f"State retrieval failed: {e}")
        return None
        
    def _check_threshold_alerts(self, state: Dict[str, Any]) -> None:
        """Check if any threshold alerts should be triggered."""
        for alert in self.threshold_alerts:
            variable = alert['variable']
            operator = alert['operator']
            threshold = alert['threshold']
            
            if variable in state:
                value = state[variable]
                triggered = False
                
                if operator == '>' and value > threshold:
                    triggered = True
                elif operator == '<' and value < threshold:
                    triggered = True
                elif operator == '>=' and value >= threshold:
                    triggered = True
                elif operator == '<=' and value <= threshold:
                    triggered = True
                elif operator == '==' and value == threshold:
                    triggered = True
                elif operator == '!=' and value != threshold:
                    triggered = True
                    
                if triggered and not alert['triggered']:
                    alert['triggered'] = True
                    try:
                        alert['callback'](value)
                    except Exception as e:
                        logger.error(f"Alert callback error: {e}")
                elif not triggered:
                    alert['triggered'] = False
                    
    def get_history(self, minutes: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get monitoring history.
        
        Args:
            minutes: Number of minutes of history to return (None for all)
            
        Returns:
            List of state dictionaries
        """
        if minutes is None:
            return self.history.copy()
            
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        return [
            state for state in self.history
            if datetime.fromisoformat(state['timestamp']).timestamp() > cutoff_time
        ]
        
    def get_variable_trend(self, variable: str, minutes: int = 10) -> List[float]:
        """
        Get trend data for a specific variable.
        
        Args:
            variable: Variable name
            minutes: Number of minutes of history
            
        Returns:
            List of values over time
        """
        history = self.get_history(minutes)
        return [state.get(variable, 0.0) for state in history]


class AdaptiveController:
    """
    Adaptive controller for real-time simulation modification.
    
    Implements control logic that modifies simulation parameters based on
    current conditions to achieve specified goals.
    
    Example:
        controller = AdaptiveController(sim_id)
        
        # Add temperature control rule
        controller.add_rule(
            condition=lambda state: state.get('zone_temperature', 20) > 26,
            action=lambda: state_manager.set_window_state(sim_id, 'WINDOW_1', True)
        )
        
        # Start adaptive control
        controller.start(interval=60)
    """
    
    def __init__(self, sim_id: str, base_url: str = 'http://localhost:5000'):
        """
        Initialize adaptive controller.
        
        Args:
            sim_id: Simulation identifier
            base_url: Backend API base URL
        """
        self.sim_id = sim_id
        self.base_url = base_url
        self.monitor = SimulationMonitor(sim_id, base_url)
        self.rules: List[Dict[str, Any]] = []
        self.rule_history: List[Dict[str, Any]] = []
        
    def add_rule(self, name: str, condition: Callable[[Dict[str, Any]], bool],
                action: Callable[[], None], cooldown: int = 300) -> None:
        """
        Add a control rule.
        
        Args:
            name: Rule name for identification
            condition: Function that returns True when rule should trigger
            action: Function to execute when condition is met
            cooldown: Minimum seconds between rule executions
        """
        rule = {
            'name': name,
            'condition': condition,
            'action': action,
            'cooldown': cooldown,
            'last_triggered': 0
        }
        self.rules.append(rule)
        logger.info(f"Added control rule: {name}")
        
    def start(self, interval: int = 60) -> None:
        """
        Start adaptive control.
        
        Args:
            interval: Control interval in seconds
        """
        self.monitor.add_callback(self._evaluate_rules)
        self.monitor.start(interval)
        logger.info("Started adaptive controller")
        
    def stop(self) -> None:
        """Stop adaptive control."""
        self.monitor.stop()
        logger.info("Stopped adaptive controller")
        
    def _evaluate_rules(self, state: Dict[str, Any]) -> None:
        """Evaluate all rules against current state."""
        current_time = time.time()
        
        for rule in self.rules:
            # Check cooldown
            if current_time - rule['last_triggered'] < rule['cooldown']:
                continue
                
            # Check condition
            try:
                if rule['condition'](state):
                    # Execute action
                    try:
                        rule['action']()
                        rule['last_triggered'] = current_time
                        
                        # Log to history
                        self.rule_history.append({
                            'timestamp': datetime.now().isoformat(),
                            'rule': rule['name'],
                            'state': state.copy()
                        })
                        
                        logger.info(f"Triggered rule: {rule['name']}")
                    except Exception as e:
                        logger.error(f"Action execution error: {e}")
            except Exception as e:
                logger.error(f"Condition evaluation error: {e}")
                
    def get_rule_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Get history of rule executions.
        
        Args:
            minutes: Number of minutes of history
            
        Returns:
            List of rule execution records
        """
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        return [
            record for record in self.rule_history
            if datetime.fromisoformat(record['timestamp']).timestamp() > cutoff_time
        ]


class LiveDashboard:
    """
    Live dashboard data provider for real-time visualization.
    
    Aggregates data from monitoring and provides formatted data
    suitable for dashboard displays.
    """
    
    def __init__(self, sim_id: str, base_url: str = 'http://localhost:5000'):
        """
        Initialize live dashboard.
        
        Args:
            sim_id: Simulation identifier
            base_url: Backend API base URL
        """
        self.sim_id = sim_id
        self.monitor = SimulationMonitor(sim_id, base_url)
        
    def start(self, interval: int = 5) -> None:
        """
        Start dashboard data collection.
        
        Args:
            interval: Update interval in seconds
        """
        self.monitor.start(interval)
        
    def stop(self) -> None:
        """Stop dashboard data collection."""
        self.monitor.stop()
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current simulation metrics for dashboard display.
        
        Returns:
            Dictionary with formatted metrics
        """
        if not self.monitor.history:
            return {}
            
        latest_state = self.monitor.history[-1]
        
        return {
            'timestamp': latest_state.get('timestamp'),
            'progress': latest_state.get('percent_complete', 0),
            'current_date': latest_state.get('current_date'),
            'zones': self._format_zone_data(latest_state),
            'energy': self._format_energy_data(latest_state),
            'status': latest_state.get('status', 'running')
        }
        
    def get_time_series(self, variables: List[str], 
                       minutes: int = 60) -> Dict[str, List]:
        """
        Get time series data for plotting.
        
        Args:
            variables: List of variable names
            minutes: Number of minutes of history
            
        Returns:
            Dictionary with timestamps and data series
        """
        history = self.monitor.get_history(minutes)
        
        result = {
            'timestamps': [s['timestamp'] for s in history]
        }
        
        for var in variables:
            result[var] = [s.get(var, 0) for s in history]
            
        return result
        
    def _format_zone_data(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format zone data for display."""
        zones = []
        # Extract zone data from state
        # This is a simplified example
        for key in state:
            if '_temperature' in key:
                zone_name = key.replace('_temperature', '')
                zones.append({
                    'name': zone_name,
                    'temperature': state[key],
                    'humidity': state.get(f'{zone_name}_humidity', 0),
                    'co2': state.get(f'{zone_name}_co2', 0)
                })
        return zones
        
    def _format_energy_data(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Format energy data for display."""
        return {
            'heating': state.get('total_heating_energy', 0),
            'cooling': state.get('total_cooling_energy', 0),
            'lighting': state.get('total_lighting_energy', 0),
            'equipment': state.get('total_equipment_energy', 0),
            'total': state.get('total_energy', 0)
        }
