"""
File logging utilities for real-time simulation monitoring.

Provides multiple file output formats for logging simulation data
with support for real-time monitoring via tail -f and other tools.
"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, TextIO
from pathlib import Path

logger = logging.getLogger(__name__)


class FileLogger:
    """
    Multi-format file logger for simulation data.
    
    Supports CSV, JSON, and text formats with automatic flushing
    for real-time monitoring via tail -f.
    
    Example:
        logger = FileLogger('./logs')
        logger.start()
        
        # Log data
        logger.log({
            'zone_temperature': 23.5,
            'window_state': 'open'
        })
        
        # Monitor with: tail -f logs/simulation_YYYYMMDD_HHMMSS.csv
    """
    
    def __init__(self, log_dir: str = './simulation_logs'):
        """
        Initialize file logger.
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp_start = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # File handles
        self.csv_file: Optional[TextIO] = None
        self.csv_writer: Optional[csv.DictWriter] = None
        self.json_file: Optional[TextIO] = None
        self.text_file: Optional[TextIO] = None
        
        self.is_started = False
        self.fieldnames: Optional[List[str]] = None
        self.entry_count = 0
    
    def start(self) -> None:
        """Start logging to files."""
        if self.is_started:
            logger.warning("FileLogger already started")
            return
        
        # Open CSV file
        csv_path = self.log_dir / f'simulation_{self.timestamp_start}.csv'
        self.csv_file = open(csv_path, 'w', newline='', buffering=1)
        
        # Open JSON lines file
        json_path = self.log_dir / f'simulation_{self.timestamp_start}.jsonl'
        self.json_file = open(json_path, 'w', buffering=1)
        
        # Open text log file
        text_path = self.log_dir / f'simulation_{self.timestamp_start}.log'
        self.text_file = open(text_path, 'w', buffering=1)
        
        self.is_started = True
        
        print(f"\n📁 Logging to directory: {self.log_dir.absolute()}")
        print(f"   CSV:  {csv_path.name}")
        print(f"   JSON: {json_path.name}")
        print(f"   Text: {text_path.name}")
        print(f"\n💡 Monitor in real-time with:")
        print(f"   tail -f {csv_path}")
        print(f"   tail -f {text_path}")
    
    def log(self, data: Dict[str, Any], message: Optional[str] = None) -> None:
        """
        Log data to all output formats.
        
        Args:
            data: Dictionary of values to log
            message: Optional message for text log
        """
        if not self.is_started:
            raise RuntimeError("FileLogger not started. Call start() first.")
        
        # Add timestamp
        data_with_timestamp = {
            'timestamp': datetime.now().isoformat(),
            **data
        }
        
        # Initialize CSV writer with headers on first call
        if self.csv_writer is None:
            self.fieldnames = list(data_with_timestamp.keys())
            self.csv_writer = csv.DictWriter(
                self.csv_file,
                fieldnames=self.fieldnames
            )
            self.csv_writer.writeheader()
            self.csv_file.flush()
        
        # Write to CSV
        try:
            self.csv_writer.writerow(data_with_timestamp)
            self.csv_file.flush()
        except Exception as e:
            logger.error(f"Error writing to CSV: {e}")
        
        # Write to JSON lines
        try:
            json.dump(data_with_timestamp, self.json_file)
            self.json_file.write('\n')
            self.json_file.flush()
        except Exception as e:
            logger.error(f"Error writing to JSON: {e}")
        
        # Write to text log
        try:
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if message:
                self.text_file.write(f"[{timestamp_str}] {message}\n")
            else:
                # Format data nicely
                data_str = ' | '.join(
                    f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}"
                    for k, v in data.items()
                )
                self.text_file.write(f"[{timestamp_str}] {data_str}\n")
            self.text_file.flush()
        except Exception as e:
            logger.error(f"Error writing to text log: {e}")
        
        self.entry_count += 1
    
    def log_event(self, event_type: str, description: str, 
                  data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a specific event.
        
        Args:
            event_type: Type of event (e.g., 'CONTROL', 'ALERT', 'INFO')
            description: Event description
            data: Optional event data
        """
        event_data = {
            'event_type': event_type,
            'description': description
        }
        if data:
            event_data.update(data)
        
        self.log(event_data, message=f"[{event_type}] {description}")
    
    def stop(self) -> None:
        """Close all log files."""
        if not self.is_started:
            return
        
        # Close files
        if self.csv_file:
            self.csv_file.close()
        if self.json_file:
            self.json_file.close()
        if self.text_file:
            self.text_file.close()
        
        self.is_started = False
        print(f"\n✅ Logged {self.entry_count} entries to {self.log_dir}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class StructuredLogger:
    """
    Structured logger for detailed simulation events.
    
    Provides hierarchical logging with categorization and filtering.
    
    Example:
        logger = StructuredLogger('./logs/structured')
        logger.start()
        
        logger.log_control_action('window_open', {
            'zone': 'ZONE_1',
            'opening': 0.8,
            'reason': 'high_temperature'
        })
        
        logger.log_measurement('zone_temperature', 25.3, unit='°C')
    """
    
    def __init__(self, log_dir: str = './simulation_logs/structured'):
        """
        Initialize structured logger.
        
        Args:
            log_dir: Directory for structured log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp_start = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Category-specific files
        self.files: Dict[str, TextIO] = {}
        self.is_started = False
    
    def start(self) -> None:
        """Start structured logging."""
        if self.is_started:
            return
        
        # Create category files
        categories = ['control', 'measurements', 'alerts', 'events', 'errors']
        
        for category in categories:
            file_path = self.log_dir / f'{category}_{self.timestamp_start}.jsonl'
            self.files[category] = open(file_path, 'w', buffering=1)
        
        self.is_started = True
        print(f"\n📊 Structured logging to: {self.log_dir.absolute()}")
    
    def _log_to_category(self, category: str, entry_type: str, 
                        data: Dict[str, Any]) -> None:
        """Log entry to specific category."""
        if not self.is_started:
            raise RuntimeError("StructuredLogger not started")
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': entry_type,
            **data
        }
        
        if category in self.files:
            json.dump(entry, self.files[category])
            self.files[category].write('\n')
            self.files[category].flush()
    
    def log_control_action(self, action: str, params: Dict[str, Any]) -> None:
        """Log a control action."""
        self._log_to_category('control', 'action', {
            'action': action,
            **params
        })
    
    def log_measurement(self, variable: str, value: float, 
                       unit: Optional[str] = None) -> None:
        """Log a measurement."""
        data = {'variable': variable, 'value': value}
        if unit:
            data['unit'] = unit
        self._log_to_category('measurements', 'measurement', data)
    
    def log_alert(self, alert_type: str, message: str, 
                  severity: str = 'warning') -> None:
        """Log an alert."""
        self._log_to_category('alerts', 'alert', {
            'alert_type': alert_type,
            'message': message,
            'severity': severity
        })
    
    def log_event(self, event: str, details: Dict[str, Any]) -> None:
        """Log a general event."""
        self._log_to_category('events', 'event', {
            'event': event,
            **details
        })
    
    def log_error(self, error: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log an error."""
        data = {'error': error}
        if details:
            data.update(details)
        self._log_to_category('errors', 'error', data)
    
    def stop(self) -> None:
        """Close all log files."""
        if not self.is_started:
            return
        
        for file_handle in self.files.values():
            file_handle.close()
        
        self.is_started = False
        print(f"✅ Structured logs saved to {self.log_dir}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class MetricsAggregator:
    """
    Aggregate and export simulation metrics.
    
    Collects metrics over time and exports summary statistics.
    
    Example:
        aggregator = MetricsAggregator()
        
        # Record metrics
        aggregator.record('zone_temperature', 23.5)
        aggregator.record('zone_temperature', 24.1)
        
        # Export summary
        aggregator.export_summary('./summary.json')
    """
    
    def __init__(self):
        """Initialize metrics aggregator."""
        self.metrics: Dict[str, List[float]] = {}
        self.timestamps: Dict[str, List[datetime]] = {}
    
    def record(self, metric: str, value: float) -> None:
        """
        Record a metric value.
        
        Args:
            metric: Metric name
            value: Metric value
        """
        if metric not in self.metrics:
            self.metrics[metric] = []
            self.timestamps[metric] = []
        
        self.metrics[metric].append(value)
        self.timestamps[metric].append(datetime.now())
    
    def get_statistics(self, metric: str) -> Optional[Dict[str, float]]:
        """
        Get statistics for a metric.
        
        Args:
            metric: Metric name
            
        Returns:
            Dictionary with min, max, mean, std, count
        """
        if metric not in self.metrics or not self.metrics[metric]:
            return None
        
        values = self.metrics[metric]
        mean_val = sum(values) / len(values)
        
        # Calculate standard deviation
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_val = variance ** 0.5
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': mean_val,
            'std': std_val
        }
    
    def export_summary(self, output_path: str) -> None:
        """
        Export summary statistics to JSON file.
        
        Args:
            output_path: Path for output file
        """
        summary = {}
        
        for metric in self.metrics:
            summary[metric] = self.get_statistics(metric)
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📈 Metrics summary exported to: {output_path}")
    
    def export_timeseries(self, output_path: str, metric: Optional[str] = None) -> None:
        """
        Export time series data to CSV.
        
        Args:
            output_path: Path for output CSV file
            metric: Optional specific metric (exports all if None)
        """
        with open(output_path, 'w', newline='') as f:
            if metric:
                # Export single metric
                writer = csv.writer(f)
                writer.writerow(['timestamp', metric])
                
                for ts, val in zip(self.timestamps[metric], self.metrics[metric]):
                    writer.writerow([ts.isoformat(), val])
            else:
                # Export all metrics
                all_metrics = list(self.metrics.keys())
                writer = csv.DictWriter(f, fieldnames=['timestamp'] + all_metrics)
                writer.writeheader()
                
                # Find all unique timestamps
                all_ts = set()
                for ts_list in self.timestamps.values():
                    all_ts.update(ts_list)
                
                # Sort timestamps
                sorted_ts = sorted(all_ts)
                
                # Write rows
                for ts in sorted_ts:
                    row = {'timestamp': ts.isoformat()}
                    for metric_name in all_metrics:
                        # Find closest value for this timestamp
                        if ts in self.timestamps[metric_name]:
                            idx = self.timestamps[metric_name].index(ts)
                            row[metric_name] = self.metrics[metric_name][idx]
                    writer.writerow(row)
        
        print(f"📊 Time series data exported to: {output_path}")
