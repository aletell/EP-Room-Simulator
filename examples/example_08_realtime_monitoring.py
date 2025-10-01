"""
Example 8: Complete Real-Time Monitoring and Control

This example demonstrates a complete real-time monitoring and control system
showing how to observe and modify simulation parameters during execution
and see the results immediately.

Features:
- Real-time temperature monitoring
- Automatic window control
- HVAC adaptive control
- Live console output showing changes
- Data logging for post-simulation analysis
- Visualization of control actions

This is a practical, working example that can be adapted for real projects.
"""

import sys
import os
from datetime import datetime
import csv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api import ENERGYPLUS_RUNTIME_AVAILABLE

if not ENERGYPLUS_RUNTIME_AVAILABLE:
    print("\n" + "=" * 70)
    print("Real-Time Monitoring Example")
    print("=" * 70)
    print("\n❌ ERROR: EnergyPlus Python API not available")
    print("\nThis example requires pyenergyplus package.")
    print("Install with: pip install pyenergyplus")
    print("\nNote: Requires EnergyPlus 9.3 or later")
    print("=" * 70)
    sys.exit(1)

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    print("\n❌ Could not import pyenergyplus")
    print("Install with: pip install pyenergyplus")
    sys.exit(1)


class RealTimeController:
    """Real-time controller with monitoring and adaptive control."""
    
    def __init__(self):
        self.api = EnergyPlusAPI()
        self.handles = {}
        self.data_log = []
        self.timestep_count = 0
        self.control_actions = []
        
        # Control thresholds
        self.temp_threshold_high = 26.0  # °C
        self.temp_threshold_low = 20.0   # °C
        self.temp_diff_min = 2.0          # Minimum temp difference for natural ventilation
        
        # Statistics
        self.stats = {
            'window_openings': 0,
            'window_closings': 0,
            'hvac_adjustments': 0,
            'max_temp': -999,
            'min_temp': 999
        }
        
        print("\n" + "=" * 70)
        print("REAL-TIME SIMULATION CONTROLLER")
        print("=" * 70)
        print("\nController initialized with thresholds:")
        print(f"  High temperature threshold: {self.temp_threshold_high}°C")
        print(f"  Low temperature threshold: {self.temp_threshold_low}°C")
        print(f"  Minimum temp difference for ventilation: {self.temp_diff_min}°C")
        print("=" * 70)
    
    def setup_sensors_actuators(self, state):
        """Setup all sensors and actuators (called once at start)."""
        print("\n🔧 SETUP: Registering sensors and actuators...")
        
        # Register sensors
        self.handles['zone_temp'] = self.api.exchange.get_variable_handle(
            state,
            'Zone Mean Air Temperature',
            'ZONE_1'
        )
        
        self.handles['outdoor_temp'] = self.api.exchange.get_variable_handle(
            state,
            'Site Outdoor Air Drybulb Temperature',
            'Environment'
        )
        
        self.handles['outdoor_rh'] = self.api.exchange.get_variable_handle(
            state,
            'Site Outdoor Air Relative Humidity',
            'Environment'
        )
        
        self.handles['zone_humidity'] = self.api.exchange.get_variable_handle(
            state,
            'Zone Air Relative Humidity',
            'ZONE_1'
        )
        
        # Register actuators
        self.handles['window'] = self.api.exchange.get_actuator_handle(
            state,
            'AirFlow Network Window/Door Opening',
            'Venting Opening Factor',
            'WINDOW_1'
        )
        
        self.handles['heating_sp'] = self.api.exchange.get_actuator_handle(
            state,
            'Schedule:Constant',
            'Schedule Value',
            'HEATING_SETPOINT_SCHEDULE'
        )
        
        self.handles['cooling_sp'] = self.api.exchange.get_actuator_handle(
            state,
            'Schedule:Constant',
            'Schedule Value',
            'COOLING_SETPOINT_SCHEDULE'
        )
        
        # Validate handles
        valid = True
        for name, handle in self.handles.items():
            status = "✅" if handle != -1 else "❌"
            print(f"  {status} {name}: handle = {handle}")
            if handle == -1:
                valid = False
        
        if not valid:
            print("\n❌ ERROR: Some sensors/actuators not found!")
            print("This is expected in demonstration mode without a real IDF.")
            print("In production, ensure IDF contains required objects.")
        else:
            print("\n✅ All sensors and actuators registered successfully!")
        
        # Create log file
        self.log_file = open('realtime_simulation_log.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.log_file)
        self.csv_writer.writerow([
            'Timestamp', 'Day', 'Hour', 'Minute', 'Timestep',
            'Zone_Temp', 'Outdoor_Temp', 'Zone_RH', 'Outdoor_RH',
            'Window_Opening', 'Heating_SP', 'Cooling_SP',
            'Action'
        ])
        print("\n📝 Data logging to: realtime_simulation_log.csv")
    
    def control_logic(self, state):
        """Main control logic executed at each timestep."""
        self.timestep_count += 1
        
        # Get current time
        month = self.api.exchange.month(state)
        day = self.api.exchange.day_of_month(state)
        hour = self.api.exchange.hour(state)
        minute = self.api.exchange.minutes(state)
        current_time = f"{month:02d}/{day:02d} {hour:02d}:{minute:02d}"
        
        # Read sensors
        zone_temp = self.api.exchange.get_variable_value(state, self.handles['zone_temp'])
        outdoor_temp = self.api.exchange.get_variable_value(state, self.handles['outdoor_temp'])
        zone_rh = self.api.exchange.get_variable_value(state, self.handles['zone_humidity'])
        outdoor_rh = self.api.exchange.get_variable_value(state, self.handles['outdoor_rh'])
        
        # Handle None values (early simulation)
        if zone_temp is None:
            zone_temp = 20.0
        if outdoor_temp is None:
            outdoor_temp = 15.0
        if zone_rh is None:
            zone_rh = 50.0
        if outdoor_rh is None:
            outdoor_rh = 60.0
        
        # Update statistics
        self.stats['max_temp'] = max(self.stats['max_temp'], zone_temp)
        self.stats['min_temp'] = min(self.stats['min_temp'], zone_temp)
        
        # === CONTROL LOGIC ===
        actions = []
        
        # 1. Window Control
        temp_diff = zone_temp - outdoor_temp
        window_opening = 0.0
        
        if zone_temp > self.temp_threshold_high and temp_diff > self.temp_diff_min:
            # Hot inside and cooler outside - natural ventilation
            window_opening = min((temp_diff - self.temp_diff_min) / 5.0, 1.0)
            if window_opening > 0.1:
                action = f"OPEN_WINDOW_{int(window_opening*100)}%"
                actions.append(action)
                self.stats['window_openings'] += 1
        else:
            if self.timestep_count > 1:  # Track closings
                prev_opening = self.data_log[-1]['window_opening'] if self.data_log else 0
                if prev_opening > 0:
                    actions.append("CLOSE_WINDOW")
                    self.stats['window_closings'] += 1
        
        # Apply window control
        self.api.exchange.set_actuator_value(state, self.handles['window'], window_opening)
        
        # 2. HVAC Control
        heating_sp = 20.0
        cooling_sp = 24.0
        
        # Adaptive setpoints based on outdoor conditions
        if outdoor_temp < 5:
            # Very cold outside - raise heating setpoint
            heating_sp = 21.0
            actions.append("RAISE_HEATING_SP")
            self.stats['hvac_adjustments'] += 1
        elif outdoor_temp > 30:
            # Very hot outside - lower cooling setpoint
            cooling_sp = 23.0
            actions.append("LOWER_COOLING_SP")
            self.stats['hvac_adjustments'] += 1
        
        # Occupancy-based control (8am-6pm weekdays)
        if 8 <= hour < 18:
            # Occupied hours - comfort priority
            heating_sp = 21.0
            cooling_sp = 24.0
        else:
            # Unoccupied - energy saving
            heating_sp = 18.0
            cooling_sp = 27.0
            if hour == 18 and minute == 0:
                actions.append("ENERGY_SAVING_MODE")
        
        # Apply HVAC control
        self.api.exchange.set_actuator_value(state, self.handles['heating_sp'], heating_sp)
        self.api.exchange.set_actuator_value(state, self.handles['cooling_sp'], cooling_sp)
        
        # === LOGGING ===
        action_str = ", ".join(actions) if actions else "NO_ACTION"
        
        # Log data
        log_entry = {
            'timestamp': current_time,
            'day': day,
            'hour': hour,
            'minute': minute,
            'timestep': self.timestep_count,
            'zone_temp': zone_temp,
            'outdoor_temp': outdoor_temp,
            'zone_rh': zone_rh,
            'outdoor_rh': outdoor_rh,
            'window_opening': window_opening,
            'heating_sp': heating_sp,
            'cooling_sp': cooling_sp,
            'actions': action_str
        }
        self.data_log.append(log_entry)
        
        # Write to CSV
        self.csv_writer.writerow([
            current_time, day, hour, minute, self.timestep_count,
            f"{zone_temp:.2f}", f"{outdoor_temp:.2f}",
            f"{zone_rh:.1f}", f"{outdoor_rh:.1f}",
            f"{int(window_opening*100)}", f"{heating_sp:.1f}", f"{cooling_sp:.1f}",
            action_str
        ])
        self.log_file.flush()  # Ensure immediate write
        
        # === CONSOLE OUTPUT ===
        # Print detailed status every 15 minutes
        if minute % 15 == 0:
            print(f"\n[{current_time}] ⏱️  Timestep {self.timestep_count}")
            print(f"  🌡️  Zone: {zone_temp:.1f}°C | Outdoor: {outdoor_temp:.1f}°C | Δ: {temp_diff:+.1f}°C")
            print(f"  💧 Zone RH: {zone_rh:.0f}% | Outdoor RH: {outdoor_rh:.0f}%")
            print(f"  🪟 Window: {int(window_opening*100):3d}% open")
            print(f"  🔥 Heating SP: {heating_sp:.1f}°C | ❄️  Cooling SP: {cooling_sp:.1f}°C")
            if actions:
                print(f"  ⚡ Actions: {action_str}")
            
            # Status indicators
            if zone_temp > self.temp_threshold_high:
                print(f"  🔴 Temperature HIGH (>{self.temp_threshold_high}°C)")
            elif zone_temp < self.temp_threshold_low:
                print(f"  🔵 Temperature LOW (<{self.temp_threshold_low}°C)")
            else:
                print(f"  🟢 Temperature COMFORTABLE")
            
            if window_opening > 0:
                print(f"  🌬️  Natural ventilation active")
    
    def finalize(self, state):
        """Cleanup and final statistics."""
        self.log_file.close()
        
        print("\n" + "=" * 70)
        print("SIMULATION COMPLETE - FINAL STATISTICS")
        print("=" * 70)
        print(f"\n📊 Simulation Statistics:")
        print(f"  Total timesteps: {self.timestep_count}")
        print(f"  Window openings: {self.stats['window_openings']}")
        print(f"  Window closings: {self.stats['window_closings']}")
        print(f"  HVAC adjustments: {self.stats['hvac_adjustments']}")
        print(f"  Max temperature: {self.stats['max_temp']:.1f}°C")
        print(f"  Min temperature: {self.stats['min_temp']:.1f}°C")
        print(f"\n📁 Results saved to: realtime_simulation_log.csv")
        print("=" * 70)
        
        # Generate simple visualization
        try:
            self.visualize_results()
        except Exception as e:
            print(f"\n⚠️  Visualization skipped: {e}")
    
    def visualize_results(self):
        """Create visualization of results."""
        try:
            import pandas as pd
            import matplotlib.pyplot as plt
        except ImportError:
            print("\n⚠️  matplotlib/pandas not available for visualization")
            return
        
        if not self.data_log:
            print("\n⚠️  No data to visualize")
            return
        
        print("\n📈 Generating visualization...")
        
        # Convert to DataFrame
        df = pd.DataFrame(self.data_log)
        
        # Create plot
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        
        # Plot 1: Temperatures
        ax1 = axes[0]
        ax1.plot(df.index, df['zone_temp'], 'r-', linewidth=2, label='Zone Temperature')
        ax1.plot(df.index, df['outdoor_temp'], 'b-', linewidth=2, label='Outdoor Temperature')
        ax1.axhline(y=self.temp_threshold_high, color='orange', linestyle='--', 
                    label=f'High Threshold ({self.temp_threshold_high}°C)')
        ax1.axhline(y=self.temp_threshold_low, color='cyan', linestyle='--',
                    label=f'Low Threshold ({self.temp_threshold_low}°C)')
        ax1.set_ylabel('Temperature (°C)', fontsize=12)
        ax1.set_title('Real-Time Temperature Monitoring', fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Window Opening
        ax2 = axes[1]
        window_pct = df['window_opening'] * 100
        ax2.fill_between(df.index, 0, window_pct, alpha=0.5, color='green', label='Window Opening')
        ax2.set_ylabel('Window Opening (%)', fontsize=12)
        ax2.set_title('Automatic Window Control', fontsize=14, fontweight='bold')
        ax2.set_ylim(0, 105)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: HVAC Setpoints
        ax3 = axes[2]
        ax3.plot(df.index, df['heating_sp'], 'r-', linewidth=2, label='Heating Setpoint')
        ax3.plot(df.index, df['cooling_sp'], 'b-', linewidth=2, label='Cooling Setpoint')
        ax3.fill_between(df.index, df['heating_sp'], df['cooling_sp'], 
                         alpha=0.2, color='gray', label='Comfort Zone')
        ax3.set_ylabel('Temperature (°C)', fontsize=12)
        ax3.set_xlabel('Timestep', fontsize=12)
        ax3.set_title('Adaptive HVAC Control', fontsize=14, fontweight='bold')
        ax3.legend(loc='best')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('realtime_control_results.png', dpi=300, bbox_inches='tight')
        print("  ✅ Visualization saved to: realtime_control_results.png")
        
        # Show plot
        try:
            plt.show()
        except:
            pass  # May fail in non-interactive environment
    
    def run(self, idf_path='model.idf', epw_path='weather.epw', output_dir='output'):
        """Run simulation with real-time control."""
        state = self.api.state_manager.new_state()
        
        # Register callbacks
        self.api.runtime.callback_begin_new_environment(
            state, self.setup_sensors_actuators
        )
        self.api.runtime.callback_begin_zone_timestep_after_init_heat_balance(
            state, self.control_logic
        )
        self.api.runtime.callback_end_zone_timestep_after_zone_reporting(
            state, self.finalize
        )
        
        # Run simulation
        print(f"\n🚀 Starting simulation...")
        print(f"  IDF: {idf_path}")
        print(f"  EPW: {epw_path}")
        print(f"  Output: {output_dir}")
        print("\n⏳ Running... (this may take several minutes)")
        print("=" * 70)
        
        args = [
            '-w', epw_path,
            '-d', output_dir,
            idf_path
        ]
        
        try:
            self.api.runtime.run_energyplus(state, args)
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")
            print("\nThis is expected in demonstration mode without actual IDF/EPW files.")
            print("In production, provide valid EnergyPlus model and weather files.")


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: REAL-TIME MONITORING AND CONTROL")
    print("=" * 70)
    print("\nThis example demonstrates:")
    print("  • Real-time temperature monitoring")
    print("  • Automatic window control based on conditions")
    print("  • Adaptive HVAC setpoint adjustment")
    print("  • Live console output showing changes")
    print("  • Data logging for post-simulation analysis")
    print("  • Visualization of control actions")
    print("=" * 70)
    
    # Create controller
    controller = RealTimeController()
    
    # In production, use actual files:
    # controller.run('path/to/model.idf', 'path/to/weather.epw')
    
    # For demonstration, show the structure
    print("\n📝 DEMONSTRATION MODE")
    print("\nTo run with actual simulation:")
    print("  1. Prepare EnergyPlus IDF file with:")
    print("     - Zone named 'ZONE_1'")
    print("     - Window named 'WINDOW_1' with AirflowNetwork")
    print("     - Heating and cooling setpoint schedules")
    print("  2. Provide weather file (EPW)")
    print("  3. Run: controller.run('model.idf', 'weather.epw')")
    print("\nThe controller will:")
    print("  ✓ Monitor temperatures every timestep")
    print("  ✓ Open windows when beneficial for cooling")
    print("  ✓ Adjust HVAC setpoints based on conditions")
    print("  ✓ Log all data to CSV file")
    print("  ✓ Print status updates every 15 minutes")
    print("  ✓ Generate visualization at the end")
    print("\n" + "=" * 70)
    
    # Demonstrate the workflow (without actual simulation)
    print("\n🎯 WORKFLOW SUMMARY:")
    print("\n1️⃣  INITIALIZATION")
    print("   → Create RealTimeController")
    print("   → Set control thresholds")
    
    print("\n2️⃣  SENSOR/ACTUATOR SETUP (once at start)")
    print("   → Register temperature sensors")
    print("   → Register humidity sensors")
    print("   → Register window actuator")
    print("   → Register HVAC actuators")
    
    print("\n3️⃣  CONTROL LOOP (every timestep)")
    print("   → Read sensor values")
    print("   → Evaluate control logic")
    print("   → Set actuator values")
    print("   → Log data")
    print("   → Print status")
    
    print("\n4️⃣  VISUALIZATION (at end)")
    print("   → Generate temperature plot")
    print("   → Generate window control plot")
    print("   → Generate HVAC setpoint plot")
    print("   → Save results")
    
    print("\n" + "=" * 70)
    print("✅ Example complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
