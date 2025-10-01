# EnergyPlus Room Simulator

This is a Python-based web application that allows the simulation of indoor climate (temperature, humidity, CO2) in standalone rooms (zones) for data generation purposes using the simulation software EnergyPlus.<br><br>
For this, an easy-to-use and straightforward GUI is provided, along with a REST API supporting the automation of simulations. It is possible to simulate the indoor climate of a room with individual IDF and EPW files. Furthermore, adjustments can be made to occupancy (presence of people and window openings), room dimensions, room orientation, and infiltration rate. Before starting the simulation, the modified version of a room model can be visualized. After the simulation, plots of the simulation results can then be displayed, and the simulation results can be downloaded as a CSV file and an ESO file. All inputs and outputs are persistently stored in a NoSQL database (MongoDB).

The application is primarily written in Python and uses the Python package *eppy* to work with EnergyPlus.<br>
It is divided into a frontend (GUI) and a backend (REST API), which are implemented as two separate Python Flask servers. 

<p style="float:left;">
    <img src="frontend/static/frontpage.png" alt="Screenshot Frontpage" style="width:45%;">
    <img src="frontend/static/roompage.png" alt="Screenshot Room page", style="width:45%;">
</p>
<p style="float:left;">
  
</p>

***
## Documentation

### Project Documentation
- **[OVERVIEW.md](OVERVIEW.md)** - Comprehensive project overview with architecture details, module breakdown, and technical stack
- **[IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md)** - Roadmap for future enhancements including Python API and occupancy forecasting
- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - Multi-zone simulation and real-time monitoring guide
- **[ENERGYPLUS_API_INTEGRATION.md](ENERGYPLUS_API_INTEGRATION.md)** - eppy vs EnergyPlus Python API comparison and integration
- **[REALTIME_CONTROL_GUIDE.md](REALTIME_CONTROL_GUIDE.md)** - Complete guide to real-time control and monitoring 🆕

### Module Documentation
- **[Python API](backend/api/)** - Programmatic interface for simulation control and state management
- **[Occupancy Forecasting](backend/forecast/)** - Machine learning-based occupancy prediction module
- **[Examples](examples/)** - Sample scripts demonstrating API usage and forecasting

