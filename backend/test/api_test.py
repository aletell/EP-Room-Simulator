"""
Unit tests for the Python API module.

Tests basic functionality of SimulationAPI, StateManager, SimulationConfig,
and SimulationEventHandler classes.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.exceptions import (
    SimulationAPIError,
    SimulationNotFoundError,
    InvalidParameterError,
    InvalidStateError
)
from api.config_builder import SimulationConfig
from api.event_hooks import SimulationEventHandler, EventType


class TestSimulationConfig(unittest.TestCase):
    """Test cases for SimulationConfig builder."""
    
    def test_config_builder_basic(self):
        """Test basic configuration building."""
        # Create a temporary test file
        test_idf = 'tmp/test.idf'
        test_epw = 'tmp/test.epw'
        
        # Create test files
        os.makedirs('tmp', exist_ok=True)
        with open(test_idf, 'w') as f:
            f.write('test idf content')
        with open(test_epw, 'w') as f:
            f.write('test epw content')
        
        try:
            # Build config
            config = (SimulationConfig()
                .with_idf_file(test_idf)
                .with_epw_file(test_epw)
                .with_room_dimensions(5.0, 6.0, 3.0)
                .with_timestep(10)
                .build())
            
            self.assertIn('idf_file', config)
            self.assertIn('epw_file', config)
            self.assertIn('room_dimensions', config)
            self.assertIn('timestep', config)
            self.assertEqual(config['room_dimensions']['width'], 5.0)
            self.assertEqual(config['timestep'], 10)
        finally:
            # Clean up
            if os.path.exists(test_idf):
                os.remove(test_idf)
            if os.path.exists(test_epw):
                os.remove(test_epw)
    
    def test_invalid_dimensions(self):
        """Test that invalid dimensions raise an error."""
        config = SimulationConfig()
        
        with self.assertRaises(InvalidParameterError):
            config.with_room_dimensions(-5.0, 6.0, 3.0)
        
        with self.assertRaises(InvalidParameterError):
            config.with_room_dimensions(5.0, 0, 3.0)
    
    def test_invalid_timestep(self):
        """Test that invalid timestep raises an error."""
        config = SimulationConfig()
        
        with self.assertRaises(InvalidParameterError):
            config.with_timestep(0)
        
        with self.assertRaises(InvalidParameterError):
            config.with_timestep(7)  # Doesn't divide evenly into 60
    
    def test_invalid_files(self):
        """Test that non-existent files raise an error."""
        config = SimulationConfig()
        
        with self.assertRaises(InvalidParameterError):
            config.with_idf_file('nonexistent.idf')
        
        with self.assertRaises(InvalidParameterError):
            config.with_epw_file('nonexistent.epw')
    
    def test_simulation_period(self):
        """Test simulation period configuration."""
        config = SimulationConfig()
        config.with_simulation_period('2024-01-01', '2024-01-31')
        
        config_dict = config.to_dict()
        self.assertIn('simulation_period', config_dict)
        self.assertEqual(config_dict['simulation_period']['start_date'], '2024-01-01')
        self.assertEqual(config_dict['simulation_period']['end_date'], '2024-01-31')
    
    def test_invalid_dates(self):
        """Test that invalid dates raise an error."""
        config = SimulationConfig()
        
        with self.assertRaises(InvalidParameterError):
            config.with_simulation_period('2024-01-31', '2024-01-01')  # End before start
    
    def test_custom_parameters(self):
        """Test custom parameter setting."""
        config = (SimulationConfig()
            .with_custom_parameter('my_param', 42)
            .with_custom_parameter('another_param', 'value'))
        
        config_dict = config.to_dict()
        self.assertIn('custom_parameters', config_dict)
        self.assertEqual(config_dict['custom_parameters']['my_param'], 42)
        self.assertEqual(config_dict['custom_parameters']['another_param'], 'value')


class TestEventHandler(unittest.TestCase):
    """Test cases for SimulationEventHandler."""
    
    def test_event_registration(self):
        """Test event callback registration."""
        handler = SimulationEventHandler()
        callback_called = []
        
        @handler.on_start
        def test_callback(sim_id):
            callback_called.append(sim_id)
        
        # Trigger event
        handler.trigger(EventType.START, 'test_sim_123')
        
        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0], 'test_sim_123')
    
    def test_multiple_callbacks(self):
        """Test that multiple callbacks can be registered."""
        handler = SimulationEventHandler()
        call_count = []
        
        @handler.on_start
        def callback1(sim_id):
            call_count.append(1)
        
        @handler.on_start
        def callback2(sim_id):
            call_count.append(2)
        
        handler.trigger(EventType.START, 'test_sim')
        
        self.assertEqual(len(call_count), 2)
        self.assertIn(1, call_count)
        self.assertIn(2, call_count)
    
    def test_timestep_callback(self):
        """Test timestep callback."""
        handler = SimulationEventHandler()
        timesteps = []
        
        @handler.on_timestep
        def record_timestep(timestep, state):
            timesteps.append((timestep, state))
        
        handler.trigger(EventType.TIMESTEP, 1, {'temp': 22.0})
        handler.trigger(EventType.TIMESTEP, 2, {'temp': 23.0})
        
        self.assertEqual(len(timesteps), 2)
        self.assertEqual(timesteps[0][0], 1)
        self.assertEqual(timesteps[1][1]['temp'], 23.0)
    
    def test_state_change_callback(self):
        """Test state change callback."""
        handler = SimulationEventHandler()
        changes = []
        
        def record_change(var_name, old_val, new_val):
            changes.append((var_name, old_val, new_val))
        
        handler.on_state_change('temperature', record_change)
        
        handler.trigger_state_change('temperature', 20.0, 22.0)
        
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], ('temperature', 20.0, 22.0))
    
    def test_clear_callbacks(self):
        """Test clearing callbacks."""
        handler = SimulationEventHandler()
        call_count = []
        
        @handler.on_start
        def callback(sim_id):
            call_count.append(1)
        
        handler.trigger(EventType.START, 'test')
        self.assertEqual(len(call_count), 1)
        
        handler.clear_callbacks(EventType.START)
        handler.trigger(EventType.START, 'test')
        self.assertEqual(len(call_count), 1)  # Should not increase


class TestExceptions(unittest.TestCase):
    """Test cases for custom exceptions."""
    
    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from SimulationAPIError."""
        self.assertTrue(issubclass(SimulationNotFoundError, SimulationAPIError))
        self.assertTrue(issubclass(InvalidParameterError, SimulationAPIError))
        self.assertTrue(issubclass(InvalidStateError, SimulationAPIError))
    
    def test_exception_messages(self):
        """Test that exceptions can carry messages."""
        try:
            raise InvalidParameterError("Test parameter error")
        except InvalidParameterError as e:
            self.assertEqual(str(e), "Test parameter error")


if __name__ == '__main__':
    unittest.main()
