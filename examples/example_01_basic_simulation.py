"""
Example 1: Basic Simulation Control

This example demonstrates basic simulation creation, configuration,
and execution using the EP-Room-Simulator Python API.
"""

import sys
import os

# Add parent directory to path to import API modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api import SimulationAPI, SimulationConfig


def main():
    """Run a basic simulation example."""
    
    print("EP-Room-Simulator API - Basic Example")
    print("=" * 50)
    
    # Initialize API client
    print("\n1. Initializing API client...")
    api = SimulationAPI(base_url='http://localhost:5000')
    print("   ✓ Connected to backend")
    
    # Build configuration
    print("\n2. Building simulation configuration...")
    config = (SimulationConfig()
        .with_idf_file('models/example_office.idf')
        .with_epw_file('weather/chicago.epw')
        .with_room_dimensions(width=5.0, length=6.0, height=3.0)
        .with_simulation_period('2024-01-01', '2024-01-31')
        .with_timestep(10)
        .build())
    print("   ✓ Configuration built")
    
    # Create simulation
    print("\n3. Creating simulation...")
    sim = api.create_simulation(
        name='Basic Office Simulation',
        description='Example simulation using Python API'
    )
    print(f"   ✓ Simulation created with ID: {sim.sim_id}")
    
    # Configure simulation
    print("\n4. Applying configuration...")
    sim.configure(config)
    print("   ✓ Configuration applied")
    
    # Start simulation
    print("\n5. Starting simulation...")
    sim.start(async_mode=False)  # Wait for completion
    print("   ✓ Simulation completed")
    
    # Get results
    print("\n6. Retrieving results...")
    results = sim.get_results(output_format='json')
    print(f"   ✓ Retrieved {len(results)} data points")
    
    print("\n" + "=" * 50)
    print("Simulation completed successfully!")
    print(f"Simulation ID: {sim.sim_id}")
    
    return sim.sim_id


if __name__ == '__main__':
    try:
        sim_id = main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
