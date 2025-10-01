"""
Example 5: Multi-Zone Simulation

This example demonstrates how to create and manage multi-zone simulations
with multiple IDF files and inter-zone connections.
"""

import sys
import os

# Add parent directory to path to import API modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api import SimulationAPI, MultiZoneManager, MultiZoneStateManager


def main():
    """Run multi-zone simulation example."""
    
    print("EP-Room-Simulator API - Multi-Zone Simulation")
    print("=" * 60)
    
    # Initialize API
    print("\n1. Initializing API client...")
    api = SimulationAPI(base_url='http://localhost:5000')
    print("   ✓ Connected to backend")
    
    # Create multi-zone manager
    print("\n2. Creating multi-zone manager...")
    manager = MultiZoneManager(api)
    print("   ✓ Multi-zone manager created")
    
    # Define zones
    print("\n3. Defining zones...")
    
    # Office zones
    zone1 = manager.add_zone(
        zone_id='office_1',
        zone_name='Office Room 1',
        idf_file='models/office.idf'
    )
    zone1.set_parameter('width', 5.0)
    zone1.set_parameter('length', 6.0)
    zone1.set_parameter('height', 3.0)
    print("   ✓ Added Office Room 1")
    
    zone2 = manager.add_zone(
        zone_id='office_2',
        zone_name='Office Room 2',
        idf_file='models/office.idf'
    )
    zone2.set_parameter('width', 5.0)
    zone2.set_parameter('length', 6.0)
    zone2.set_parameter('height', 3.0)
    print("   ✓ Added Office Room 2")
    
    # Corridor
    corridor = manager.add_zone(
        zone_id='corridor',
        zone_name='Corridor',
        idf_file='models/corridor.idf'
    )
    corridor.set_parameter('width', 2.5)
    corridor.set_parameter('length', 10.0)
    corridor.set_parameter('height', 3.0)
    print("   ✓ Added Corridor")
    
    # Meeting room
    meeting = manager.add_zone(
        zone_id='meeting',
        zone_name='Meeting Room',
        idf_file='models/meeting_room.idf'
    )
    meeting.set_parameter('width', 8.0)
    meeting.set_parameter('length', 6.0)
    meeting.set_parameter('height', 3.5)
    print("   ✓ Added Meeting Room")
    
    # Define connections
    print("\n4. Defining zone connections...")
    
    # Office 1 connects to corridor
    manager.connect_zones(
        from_zone='office_1',
        to_zone='corridor',
        connection_type='airflow',
        airflow_rate=0.05  # m³/s
    )
    print("   ✓ Connected Office 1 to Corridor")
    
    # Office 2 connects to corridor
    manager.connect_zones(
        from_zone='office_2',
        to_zone='corridor',
        connection_type='airflow',
        airflow_rate=0.05
    )
    print("   ✓ Connected Office 2 to Corridor")
    
    # Meeting room connects to corridor
    manager.connect_zones(
        from_zone='meeting',
        to_zone='corridor',
        connection_type='airflow',
        airflow_rate=0.10
    )
    print("   ✓ Connected Meeting Room to Corridor")
    
    # Set parameters for all zones
    print("\n5. Setting common parameters...")
    manager.set_all_zones_parameter('infiltration_rate', 0.0019)
    manager.set_all_zones_parameter('max_occupants', 4)
    print("   ✓ Set common parameters")
    
    # Set zone-specific parameters
    print("\n6. Setting zone-specific parameters...")
    manager.set_zone_parameter('meeting', 'max_occupants', 12)
    manager.set_zone_parameter('corridor', 'max_occupants', 0)
    print("   ✓ Set zone-specific parameters")
    
    # Export configuration
    print("\n7. Exporting configuration...")
    config = manager.export_configuration()
    
    import json
    with open('multi_zone_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("   ✓ Configuration saved to multi_zone_config.json")
    
    # Display summary
    print("\n8. Configuration Summary:")
    print(f"   Total zones: {len(manager.get_zone_list())}")
    print(f"   Zones: {', '.join(manager.get_zone_list())}")
    print(f"   Total connections: {len(manager.zone_connections)}")
    
    print("\n   Zone Details:")
    for zone_id in manager.get_zone_list():
        info = manager.get_zone_info(zone_id)
        print(f"   - {info['zone_name']} ({zone_id})")
        print(f"     IDF: {info['idf_file']}")
        print(f"     Parameters: {info['parameters']}")
        print(f"     Connections: {len(info['connections'])}")
    
    # Create simulation (requires backend support)
    print("\n9. Creating multi-zone simulation...")
    print("   ⚠ Note: Full multi-zone simulation requires backend support")
    
    try:
        sim = manager.create_simulation(
            name='Multi-Zone Office Building',
            description='4-zone building with offices, meeting room, and corridor'
        )
        print(f"   ✓ Simulation created: {sim.sim_id}")
    except Exception as e:
        print(f"   ⚠ Simulation creation: {e}")
    
    print("\n" + "=" * 60)
    print("Multi-zone simulation example completed!")
    print("\nNext steps:")
    print("  1. Backend implementation for multi-zone support")
    print("  2. Inter-zone air flow modeling")
    print("  3. Thermal coupling between zones")
    print("  4. Zone-specific control strategies")


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
