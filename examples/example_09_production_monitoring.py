"""
Example 9: Production-Ready Real-Time Monitoring and Control System

This comprehensive example demonstrates a complete production-ready system for
real-time simulation monitoring and control with:

1. Multiple File Logging Formats:
   - CSV for tabular data
   - JSON Lines for structured events
   - Text logs for human-readable monitoring
   - Structured logging by category

2. Live Web Dashboard:
   - Real-time visualization in browser
   - Automatic updates every second
   - Temperature trends chart
   - Activity log

3. File Monitoring:
   - Real-time monitoring with tail -f
   - Immediate flush for live updates
   - Multiple output formats

4. Production Features:
   - Error handling and recovery
   - Performance metrics
   - Graceful shutdown
   - Resource cleanup

Run this example and:
- Open http://localhost:5001 in browser for live dashboard
- In another terminal: tail -f simulation_logs/simulation_*.csv
- In another terminal: tail -f simulation_logs/simulation_*.log

This demonstrates industrial-grade simulation control suitable for
research, building automation, and energy optimization projects.
"""

import sys
import os
import time
from datetime import datetime
import signal

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api import ENERGYPLUS_RUNTIME_AVAILABLE

if not ENERGYPLUS_RUNTIME_AVAILABLE:
    print("\n" + "=" * 80)
    print("Production Real-Time Monitoring Example")
    print("=" * 80)
    print("\n❌ ERROR: EnergyPlus Python API not available")
    print("\nThis example requires pyenergyplus package.")
    print("Install with: pip install pyenergyplus")
    print("\nNote: Requires EnergyPlus 9.3 or later")
    print("=" * 80)
    sys.exit(1)

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    print("\n❌ Could not import pyenergyplus")
    print("Install with: pip install pyenergyplus")
    sys.exit(1)

from api import FileLogger, StructuredLogger, MetricsAggregator

# Try to import LiveDashboard (requires Flask)
try:
    from api import LiveDashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("\n⚠️  Flask not available - dashboard disabled")
    print("Install with: pip install flask flask-cors")


