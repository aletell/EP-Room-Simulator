# Enhanced API Features - Multi-Zone and Real-Time Control

## Overview

This document describes the enhanced API features added to support:
1. **Multi-zone simulations** with multiple IDF files
2. **Real-time monitoring** of simulation execution
3. **Adaptive control** for dynamic parameter modification
4. **Enhanced state management** with comprehensive variable access

## Multi-Zone Simulation Support

### MultiZoneManager

The `MultiZoneManager` class enables complex building simulations with multiple zones and IDF files.

#### Key Features

- Define multiple zones from different IDF files
- Connect zones for air flow and thermal exchange
- Set parameters for individual zones or all zones
- Export/import zone configurations
- Coordinate multi-zone simulation execution

#### Example Usage

```python
from backend.api import SimulationAPI, MultiZoneManager

# Initialize
api = SimulationAPI()
manager = MultiZoneManager(api)

# Add zones
zone1 = manager.add_zone('office_1', 'Office Room 1', 'office.idf')
zone2 = manager.add_zone('office_2', 'Office Room 2', 'office.idf')
corridor = manager.add_zone('corridor', 'Corridor', 'corridor.idf')

# Set parameters
zone1.set_parameter('width', 5.0)
zone1.set_parameter('max_occupants', 4)

# Connect zones for airflow
manager.connect_zones('office_1', 'corridor', airflow_rate=0.05)
manager.connect_zones('office_2', 'corridor', airflow_rate=0.05)

# Set common parameters for all zones
manager.set_all_zones_parameter('infiltration_rate', 0.0019)

# Create simulation
sim = manager.create_simulation('Multi-Zone Building')
```

#### Zone Connections

Zones can be connected for different types of interactions:

**Airflow Connection**
```python
manager.connect_zones(
    from_zone='office',
    to_zone='corridor',
    connection_type='airflow',
    airflow_rate=0.05  # m³/s
)
```

**Thermal Connection**
```python
manager.connect_zones(
    from_zone='office',
    to_zone='adjacent',
    connection_type='thermal',
    thermal_conductance=10.0  # W/K
)
```

**Both Airflow and Thermal**
```python
manager.connect_zones(
    from_zone='office',
    to_zone='corridor',
    connection_type='both',
    airflow_rate=0.05,
    thermal_conductance=10.0
)
```

#### Configuration Management

Export and save configurations:
```python
# Export configuration
config = manager.export_configuration()

# Save to file
import json
with open('building_config.json', 'w') as f:
    json.dump(config, f, indent=2)

# Load configuration
with open('building_config.json', 'r') as f:
    config = json.load(f)
manager.import_configuration(config)
```

### MultiZoneStateManager

Specialized state manager for multi-zone simulations:

```python
from backend.api import MultiZoneStateManager

state_mgr = MultiZoneStateManager()

# Get temperatures for all zones
temps = state_mgr.get_all_zones_temperature(sim_id)

# Get zone-specific variable
value = state_mgr.get_zone_variable(sim_id, 'office_1', 'humidity')

# Set zone-specific variable
state_mgr.set_zone_variable(sim_id, 'office_1', 'occupancy', 10)

# Monitor inter-zone flows
flow = state_mgr.get_inter_zone_flow(sim_id, 'office_1', 'corridor')
```

## Real-Time Monitoring

### SimulationMonitor

Monitor simulation execution in real-time with callbacks and alerts.

#### Basic Monitoring

```python
from backend.api import SimulationMonitor

monitor = SimulationMonitor(sim_id)

# Add callback for every update
def log_state(state):
    print(f"Temp: {state.get('zone_temperature')}°C")
    print(f"Progress: {state.get('percent_complete')}%")

monitor.add_callback(log_state)

# Start monitoring (runs in background thread)
monitor.start(interval=10)  # Check every 10 seconds

# Monitor runs in background...
time.sleep(300)

# Stop monitoring
monitor.stop()
```

#### Threshold Alerts

Set up alerts for specific conditions:

