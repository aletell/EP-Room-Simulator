"""
Live Dashboard for Real-Time Simulation Monitoring.

This module provides a Flask-based web dashboard for monitoring
simulation parameters in real-time with automatic updates.
"""

import json
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import deque

try:
    from flask import Flask, render_template_string, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None

logger = logging.getLogger(__name__)


class LiveDashboard:
    """
    Live web dashboard for real-time simulation monitoring.
    
    Provides a Flask-based web interface that displays simulation
    parameters and updates automatically via AJAX polling.
    
    Example:
        dashboard = LiveDashboard(port=5001)
        dashboard.start()
        
        # Update data from simulation
        dashboard.update_data({
            'zone_temperature': 23.5,
            'outdoor_temperature': 18.2,
            'window_state': 'open'
        })
        
        # Dashboard accessible at http://localhost:5001
    """
    
    def __init__(self, port: int = 5001, title: str = "Simulation Dashboard"):
        """
        Initialize live dashboard.
        
        Args:
            port: Port number for web server
            title: Dashboard title
        """
        if not FLASK_AVAILABLE:
            raise ImportError(
                "Flask is required for LiveDashboard. "
                "Install with: pip install flask flask-cors"
            )
        
        self.port = port
        self.title = title
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.current_data: Dict[str, Any] = {}
        self.history: Dict[str, deque] = {}
        self.max_history = 100
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return render_template_string(self._get_html_template())
        
        @self.app.route('/api/current')
        def get_current():
            """Get current simulation data."""
            return jsonify(self.current_data)
        
        @self.app.route('/api/history')
        def get_history():
            """Get historical data."""
            return jsonify({
                key: list(values)
                for key, values in self.history.items()
            })
        
        @self.app.route('/api/summary')
        def get_summary():
            """Get data summary statistics."""
            summary = {}
            for key, values in self.history.items():
                if values and isinstance(values[0], (int, float)):
                    summary[key] = {
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'latest': values[-1] if values else None
                    }
            return jsonify(summary)
    
    def _get_html_template(self) -> str:
        """Get HTML template for dashboard."""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .status-running {
            background: #10b981;
            color: white;
        }
        
        .status-stopped {
            background: #ef4444;
            color: white;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .card-title {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .card-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .card-unit {
            font-size: 1.2em;
            color: #999;
        }
        
        .card-temp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .card-temp .card-title,
        .card-temp .card-value,
        .card-temp .card-unit {
            color: white;
        }
        
        .card-window {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .card-window .card-title,
        .card-window .card-value,
        .card-window .card-unit {
            color: white;
        }
        
        .card-hvac {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        
        .card-hvac .card-title,
        .card-hvac .card-value,
        .card-hvac .card-unit {
            color: white;
        }
        
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .chart-title {
            font-size: 1.2em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        canvas {
            max-width: 100%;
            height: 300px;
        }
        
        .log-container {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            max-height: 400px;
            overflow-y: auto;
        }
        
        .log-entry {
            padding: 10px;
            border-left: 3px solid #667eea;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .log-time {
            color: #666;
            font-weight: bold;
        }
        
        .timestamp {
            color: #999;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .card-value {
                font-size: 2em;
            }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 ''' + self.title + '''</h1>
            <div id="status" class="status-badge status-running">● LIVE</div>
            <div class="timestamp">Last Update: <span id="last-update">--:--:--</span></div>
        </div>
        
        <div class="grid" id="metrics-grid">
            <!-- Metrics will be dynamically added here -->
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📊 Real-Time Temperature Trends</div>
            <canvas id="temperatureChart"></canvas>
        </div>
        
        <div class="log-container">
            <div class="chart-title">📝 Activity Log</div>
            <div id="log-entries"></div>
        </div>
    </div>
    
    <script>
        // Chart.js configuration
        const ctx = document.getElementById('temperatureChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Zone Temperature',
                    data: [],
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Outdoor Temperature',
                    data: [],
                    borderColor: 'rgb(118, 75, 162)',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
        
        const maxDataPoints = 50;
        const logEntries = [];
        
        function updateDashboard() {
            fetch('/api/current')
                .then(response => response.json())
                .then(data => {
                    updateMetrics(data);
                    updateChart(data);
                    updateLog(data);
                    document.getElementById('last-update').textContent = 
                        new Date().toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    document.getElementById('status').className = 
                        'status-badge status-stopped';
                    document.getElementById('status').textContent = '● OFFLINE';
                });
        }
        
        function updateMetrics(data) {
            const grid = document.getElementById('metrics-grid');
            grid.innerHTML = '';
            
            // Define metric configurations
            const metrics = [
                {
                    key: 'zone_temperature',
                    title: 'Zone Temperature',
                    unit: '°C',
                    className: 'card-temp',
                    format: (v) => v.toFixed(1)
                },
                {
                    key: 'outdoor_temperature',
                    title: 'Outdoor Temperature',
                    unit: '°C',
                    className: 'card-temp',
                    format: (v) => v.toFixed(1)
                },
                {
                    key: 'window_opening',
                    title: 'Window Opening',
                    unit: '%',
                    className: 'card-window',
                    format: (v) => Math.round(v * 100)
                },
                {
                    key: 'hvac_heating_setpoint',
                    title: 'Heating Setpoint',
                    unit: '°C',
                    className: 'card-hvac',
                    format: (v) => v.toFixed(1)
                },
                {
                    key: 'hvac_cooling_setpoint',
                    title: 'Cooling Setpoint',
                    unit: '°C',
                    className: 'card-hvac',
                    format: (v) => v.toFixed(1)
                },
                {
                    key: 'relative_humidity',
                    title: 'Relative Humidity',
                    unit: '%',
                    className: 'card',
                    format: (v) => v.toFixed(0)
                }
            ];
            
            metrics.forEach(metric => {
                if (data[metric.key] !== undefined) {
                    const card = document.createElement('div');
                    card.className = `card ${metric.className}`;
                    card.innerHTML = `
                        <div class="card-title">${metric.title}</div>
                        <div class="card-value">
                            ${metric.format(data[metric.key])}
                            <span class="card-unit">${metric.unit}</span>
                        </div>
                    `;
                    grid.appendChild(card);
                }
            });
        }
        
        function updateChart(data) {
            const now = new Date().toLocaleTimeString();
            
            if (chart.data.labels.length >= maxDataPoints) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
                chart.data.datasets[1].data.shift();
            }
            
            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(data.zone_temperature || null);
            chart.data.datasets[1].data.push(data.outdoor_temperature || null);
            
            chart.update('none');
        }
        
        function updateLog(data) {
            const logContainer = document.getElementById('log-entries');
            const now = new Date().toLocaleTimeString();
            
            // Create log message
            let message = `Updated: `;
            if (data.zone_temperature !== undefined) {
                message += `Zone ${data.zone_temperature.toFixed(1)}°C `;
            }
            if (data.window_opening !== undefined) {
                message += `| Window ${(data.window_opening * 100).toFixed(0)}% `;
            }
            if (data.control_action) {
                message += `| ${data.control_action}`;
            }
            
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `<span class="log-time">${now}</span> ${message}`;
            
            logContainer.insertBefore(entry, logContainer.firstChild);
            
            // Keep only last 20 entries
            while (logContainer.children.length > 20) {
                logContainer.removeChild(logContainer.lastChild);
            }
        }
        
        // Update every 1 second
        updateDashboard();
        setInterval(updateDashboard, 1000);
    </script>
</body>
</html>
        '''
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Update dashboard with new data.
        
        Args:
            data: Dictionary of current simulation values
        """
        self.current_data = {
            **data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Update history
        for key, value in data.items():
            if key not in self.history:
                self.history[key] = deque(maxlen=self.max_history)
            self.history[key].append(value)
    
    def start(self) -> None:
        """Start the dashboard server in a background thread."""
        if self.running:
            logger.warning("Dashboard already running")
            return
        
        self.running = True
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()
        logger.info(f"Dashboard started on http://localhost:{self.port}")
        print(f"\n🌐 Dashboard available at: http://localhost:{self.port}")
    
    def _run_server(self) -> None:
        """Run Flask server (internal method)."""
        self.app.run(
            host='0.0.0.0',
            port=self.port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    
    def stop(self) -> None:
        """Stop the dashboard server."""
        self.running = False
        logger.info("Dashboard stopped")