class ProductionController:
    """
    Production-grade real-time simulation controller.
    
    Features:
    - Multi-format logging
    - Live dashboard
    - Structured event tracking
    - Performance monitoring
    - Error handling
    - Graceful shutdown
    """
    
    def __init__(self, idf_path: str, epw_path: str):
        """
        Initialize production controller.
        
        Args:
            idf_path: Path to IDF file
            epw_path: Path to weather file
        """
        self.idf_path = idf_path
        self.epw_path = epw_path
        
        self.api = EnergyPlusAPI()
        self.handles = {}
        self.running = True
        
        # Loggers
        self.file_logger = FileLogger('./simulation_logs')
        self.structured_logger = StructuredLogger('./simulation_logs/structured')
        self.metrics = MetricsAggregator()
        
        # Dashboard
        self.dashboard = None
        if DASHBOARD_AVAILABLE:
            self.dashboard = LiveDashboard(port=5001, title="EP-Room Simulator")
        
        # Control parameters
        self.control_params = {
            'temp_high_threshold': 26.0,
            'temp_low_threshold': 20.0,
            'temp_diff_min': 2.0,
            'window_max_opening': 0.9,
            'hvac_setpoint_heating': 21.0,
            'hvac_setpoint_cooling': 24.0
        }
        
        # State tracking
        self.current_state = {}
        self.last_control_action = None
        self.timestep_count = 0
        self.control_action_count = 0
        
        # Performance metrics
        self.start_time = None
        self.processing_times = []
        
        print("\n" + "=" * 80)
        print("PRODUCTION REAL-TIME MONITORING & CONTROL SYSTEM")
        print("=" * 80)
        print("\n🏗️  System Configuration:")
        print(f"   IDF: {idf_path}")
        print(f"   EPW: {epw_path}")
        print(f"   Log Directory: ./simulation_logs")
        if DASHBOARD_AVAILABLE:
            print(f"   Dashboard: http://localhost:5001")
        print("\n🎛️  Control Parameters:")
        for key, value in self.control_params.items():
            print(f"   {key}: {value}")
        print("=" * 80)
    
    def setup_sensors_actuators(self, state):
        """Setup all sensors and actuators."""
        print("\n🔧 Setting up sensors and actuators...")
        
        # Temperature sensors
        self.handles['zone_temp'] = self.api.exchange.get_variable_handle(
            state, 'Zone Mean Air Temperature', 'ZONE_1'
        )
        self.handles['outdoor_temp'] = self.api.exchange.get_variable_handle(
            state, 'Site Outdoor Air Drybulb Temperature', 'Environment'
        )
        self.handles['outdoor_rh'] = self.api.exchange.get_variable_handle(
            state, 'Site Outdoor Air Relative Humidity', 'Environment'
        )
        
        # Window actuator
        self.handles['window'] = self.api.exchange.get_actuator_handle(
            state,
            'AirFlow Network Window/Door Opening',
            'Venting Opening Factor',
            'WINDOW_1'
        )
        
        # HVAC actuators
        self.handles['heating_setpoint'] = self.api.exchange.get_actuator_handle(
            state,
            'Schedule:Constant',
            'Schedule Value',
            'HEATING_SETPOINT_SCHEDULE'
        )
        self.handles['cooling_setpoint'] = self.api.exchange.get_actuator_handle(
            state,
            'Schedule:Constant',
            'Schedule Value',
            'COOLING_SETPOINT_SCHEDULE'
        )
        
        # Verify handles
        valid_handles = all(h != -1 for h in self.handles.values())
        if not valid_handles:
            print("⚠️  Warning: Some handles could not be registered")
            print("   Simulation will run with limited control capability")
        else:
            print("✅ All sensors and actuators registered successfully")
        
        # Log initialization event
        self.structured_logger.log_event('initialization', {
            'handles': list(self.handles.keys()),
            'valid': valid_handles
        })
    
    def control_logic(self, state):
        """
        Main control logic executed each timestep.
        
        Args:
            state: EnergyPlus state object
        """
        if not self.running:
            return
        
        step_start = time.time()
        
        try:
            # Get current time
            hour = self.api.exchange.hour(state)
            minute = self.api.exchange.minutes(state)
            day = self.api.exchange.day_of_month(state)
            month = self.api.exchange.month(state)
            
            # Read sensors
            zone_temp = self.api.exchange.get_variable_value(
                state, self.handles['zone_temp']
            )
            outdoor_temp = self.api.exchange.get_variable_value(
                state, self.handles['outdoor_temp']
            )
            outdoor_rh = self.api.exchange.get_variable_value(
                state, self.handles['outdoor_rh']
            )
            
            # Get current window state
            window_opening = self.api.exchange.get_actuator_value(
                state, self.handles['window']
            )
            
            # Update state
            self.current_state = {
                'timestep': self.timestep_count,
                'month': month,
                'day': day,
                'hour': hour,
                'minute': minute,
                'zone_temperature': zone_temp,
                'outdoor_temperature': outdoor_temp,
                'relative_humidity': outdoor_rh,
                'window_opening': window_opening,
                'hvac_heating_setpoint': self.control_params['hvac_setpoint_heating'],
                'hvac_cooling_setpoint': self.control_params['hvac_setpoint_cooling']
            }
            
            # Record metrics
            self.metrics.record('zone_temperature', zone_temp)
            self.metrics.record('outdoor_temperature', outdoor_temp)
            self.metrics.record('window_opening', window_opening)
            
            # Log measurements
            self.structured_logger.log_measurement('zone_temperature', zone_temp, '°C')
            self.structured_logger.log_measurement('outdoor_temperature', outdoor_temp, '°C')
            
            # Control decisions
            control_action = None
            
            # Window control logic
            temp_diff = zone_temp - outdoor_temp
            if zone_temp > self.control_params['temp_high_threshold'] and \
               temp_diff > self.control_params['temp_diff_min']:
                # Open window for natural ventilation
                new_opening = self.control_params['window_max_opening']
                if abs(new_opening - window_opening) > 0.1:
                    self.api.exchange.set_actuator_value(
                        state, self.handles['window'], new_opening
                    )
                    control_action = f"WINDOW OPEN {new_opening*100:.0f}%"
                    self.control_action_count += 1
                    
                    self.structured_logger.log_control_action('window_open', {
                        'opening': new_opening,
                        'zone_temp': zone_temp,
                        'outdoor_temp': outdoor_temp,
                        'reason': 'natural_ventilation'
                    })
            
            elif zone_temp < self.control_params['temp_low_threshold'] or \
                 temp_diff < 0:
                # Close window
                new_opening = 0.0
                if abs(new_opening - window_opening) > 0.1:
                    self.api.exchange.set_actuator_value(
                        state, self.handles['window'], new_opening
                    )
                    control_action = "WINDOW CLOSE"
                    self.control_action_count += 1
                    
                    self.structured_logger.log_control_action('window_close', {
                        'opening': new_opening,
                        'zone_temp': zone_temp,
                        'reason': 'temperature_maintenance'
                    })
            
            # HVAC adaptive control
            if zone_temp > 28.0:
                # Reduce cooling setpoint for more aggressive cooling
                new_cooling = 22.0
                if new_cooling != self.control_params['hvac_setpoint_cooling']:
                    self.api.exchange.set_actuator_value(
                        state, self.handles['cooling_setpoint'], new_cooling
                    )
                    self.control_params['hvac_setpoint_cooling'] = new_cooling
                    control_action = f"HVAC COOLING ADJUST {new_cooling}°C"
                    
                    self.structured_logger.log_control_action('hvac_adjust', {
                        'type': 'cooling',
                        'setpoint': new_cooling,
                        'zone_temp': zone_temp,
                        'reason': 'high_temperature'
                    })
            
            # Update dashboard
            if self.dashboard:
                state_with_action = self.current_state.copy()
                if control_action:
                    state_with_action['control_action'] = control_action
                self.dashboard.update_data(state_with_action)
            
            # Log to files
            log_message = None
            if control_action:
                log_message = f"[{month:02d}/{day:02d} {hour:02d}:{minute:02d}] {control_action}"
                self.current_state['control_action'] = control_action
            
            self.file_logger.log(self.current_state, message=log_message)
            
            # Console output (every 10 timesteps)
            if self.timestep_count % 10 == 0:
                timestamp = f"{month:02d}/{day:02d} {hour:02d}:{minute:02d}"
                print(f"\n[{timestamp}] "
                      f"Zone: {zone_temp:5.1f}°C | "
                      f"Out: {outdoor_temp:5.1f}°C | "
                      f"Window: {window_opening*100:3.0f}% | "
                      f"Actions: {self.control_action_count}")
                if control_action:
                    print(f"           ⚡ {control_action}")
            
            # Check thresholds for alerts
            if zone_temp > 30.0:
                self.structured_logger.log_alert(
                    'high_temperature',
                    f'Zone temperature critically high: {zone_temp:.1f}°C',
                    severity='critical'
                )
            
            self.timestep_count += 1
            
            # Track processing time
            processing_time = time.time() - step_start
            self.processing_times.append(processing_time)
            
        except Exception as e:
            print(f"\n❌ Error in control logic: {e}")
            self.structured_logger.log_error(str(e), {
                'timestep': self.timestep_count
            })
    
    def run(self):
        """Run the simulation with production monitoring."""
        print("\n🚀 Starting production simulation...")
        print("=" * 80)
        
        # Start loggers
        self.file_logger.start()
        self.structured_logger.start()
        
        # Start dashboard
        if self.dashboard:
            self.dashboard.start()
            print(f"\n🌐 Live Dashboard: http://localhost:5001")
            print("   (Open in your browser to see real-time updates)")
        
        print("\n💡 Monitor logs in real-time:")
        print("   Terminal 1: tail -f simulation_logs/simulation_*.csv")
        print("   Terminal 2: tail -f simulation_logs/simulation_*.log")
        print("\n⏸️  Press Ctrl+C to stop gracefully")
        print("=" * 80)
        
        self.start_time = time.time()
        
        try:
            # Setup EnergyPlus state
            state = self.api.state_manager.new_state()
            self.api.runtime.callback_begin_system_timestep_before_predictor(
                state, self.setup_sensors_actuators
            )
            self.api.runtime.callback_after_predictor_after_hvac_managers(
                state, self.control_logic
            )
            
            # Prepare arguments
            args = ['-w', self.epw_path, '-d', './output', self.idf_path]
            
            # Run simulation
            print("\n⏳ Running EnergyPlus simulation...\n")
            self.api.runtime.run_energyplus(state, args)
            
        except KeyboardInterrupt:
            print("\n\n⏸️  Graceful shutdown requested...")
            self.running = False
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")
            self.structured_logger.log_error('simulation_error', {'error': str(e)})
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Perform graceful shutdown and cleanup."""
        print("\n" + "=" * 80)
        print("SHUTTING DOWN")
        print("=" * 80)
        
        # Calculate runtime
        if self.start_time:
            runtime = time.time() - self.start_time
            print(f"\n📊 Simulation Statistics:")
            print(f"   Total Runtime: {runtime:.1f} seconds")
            print(f"   Timesteps Processed: {self.timestep_count}")
            print(f"   Control Actions: {self.control_action_count}")
            
            if self.processing_times:
                avg_time = sum(self.processing_times) / len(self.processing_times)
                max_time = max(self.processing_times)
                print(f"   Avg Processing Time: {avg_time*1000:.2f} ms")
                print(f"   Max Processing Time: {max_time*1000:.2f} ms")
        
        # Export metrics
        print("\n📈 Exporting metrics...")
        try:
            self.metrics.export_summary('./simulation_logs/metrics_summary.json')
            self.metrics.export_timeseries('./simulation_logs/metrics_timeseries.csv')
        except Exception as e:
            print(f"⚠️  Error exporting metrics: {e}")
        
        # Stop loggers
        print("\n📁 Closing log files...")
        self.file_logger.stop()
        self.structured_logger.stop()
        
        if self.dashboard:
            print("\n🌐 Stopping dashboard...")
            self.dashboard.stop()
        
        print("\n✅ Shutdown complete")
        print("=" * 80)
        print(f"\n📂 All logs saved to: ./simulation_logs/")
        print(f"   - CSV: simulation_*.csv")
        print(f"   - JSON: simulation_*.jsonl")
        print(f"   - Text: simulation_*.log")
        print(f"   - Structured: structured/")
        print(f"   - Metrics: metrics_summary.json, metrics_timeseries.csv")
        print("\n" + "=" * 80)


def main():
    """Main entry point."""
    # Example IDF and EPW paths (update these for your system)
    idf_path = './examples/model.idf'
    epw_path = './examples/weather.epw'
    
    # Check if files exist
    if not os.path.exists(idf_path):
        print(f"\n⚠️  IDF file not found: {idf_path}")
        print("Please provide a valid IDF file path")
        print("\nUsage:")
        print("  1. Update idf_path and epw_path in the script")
        print("  2. Or copy your IDF file to ./examples/model.idf")
        print("  3. Copy your EPW file to ./examples/weather.epw")
        return
    
    if not os.path.exists(epw_path):
        print(f"\n⚠️  EPW file not found: {epw_path}")
        print("Please provide a valid weather file path")
        return
    
    # Create controller and run
    controller = ProductionController(idf_path, epw_path)
    
    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n⏸️  Interrupt signal received...")
        controller.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run simulation
    controller.run()


if __name__ == '__main__':
    main()
