# EP-Room-Simulator - Project Overview

## Table of Contents
- [Introduction](#introduction)
- [Architecture Overview](#architecture-overview)
- [Module Breakdown](#module-breakdown)
  - [Backend Module](#backend-module)
  - [Frontend Module](#frontend-module)
  - [Visualization Module](#visualization-module)
  - [Database Module](#database-module)
- [Key Features](#key-features)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [System Requirements](#system-requirements)

---

## Introduction

The **EP-Room-Simulator** is a comprehensive Python-based web application designed for simulating indoor climate conditions (temperature, humidity, CO2 levels) in standalone rooms using the EnergyPlus simulation software. The system is architected for data generation purposes and provides both an intuitive GUI and a REST API for automation.

### Primary Use Cases
- Indoor climate simulation for research and analysis
- Data generation for machine learning models
- Building energy performance evaluation
- HVAC system optimization studies
- Occupancy impact analysis on indoor environments

---

## Architecture Overview

The application follows a **three-tier architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│                  (Flask Web Application)                     │
│     - Web GUI for user interaction                          │
│     - File upload and management                            │
│     - Visualization and result display                      │
└───────────────────┬─────────────────────────────────────────┘
                    │ REST API
                    │ (HTTP/JSON)
┌───────────────────▼─────────────────────────────────────────┐
│                        Backend Layer                         │
│                  (Flask REST API Server)                     │
│     - Simulation orchestration                              │
│     - EnergyPlus integration (via eppy)                     │
│     - Data processing and transformation                    │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ MongoDB Driver
┌───────────────────▼─────────────────────────────────────────┐
│                      Persistence Layer                       │
│                   (MongoDB Database)                         │
│     - Simulation inputs/outputs storage                     │
│     - Historical data management                            │
│     - Result caching                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Breakdown

### Backend Module

**Location:** `/backend/`

The backend serves as the core simulation engine and data processing hub.

#### Key Components:

1. **Simulation_Helper.py**
   - Core simulation orchestration
   - EnergyPlus integration via eppy library
   - IDF file manipulation and configuration
   - Occupancy schedule management
   - Methods:
     - `set_occupancy()`: Configure occupant schedules
     - `run_simulation()`: Execute EnergyPlus simulation
     - `set_timestep()`: Configure simulation time resolution
     - `request_output_variables()`: Define desired outputs

2. **Room_Helper.py**
   - Room geometry and dimension management
   - Wall, floor, ceiling, and window manipulation
   - 3D model updates for visualization
   - Methods:
     - `update_room_size()`: Modify room dimensions
     - `get_floor()`, `get_ceiling()`, `get_walls()`: Retrieve surfaces
     - `update_infiltration()`: Adjust air infiltration rates

3. **endpoint.py**
   - REST API endpoint definitions
   - Request/response handling
   - Simulation lifecycle management
   - Endpoints:
     - `/simulation` - Create/retrieve simulations
     - `/simulation/start` - Execute simulations
     - `/result` - Fetch simulation results
     - `/result/csv` - Export results as CSV

4. **db_controller.py**
   - MongoDB database operations
   - CRUD operations for simulations
   - Result persistence and retrieval
   - Data validation and integrity

5. **simulation.py**
   - Main simulation execution logic
   - File encoding/decoding (base64)
   - EnergyPlus runner coordination
   - Error handling and logging

6. **converterEsoToCsv.py**
   - EnergyPlus ESO output file parsing
   - CSV conversion for data analysis
   - Time-series data extraction

7. **utils.py**
   - Utility functions for file operations
   - Configuration file parsing
   - Base64 encoding/decoding
   - Common helper methods

### Frontend Module

**Location:** `/frontend/`

The frontend provides an intuitive web interface for users to interact with the simulation system.

#### Key Components:

1. **app.py**
   - Flask application factory
   - Blueprint registration
   - Route configuration
   - CORS setup

2. **fileHandler.py**
   - IDF file upload and validation
   - EPW (weather data) file management
   - File caching mechanisms
   - Secure filename handling

3. **startSim.py**
   - Simulation startup interface
   - Parameter transfer to backend
   - Progress monitoring
   - Status tracking
   - Helper class: `SimHelper` for state management

4. **OccupancyUpload.py**
   - Occupancy data file upload
   - CSV format validation
   - Time frame verification
   - Integration with simulation setup

5. **OccupancyCustom.py**
   - Custom occupancy schedule creation
   - Interactive table-based input
   - Data validation and formatting

6. **OccupancyModifier.py**
   - Post-upload occupancy editing
   - Time slot modification
   - Window opening schedule adjustments
   - Methods:
     - `modifyBase()`: Modify occupancy data
     - `loadCSV()`: Load base occupancy file
     - `saveCSV()`: Persist modifications

7. **OccupancyData.py**
   - Occupancy data processing
   - Date/time validation
   - Data frame manipulation
   - Error handling with JSON notifications

8. **editParameters.py**
   - Room parameter configuration UI
   - Dimension adjustment (width, length, height)
   - Infiltration rate settings
   - Orientation configuration
   - Methods:
     - `resetParameter()`: Reset to defaults
     - `loadParameters()`: Load from JSON

9. **viewResult.py**
   - Simulation result visualization
   - Interactive plotting (Plotly)
   - Data download options
   - Historical comparison

10. **IDFUpdater.py**
    - Dynamic IDF file modification
    - Room dimension updates
    - Infiltration parameter changes
    - Zone configuration

11. **endpoint_connector.py**
    - Backend API client
    - Request/response handling
    - Error management
    - Data serialization

### Visualization Module

**Location:** `/ladybug_spider/`

3D visualization component for building geometry using Node.js server.

#### Key Components:
- **Spider IDF Viewer**: Interactive 3D visualization of IDF models
- **Node.js Server**: Serves visualization interface
- **Three.js Integration**: WebGL-based 3D rendering

### Database Module

**Technology:** MongoDB (NoSQL)

#### Collections:
1. **Simulations Collection**
   - Simulation metadata
   - Input files (IDF, EPW, occupancy CSV)
   - Configuration parameters
   - Status tracking

2. **Results Collection**
   - Time-series output data
   - Calculated metrics
   - ESO file data
   - CSV exports

---

## Key Features

### 1. Simulation Configuration
- **Room Dimensions**: Customizable width, length, height
- **Orientation**: Adjustable building orientation (0-360°)
- **Infiltration Rate**: Air leakage configuration
- **Weather Data**: EPW file support for various locations

### 2. Occupancy Management
- **Upload Custom Schedules**: CSV-based occupancy data import
- **Interactive Creation**: Web-based schedule builder
- **Modification Tools**: Edit existing schedules
- **Window Control**: Integrate window opening patterns
- **People Load**: Configure number of occupants and activity levels

### 3. Simulation Execution
- **Two Modes**:
  - Full simulation with occupancy data
  - IDF-only simulation (standard EnergyPlus)
- **Progress Monitoring**: Real-time status updates
- **Error Handling**: Comprehensive error reporting
- **Asynchronous Processing**: Non-blocking execution

### 4. Results Analysis
- **Interactive Plots**: Temperature, humidity, CO2 visualization
- **Data Export**: CSV and ESO file downloads
- **Historical Tracking**: Simulation history management
- **Comparative Analysis**: Multi-simulation comparison

### 5. REST API
- **Full Automation**: Programmatic access to all features
- **Standard HTTP Methods**: RESTful design
- **JSON Payloads**: Structured data exchange
- **Base64 Encoding**: Secure file transfer

---

## Data Flow

### Typical Simulation Workflow

```
1. User Input Phase
   ├─ Upload IDF file (building model)
   ├─ Upload EPW file (weather data)
   ├─ Configure room parameters
   └─ Define/upload occupancy schedule

2. Preprocessing Phase
   ├─ Frontend validates inputs
   ├─ Files cached locally
   ├─ Parameters stored in JSON
   └─ Data encoded for transfer

3. Simulation Setup Phase
   ├─ Backend receives encoded files
   ├─ Files decoded and validated
   ├─ IDF modified with parameters
   ├─ Occupancy schedules integrated
   └─ Simulation object created in DB

4. Execution Phase
   ├─ EnergyPlus invoked via eppy
   ├─ Simulation runs (can take minutes)
   ├─ Status checked periodically
   └─ Output files generated (ESO, etc.)

5. Post-Processing Phase
   ├─ ESO files parsed
   ├─ Data converted to CSV
   ├─ Results stored in database
   └─ Outputs encoded for transfer

6. Result Display Phase
   ├─ Frontend retrieves results
   ├─ Data decoded and processed
   ├─ Interactive plots generated
   └─ Download options provided
```

---

## Technology Stack

### Backend Technologies
- **Python 3.10**: Core programming language
- **Flask 2.0.3**: Web framework for REST API
- **eppy 0.5.60**: EnergyPlus Python interface
- **pandas 1.5.1**: Data manipulation and analysis
- **numpy 1.23.4**: Numerical computations
- **pymongo 4.3.2**: MongoDB driver
- **EnergyPlus 22-2-0/23-1-0**: Building simulation engine

### Frontend Technologies
- **Flask 2.0.3**: Web framework for GUI
- **WTForms 3.0.1**: Form handling and validation
- **Plotly 5.11.0**: Interactive plotting library
- **Matplotlib 3.6.2**: Static plot generation
- **Flask-CORS 3.0.10**: Cross-origin resource sharing

### Visualization Technologies
- **Node.js**: JavaScript runtime for spider server
- **Three.js**: 3D graphics library
- **Ladybug Tools**: Building visualization framework

### Database
- **MongoDB**: NoSQL document database
- **Docker**: Container platform for MongoDB deployment

### Additional Tools
- **requests 2.28.1**: HTTP library for API calls
- **marshmallow 3.18.0**: Object serialization
- **responses 0.22.0**: Mock HTTP responses for testing

---

## System Requirements

### Software Requirements
- **Operating System**: Windows 10/11 or Linux
- **Python**: Version 3.10 or higher
- **EnergyPlus**: Version 22-2-0 or 23-1-0
- **Docker**: Latest version (for MongoDB)
- **Node.js**: Latest LTS version (for visualization)

### Hardware Requirements (Recommended)
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8 GB minimum, 16 GB recommended
- **Storage**: 5 GB free space for application and simulations
- **Network**: Internet connection for initial setup

### Port Configuration
- **Backend API**: Port 5000 (configurable)
- **Frontend GUI**: Port 5001 (configurable)
- **MongoDB**: Port 27017 (default)
- **Spider Viewer**: Port 50715 (configurable)

---

## File Structure

```
EP-Room-Simulator/
├── backend/                 # Backend API server
│   ├── app.py              # Flask application entry
│   ├── endpoint.py         # REST API endpoints
│   ├── simulation.py       # Simulation logic
│   ├── Simulation_Helper.py # EnergyPlus integration
│   ├── Room_Helper.py      # Room geometry handling
│   ├── db_controller.py    # Database operations
│   ├── converterEsoToCsv.py # Output conversion
│   ├── utils.py            # Utility functions
│   ├── test/               # Backend tests
│   └── config.ini          # Configuration file
│
├── frontend/               # Frontend web application
│   ├── app.py             # Flask application entry
│   ├── fileHandler.py     # File upload/management
│   ├── startSim.py        # Simulation control
│   ├── viewResult.py      # Result visualization
│   ├── editParameters.py  # Parameter configuration
│   ├── OccupancyUpload.py # Occupancy file upload
│   ├── OccupancyCustom.py # Custom occupancy creation
│   ├── OccupancyModifier.py # Occupancy editing
│   ├── OccupancyData.py   # Occupancy data processing
│   ├── IDFUpdater.py      # IDF file modification
│   ├── template/          # HTML templates
│   ├── static/            # CSS, JS, images
│   └── test/              # Frontend tests
│
├── ladybug_spider/        # 3D visualization component
│   └── spider-idf-viewer/ # IDF viewer application
│
├── README.md              # Main documentation
├── OVERVIEW.md            # This file
├── requirements.txt       # Python dependencies
└── install.py            # Installation script
```

---

## Configuration Files

### Backend Configuration (`backend/config.ini`)
- EnergyPlus installation path
- Output directory paths
- MongoDB connection settings

### Frontend Configuration (`frontend/frontend_config.ini`)
- Server IP and port
- Upload directory paths
- Cache locations

### Metadata Storage (`frontend/meta_data/`)
- `date.json`: Simulation time frames
- `param.json`: Room parameters
- `ocp_error.json`: Occupancy validation errors
- `timeframe_error.json`: Time frame validation errors

---

## Key Workflows

### 1. Standard Simulation with Occupancy

```python
# Workflow steps:
1. Upload IDF file (building geometry)
2. Upload EPW file (weather data)
3. Set room parameters (dimensions, infiltration)
4. Upload or create occupancy schedule
5. Modify occupancy if needed
6. Start simulation
7. Monitor progress
8. View and download results
```

### 2. IDF-Only Simulation

```python
# Workflow steps:
1. Upload IDF file (must be complete)
2. Upload EPW file
3. Start simulation
4. Monitor progress
5. View and download results
```

### 3. API-Based Automation

```python
# Example workflow:
1. POST /simulation (create simulation)
2. PUT /simulation (upload IDF via base64)
3. PUT /simulation (upload EPW via base64)
4. POST /simulation/start (execute)
5. GET /simulation (check status)
6. GET /result (retrieve results)
7. GET /result/csv (download CSV)
```

---

## Integration Points

### 1. EnergyPlus Integration
- Via `eppy` library for IDF manipulation
- Direct command-line execution for simulation
- ESO file parsing for results extraction

### 2. MongoDB Integration
- Document-based storage for flexibility
- Base64 encoding for binary file storage
- Indexed queries for performance

### 3. Visualization Integration
- Node.js server for 3D rendering
- JSON-based model transfer
- WebGL/Three.js for graphics

---

## Error Handling

### Frontend Error Management
- JSON-based error notifications
- User-friendly error messages
- Validation before backend submission
- Graceful degradation

### Backend Error Management
- Exception logging with detailed traces
- HTTP status codes for API errors
- Simulation failure detection
- Database connection retry logic

### Common Error Scenarios
1. Invalid IDF file format
2. Mismatched occupancy time frames
3. EnergyPlus execution failures
4. Database connection issues
5. File encoding/decoding errors

---

## Security Considerations

### File Upload Security
- Filename sanitization via `werkzeug.utils.secure_filename`
- Extension validation
- File size limits (implicitly via Flask)
- Isolated storage directories

### API Security
- CORS configuration for allowed origins
- Input validation and sanitization
- Database query parameterization
- No direct file system access via API

### Data Storage
- Isolated simulation workspaces
- Temporary file cleanup
- Database access control (MongoDB authentication)

---

## Performance Characteristics

### Simulation Duration
- Typical simulation: 5-15 minutes
- Depends on:
  - Simulation period length
  - Time step resolution
  - Model complexity
  - Hardware capabilities

### Database Performance
- Fast document retrieval (indexed)
- Efficient binary storage (Base64)
- Scalable for multiple concurrent simulations

### Memory Usage
- Peak during simulation execution
- Moderate during file transfers
- Low during idle state

---

## Extensibility

The architecture supports extension through:

1. **New Simulation Parameters**: Add fields to `param.json` and corresponding UI
2. **Additional Output Variables**: Configure via `request_output_variables()`
3. **Custom Visualization**: Extend plotting functions in `viewResult.py`
4. **API Extensions**: Add endpoints in `endpoint.py`
5. **New File Formats**: Extend converters in backend
6. **Occupancy Patterns**: Enhance `OccupancyModifier.py` with new algorithms

---

## Testing

### Backend Tests
- `simulation_test.py`: Core simulation logic
- `endpoint_test.py`: API endpoint validation
- `db_controller_test.py`: Database operations
- `utils_test.py`: Utility function testing

### Frontend Tests
- `endpoint_connector_test.py`: API client testing

### Test Execution
```bash
# Backend tests
cd backend
python -m pytest test/

# Frontend tests
cd frontend
python -m pytest test/
```

---

## Logging

### Log Locations
- Backend: Console output with configurable levels
- Frontend: Console output and JSON error files
- EnergyPlus: Output files in `eppy_output/`

### Log Levels
- `INFO`: Normal operation messages
- `ERROR`: Failure scenarios with traces
- `DEBUG`: Detailed execution flow (when enabled)

---

## Maintenance

### Regular Tasks
1. MongoDB backup and cleanup
2. Temporary file directory cleanup
3. Log file rotation
4. Dependency updates
5. EnergyPlus version compatibility checks

### Troubleshooting
1. Check MongoDB container status
2. Verify EnergyPlus path configuration
3. Review log files for errors
4. Validate file permissions
5. Check port availability

---

## Related Documentation

- **Main README**: `/README.md` - Installation and quick start
- **EnergyPlus Documentation**: Official EnergyPlus guides
- **eppy Documentation**: Python library for EnergyPlus
- **Flask Documentation**: Web framework references
- **MongoDB Documentation**: Database operations

---

*This overview is part of the EP-Room-Simulator project documentation. For installation instructions, please refer to README.md.*
