"""
Example 2: Dynamic State Modification

This example demonstrates how to use the StateManager to inspect
and modify simulation state during execution.
"""

import sys
import os
import time

# Add parent directory to path to import API modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api import SimulationAPI, StateManager, SimulationConfig


def main():
    """Run dynamic state modification example."""
    
    print("EP-Room-Simulator API - Dynamic State Modification")
    print("=" * 60)
    
    # Initialize API client and state manager
    print("\n1. Initializing API client and state manager...")
    api = SimulationAPI(base_url='http://localhost:5000')
    state_manager = StateManager(base_url='http://localhost:5000')
    print("   ✓ Connected to backend")
    
    # Build configuration
    print("\n2. Building simulation configuration...")
    config = (SimulationConfig()
        .with_idf_file('models/example_office.idf')
        .with_epw_file('weather/chicago.epw')
        .with_room_dimensions(width=5.0, length=6.0, height=3.0)
        .with_simulation_period('2024-01-01', '2024-01-07')  # One week
        .with_timestep(15)
        .build())
    print("   ✓ Configuration built")
    
    # Create and start simulation
    print("\n3. Creating and starting simulation...")
    sim = api.create_simulation(
        name='Dynamic Control Example',
        description='Demonstration of state modification during execution'
    )
    sim.configure(config)
    sim.start(async_mode=True)  # Start asynchronously
    print(f"   ✓ Simulation started (ID: {sim.sim_id})")
    
    # Monitor and control simulation
    print("\n4. Monitoring and controlling simulation...")
    print("   (Note: State modification requires backend support)")
    
    # Simulate checking conditions every hour
    hour_count = 0
    max_hours = 24  # Monitor for 24 hours
    
    while hour_count < max_hours and not sim.is_complete():
        time.sleep(10)  # Wait 10 seconds between checks
        
        try:
            # Get current state
            variables = state_manager.get_all_variables(sim.sim_id)
            
            if variables:
                temp = state_manager.get_zone_temperature(sim.sim_id, 'ZONE_1')
                print(f"   Hour {hour_count}: Temperature = {temp}°C")
                
                # Adaptive control logic
                if temp > 26.0:
                    print(f"   → Temperature too high! Opening windows...")
                    state_manager.set_window_state(sim.sim_id, 'WINDOW_1', is_open=True)
                elif temp < 20.0:
                    print(f"   → Temperature too low! Closing windows...")
                    state_manager.set_window_state(sim.sim_id, 'WINDOW_1', is_open=False)
                    
        except Exception as e:
            print(f"   ⚠ State access not yet available: {e}")
            break
            
        hour_count += 1
    
    # Wait for completion if still running
    if not sim.is_complete():
        print("\n5. Waiting for simulation to complete...")
        sim.wait_for_completion()
    
    print("   ✓ Simulation completed")
    
    # Get results
    print("\n6. Retrieving results...")
    results = sim.get_results(output_format='json')
    print(f"   ✓ Retrieved results")
    
    print("\n" + "=" * 60)
    print("Dynamic control example completed!")
    print(f"Simulation ID: {sim.sim_id}")
    
    return sim.sim_id


if __name__ == '__main__':
    try:
        sim_id = main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
