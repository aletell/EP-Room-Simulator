# Real-Time Control with EnergyPlus Python API

## Overview

This guide explains how to implement real-time control and monitoring with the EnergyPlus Python API, allowing you to observe and modify simulation parameters during execution and see the results immediately.

## Table of Contents
- [Introduction](#introduction)
- [How Real-Time Control Works](#how-real-time-control-works)
- [Step-by-Step Workflow](#step-by-step-workflow)
- [Observing Changes in Real-Time](#observing-changes-in-real-time)
- [Complete Working Example](#complete-working-example)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)

---

## Introduction

Real-time control with EnergyPlus allows you to:
- **Monitor** simulation variables during execution (temperatures, energy consumption, etc.)
- **Control** building systems dynamically (HVAC, windows, lighting, etc.)
- **React** to conditions as they occur in the simulation
- **Integrate** with external systems (ML models, optimization algorithms, IoT data)
- **Visualize** changes as they happen

### Why Real-Time Control?

Traditional EnergyPlus simulation:
```
Configure IDF → Run Simulation → Wait → Read Results
```

With real-time control:
```
Configure IDF → Start Simulation → Monitor & Control → See Changes Immediately
                      ↑__________________|
```

---

## How Real-Time Control Works

### EnergyPlus Execution Flow

EnergyPlus runs in **timesteps** (typically 4-15 per hour). At each timestep:

1. **Pre-calculations** - EnergyPlus prepares the timestep
2. **System calculations** - HVAC, lighting, thermal calculations
3. **Callback execution** - Your Python code runs here
4. **Post-calculations** - Results are computed
5. **Output** - Variables are written to output files

### Callback Points

The EnergyPlus Python API provides several callback points where your code can execute:

```python
# After initialization (once at beginning)
api.runtime.callback_begin_new_environment(state, my_function)

# After each zone timestep initialization
api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, my_function)

# After HVAC systems are calculated
api.runtime.callback_after_predictor_after_hvac_managers(state, my_function)

# Before simulation ends (once at end)
api.runtime.callback_end_zone_timestep_after_zone_reporting(state, my_function)
```

### Sensors and Actuators

**Sensors**: Read simulation variables
```python
# Temperature sensor
temperature = api.exchange.get_variable_value(state, temp_handle)

# Energy consumption sensor
energy = api.exchange.get_meter_value(state, meter_handle)
```

**Actuators**: Modify simulation variables
```python
# Window opening actuator
api.exchange.set_actuator_value(state, window_handle, 0.5)  # 50% open

# HVAC setpoint actuator
api.exchange.set_actuator_value(state, setpoint_handle, 22.0)  # 22°C
```

---

## Step-by-Step Workflow

### Step 1: Setup - Import and Initialize

```python
from pyenergyplus.api import EnergyPlusAPI

# Initialize API
api = EnergyPlusAPI()
state = api.state_manager.new_state()

# Storage for sensor and actuator handles
handles = {}
data_log = []
```

### Step 2: Register Sensors (What to Monitor)

```python
def setup_sensors(state):
    """Register all sensors you want to monitor."""
    
    # Zone temperature
    handles['zone_temp'] = api.exchange.get_variable_handle(
        state,
        'Zone Mean Air Temperature',  # Variable name
        'ZONE_1'                       # Key (zone name)
    )
    
    # Outdoor temperature
    handles['outdoor_temp'] = api.exchange.get_variable_handle(
        state,
        'Site Outdoor Air Drybulb Temperature',
        'Environment'
    )
    
    # Electricity consumption
    handles['electricity'] = api.exchange.get_meter_handle(
        state,
        'Electricity:Facility'
    )
    
    # CO2 concentration
    handles['co2'] = api.exchange.get_variable_handle(
        state,
        'Zone Air CO2 Concentration',
        'ZONE_1'
    )
    
    print("✓ Sensors registered")

# Call this at the beginning of simulation
api.runtime.callback_begin_new_environment(state, setup_sensors)
```

### Step 3: Register Actuators (What to Control)

```python
def setup_actuators(state):
    """Register all actuators you want to control."""
    
    # Window opening
    handles['window'] = api.exchange.get_actuator_handle(
        state,
        'AirFlow Network Window/Door Opening',  # Component type
        'Venting Opening Factor',                # Control type
        'WINDOW_1'                               # Component name
    )
    
    # Heating setpoint
    handles['heat_setpoint'] = api.exchange.get_actuator_handle(
        state,
        'Schedule:Constant',
        'Schedule Value',
        'HEATING_SETPOINT_SCHEDULE'
    )
    
    # Cooling setpoint
    handles['cool_setpoint'] = api.exchange.get_actuator_handle(
        state,
        'Schedule:Constant',
        'Schedule Value',
        'COOLING_SETPOINT_SCHEDULE'
    )
    
    # Lighting power
    handles['lighting'] = api.exchange.get_actuator_handle(
        state,
        'Lights',
        'Electricity Rate',
        'ZONE_1_LIGHTS'
    )
    
    print("✓ Actuators registered")

# Call this at the beginning of simulation
api.runtime.callback_begin_new_environment(state, setup_actuators)
```

### Step 4: Define Control Logic (How to React)

```python
def control_logic(state):
    """Execute at each timestep to monitor and control."""
    
    # 1. READ current state
    zone_temp = api.exchange.get_variable_value(state, handles['zone_temp'])
    outdoor_temp = api.exchange.get_variable_value(state, handles['outdoor_temp'])
    co2_level = api.exchange.get_variable_value(state, handles['co2'])
    
    # Get current time information
    hour = api.exchange.hour(state)
    minute = api.exchange.minutes(state)
    day_of_week = api.exchange.day_of_week(state)
    
    # 2. LOG data for visualization
    current_time = f"{hour:02d}:{minute:02d}"
    data_log.append({
        'time': current_time,
        'zone_temp': zone_temp,
        'outdoor_temp': outdoor_temp,
        'co2': co2_level
    })
    
    # 3. IMPLEMENT control logic
    
    # Window control based on temperature
    if zone_temp > 26 and outdoor_temp < zone_temp - 2:
        # It's hot inside and cooler outside - open window
        api.exchange.set_actuator_value(state, handles['window'], 1.0)
        print(f"[{current_time}] 🪟 WINDOW OPENED - Zone: {zone_temp:.1f}°C, Outdoor: {outdoor_temp:.1f}°C")
    else:
        # Close window
        api.exchange.set_actuator_value(state, handles['window'], 0.0)
    
    # HVAC control based on occupancy and time
    if 8 <= hour <= 18 and day_of_week <= 5:  # Workday hours
        # Occupied - comfortable setpoints
        api.exchange.set_actuator_value(state, handles['heat_setpoint'], 21.0)
        api.exchange.set_actuator_value(state, handles['cool_setpoint'], 24.0)
    else:
        # Unoccupied - energy-saving setpoints
        api.exchange.set_actuator_value(state, handles['heat_setpoint'], 18.0)
        api.exchange.set_actuator_value(state, handles['cool_setpoint'], 28.0)
    
    # Lighting control based on occupancy and CO2
    if co2_level > 800:  # Indicates occupancy
        api.exchange.set_actuator_value(state, handles['lighting'], 10.0)  # Full power
    else:
        api.exchange.set_actuator_value(state, handles['lighting'], 2.0)   # Standby
    
    # 4. PRINT status (real-time feedback)
    if minute == 0:  # Print every hour
        print(f"[{current_time}] Status - Temp: {zone_temp:.1f}°C, CO2: {co2_level:.0f}ppm")

# Register control logic to run at each timestep
api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, control_logic)
```

### Step 5: Run Simulation

```python
# Run the simulation with callbacks
command_line_args = [
    '-w', 'weather.epw',  # Weather file
    '-d', 'output',       # Output directory
    'model.idf'           # IDF file
]

print("Starting simulation with real-time control...")
api.runtime.run_energyplus(state, command_line_args)
print("Simulation complete!")
```

### Step 6: Visualize Results

```python
import pandas as pd
import matplotlib.pyplot as plt

# Convert logged data to DataFrame
df = pd.DataFrame(data_log)

# Plot temperature changes over time
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['zone_temp'], label='Zone Temperature', linewidth=2)
plt.plot(df.index, df['outdoor_temp'], label='Outdoor Temperature', linewidth=2)
plt.axhline(y=26, color='r', linestyle='--', label='Control Threshold')
plt.xlabel('Timestep')
plt.ylabel('Temperature (°C)')
plt.title('Real-Time Temperature Control')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('realtime_control_results.png', dpi=300)
plt.show()

print(f"✓ Results visualization saved to 'realtime_control_results.png'")
print(f"✓ Total timesteps: {len(df)}")
```

---

## Observing Changes in Real-Time

### Method 1: Console Output

Print status at each timestep or at intervals:

```python
def control_with_output(state):
    """Control with real-time console output."""
    zone_temp = api.exchange.get_variable_value(state, handles['zone_temp'])
    hour = api.exchange.hour(state)
    minute = api.exchange.minutes(state)
    
    # Control logic
    window_state = 1.0 if zone_temp > 26 else 0.0
    api.exchange.set_actuator_value(state, handles['window'], window_state)
    
    # Real-time output
    status = "OPEN" if window_state > 0 else "CLOSED"
    print(f"[{hour:02d}:{minute:02d}] Temp: {zone_temp:.1f}°C | Window: {status}")
```

**Output:**
```
[08:00] Temp: 23.5°C | Window: CLOSED
[08:15] Temp: 24.2°C | Window: CLOSED
[08:30] Temp: 25.8°C | Window: CLOSED
[08:45] Temp: 26.4°C | Window: OPEN  ← Change visible immediately
[09:00] Temp: 25.9°C | Window: OPEN
[09:15] Temp: 25.1°C | Window: CLOSED ← Window closes when cool enough
```

### Method 2: Live Dashboard

Update a dashboard in real-time using a web framework:

```python
from flask import Flask, jsonify
from threading import Thread

app = Flask(__name__)
live_data = {'temperature': 0, 'window': 0, 'energy': 0}

@app.route('/api/status')
def get_status():
    """API endpoint for live dashboard."""
    return jsonify(live_data)

def control_with_dashboard(state):
    """Update dashboard with current state."""
    zone_temp = api.exchange.get_variable_value(state, handles['zone_temp'])
    window_state = 1.0 if zone_temp > 26 else 0.0
    energy = api.exchange.get_meter_value(state, handles['electricity'])
    
    # Update live data
    live_data['temperature'] = round(zone_temp, 1)
    live_data['window'] = int(window_state * 100)
    live_data['energy'] = round(energy, 2)
    
    # Apply control
    api.exchange.set_actuator_value(state, handles['window'], window_state)

# Start dashboard server in background
def run_dashboard():
    app.run(port=5001, debug=False)

dashboard_thread = Thread(target=run_dashboard, daemon=True)
dashboard_thread.start()

print("📊 Live dashboard available at: http://localhost:5001/api/status")
```

**Dashboard HTML:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Real-Time Simulation Monitor</title>
    <script>
        // Update every second
        setInterval(async () => {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            document.getElementById('temp').textContent = data.temperature;
            document.getElementById('window').textContent = data.window;
            document.getElementById('energy').textContent = data.energy;
        }, 1000);
    </script>
</head>
<body>
    <h1>Real-Time Simulation Status</h1>
    <div>Temperature: <span id="temp">--</span>°C</div>
    <div>Window Opening: <span id="window">--</span>%</div>
    <div>Energy: <span id="energy">--</span> kWh</div>
</body>
</html>
```

### Method 3: File-Based Monitoring

Write to a file that can be monitored with `tail -f`:

```python
import csv
from datetime import datetime

# Open file for real-time logging
log_file = open('realtime_log.csv', 'w', newline='')
csv_writer = csv.writer(log_file)
csv_writer.writerow(['Timestamp', 'Hour', 'Minute', 'Zone_Temp', 'Window_State', 'Action'])

def control_with_logging(state):
    """Control with file-based logging."""
    zone_temp = api.exchange.get_variable_value(state, handles['zone_temp'])
    hour = api.exchange.hour(state)
    minute = api.exchange.minutes(state)
    
    # Control logic
    window_state = 1.0 if zone_temp > 26 else 0.0
    action = "OPENED" if window_state > 0 and last_state == 0 else \
             "CLOSED" if window_state == 0 and last_state > 0 else \
             "NO_CHANGE"
    
    api.exchange.set_actuator_value(state, handles['window'], window_state)
    
    # Write to file (flushes immediately)
    csv_writer.writerow([
        datetime.now().isoformat(),
        hour,
        minute,
        round(zone_temp, 2),
        int(window_state * 100),
        action
    ])
    log_file.flush()  # Ensure immediate write

# Monitor with: tail -f realtime_log.csv
```

### Method 4: Matplotlib Animation

Create animated plots that update in real-time:

```python
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# Setup plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
temperatures = deque(maxlen=100)
window_states = deque(maxlen=100)

def update_plot(frame):
    """Update plot with latest data."""
    if len(data_log) > 0:
        latest = data_log[-1]
        temperatures.append(latest['zone_temp'])
        window_states.append(latest['window_state'])
        
        ax1.clear()
        ax1.plot(list(temperatures), 'b-', linewidth=2)
        ax1.set_ylabel('Temperature (°C)')
        ax1.set_title('Real-Time Zone Temperature')
        ax1.grid(True, alpha=0.3)
        
        ax2.clear()
        ax2.fill_between(range(len(window_states)), window_states, alpha=0.5)
        ax2.set_ylabel('Window State')
        ax2.set_xlabel('Timestep')
        ax2.set_title('Window Opening Control')
        ax2.grid(True, alpha=0.3)
        
    return ax1, ax2

# Start animation
ani = FuncAnimation(fig, update_plot, interval=1000, blit=False)
plt.tight_layout()

# Show plot (non-blocking)
plt.ion()
plt.show()

# Now run simulation - plot updates in real-time
api.runtime.run_energyplus(state, command_line_args)
```

---

## Complete Working Example

Here's a complete, self-contained example showing real-time window control:

```python
"""
Complete Real-Time Control Example
Window opens automatically when indoor temperature exceeds 26°C
and outdoor temperature is at least 2°C cooler.
"""

from pyenergyplus.api import EnergyPlusAPI
import sys

def main():
    # Initialize API
    api = EnergyPlusAPI()
    state = api.state_manager.new_state()
    
    # Storage
    handles = {}
    timestep_count = [0]
    
    def setup_callback(state_arg):
        """Setup sensors and actuators (called once at start)."""
        print("\n🔧 Setting up sensors and actuators...")
        
        # Register sensors
        handles['zone_temp'] = api.exchange.get_variable_handle(
            state_arg,
            'Zone Mean Air Temperature',
            'ZONE_1'
        )
        handles['outdoor_temp'] = api.exchange.get_variable_handle(
            state_arg,
            'Site Outdoor Air Drybulb Temperature',
            'Environment'
        )
        
        # Register actuators
        handles['window'] = api.exchange.get_actuator_handle(
            state_arg,
            'AirFlow Network Window/Door Opening',
            'Venting Opening Factor',
            'WINDOW_1'
        )
        
        # Validate handles
        if handles['zone_temp'] == -1:
            print("❌ Error: Zone temperature sensor not found")
            sys.exit(1)
        if handles['outdoor_temp'] == -1:
            print("❌ Error: Outdoor temperature sensor not found")
            sys.exit(1)
        if handles['window'] == -1:
            print("❌ Error: Window actuator not found")
            sys.exit(1)
            
        print("✅ All sensors and actuators registered successfully")
    
    def control_callback(state_arg):
        """Control logic (called at each timestep)."""
        timestep_count[0] += 1
        
        # Read sensors
        zone_temp = api.exchange.get_variable_value(state_arg, handles['zone_temp'])
        outdoor_temp = api.exchange.get_variable_value(state_arg, handles['outdoor_temp'])
        
        # Get time
        hour = api.exchange.hour(state_arg)
        minute = api.exchange.minutes(state_arg)
        day = api.exchange.day_of_month(state_arg)
        month = api.exchange.month(state_arg)
        
        # Control logic: Open window if hot inside and cooler outside
        if zone_temp > 26 and outdoor_temp < zone_temp - 2:
            window_opening = 1.0  # 100% open
            action = "OPENING"
            emoji = "🪟✅"
        else:
            window_opening = 0.0  # Closed
            action = "CLOSING"
            emoji = "🪟❌"
        
        # Apply control
        api.exchange.set_actuator_value(state_arg, handles['window'], window_opening)
        
        # Print status every 15 minutes
        if minute % 15 == 0:
            print(f"\n[{month:02d}/{day:02d} {hour:02d}:{minute:02d}] Timestep {timestep_count[0]}")
            print(f"  {emoji} {action} window")
            print(f"  🌡️  Zone Temperature: {zone_temp:.1f}°C")
            print(f"  🌡️  Outdoor Temperature: {outdoor_temp:.1f}°C")
            print(f"  📊 Window Opening: {int(window_opening * 100)}%")
            
            # Show temperature difference
            temp_diff = zone_temp - outdoor_temp
            if temp_diff > 2:
                print(f"  ⚠️  Indoor warmer by {temp_diff:.1f}°C - Natural ventilation possible")
            elif temp_diff < -2:
                print(f"  ❄️  Outdoor warmer by {abs(temp_diff):.1f}°C - Keep windows closed")
    
    # Register callbacks
    api.runtime.callback_begin_new_environment(state, setup_callback)
    api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, control_callback)
    
    # Run simulation
    print("\n" + "="*70)
    print("REAL-TIME WINDOW CONTROL SIMULATION")
    print("="*70)
    print("\nStarting simulation with real-time control...")
    print("Watch for automatic window opening/closing based on temperatures!")
    print("\n" + "="*70)
    
    # Command line arguments
    args = [
        '-w', 'weather.epw',
        '-d', 'output',
        'model.idf'
    ]
    
    # Run
    api.runtime.run_energyplus(state, args)
    
    print("\n" + "="*70)
    print(f"✅ Simulation complete! Total timesteps: {timestep_count[0]}")
    print("="*70)

if __name__ == '__main__':
    main()
```

**Output:**
```
======================================================================
REAL-TIME WINDOW CONTROL SIMULATION
======================================================================

Starting simulation with real-time control...
Watch for automatic window opening/closing based on temperatures!

======================================================================

🔧 Setting up sensors and actuators...
✅ All sensors and actuators registered successfully

[07/15 08:00] Timestep 1
  🪟❌ CLOSING window
  🌡️  Zone Temperature: 23.5°C
  🌡️  Outdoor Temperature: 22.1°C
  📊 Window Opening: 0%

[07/15 08:15] Timestep 4
  🪟❌ CLOSING window
  🌡️  Zone Temperature: 24.8°C
  🌡️  Outdoor Temperature: 23.2°C
  📊 Window Opening: 0%

[07/15 08:30] Timestep 7
  🪟✅ OPENING window
  🌡️  Zone Temperature: 26.3°C
  🌡️  Outdoor Temperature: 23.8°C
  📊 Window Opening: 100%
  ⚠️  Indoor warmer by 2.5°C - Natural ventilation possible

[07/15 08:45] Timestep 10
  🪟✅ OPENING window
  🌡️  Zone Temperature: 25.7°C
  🌡️  Outdoor Temperature: 24.1°C
  📊 Window Opening: 100%

[07/15 09:00] Timestep 13
  🪟❌ CLOSING window
  🌡️  Zone Temperature: 25.2°C
  🌡️  Outdoor Temperature: 24.5°C
  📊 Window Opening: 0%

======================================================================
✅ Simulation complete! Total timesteps: 2880
======================================================================
```

---

## Common Use Cases

### Use Case 1: Temperature-Based Natural Ventilation

```python
def natural_ventilation_control(state):
    """Open windows when beneficial for cooling."""
    zone_temp = api.exchange.get_variable_value(state, handles['zone_temp'])
    outdoor_temp = api.exchange.get_variable_value(state, handles['outdoor_temp'])
    wind_speed = api.exchange.get_variable_value(state, handles['wind_speed'])
    
    # Natural ventilation criteria
    temp_diff = zone_temp - outdoor_temp
    is_hot = zone_temp > 24
    is_cooler_outside = temp_diff > 2
    wind_acceptable = wind_speed < 8  # m/s
    
    if is_hot and is_cooler_outside and wind_acceptable:
        opening = min(temp_diff / 5, 1.0)  # Progressive opening
        api.exchange.set_actuator_value(state, handles['window'], opening)
        return f"Window {int(opening*100)}% open for natural cooling"
    else:
        api.exchange.set_actuator_value(state, handles['window'], 0.0)
        return "Window closed"
```

### Use Case 2: Occupancy-Based HVAC Control

```python
def occupancy_based_hvac(state):
    """Adjust HVAC based on real-time occupancy."""
    co2_level = api.exchange.get_variable_value(state, handles['co2'])
    
    # Estimate occupancy from CO2 (> 800ppm indicates presence)
    is_occupied = co2_level > 800
    
    if is_occupied:
        # Comfort mode
        heating_sp = 21.0
        cooling_sp = 24.0
        ventilation = 3.0  # ACH
        status = "OCCUPIED"
    else:
        # Energy-saving mode
        heating_sp = 18.0
        cooling_sp = 28.0
        ventilation = 0.5  # ACH
        status = "VACANT"
    
    api.exchange.set_actuator_value(state, handles['heat_setpoint'], heating_sp)
    api.exchange.set_actuator_value(state, handles['cool_setpoint'], cooling_sp)
    api.exchange.set_actuator_value(state, handles['ventilation'], ventilation)
    
    return f"Mode: {status} (CO2: {co2_level:.0f}ppm)"
```

### Use Case 3: Machine Learning Integration

```python
import joblib

# Load trained ML model
ml_model = joblib.load('comfort_predictor.pkl')

def ml_based_control(state):
    """Use ML model to predict and optimize comfort."""
    # Gather features
    features = {
        'temperature': api.exchange.get_variable_value(state, handles['zone_temp']),
        'humidity': api.exchange.get_variable_value(state, handles['humidity']),
        'co2': api.exchange.get_variable_value(state, handles['co2']),
        'outdoor_temp': api.exchange.get_variable_value(state, handles['outdoor_temp']),
        'hour': api.exchange.hour(state),
        'occupancy': api.exchange.get_variable_value(state, handles['occupancy'])
    }
    
    # Create feature vector
    X = [[
        features['temperature'],
        features['humidity'],
        features['co2'],
        features['outdoor_temp'],
        features['hour'],
        features['occupancy']
    ]]
    
    # Predict optimal setpoint
    optimal_setpoint = ml_model.predict(X)[0]
    
    # Apply prediction
    api.exchange.set_actuator_value(state, handles['cool_setpoint'], optimal_setpoint)
    
    return f"ML-predicted setpoint: {optimal_setpoint:.1f}°C"
```

### Use Case 4: External Data Integration (Weather Forecast)

```python
import requests

def weather_adaptive_control(state):
    """Adjust control based on weather forecast."""
    # Get current outdoor conditions
    outdoor_temp = api.exchange.get_variable_value(state, handles['outdoor_temp'])
    hour = api.exchange.hour(state)
    
    # Fetch weather forecast (example)
    try:
        response = requests.get('http://api.weather.com/forecast')
        forecast = response.json()
        predicted_temp = forecast['next_hour_temp']
    except:
        predicted_temp = outdoor_temp  # Fallback
    
    # Predictive control
    if predicted_temp > outdoor_temp + 5:
        # It will get hotter - pre-cool now
        api.exchange.set_actuator_value(state, handles['cool_setpoint'], 22.0)
        return "PRE-COOLING for predicted heat"
    elif predicted_temp < outdoor_temp - 5:
        # It will get cooler - reduce cooling
        api.exchange.set_actuator_value(state, handles['cool_setpoint'], 26.0)
        return "REDUCING cooling (cooler weather expected)"
    else:
        # Normal operation
        api.exchange.set_actuator_value(state, handles['cool_setpoint'], 24.0)
        return "NORMAL operation"
```

---

## Troubleshooting

### Issue 1: Handles Return -1

**Problem**: Sensor or actuator handles are -1 (not found)

**Solution**:
```python
# Add validation
if handle == -1:
    print("ERROR: Handle not found!")
    print("Available variables:")
    # This will list all available sensors/actuators
    api.exchange.list_available_api_data_csv(state)
    sys.exit(1)
```

### Issue 2: Values Are None

**Problem**: `get_variable_value()` returns None

**Causes**:
- Variable not yet initialized (early in simulation)
- Wrong timestep callback used
- Variable name mismatch

**Solution**:
```python
value = api.exchange.get_variable_value(state, handle)
if value is None:
    print("Warning: Value not available yet, using default")
    value = 20.0  # Use sensible default
```

### Issue 3: Control Has No Effect

**Problem**: Setting actuator value doesn't change simulation

**Causes**:
- Actuator not correctly registered in IDF
- Wrong callback point
- Actuator overridden by schedule

**Solution**:
```python
# Use AfterPredictorAfterHVACManagers callback for HVAC
api.runtime.callback_after_predictor_after_hvac_managers(state, control)

# Ensure actuator availability in IDF
# Add Schedule:Compact with "Through: 12/31, For: AllDays, Until: 24:00, 999"
# Where 999 indicates external control
```

### Issue 4: Simulation Crashes

**Problem**: Simulation terminates unexpectedly

**Causes**:
- Exception in callback
- Invalid actuator values
- Handle errors

**Solution**:
```python
def safe_control(state):
    """Control with error handling."""
    try:
        # Control logic here
        pass
    except Exception as e:
        print(f"ERROR in control: {e}")
        import traceback
        traceback.print_exc()
        # Don't crash - continue simulation
```

---

## Summary

**Real-time control workflow:**

1. ✅ **Initialize** API and state
2. ✅ **Register** sensors (what to monitor)
3. ✅ **Register** actuators (what to control)
4. ✅ **Define** control logic (how to react)
5. ✅ **Run** simulation with callbacks
6. ✅ **Observe** changes via console, files, or dashboard
7. ✅ **Visualize** results after simulation

**Key benefits:**
- 🚀 Immediate feedback during simulation
- 🎯 Dynamic adaptation to conditions
- 🔗 Integration with external systems
- 📊 Real-time data collection
- 🤖 ML/AI control implementation

**Next steps:**
- See `example_07_energyplus_api.py` for working code
- Read `ENERGYPLUS_API_INTEGRATION.md` for detailed API reference
- Check `ENHANCED_FEATURES.md` for advanced use cases

For questions or issues, refer to the EnergyPlus Application Guide - External Interface.
