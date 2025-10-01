"""
Example 3: Event-Driven Simulation Control

This example demonstrates using event handlers to respond to
simulation lifecycle events.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path to import API modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api import SimulationAPI, SimulationConfig, SimulationEventHandler


def main():
    """Run event-driven simulation example."""
    
    print("EP-Room-Simulator API - Event-Driven Control")
    print("=" * 60)
    
    # Initialize API and event handler
    print("\n1. Initializing API client and event handler...")
    api = SimulationAPI(base_url='http://localhost:5000')
    events = SimulationEventHandler()
    print("   ✓ Connected to backend")
    
    # Register event callbacks
    print("\n2. Registering event callbacks...")
    
    @events.on_start
    def simulation_started(sim_id):
        """Called when simulation starts."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n   [EVENT] Simulation started at {timestamp}")
        print(f"   [EVENT] Simulation ID: {sim_id}")
        
    @events.on_timestep
    def check_conditions(timestep, state):
        """Called at each timestep."""
        if timestep % 100 == 0:  # Log every 100 timesteps
            print(f"   [EVENT] Timestep {timestep}")
            
            # Example adaptive control
            temp = state.get('temperature', 0)
            co2 = state.get('co2_level', 0)
            
            if co2 > 1000:
                print(f"   [EVENT] High CO2 detected ({co2} ppm) - Increasing ventilation")
            elif temp > 26:
                print(f"   [EVENT] High temperature detected ({temp}°C) - Opening windows")
                
    @events.on_complete
    def save_results(results):
        """Called when simulation completes."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n   [EVENT] Simulation completed at {timestamp}")
        
        # Save results to file
        try:
            import pandas as pd
            df = pd.DataFrame(results)
            output_file = f'results_{timestamp.replace(":", "-")}.csv'
            df.to_csv(output_file, index=False)
            print(f"   [EVENT] Results saved to {output_file}")
        except Exception as e:
            print(f"   [EVENT] Could not save results: {e}")
            
    @events.on_error
    def handle_error(error):
        """Called when an error occurs."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n   [EVENT] Error occurred at {timestamp}")
        print(f"   [EVENT] Error: {error}")
        
        # Could send notification, log to file, etc.
        with open('simulation_errors.log', 'a') as f:
            f.write(f"{timestamp}: {error}\n")
            
    print("   ✓ Event callbacks registered")
    
    # Build configuration
    print("\n3. Building simulation configuration...")
    config = (SimulationConfig()
        .with_idf_file('models/example_office.idf')
        .with_epw_file('weather/chicago.epw')
        .with_room_dimensions(width=5.0, length=6.0, height=3.0)
        .with_simulation_period('2024-01-01', '2024-01-07')
        .with_timestep(10)
        .build())
    print("   ✓ Configuration built")
    
    # Create simulation
    print("\n4. Creating simulation...")
    sim = api.create_simulation(
        name='Event-Driven Example',
        description='Demonstration of event-driven simulation control'
    )
    print(f"   ✓ Simulation created (ID: {sim.sim_id})")
    
    # Attach event handler
    print("\n5. Attaching event handler...")
    events.attach(sim.sim_id)
    print("   ✓ Event handler attached")
    
    # Configure and start simulation
    print("\n6. Starting simulation...")
    sim.configure(config)
    
    # Trigger start event
    events.trigger(events.EventType.START, sim.sim_id)
    
    sim.start(async_mode=True)
    
    # Monitor simulation (in real implementation, events would be triggered by backend)
    print("\n7. Monitoring simulation...")
    while not sim.is_complete():
        time.sleep(5)
        status = sim.get_status()
        
        # In a real implementation, timestep events would be triggered automatically
        # Here we simulate it for demonstration
        if status.get('status') == 'in Progress':
            # Simulate timestep event (would be triggered by backend in real implementation)
            pass
            
    # Trigger complete event
    try:
        results = sim.get_results(output_format='json')
        events.trigger(events.EventType.COMPLETE, results)
    except Exception as e:
        events.trigger(events.EventType.ERROR, e)
    
    print("\n" + "=" * 60)
    print("Event-driven example completed!")
    print(f"Simulation ID: {sim.sim_id}")
    
    # Detach event handler
    events.detach(sim.sim_id)
    
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
