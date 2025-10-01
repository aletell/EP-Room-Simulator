# EP-Room-Simulator API Examples

This directory contains example scripts demonstrating how to use the EP-Room-Simulator Python API for programmatic simulation control.

## Prerequisites

Before running these examples, ensure that:

1. The backend server is running on `http://localhost:5000`
2. MongoDB is accessible
3. Python dependencies are installed:
   ```bash
   pip install -r ../requirements.txt
   ```

## Examples

### Example 1: Basic Simulation Control
**File:** `example_01_basic_simulation.py`

Demonstrates:
- Creating a simulation via API
- Building configuration with fluent interface
- Starting and monitoring simulation
- Retrieving results

**Usage:**
```bash
python example_01_basic_simulation.py
```

### Example 2: Dynamic State Modification
**File:** `example_02_state_modification.py`

Demonstrates:
- Starting simulation asynchronously
- Inspecting simulation state during execution
- Modifying parameters based on conditions
- Adaptive control logic

**Usage:**
```bash
python example_02_state_modification.py
```

**Note:** This example requires backend support for state inspection and modification, which is planned for future implementation.

### Example 3: Event-Driven Control
**File:** `example_03_event_driven.py`

Demonstrates:
- Registering event callbacks
- Responding to simulation lifecycle events
- Automatic result saving
- Error handling with events

**Usage:**
```bash
python example_03_event_driven.py
```

## Required Files

For the examples to run successfully, you need:

- **IDF File:** `models/example_office.idf` (building model)
- **EPW File:** `weather/chicago.epw` (weather data)

You can replace these with your own files by modifying the configuration in each example.

## API Reference

### SimulationAPI

Main API class for simulation control.

```python
from backend.api import SimulationAPI

api = SimulationAPI(base_url='http://localhost:5000')

# Create simulation
sim = api.create_simulation('My Simulation')

# Configure simulation
config = {...}
sim.configure(config)

# Start simulation
sim.start(async_mode=False)

# Get results
results = sim.get_results(output_format='json')
```

### SimulationConfig

Fluent configuration builder.

```python
from backend.api import SimulationConfig

config = (SimulationConfig()
    .with_idf_file('path/to/model.idf')
    .with_epw_file('path/to/weather.epw')
    .with_room_dimensions(5.0, 6.0, 3.0)
    .with_simulation_period('2024-01-01', '2024-01-31')
    .with_timestep(10)
    .build())
```

### StateManager

Interface for state inspection and modification.

```python
from backend.api import StateManager

state_manager = StateManager(base_url='http://localhost:5000')

# Get current temperature
temp = state_manager.get_zone_temperature(sim_id, 'ZONE_1')

# Set occupancy
state_manager.set_occupancy(sim_id, 'ZONE_1', occupant_count=10)

# Set window state
state_manager.set_window_state(sim_id, 'WINDOW_1', is_open=True)
```

### SimulationEventHandler

Event-driven simulation control.

```python
from backend.api import SimulationEventHandler

events = SimulationEventHandler()

@events.on_start
def simulation_started(sim_id):
    print(f"Started: {sim_id}")

@events.on_complete
def save_results(results):
    results.to_csv('output.csv')

events.attach(sim_id)
```

## Creating Custom Examples

To create your own example:

1. Import the required API modules:
   ```python
   from backend.api import SimulationAPI, SimulationConfig
   ```

2. Initialize the API client:
   ```python
   api = SimulationAPI(base_url='http://localhost:5000')
   ```

3. Build your configuration:
   ```python
   config = SimulationConfig().with_idf_file(...).build()
   ```

4. Create and run simulation:
   ```python
   sim = api.create_simulation('My Custom Simulation')
   sim.configure(config)
   sim.start()
   ```

## Troubleshooting

### Connection Error
```
Failed to connect to backend at http://localhost:5000
```
**Solution:** Ensure the backend server is running:
```bash
cd backend
python -m app
```

### Simulation Not Found
```
SimulationNotFoundError: Simulation {id} not found
```
**Solution:** Check that the simulation was created successfully and the ID is correct.

### File Not Found
```
InvalidParameterError: IDF file not found: models/example_office.idf
```
**Solution:** Ensure all required files exist or update the file paths in the example.

### Backend Feature Not Implemented
```
Variable inspection endpoint not yet implemented in backend
```
**Solution:** Some features require backend implementation. See IMPROVEMENT_PLAN.md for roadmap.

## Advanced Usage

### Batch Simulations

Run multiple simulations with different configurations:

```python
from backend.api import SimulationAPI, SimulationConfig

api = SimulationAPI()

# Define configurations
configs = [
    {'width': 4.0, 'length': 5.0, 'height': 3.0},
    {'width': 5.0, 'length': 6.0, 'height': 3.0},
    {'width': 6.0, 'length': 7.0, 'height': 3.5},
]

# Run batch
simulations = []
for i, params in enumerate(configs):
    config = (SimulationConfig()
        .with_idf_file('models/office.idf')
        .with_epw_file('weather/chicago.epw')
        .with_room_dimensions(**params)
        .build())
    
    sim = api.create_simulation(f'Batch Simulation {i+1}')
    sim.configure(config)
    sim.start(async_mode=True)
    simulations.append(sim)

# Wait for all to complete
for sim in simulations:
    sim.wait_for_completion()
    print(f"Simulation {sim.sim_id} completed")
```

### Parameter Sweep

Systematically vary parameters:

```python
import numpy as np

widths = np.linspace(4.0, 8.0, 5)
results_map = {}

for width in widths:
    config = (SimulationConfig()
        .with_idf_file('models/office.idf')
        .with_epw_file('weather/chicago.epw')
        .with_room_dimensions(width, 6.0, 3.0)
        .build())
    
    sim = api.create_simulation(f'Width {width}m')
    sim.configure(config)
    sim.start(async_mode=False)
    
    results = sim.get_results(output_format='dataframe')
    results_map[width] = results
    
# Analyze results
for width, results in results_map.items():
    avg_temp = results['temperature'].mean()
    print(f"Width {width}m: Average Temperature = {avg_temp}°C")
```

## Additional Resources

- **Main Documentation:** See [OVERVIEW.md](../OVERVIEW.md) for project architecture
- **Improvement Plan:** See [IMPROVEMENT_PLAN.md](../IMPROVEMENT_PLAN.md) for future features
- **API Source Code:** See [backend/api/](../backend/api/) for implementation details

## Contributing

To contribute new examples:

1. Create a new example file: `example_XX_description.py`
2. Follow the existing example structure
3. Add documentation to this README
4. Test your example thoroughly
5. Submit a pull request

## License

These examples are part of the EP-Room-Simulator project and follow the same license.
