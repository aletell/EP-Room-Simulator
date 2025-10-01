"""
Example 6: Real-Time Monitoring and Adaptive Control

This example demonstrates real-time simulation monitoring and adaptive
control strategies that modify simulation parameters based on current conditions.
"""

import sys
import os
import time

# Add parent directory to path to import API modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api import (
    SimulationAPI,
    SimulationConfig,
    SimulationMonitor,
    AdaptiveController,
    StateManager
)


def main():
    """Run real-time monitoring and adaptive control example."""
    
    print("EP-Room-Simulator API - Real-Time Monitoring & Adaptive Control")
    print("=" * 70)
    
    # Initialize API
    print("\n1. Initializing API client...")
    api = SimulationAPI(base_url='http://localhost:5000')
    state_manager = StateManager(base_url='http://localhost:5000')
    print("   ✓ Connected to backend")
    
    # Create and configure simulation
    print("\n2. Creating simulation...")
    config = (SimulationConfig()
        .with_idf_file('models/office.idf')
        .with_epw_file('weather/chicago.epw')
        .with_room_dimensions(5.0, 6.0, 3.0)
        .with_simulation_period('2024-01-01', '2024-01-07')
        .build())
    
    sim = api.create_simulation('Adaptive Control Demo')
    sim.configure(config)
    print(f"   ✓ Simulation created: {sim.sim_id}")
    
    # Set up monitoring
    print("\n3. Setting up real-time monitoring...")
    monitor = SimulationMonitor(sim.sim_id)
    
    # Add custom callback for logging
    def log_state(state):
        """Log important metrics."""
        temp = state.get('zone_temperature', 0)
        co2 = state.get('zone_co2', 0)
        progress = state.get('percent_complete', 0)
        print(f"   📊 Progress: {progress:.1f}% | Temp: {temp:.1f}°C | CO2: {co2:.0f} ppm")
    
    monitor.add_callback(log_state)
    print("   ✓ Added state logging callback")
    
    # Add threshold alerts
    print("\n4. Configuring threshold alerts...")
    
    # Temperature alert
    monitor.add_threshold_alert(
        variable='zone_temperature',
        operator='>',
        threshold=26.0,
        callback=lambda val: print(f"   🌡️  HIGH TEMPERATURE ALERT: {val:.1f}°C")
    )
    print("   ✓ Added high temperature alert (>26°C)")
    
    # CO2 alert
    monitor.add_threshold_alert(
        variable='zone_co2',
        operator='>',
        threshold=1000.0,
        callback=lambda val: print(f"   💨 HIGH CO2 ALERT: {val:.0f} ppm")
    )
    print("   ✓ Added high CO2 alert (>1000 ppm)")
    
    # Low temperature alert
    monitor.add_threshold_alert(
        variable='zone_temperature',
        operator='<',
        threshold=18.0,
        callback=lambda val: print(f"   ❄️  LOW TEMPERATURE ALERT: {val:.1f}°C")
    )
    print("   ✓ Added low temperature alert (<18°C)")
    
    # Set up adaptive controller
    print("\n5. Configuring adaptive control rules...")
    controller = AdaptiveController(sim.sim_id)
    
    # Rule 1: Open windows when temperature is too high
    controller.add_rule(
        name='High Temperature Ventilation',
        condition=lambda state: state.get('zone_temperature', 20) > 26,
        action=lambda: state_manager.set_window_state(sim.sim_id, 'WINDOW_1', True),
        cooldown=300  # 5 minutes between actions
    )
    print("   ✓ Added high temperature ventilation rule")
    
    # Rule 2: Close windows when temperature is too low
    controller.add_rule(
        name='Low Temperature Conservation',
        condition=lambda state: state.get('zone_temperature', 20) < 19,
        action=lambda: state_manager.set_window_state(sim.sim_id, 'WINDOW_1', False),
        cooldown=300
    )
    print("   ✓ Added low temperature conservation rule")
    
    # Rule 3: Increase ventilation when CO2 is high
    controller.add_rule(
        name='High CO2 Ventilation',
        condition=lambda state: state.get('zone_co2', 400) > 1000,
        action=lambda: state_manager.set_ventilation_rate(sim.sim_id, 'ZONE_1', 5.0, 'ach'),
        cooldown=600  # 10 minutes
    )
    print("   ✓ Added high CO2 ventilation rule")
    
    # Rule 4: Adjust HVAC setpoints based on occupancy
    controller.add_rule(
        name='Occupancy-Based HVAC',
        condition=lambda state: state.get('zone_occupancy', 0) > 10,
        action=lambda: state_manager.set_hvac_setpoint(
            sim.sim_id, 'ZONE_1',
            heating_setpoint=21.0,
            cooling_setpoint=24.0
        ),
        cooldown=1800  # 30 minutes
    )
    print("   ✓ Added occupancy-based HVAC rule")
    
    # Start simulation
    print("\n6. Starting simulation with adaptive control...")
    print("   ⚠ Note: This example demonstrates the API structure.")
    print("   ⚠ Full functionality requires backend support for real-time control.")
    
    sim.start(async_mode=True)
    
    # Start monitoring and adaptive control
    print("\n7. Activating monitoring and adaptive control...")
    monitor.start(interval=10)  # Check every 10 seconds
    controller.start(interval=60)  # Evaluate rules every minute
    print("   ✓ Monitoring and control activated")
    
    # Monitor for a period
    print("\n8. Monitoring simulation (this would run for the full simulation)...")
    print("   Press Ctrl+C to stop early\n")
    
    try:
        # In a real scenario, this would run until simulation completes
        # For demonstration, we'll run for a short time
        duration = 120  # 2 minutes for demo
        start_time = time.time()
        
        while time.time() - start_time < duration:
            time.sleep(1)
            
            # Check if simulation is complete
            if sim.is_complete():
                print("\n   ✓ Simulation completed!")
                break
                
    except KeyboardInterrupt:
        print("\n\n   ⚠ Monitoring interrupted by user")
    
    # Stop monitoring and control
    print("\n9. Stopping monitoring and control...")
    controller.stop()
    monitor.stop()
    print("   ✓ Stopped")
    
    # Display monitoring history
    print("\n10. Monitoring Summary:")
    history = monitor.get_history(minutes=10)
    if history:
        print(f"   Collected {len(history)} state snapshots")
        
        # Show trend for temperature if available
        temp_trend = monitor.get_variable_trend('zone_temperature', minutes=10)
        if temp_trend:
            avg_temp = sum(temp_trend) / len(temp_trend)
            min_temp = min(temp_trend)
            max_temp = max(temp_trend)
            print(f"   Temperature: avg={avg_temp:.1f}°C, min={min_temp:.1f}°C, max={max_temp:.1f}°C")
    else:
        print("   No monitoring data collected (backend support required)")
    
    # Display control history
    print("\n11. Adaptive Control Summary:")
    rule_history = controller.get_rule_history(minutes=10)
    if rule_history:
        print(f"   Executed {len(rule_history)} control actions:")
        for record in rule_history:
            print(f"   - {record['timestamp']}: {record['rule']}")
    else:
        print("   No control actions executed")
    
    print("\n" + "=" * 70)
    print("Real-time monitoring and adaptive control example completed!")
    print("\nKey Capabilities Demonstrated:")
    print("  ✓ Real-time state monitoring")
    print("  ✓ Threshold-based alerts")
    print("  ✓ Adaptive control rules")
    print("  ✓ Historical data collection")
    print("  ✓ Variable trend analysis")
    
    print("\nBackend Requirements for Full Functionality:")
    print("  - Real-time state inspection endpoints")
    print("  - Variable modification during simulation")
    print("  - Simulation pause/resume capabilities")
    print("  - WebSocket or polling for live updates")


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
