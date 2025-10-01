"""
Example 7: EnergyPlus Python API Integration

This example demonstrates direct integration with the EnergyPlus Python API
for runtime control, going beyond eppy's capabilities.

Features demonstrated:
- Direct sensor/actuator access during simulation
- Real-time window control based on conditions
- Dynamic HVAC setpoint adjustment
- Runtime state inspection
- Custom control logic execution
"""

import sys
import os

# Add parent directory to path to import API modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api import ENERGYPLUS_RUNTIME_AVAILABLE

if not ENERGYPLUS_RUNTIME_AVAILABLE:
    print("=" * 70)
    print("EnergyPlus Python API Integration Example")
    print("=" * 70)
    print("\n❌ ERROR: EnergyPlus Python API not available")
    print("\nThis example requires the pyenergyplus package.")
    print("Install with: pip install pyenergyplus")
    print("\nNote: This requires EnergyPlus 9.3 or later to be installed.")
    print("=" * 70)
    sys.exit(1)

from api import (
    EnergyPlusRuntime,
    WindowController,
    HVACController,
    create_runtime_controller
)


def example_basic_runtime():
    """Example 1: Basic runtime control with sensors and actuators."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Runtime Control")
    print("=" * 70)
    
    # Create runtime controller
    runtime = EnergyPlusRuntime()
    
    # Register sensors
    print("\n1. Registering sensors...")
    runtime.register_sensor(
        'zone_temperature',
        'Zone Mean Air Temperature',
        'ZONE_1'
    )
    runtime.register_sensor(
        'outdoor_temperature',
        'Site Outdoor Air Drybulb Temperature',
        'Environment'
    )
    print("   ✓ Sensors registered")
    
    # Register actuators
    print("\n2. Registering actuators...")
    runtime.register_actuator(
        'window_opening',
        'AirFlow Network Window/Door Opening',
        'Venting Opening Factor',
        'WINDOW_1'
    )
    print("   ✓ Actuators registered")
    
    # Define control logic
    print("\n3. Defining control logic...")
    
    @runtime.on_timestep
    def simple_control(state):
        """Simple window control based on temperature."""
        zone_temp = runtime.get_sensor_value('zone_temperature')
        outdoor_temp = runtime.get_sensor_value('outdoor_temperature')
        
        if zone_temp is not None and outdoor_temp is not None:
            # Open window if too hot inside and cooler outside
            if zone_temp > 26 and outdoor_temp < zone_temp - 2:
                runtime.set_actuator_value('window_opening', 1.0)
                print(f"   🪟 Opening window: Indoor={zone_temp:.1f}°C, Outdoor={outdoor_temp:.1f}°C")
            else:
                runtime.set_actuator_value('window_opening', 0.0)
    
    print("   ✓ Control logic defined")
    
    # Run simulation (would use actual IDF and EPW files)
    print("\n4. Simulation would run with:")
    print("   runtime.run_simulation('model.idf', 'weather.epw')")
    print("   ✓ Setup complete")


def example_window_controller():
    """Example 2: Advanced window control."""
    print("\n" + "=" * 70)
    print("Example 2: Advanced Window Controller")
    print("=" * 70)
    
    # Create runtime
    runtime = EnergyPlusRuntime()
    
    # Create window controller
    print("\n1. Creating window controller...")
    window_ctrl = WindowController(runtime)
    
    # Configure controller
    window_ctrl.config['temp_threshold_high'] = 26.0
    window_ctrl.config['temp_threshold_low'] = 20.0
    window_ctrl.config['outdoor_temp_max'] = 28.0
    window_ctrl.config['wind_speed_max'] = 10.0
    print("   ✓ Controller configured")
    
    # Setup sensors and actuators
    print("\n2. Setting up sensors and actuators...")
    window_ctrl.setup_sensors_actuators('ZONE_1', 'WINDOW_1')
    print("   ✓ Setup complete")
    
    # Register control callback
    print("\n3. Registering adaptive control...")
    runtime.on_timestep(window_ctrl.adaptive_control)
    print("   ✓ Control registered")
    
    print("\n4. Window control strategy:")
    print("   - Opens when indoor temp > 26°C and outdoor is cooler")
    print("   - Closes when indoor temp < 20°C")
    print("   - Closes when outdoor temp > 28°C (too hot)")
    print("   - Closes when wind speed > 10 m/s")
    print("   - Partial opening (30%) when occupied and comfortable")


def example_hvac_controller():
    """Example 3: Dynamic HVAC control."""
    print("\n" + "=" * 70)
    print("Example 3: Dynamic HVAC Controller")
    print("=" * 70)
    
    # Create runtime
    runtime = EnergyPlusRuntime()
    
    # Create HVAC controller
    print("\n1. Creating HVAC controller...")
    hvac_ctrl = HVACController(runtime)
    
    # Configure controller
    hvac_ctrl.config['occupied_heating_setpoint'] = 21.0
    hvac_ctrl.config['occupied_cooling_setpoint'] = 24.0
    hvac_ctrl.config['unoccupied_heating_setpoint'] = 18.0
    hvac_ctrl.config['unoccupied_cooling_setpoint'] = 28.0
    print("   ✓ Controller configured")
    
    # Setup sensors and actuators
    print("\n2. Setting up sensors and actuators...")
    hvac_ctrl.setup_sensors_actuators('ZONE_1')
    print("   ✓ Setup complete")
    
    # Register control callback
    print("\n3. Registering adaptive control...")
    runtime.on_timestep(hvac_ctrl.adaptive_control)
    print("   ✓ Control registered")
    
    print("\n4. HVAC control strategy:")
    print("   Occupied setpoints:")
    print("   - Heating: 21.0°C")
    print("   - Cooling: 24.0°C")
    print("   Unoccupied setpoints (energy saving):")
    print("   - Heating: 18.0°C")
    print("   - Cooling: 28.0°C")


def example_combined_control():
    """Example 4: Combined window and HVAC control."""
    print("\n" + "=" * 70)
    print("Example 4: Combined Window & HVAC Control")
    print("=" * 70)
    
    # Create preconfigured controller
    print("\n1. Creating combined controller...")
    runtime = create_runtime_controller(
        'model.idf',
        'weather.epw',
        zone_name='ZONE_1',
        window_name='WINDOW_1'
    )
    print("   ✓ Controller created with:")
    print("     - Window control")
    print("     - HVAC control")
    print("     - Coordinated operation")
    
    print("\n2. Control coordination:")
    print("   - Windows open for free cooling when possible")
    print("   - HVAC adjusts based on occupancy")
    print("   - Energy-efficient operation prioritized")
    
    print("\n3. To run:")
    print("   runtime.run_simulation('model.idf', 'weather.epw')")


def example_custom_control():
    """Example 5: Custom control logic."""
    print("\n" + "=" * 70)
    print("Example 5: Custom Control Logic")
    print("=" * 70)
    
    # Create runtime
    runtime = EnergyPlusRuntime()
    
    # Setup sensors
    print("\n1. Setting up sensors...")
    runtime.register_sensor('zone_temp', 'Zone Mean Air Temperature', 'ZONE_1')
    runtime.register_sensor('zone_humidity', 'Zone Air Relative Humidity', 'ZONE_1')
    runtime.register_sensor('zone_co2', 'Zone Air CO2 Concentration', 'ZONE_1')
    runtime.register_sensor('occupancy', 'Zone People Occupant Count', 'ZONE_1')
    print("   ✓ Sensors registered")
    
    # Setup actuators
    print("\n2. Setting up actuators...")
    runtime.register_actuator(
        'ventilation',
        'Zone Ventilation',
        'Air Exchange Flow Rate',
        'ZONE_1'
    )
    runtime.register_actuator(
        'window',
        'AirFlow Network Window/Door Opening',
        'Venting Opening Factor',
        'WINDOW_1'
    )
    print("   ✓ Actuators registered")
    
    # Define custom control
    print("\n3. Defining custom control logic...")
    
    @runtime.on_timestep
    def custom_control(state):
        """Custom control based on multiple factors."""
        # Get all sensor values
        temp = runtime.get_sensor_value('zone_temp')
        humidity = runtime.get_sensor_value('zone_humidity')
        co2 = runtime.get_sensor_value('zone_co2')
        occ = runtime.get_sensor_value('occupancy')
        
        if None in [temp, humidity, co2, occ]:
            return
        
        # Ventilation control based on CO2
        if co2 > 1000:
            vent_rate = 0.01  # High ventilation
        elif co2 > 800:
            vent_rate = 0.005  # Medium ventilation
        else:
            vent_rate = 0.002  # Low ventilation
            
        runtime.set_actuator_value('ventilation', vent_rate)
        
        # Window control based on temperature and humidity
        if temp > 26 and humidity < 70:
            runtime.set_actuator_value('window', 1.0)  # Open
        elif temp > 24 and humidity > 70:
            runtime.set_actuator_value('window', 0.5)  # Partial
        else:
            runtime.set_actuator_value('window', 0.0)  # Close
    
    print("   ✓ Custom control defined")
    print("\n4. Control logic:")
    print("   - CO2-based ventilation control")
    print("   - Temperature and humidity-based window control")
    print("   - Coordinated operation for comfort and air quality")


def example_comparison():
    """Example 6: Comparison with eppy."""
    print("\n" + "=" * 70)
    print("Example 6: eppy vs EnergyPlus Python API")
    print("=" * 70)
    
    print("\n📊 Capability Comparison:")
    print("\n┌─────────────────────────────┬────────┬─────────────┐")
    print("│ Feature                     │ eppy   │ EP Python API│")
    print("├─────────────────────────────┼────────┼─────────────┤")
    print("│ IDF file manipulation       │   ✅   │      ⚠️     │")
    print("│ Runtime state access        │   ❌   │      ✅     │")
    print("│ Modify during simulation    │   ❌   │      ✅     │")
    print("│ Real-time control           │   ❌   │      ✅     │")
    print("│ Window opening control      │   ⚠️*  │      ✅     │")
    print("│ Dynamic HVAC control        │   ❌   │      ✅     │")
    print("│ External data integration   │   ❌   │      ✅     │")
    print("│ Ease of use                 │   ✅   │      ⚠️     │")
    print("└─────────────────────────────┴────────┴─────────────┘")
    print("\n* eppy can set schedules, but not modify during simulation")
    
    print("\n🎯 Best Practice - Use Both:")
    print("   1. Use eppy for IDF file setup and configuration")
    print("   2. Use EnergyPlus Python API for runtime control")
    print("   3. Combine for maximum flexibility")
    
    print("\n💡 Example workflow:")
    print("   ```python")
    print("   # 1. Setup with eppy")
    print("   from eppy.modeleditor import IDF")
    print("   idf = IDF('model.idf', 'weather.epw')")
    print("   # Modify IDF as needed")
    print("   idf.saveas('prepared.idf')")
    print("   ")
    print("   # 2. Run with EnergyPlus Python API")
    print("   runtime = create_runtime_controller('prepared.idf', 'weather.epw')")
    print("   runtime.run_simulation('prepared.idf', 'weather.epw')")
    print("   ```")


def main():
    """Run all examples."""
    print("=" * 70)
    print("EnergyPlus Python API Integration Examples")
    print("=" * 70)
    print("\nThese examples demonstrate how to use the EnergyPlus Python API")
    print("for runtime control, going beyond eppy's capabilities.")
    print("\nNote: These are demonstration examples showing the API structure.")
    print("To run actual simulations, you need:")
    print("  - EnergyPlus 9.3 or later installed")
    print("  - pyenergyplus package (pip install pyenergyplus)")
    print("  - Properly configured IDF and EPW files")
    
    # Run examples
    example_basic_runtime()
    example_window_controller()
    example_hvac_controller()
    example_combined_control()
    example_custom_control()
    example_comparison()
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
    
    print("\n📚 Next Steps:")
    print("  1. Review ENERGYPLUS_API_INTEGRATION.md for detailed documentation")
    print("  2. Prepare IDF file with sensors and actuators")
    print("  3. Implement your custom control logic")
    print("  4. Run simulation with runtime control")
    
    print("\n🔗 Resources:")
    print("  - EnergyPlus Python API: https://energyplus.readthedocs.io/en/latest/api.html")
    print("  - eppy Documentation: https://eppy.readthedocs.io/")
    print("  - Project Documentation: ENERGYPLUS_API_INTEGRATION.md")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
