# EnergyPlus Integration - eppy vs Native Python API

## Overview

This document compares eppy and the native EnergyPlus Python API, documenting their respective capabilities, limitations, and when to use each approach for the EP-Room-Simulator.

## Table of Contents
- [What is eppy?](#what-is-eppy)
- [What is the EnergyPlus Python API?](#what-is-the-energyplus-python-api)
- [Comparison](#comparison)
- [eppy Limitations](#eppy-limitations)
- [EnergyPlus Python API Advantages](#energyplus-python-api-advantages)
- [Integration Strategy](#integration-strategy)
- [Implementation Examples](#implementation-examples)

---

## What is eppy?

**eppy** (EnergyPlus Python) is a Python library for reading, modifying, and creating EnergyPlus IDF files. It provides a high-level, Pythonic interface for working with IDF objects.

### eppy Capabilities
- ✅ Read and parse IDF files
- ✅ Modify IDF objects before simulation
- ✅ Create new IDF objects programmatically
- ✅ Run simulations via subprocess
- ✅ Simple, intuitive API for IDF manipulation
- ✅ Good for pre-simulation configuration

### eppy Architecture
```python
from eppy.modeleditor import IDF

# Set IDD file
IDF.setiddname('/path/to/Energy+.idd')

# Load IDF
idf = IDF('building.idf', 'weather.epw')

# Modify objects
zones = idf.idfobjects['ZONE']
zones[0].Name = 'New Zone Name'

# Run simulation (subprocess)
idf.run()
```

---

## What is the EnergyPlus Python API?

The **EnergyPlus Python API** (available since EnergyPlus 9.3) is the official native Python interface built into EnergyPlus. It provides direct access to EnergyPlus internals during simulation runtime.

### EnergyPlus Python API Capabilities
- ✅ Runtime access to simulation state
- ✅ Read sensor values during simulation
- ✅ Modify actuator values during simulation
- ✅ Exchange data with external systems in real-time
- ✅ Implement custom control logic
- ✅ Access to Energy Management System (EMS) capabilities
- ✅ Plugin/callback mechanism for custom code execution

### EnergyPlus Python API Architecture
```python
from pyenergyplus.api import EnergyPlusAPI

api = EnergyPlusAPI()

# Define callback for runtime access
def my_callback(state):
    # Get sensor value
    temp = api.exchange.get_variable_value(state, temp_handle)
    
    # Implement control logic
    if temp > 26:
        # Set actuator value
        api.exchange.set_actuator_value(state, actuator_handle, 1.0)

# Register callback
api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, my_callback)

# Run simulation
api.runtime.run_energyplus(sys.argv[1:])
```

---

## Comparison

| Feature | eppy | EnergyPlus Python API |
|---------|------|----------------------|
| **IDF File Manipulation** | ✅ Excellent | ⚠️ Limited (pre-run only) |
| **Runtime State Access** | ❌ No | ✅ Yes |
| **Modify During Simulation** | ❌ No | ✅ Yes |
| **Real-time Control** | ❌ No | ✅ Yes |
| **External Data Integration** | ❌ No | ✅ Yes |
| **Ease of Use** | ✅ Very easy | ⚠️ More complex |
| **Learning Curve** | ✅ Gentle | ⚠️ Steep |
| **Documentation** | ✅ Good community docs | ⚠️ Official docs only |
| **IDF Object Creation** | ✅ Excellent | ⚠️ Manual |
| **Sensor/Actuator Access** | ❌ No | ✅ Extensive |
| **Custom Control Logic** | ❌ No | ✅ Full support |
| **Multi-IDF Coordination** | ⚠️ Multiple processes | ✅ Single process |
| **Performance** | ⚠️ Subprocess overhead | ✅ Native integration |

---

## eppy Limitations

### 1. **No Runtime Access**
eppy can only modify IDF files before simulation starts. Once EnergyPlus is running, eppy has no access to the simulation state.

**Impact:**
- Cannot read current temperature, humidity, CO2, etc. during simulation
- Cannot implement adaptive control based on real-time conditions
- Cannot respond to external events during simulation

**Example of what you CAN'T do:**
```python
# This doesn't work with eppy
idf.run()  # Simulation starts
current_temp = idf.get_zone_temperature('ZONE_1')  # ❌ Not possible
```

### 2. **No Dynamic Parameter Modification**
Cannot change simulation parameters while the simulation is running.

**Impact:**
- Window opening schedules must be predefined
- HVAC setpoints cannot adapt to conditions
- Occupancy cannot respond to real-time data
- Equipment schedules are static

**Example of what you CAN'T do:**
```python
# Cannot modify during simulation
idf.run()  # Simulation starts
if some_condition():
    idf.set_window_opening(0.5)  # ❌ Not possible during run
```

### 3. **Limited Multi-Zone Coordination**
Running multiple IDF files requires multiple separate processes, making coordination difficult.

**Impact:**
- Inter-zone air flow is hard to model accurately
- Thermal coupling between zones is approximated
- Shared HVAC systems are challenging
- Coordinated control across zones is complex

**Current approach with eppy:**
```python
# Each zone is a separate process
idf1 = IDF('zone1.idf', 'weather.epw')
idf2 = IDF('zone2.idf', 'weather.epw')

# Run separately (hard to coordinate)
idf1.run()  # Process 1
idf2.run()  # Process 2
```

### 4. **No Energy Management System (EMS) Integration**
eppy doesn't provide direct access to EnergyPlus EMS capabilities.

**Impact:**
- Custom control strategies require manual EMS programming in IDF
- No Python-based EMS logic
- Limited integration with machine learning models
- Difficult to implement optimization algorithms

### 5. **Subprocess-Based Execution**
eppy runs EnergyPlus as an external subprocess.

**Impact:**
- Higher overhead for starting simulations
- Difficult to debug simulation issues
- Limited error handling capabilities
- No direct memory access to simulation data

### 6. **Post-Processing Only**
Results are only available after simulation completes.

**Impact:**
- Cannot make decisions based on intermediate results
- Early stopping not possible
- Real-time dashboards require separate monitoring
- Validation of results is delayed

---

## EnergyPlus Python API Advantages

### 1. **Runtime State Inspection**
Full access to all simulation variables during execution.

**Capabilities:**
```python
# Access any sensor value
temperature = api.exchange.get_variable_value(state, temp_handle)
humidity = api.exchange.get_variable_value(state, humidity_handle)
co2 = api.exchange.get_variable_value(state, co2_handle)
power = api.exchange.get_meter_value(state, power_meter_handle)
```

### 2. **Dynamic Control**
Modify actuator values in real-time based on conditions.

**Capabilities:**
```python
# Adaptive window control
if temperature > 26 and outdoor_temp < 22:
    api.exchange.set_actuator_value(state, window_actuator, 1.0)  # Open
else:
    api.exchange.set_actuator_value(state, window_actuator, 0.0)  # Close

# Dynamic HVAC setpoints
if occupancy > 10:
    api.exchange.set_actuator_value(state, cooling_setpoint, 24.0)
else:
    api.exchange.set_actuator_value(state, cooling_setpoint, 26.0)  # Save energy
```

### 3. **External System Integration**
Exchange data with external systems during simulation.

**Capabilities:**
```python
def my_callback(state):
    # Get current state
    temp = api.exchange.get_variable_value(state, temp_handle)
    
    # Query external ML model
    prediction = ml_model.predict(temp, humidity, time_of_day)
    
    # Apply control action
    api.exchange.set_actuator_value(state, hvac_actuator, prediction)
```

### 4. **Multi-Zone Coordination**
Single process can coordinate multiple zones effectively.

**Capabilities:**
```python
def coordinate_zones(state):
    # Read temperatures from all zones
    temp_zone1 = api.exchange.get_variable_value(state, temp_handle_1)
    temp_zone2 = api.exchange.get_variable_value(state, temp_handle_2)
    
    # Coordinate airflow between zones
    if temp_zone1 > temp_zone2 + 2:
        # Transfer air from zone1 to zone2
        api.exchange.set_actuator_value(state, airflow_actuator, 0.5)
```

### 5. **Early Stopping & Validation**
Can stop simulation early or validate conditions during run.

**Capabilities:**
```python
def validation_callback(state):
    temp = api.exchange.get_variable_value(state, temp_handle)
    
    # Stop if temperature is unrealistic
    if temp > 60 or temp < -20:
        api.runtime.issue_severe(state, "Unrealistic temperature detected")
        api.runtime.stop_simulation(state)
```

### 6. **Performance Optimization**
Direct access without subprocess overhead.

**Benefits:**
- Faster startup (no subprocess creation)
- Lower memory overhead
- Better error handling
- Direct memory access to data

---

## Integration Strategy

### Recommended Hybrid Approach

Use **both** eppy and the EnergyPlus Python API to get the best of both worlds:

```
┌─────────────────────────────────────────────────────────┐
│                     Simulation Setup                     │
│                                                          │
│  Use eppy for:                                          │
│  - Reading and parsing IDF files                        │
│  - Creating/modifying IDF objects                       │
│  - Setting up base configuration                        │
│  - Managing multiple IDF files                          │
│                                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Simulation Execution                    │
│                                                          │
│  Use EnergyPlus Python API for:                         │
│  - Runtime state inspection                             │
│  - Dynamic parameter modification                       │
│  - Real-time control logic                              │
│  - External system integration                          │
│  - Multi-zone coordination                              │
│                                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Post-Processing                        │
│                                                          │
│  Use eppy for:                                          │
│  - Reading result files                                 │
│  - Data extraction                                      │
│  - Report generation                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Implementation Pattern

```python
# 1. Setup with eppy
from eppy.modeleditor import IDF

IDF.setiddname('/path/to/Energy+.idd')
idf = IDF('building.idf', 'weather.epw')

# Modify IDF for sensors and actuators
idf = setup_ems_sensors_actuators(idf)

# Save modified IDF
idf.saveas('prepared.idf')

# 2. Run with EnergyPlus Python API
from pyenergyplus.api import EnergyPlusAPI

api = EnergyPlusAPI()
state = api.state_manager.new_state()

# Setup handles
temp_handle = api.exchange.get_variable_handle(
    state, "Zone Mean Air Temperature", "ZONE_1"
)
window_handle = api.exchange.get_actuator_handle(
    state, "AirFlow Network Window/Door Opening", "WINDOW_1", "Venting Opening Factor"
)

# Define runtime control
def control_callback(state_arg):
    temp = api.exchange.get_variable_value(state_arg, temp_handle)
    
    # Adaptive control
    if temp > 26:
        api.exchange.set_actuator_value(state_arg, window_handle, 1.0)
    else:
        api.exchange.set_actuator_value(state_arg, window_handle, 0.0)

# Register callback
api.runtime.callback_begin_zone_timestep_after_init_heat_balance(
    state, control_callback
)

# Run simulation
api.runtime.run_energyplus(state, ['-w', 'weather.epw', '-d', 'output', 'prepared.idf'])

# 3. Post-process with eppy
# (eppy can read result files)
```

---

## Implementation Examples

### Example 1: Window Control with EnergyPlus Python API

```python
"""
Example: Adaptive window control using EnergyPlus Python API
"""
from pyenergyplus.api import EnergyPlusAPI
import sys

class WindowController:
    def __init__(self):
        self.api = EnergyPlusAPI()
        self.temp_handle = None
        self.outdoor_temp_handle = None
        self.window_handle = None
        
    def setup_handles(self, state):
        """Setup sensor and actuator handles."""
        # Temperature sensor
        self.temp_handle = self.api.exchange.get_variable_handle(
            state, "Zone Mean Air Temperature", "ZONE_1"
        )
        
        # Outdoor temperature sensor
        self.outdoor_temp_handle = self.api.exchange.get_variable_handle(
            state, "Site Outdoor Air Drybulb Temperature", "Environment"
        )
        
        # Window actuator
        self.window_handle = self.api.exchange.get_actuator_handle(
            state, 
            "AirFlow Network Window/Door Opening", 
            "WINDOW_1", 
            "Venting Opening Factor"
        )
        
    def control_logic(self, state):
        """Implement adaptive window control."""
        if self.temp_handle == -1 or self.window_handle == -1:
            return
            
        # Get current temperatures
        indoor_temp = self.api.exchange.get_variable_value(state, self.temp_handle)
        outdoor_temp = self.api.exchange.get_variable_value(state, self.outdoor_temp_handle)
        
        # Control logic
        if indoor_temp > 26 and outdoor_temp < 22:
            # Hot inside, cool outside -> open window
            self.api.exchange.set_actuator_value(state, self.window_handle, 1.0)
        elif indoor_temp < 20:
            # Too cold -> close window
            self.api.exchange.set_actuator_value(state, self.window_handle, 0.0)
        elif outdoor_temp > 30:
            # Too hot outside -> close window
            self.api.exchange.set_actuator_value(state, self.window_handle, 0.0)
        # Otherwise maintain current state
        
def main():
    controller = WindowController()
    state = controller.api.state_manager.new_state()
    
    # Setup handles after warmup
    controller.api.runtime.callback_end_zone_timestep_after_zone_reporting(
        state, lambda s: controller.setup_handles(s)
    )
    
    # Run control logic every timestep
    controller.api.runtime.callback_begin_zone_timestep_after_init_heat_balance(
        state, lambda s: controller.control_logic(s)
    )
    
    # Run simulation
    controller.api.runtime.run_energyplus(state, sys.argv[1:])

if __name__ == '__main__':
    main()
```

### Example 2: Multi-Zone Coordination

```python
"""
Example: Coordinate HVAC control across multiple zones
"""
from pyenergyplus.api import EnergyPlusAPI

class MultiZoneController:
    def __init__(self, zone_names):
        self.api = EnergyPlusAPI()
        self.zone_names = zone_names
        self.temp_handles = {}
        self.hvac_handles = {}
        
    def setup_handles(self, state):
        """Setup handles for all zones."""
        for zone in self.zone_names:
            # Temperature sensors
            self.temp_handles[zone] = self.api.exchange.get_variable_handle(
                state, "Zone Mean Air Temperature", zone
            )
            
            # HVAC actuators
            self.hvac_handles[zone] = self.api.exchange.get_actuator_handle(
                state, "Zone Temperature Control", zone, "Heating Setpoint"
            )
            
    def coordinate_control(self, state):
        """Coordinate HVAC control across zones."""
        # Get all temperatures
        temps = {}
        for zone in self.zone_names:
            if self.temp_handles[zone] != -1:
                temps[zone] = self.api.exchange.get_variable_value(
                    state, self.temp_handles[zone]
                )
        
        if not temps:
            return
            
        # Calculate average
        avg_temp = sum(temps.values()) / len(temps)
        
        # Coordinate setpoints
        for zone in self.zone_names:
            if self.hvac_handles[zone] == -1:
                continue
                
            zone_temp = temps.get(zone, avg_temp)
            
            # Adjust setpoint based on zone temperature relative to average
            if zone_temp > avg_temp + 1:
                # Zone is warmer -> lower heating setpoint
                setpoint = 20.0
            elif zone_temp < avg_temp - 1:
                # Zone is cooler -> higher heating setpoint
                setpoint = 22.0
            else:
                # Near average -> standard setpoint
                setpoint = 21.0
                
            self.api.exchange.set_actuator_value(
                state, self.hvac_handles[zone], setpoint
            )
```

### Example 3: Integration with External ML Model

```python
"""
Example: Use machine learning model for occupancy-based control
"""
from pyenergyplus.api import EnergyPlusAPI
import pickle

class MLControlController:
    def __init__(self, model_path):
        self.api = EnergyPlusAPI()
        self.ml_model = self.load_model(model_path)
        self.sensor_handles = {}
        self.actuator_handles = {}
        
    def load_model(self, path):
        """Load trained ML model."""
        with open(path, 'rb') as f:
            return pickle.load(f)
            
    def setup_handles(self, state):
        """Setup required handles."""
        # Sensors
        self.sensor_handles['temp'] = self.api.exchange.get_variable_handle(
            state, "Zone Mean Air Temperature", "ZONE_1"
        )
        self.sensor_handles['humidity'] = self.api.exchange.get_variable_handle(
            state, "Zone Air Relative Humidity", "ZONE_1"
        )
        self.sensor_handles['occupancy'] = self.api.exchange.get_variable_handle(
            state, "Zone People Occupant Count", "ZONE_1"
        )
        
        # Actuators
        self.actuator_handles['cooling'] = self.api.exchange.get_actuator_handle(
            state, "Zone Temperature Control", "ZONE_1", "Cooling Setpoint"
        )
        self.actuator_handles['ventilation'] = self.api.exchange.get_actuator_handle(
            state, "Zone Ventilation", "ZONE_1", "Air Exchange Flow Rate"
        )
        
    def ml_control(self, state):
        """Apply ML-based control."""
        # Collect current state
        features = []
        for sensor in ['temp', 'humidity', 'occupancy']:
            handle = self.sensor_handles.get(sensor)
            if handle and handle != -1:
                value = self.api.exchange.get_variable_value(state, handle)
                features.append(value)
                
        if len(features) < 3:
            return
            
        # Get ML model prediction
        prediction = self.ml_model.predict([features])[0]
        
        # Apply control action
        cooling_setpoint, ventilation_rate = prediction
        
        cooling_handle = self.actuator_handles.get('cooling')
        if cooling_handle and cooling_handle != -1:
            self.api.exchange.set_actuator_value(state, cooling_handle, cooling_setpoint)
            
        vent_handle = self.actuator_handles.get('ventilation')
        if vent_handle and vent_handle != -1:
            self.api.exchange.set_actuator_value(state, vent_handle, ventilation_rate)
```

---

## Lessons from nestli

Based on the nestli architecture, key insights for multi-IDF handling:

### 1. **Co-simulation Approach**
nestli uses a co-simulation framework where multiple EnergyPlus instances can communicate:
- Each zone/building is its own IDF
- Zones exchange boundary conditions
- Central coordinator manages synchronization

### 2. **Data Exchange Patterns**
- Surface temperatures for thermal coupling
- Air flow rates for inter-zone ventilation
- Shared HVAC system states
- Weather data consistency

### 3. **Synchronization Strategy**
- Timestep-level synchronization
- Consistent weather data
- Aligned simulation periods
- Communication protocol for data exchange

---

## Recommendations for EP-Room-Simulator

### Short Term (Immediate)
1. ✅ Continue using eppy for IDF file manipulation (already implemented)
2. ✅ Implement StateManager interface (already implemented)
3. 🔄 Add EnergyPlus Python API integration layer
4. 🔄 Document eppy limitations (this document)
5. 🔄 Create examples using both approaches

### Medium Term (Next Phase)
1. Implement runtime control using EnergyPlus Python API
2. Add sensor/actuator setup utilities
3. Create callback framework for adaptive control
4. Integrate with existing StateManager interface

### Long Term (Future)
1. Implement nestli-style co-simulation for true multi-zone support
2. Create data exchange protocol between zones
3. Add synchronization coordinator
4. Support complex building geometries

---

## Conclusion

**eppy** and the **EnergyPlus Python API** serve different purposes:

- **eppy**: Excellent for IDF file manipulation and setup
- **EnergyPlus Python API**: Essential for runtime control and real-time monitoring

The EP-Room-Simulator should use **both**:
- eppy for configuration and multi-IDF management
- EnergyPlus Python API for the runtime features users requested (state inspection, dynamic control, real-time modification)

This hybrid approach provides:
- ✅ Easy IDF file management (eppy)
- ✅ Runtime state inspection (EnergyPlus API)
- ✅ Dynamic parameter modification (EnergyPlus API)
- ✅ Multi-zone coordination capability (both)
- ✅ Best of both worlds

---

## References

- [eppy Documentation](https://eppy.readthedocs.io/)
- [EnergyPlus Python API Documentation](https://energyplus.readthedocs.io/en/latest/api.html)
- [nestli Project](https://github.com/sentinelhive/nestli)
- [EnergyPlus Application Guide - Energy Management System](https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v23.1.0/EMSApplicationGuide.pdf)