### External Documentation
Further documentation can be found [here](https://ccwi.github.io/EP-Room-Simulator/). 

You may also watch our [Demo Video](https://ccwi.github.io/EP-Room-Simulator/images/demo_video.mp4). 

***

## Installation 
To install the software, you need an installation of<br>
Python 3.10, <br>
EnergyPlus version 22-2-0 or 23-1-0,<br>
and either Windows cmd.exe or Linux Bash console.<br>
Additionally, a recent version of Docker must be installed on the machine or a local installation of MongoDB.<br> 
Furthermore, node.js is required in order to be able to use the visualization functionality of the tool.<br>
The installation is then performed through the installation script <i>install.py</i>.

### Important!
The script performs either a complete installation or simply starts the resources and the program. The complete installation includes creating a virtual Python VENV environment, downloading and starting the MongoDB image and container, installing all required Python packages, and starting the frontend and backend. The simple start involves starting the existing MongoDB Docker container and the program. It is important to note that for a complete installation, a system path equality check is performed. This check is successful only if no virtual environment is activated. Therefore, to perform a completely fresh installation, all existing currently activated virtual environments must be deactivated. On the other hand, for a simple start of the programs (if an installation has already been performed), the dedicated VENV created by the installation needs to be manually activated before running the script. 

### Installation on Windows (for Windows 10 / 11)
*Prerequisites:* Installation of [Docker](https://www.docker.com/), [EnergyPlus](https://energyplus.net/) and [node.js](https://nodejs.org/en)

You may use the <i>installation.bat</i> file and the three run files (<i>run_backend.bat</i>, <i>run_frontend.bat</i>, <i>run_spider.bat</i>) to install and run the application. Alternatively, you may use the following commands.<br>

Run the script install.py after you navigated to your project folder:
```
 python install.py
```

After the first installation, you can use the same command *python install.py* to start all three components at once. Three console windows should open up (backend, frontend, spider server). Alternatively, you can start the components individually by the following commands.

Start frontend, backend, and spider server individually:
```
cd frontend
python -m app
```
```
cd backend
python -m app
```
```
cd ladybug_spider/spider-idf-viewer/v-2020-10-09/
node server.js
```

If only the REST API is needed, the backend application can be run standalone.<br>
However, if the frontend is started without the backend, it will not be able to perform any simulation!<br>
Always make sure, that the MongoDB instance is accessible (Docker is running).

***

## New Features

### Python API for Programmatic Control

A comprehensive Python API is now available for programmatic simulation control:

```python
from backend.api import SimulationAPI, SimulationConfig

# Initialize API
api = SimulationAPI(base_url='http://localhost:5000')

# Build configuration
config = (SimulationConfig()
    .with_idf_file('models/office.idf')
    .with_epw_file('weather/chicago.epw')
    .with_room_dimensions(5.0, 6.0, 3.0)
    .with_simulation_period('2024-01-01', '2024-01-31')
    .build())

# Create and run simulation
sim = api.create_simulation('My Simulation')
sim.configure(config)
sim.start(async_mode=False)

# Get results
results = sim.get_results(output_format='dataframe')
```

**Features:**
- Fluent configuration builder
- State inspection and modification
- Event-driven simulation control
- Comprehensive error handling

See [backend/api/](backend/api/) and [examples/](examples/) for more details.

### Occupancy Forecasting

Machine learning-based occupancy forecasting is now available:

```python
from backend.forecast import OccupancyForecaster

# Train forecaster
forecaster = OccupancyForecaster(model_type='linear')
forecaster.train(historical_data)

# Generate forecast
forecast = forecaster.predict(
    start_date='2024-02-01',
    end_date='2024-02-29',
    interval='15min'
)

# Use in simulation
forecast.to_csv('occupancy_forecast.csv')
```

**Supported Models:**
- Simple pattern-based forecasting
- Hourly average models
- Linear regression with temporal features
- (Future: LSTM, Prophet, and ensemble models)

See [backend/forecast/](backend/forecast/) for more details.

### Production-Ready Monitoring & Logging 🆕

Comprehensive logging and monitoring capabilities for production deployments:

```python
from backend.api import FileLogger, StructuredLogger, LiveDashboard, MetricsAggregator

# Multi-format file logging (CSV, JSON, Text)
file_logger = FileLogger('./simulation_logs')
file_logger.start()
file_logger.log({'zone_temperature': 23.5, 'window_opening': 0.8})

# Structured event logging
structured_logger = StructuredLogger('./simulation_logs/structured')
structured_logger.log_control_action('window_open', {'opening': 0.8})
structured_logger.log_measurement('zone_temperature', 23.5, '°C')

# Live web dashboard with real-time updates
dashboard = LiveDashboard(port=5001)
dashboard.start()  # Access at http://localhost:5001
dashboard.update_data({'zone_temperature': 23.5})

# Metrics aggregation and export
metrics = MetricsAggregator()
metrics.record('zone_temperature', 23.5)
metrics.export_summary('./metrics_summary.json')
```

**Features:**
- **Multiple File Formats:** CSV, JSON Lines, Text logs
- **Real-Time Monitoring:** tail -f compatible with immediate flush
- **Live Dashboard:** Web-based visualization with automatic updates
- **Structured Logging:** Categorized events (control, measurements, alerts, errors)
- **Metrics Export:** Statistical summaries and time series data
- **Production Ready:** Error handling, graceful shutdown, resource cleanup

**Usage:**
```bash
# Terminal 1: Run simulation with logging
python examples/example_09_production_monitoring.py

# Terminal 2: Monitor CSV log in real-time
tail -f simulation_logs/simulation_*.csv

# Terminal 3: Monitor text log
tail -f simulation_logs/simulation_*.log

# Browser: Open http://localhost:5001 for live dashboard
```

See [examples/example_09_production_monitoring.py](examples/example_09_production_monitoring.py) for complete working example.

***