```python
# High temperature alert
monitor.add_threshold_alert(
    variable='zone_temperature',
    operator='>',
    threshold=26.0,
    callback=lambda val: print(f"HIGH TEMP: {val}°C")
)

# Low humidity alert
monitor.add_threshold_alert(
    variable='zone_humidity',
    operator='<',
    threshold=30.0,
    callback=lambda val: send_notification(f"Low humidity: {val}%")
)

# CO2 alert
monitor.add_threshold_alert(
    variable='zone_co2',
    operator='>',
    threshold=1000.0,
    callback=lambda val: increase_ventilation()
)
```

#### Historical Data

Access monitoring history:

```python
# Get all history
history = monitor.get_history()

# Get last 30 minutes
recent = monitor.get_history(minutes=30)

# Get trend for specific variable
temp_trend = monitor.get_variable_trend('zone_temperature', minutes=60)
```

## Adaptive Control

### AdaptiveController

Implement control logic that automatically adjusts simulation parameters:

```python
from backend.api import AdaptiveController, StateManager

controller = AdaptiveController(sim_id)
state_manager = StateManager()

# Define control rules
controller.add_rule(
    name='High Temperature Ventilation',
    condition=lambda state: state.get('zone_temperature', 20) > 26,
    action=lambda: state_manager.set_window_state(sim_id, 'WINDOW_1', True),
    cooldown=300  # Wait 5 minutes between actions
)

controller.add_rule(
    name='CO2 Control',
    condition=lambda state: state.get('zone_co2', 400) > 1000,
    action=lambda: state_manager.set_ventilation_rate(sim_id, 'ZONE_1', 5.0),
    cooldown=600
)

# Start adaptive control
controller.start(interval=60)  # Evaluate rules every minute

# Control runs in background...

# Stop control
controller.stop()

# Get control history
actions = controller.get_rule_history(minutes=60)
```

### Complex Control Strategies

Implement sophisticated control logic:

```python
def optimize_hvac(state):
    """Complex control strategy for HVAC optimization."""
    temp = state.get('zone_temperature', 22)
    occupancy = state.get('zone_occupancy', 0)
    outdoor_temp = state.get('outdoor_temperature', 20)
    
    # Adjust setpoints based on conditions
    if occupancy > 0:
        # Occupied: maintain comfort
        if temp > 26:
            state_manager.set_hvac_setpoint(sim_id, 'ZONE_1', 
                                           cooling_setpoint=24.0)
        elif temp < 20:
            state_manager.set_hvac_setpoint(sim_id, 'ZONE_1',
                                           heating_setpoint=21.0)
    else:
        # Unoccupied: save energy
        if outdoor_temp < 15:
            state_manager.set_hvac_setpoint(sim_id, 'ZONE_1',
                                           heating_setpoint=18.0)
        elif outdoor_temp > 25:
            state_manager.set_hvac_setpoint(sim_id, 'ZONE_1',
                                           cooling_setpoint=28.0)

controller.add_rule(
    name='Advanced HVAC Optimization',
    condition=lambda state: True,  # Always evaluate
    action=lambda: optimize_hvac(state),
    cooldown=1800  # 30 minutes
)
```

## Enhanced State Management

### Additional StateManager Methods

The `StateManager` class now includes many more parameter control methods:

#### HVAC Control

```python
# Set heating/cooling setpoints
state_manager.set_hvac_setpoint(
    sim_id, 'ZONE_1',
    heating_setpoint=21.0,
    cooling_setpoint=24.0
)
```

#### Lighting Control

```python
# Set lighting power density
state_manager.set_lighting_power(sim_id, 'ZONE_1', power_density=10.0)
```

#### Equipment Control

```python
# Set equipment power density
state_manager.set_equipment_power(sim_id, 'ZONE_1', power_density=8.0)
```

#### Ventilation Control

```python
# Set ventilation rate (air changes per hour)
state_manager.set_ventilation_rate(sim_id, 'ZONE_1', rate=3.0, rate_type='ach')

# Or volumetric flow rate
state_manager.set_ventilation_rate(sim_id, 'ZONE_1', rate=0.5, rate_type='m3/s')
```

#### Energy Monitoring

```python
# Get energy consumption breakdown
energy = state_manager.get_energy_consumption(sim_id, 'ZONE_1')
# Returns: {'heating': X, 'cooling': Y, 'lighting': Z, ...}
```

#### Thermal Comfort

```python
# Get thermal comfort metrics
comfort = state_manager.get_thermal_comfort(sim_id, 'ZONE_1')
# Returns: {'pmv': X, 'ppd': Y, 'operative_temperature': Z}
```

#### Batch Operations

```python
# Set multiple variables at once
state_manager.batch_set_variables(sim_id, {
    'zone_occupancy': 10,
    'zone_lighting_power': 12.0,
    'zone_equipment_power': 8.0,
    'window_1_opening': 0.5
})
```

#### Progress Monitoring

```python
# Get detailed progress information
progress = state_manager.get_simulation_progress(sim_id)
# Returns: {
#     'current_timestep': X,
#     'total_timesteps': Y,
#     'percent_complete': Z,
#     'elapsed_time': A,
#     'estimated_remaining': B,
#     'current_date': 'YYYY-MM-DD HH:MM',
#     'status': 'running'
# }
```

## Live Dashboard

### LiveDashboard

Aggregate monitoring data for dashboard visualization:

```python
from backend.api import LiveDashboard

dashboard = LiveDashboard(sim_id)
dashboard.start(interval=5)

# Get current metrics for display
metrics = dashboard.get_current_metrics()
# Returns: {
#     'timestamp': '...',
#     'progress': 45.2,
#     'current_date': '2024-01-15 14:30',
#     'zones': [...],
#     'energy': {...},
#     'status': 'running'
# }

# Get time series for plotting
series = dashboard.get_time_series(
    variables=['zone_temperature', 'zone_co2'],
    minutes=60
)
# Returns: {
#     'timestamps': [...],
#     'zone_temperature': [...],
#     'zone_co2': [...]
# }
```

## Backend Requirements

These enhanced features require backend implementation:

### Required Endpoints

1. **State Inspection**
   - `GET /simulation/{id}/state` - Get current simulation state
   - `GET /simulation/{id}/variables` - Get all variable values
   - `GET /simulation/{id}/zones` - Get zone list and info

2. **Variable Modification**
   - `POST /simulation/{id}/variables/{name}` - Set variable value
   - `POST /simulation/{id}/variables/batch` - Set multiple variables

3. **Multi-Zone Support**
   - `POST /simulation/multi-zone` - Create multi-zone simulation
   - `GET /simulation/{id}/zones/{zone_id}/state` - Zone-specific state
   - `GET /simulation/{id}/inter-zone-flow` - Inter-zone flow data

4. **Real-Time Updates**
   - WebSocket endpoint for live state streaming
   - Or polling-friendly endpoints with minimal latency

### Backend Implementation Guide

See `IMPROVEMENT_PLAN.md` for detailed backend implementation specifications including:
- Database schema for multi-zone simulations
- API endpoint specifications
- Real-time update mechanisms
- Performance optimization strategies

## Examples

Complete working examples are provided:

- `example_05_multi_zone.py` - Multi-zone simulation setup
- `example_06_realtime_control.py` - Real-time monitoring and adaptive control

## Integration with nestli

The multi-zone architecture is designed to be compatible with projects like [nestli](https://github.com/sentinelhive/nestli), enabling:

- Multiple IDF files in one simulation
- Complex building geometries
- Inter-zone interactions
- Coordinated control strategies

## Summary of Enhancements

| Feature | Description | Status |
|---------|-------------|---------|
| Multi-Zone Manager | Manage multiple zones and IDF files | ✅ Implemented |
| Zone Connections | Define airflow and thermal connections | ✅ Implemented |
| Real-Time Monitoring | Monitor simulation during execution | ✅ Implemented |
| Threshold Alerts | Alert on specific conditions | ✅ Implemented |
| Adaptive Control | Dynamic parameter modification | ✅ Implemented |
| Enhanced State Mgr | Comprehensive variable access | ✅ Implemented |
| Live Dashboard | Real-time visualization data | ✅ Implemented |
| Backend Support | Server-side implementation | ⏳ Planned |

All client-side API features are implemented and ready to use. Full functionality requires corresponding backend implementation as outlined in the improvement plan.
