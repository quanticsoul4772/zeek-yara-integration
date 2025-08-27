#!/usr/bin/env python3
"""
Monitoring and Metrics System for Distributed Scanner
Created: August 2025
Author: Security Team

This module provides comprehensive monitoring and alerting for the distributed
scanning system including metrics collection, performance tracking, and alerts.
"""

import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class AlertLevel(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Alert:
    """Alert data structure"""

    alert_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: float
    source: str
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[float] = None


@dataclass
class Metric:
    """Metric data structure"""

    name: str
    type: MetricType
    value: Union[int, float, List[float]]
    timestamp: float
    tags: Dict[str, str]
    description: str = ""


class MetricsCollector:
    """Collects and stores metrics from the distributed system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("zeek_yara.monitoring.MetricsCollector")

        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        self.lock = threading.Lock()
        self.collection_thread = None
        self.stop_event = threading.Event()
        self.collection_interval = config.get("METRICS_COLLECTION_INTERVAL", 30)

    def start_collection(self) -> None:
        """Start metrics collection thread"""
        if self.collection_thread and self.collection_thread.is_alive():
            return

        self.stop_event.clear()
        self.collection_thread = threading.Thread(
            target=self._collection_loop, daemon=True
        )
        self.collection_thread.start()
        self.logger.info("Started metrics collection")

    def stop_collection(self) -> None:
        """Stop metrics collection thread"""
        self.stop_event.set()
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=5.0)
        self.logger.info("Stopped metrics collection")

    def increment_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric"""
        with self.lock:
            self.counters[name] += value
            self._record_metric(
                name, MetricType.COUNTER, self.counters[name], tags or {}
            )

    def set_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric"""
        with self.lock:
            self.gauges[name] = value
            self._record_metric(name, MetricType.GAUGE, value, tags or {})

    def record_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram value"""
        with self.lock:
            self.histograms[name].append(value)
            self._record_metric(name, MetricType.HISTOGRAM, value, tags or {})

    def record_timer(
        self, name: str, duration: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer duration"""
        with self.lock:
            self.timers[name].append(duration)
            self._record_metric(name, MetricType.TIMER, duration, tags or {})

    def _record_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: Union[int, float],
        tags: Dict[str, str],
    ) -> None:
        """Record a metric internally"""
        metric = Metric(
            name=name, type=metric_type, value=value, timestamp=time.time(), tags=tags
        )
        self.metrics[name].append(metric)

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values"""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    name: {
                        "count": len(values),
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                        "avg": statistics.mean(values) if values else 0,
                        "median": statistics.median(values) if values else 0,
                    }
                    for name, values in self.histograms.items()
                },
                "timers": {
                    name: {
                        "count": len(values),
                        "min_ms": min(values) * 1000 if values else 0,
                        "max_ms": max(values) * 1000 if values else 0,
                        "avg_ms": statistics.mean(values) * 1000 if values else 0,
                        "median_ms": statistics.median(values) * 1000 if values else 0,
                    }
                    for name, values in self.timers.items()
                },
            }

    def get_metrics_summary(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get metrics summary for a time window (seconds)"""
        cutoff_time = time.time() - time_window

        with self.lock:
            summary = {}

            for name, metric_history in self.metrics.items():
                recent_metrics = [
                    m for m in metric_history if m.timestamp >= cutoff_time
                ]

                if recent_metrics:
                    values = [
                        m.value
                        for m in recent_metrics
                        if isinstance(m.value, (int, float))
                    ]

                    if values:
                        summary[name] = {
                            "count": len(values),
                            "min": min(values),
                            "max": max(values),
                            "avg": statistics.mean(values),
                            "median": (
                                statistics.median(values) if len(values) > 0 else 0
                            ),
                            "latest": values[-1] if values else 0,
                            "trend": self._calculate_trend(values),
                        }

            return summary

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values"""
        if len(values) < 2:
            return "stable"

        # Simple trend calculation using first and last quartiles
        q1_end = len(values) // 4
        q4_start = 3 * len(values) // 4

        if q1_end == q4_start:
            return "stable"

        q1_avg = statistics.mean(values[:q1_end]) if q1_end > 0 else values[0]
        q4_avg = (
            statistics.mean(values[q4_start:]) if q4_start < len(values) else values[-1]
        )

        diff_percent = ((q4_avg - q1_avg) / q1_avg * 100) if q1_avg != 0 else 0

        if diff_percent > 10:
            return "increasing"
        elif diff_percent < -10:
            return "decreasing"
        else:
            return "stable"

    def _collection_loop(self) -> None:
        """Main metrics collection loop"""
        while not self.stop_event.is_set():
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Sleep with responsive shutdown checking
                sleep_remaining = self.collection_interval
                while sleep_remaining > 0 and not self.stop_event.is_set():
                    sleep_time = min(1.0, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time

            except Exception as e:
                self.logger.error(f"Error in metrics collection: {e}")
                time.sleep(5.0)

    def _collect_system_metrics(self) -> None:
        """Collect system-level metrics"""
        import psutil

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("system.cpu_percent", cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge("system.memory_percent", memory.percent)
            self.set_gauge("system.memory_available_mb", memory.available / 1024 / 1024)

            # Disk usage
            disk = psutil.disk_usage("/")
            self.set_gauge("system.disk_percent", disk.percent)
            self.set_gauge("system.disk_free_gb", disk.free / 1024 / 1024 / 1024)

            # Network I/O
            net_io = psutil.net_io_counters()
            self.increment_counter("system.network_bytes_sent", net_io.bytes_sent)
            self.increment_counter("system.network_bytes_recv", net_io.bytes_recv)

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")


class AlertManager:
    """Manages alerts and notifications for the monitoring system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("zeek_yara.monitoring.AlertManager")

        # Alert storage
        self.alerts: List[Alert] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

        # Alert history
        self.max_alerts = config.get("MAX_ALERT_HISTORY", 1000)

        # Load default alert rules
        self._load_default_alert_rules()

    def _load_default_alert_rules(self) -> None:
        """Load default alert rules"""
        default_rules = {
            "high_error_rate": {
                "metric": "scanner.error_rate",
                "condition": ">",
                "threshold": self.config.get("ALERT_HIGH_ERROR_RATE", 0.1),
                "level": AlertLevel.ERROR,
                "message": "High error rate detected: {value:.2%}",
            },
            "high_queue_size": {
                "metric": "queue.size",
                "condition": ">",
                "threshold": self.config.get("ALERT_HIGH_QUEUE_SIZE", 100),
                "level": AlertLevel.WARNING,
                "message": "Queue size is high: {value} items",
            },
            "low_throughput": {
                "metric": "scanner.throughput",
                "condition": "<",
                "threshold": self.config.get("ALERT_LOW_THROUGHPUT", 1.0),
                "level": AlertLevel.WARNING,
                "message": "Scanner throughput is low: {value:.2f} files/sec",
            },
            "worker_offline": {
                "metric": "workers.offline_count",
                "condition": ">",
                "threshold": 0,
                "level": AlertLevel.ERROR,
                "message": "{value} worker(s) are offline",
            },
            "high_cpu_usage": {
                "metric": "system.cpu_percent",
                "condition": ">",
                "threshold": self.config.get("ALERT_HIGH_CPU", 80.0),
                "level": AlertLevel.WARNING,
                "message": "High CPU usage: {value:.1f}%",
            },
            "high_memory_usage": {
                "metric": "system.memory_percent",
                "condition": ">",
                "threshold": self.config.get("ALERT_HIGH_MEMORY", 80.0),
                "level": AlertLevel.WARNING,
                "message": "High memory usage: {value:.1f}%",
            },
            "low_disk_space": {
                "metric": "system.disk_percent",
                "condition": ">",
                "threshold": self.config.get("ALERT_LOW_DISK", 90.0),
                "level": AlertLevel.CRITICAL,
                "message": "Low disk space: {value:.1f}% used",
            },
        }

        self.alert_rules.update(default_rules)

    def add_alert_rule(self, name: str, rule: Dict[str, Any]) -> None:
        """Add a custom alert rule"""
        with self.lock:
            self.alert_rules[name] = rule
        self.logger.info(f"Added alert rule: {name}")

    def remove_alert_rule(self, name: str) -> bool:
        """Remove an alert rule"""
        with self.lock:
            if name in self.alert_rules:
                del self.alert_rules[name]
                self.logger.info(f"Removed alert rule: {name}")
                return True
        return False

    def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new alert"""
        alert_id = f"alert_{int(time.time() * 1000)}"

        alert = Alert(
            alert_id=alert_id,
            level=level,
            title=title,
            message=message,
            timestamp=time.time(),
            source=source,
            metadata=metadata or {},
        )

        with self.lock:
            self.alerts.append(alert)

            # Keep only recent alerts
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts :]

        self.logger.warning(f"Alert created [{level.value.upper()}] {title}: {message}")
        return alert_id

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = time.time()
                    self.logger.info(f"Alert resolved: {alert_id}")
                    return True
        return False

    def check_metrics_for_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        """Check metrics against alert rules and create alerts if needed"""
        created_alerts = []

        for rule_name, rule in self.alert_rules.items():
            try:
                metric_name = rule["metric"]
                condition = rule["condition"]
                threshold = rule["threshold"]
                level = rule["level"]
                message_template = rule["message"]

                # Get metric value (supports nested keys with dots)
                metric_value = self._get_nested_value(metrics, metric_name)

                if metric_value is None:
                    continue

                # Check condition
                alert_triggered = False
                if condition == ">" and metric_value > threshold:
                    alert_triggered = True
                elif condition == "<" and metric_value < threshold:
                    alert_triggered = True
                elif condition == "==" and metric_value == threshold:
                    alert_triggered = True
                elif condition == ">=" and metric_value >= threshold:
                    alert_triggered = True
                elif condition == "<=" and metric_value <= threshold:
                    alert_triggered = True

                if alert_triggered:
                    # Check if we already have an active alert for this rule
                    active_alert_exists = any(
                        not alert.resolved and alert.source == rule_name
                        for alert in self.alerts
                    )

                    if not active_alert_exists:
                        message = message_template.format(value=metric_value)
                        alert_id = self.create_alert(
                            level=level,
                            title=f"Alert: {rule_name}",
                            message=message,
                            source=rule_name,
                            metadata={
                                "metric": metric_name,
                                "value": metric_value,
                                "threshold": threshold,
                            },
                        )
                        created_alerts.append(alert_id)

            except Exception as e:
                self.logger.error(f"Error checking alert rule {rule_name}: {e}")

        return created_alerts

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = key.split(".")
        value = data

        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    return None
            return value
        except (KeyError, TypeError):
            return None

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        with self.lock:
            return [alert for alert in self.alerts if not alert.resolved]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        with self.lock:
            return self.alerts[-limit:] if self.alerts else []

    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get summary of alerts"""
        with self.lock:
            active_alerts = [alert for alert in self.alerts if not alert.resolved]

            summary = {
                "total_alerts": len(self.alerts),
                "active_alerts": len(active_alerts),
                "resolved_alerts": len(self.alerts) - len(active_alerts),
                "alerts_by_level": {},
                "recent_alerts": [asdict(alert) for alert in self.alerts[-10:]],
            }

            # Count by level
            for level in AlertLevel:
                count = sum(1 for alert in active_alerts if alert.level == level)
                summary["alerts_by_level"][level.value] = count

            return summary


class PerformanceTracker:
    """Tracks performance metrics and trends"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("zeek_yara.monitoring.PerformanceTracker")

        # Performance history
        self.performance_history: deque = deque(
            maxlen=1440
        )  # 24 hours of minute samples
        self.lock = threading.Lock()

        # Baseline metrics
        self.baseline_metrics: Dict[str, float] = {}
        self.baseline_calculation_samples = config.get(
            "BASELINE_CALCULATION_SAMPLES", 100
        )

    def record_performance(self, metrics: Dict[str, Any]) -> None:
        """Record performance snapshot"""
        performance_data = {
            "timestamp": time.time(),
            "throughput": metrics.get("scanner", {}).get("throughput", 0),
            "error_rate": metrics.get("scanner", {}).get("error_rate", 0),
            "average_scan_time": metrics.get("scanner", {}).get(
                "average_scan_time_ms", 0
            ),
            "queue_size": metrics.get("queue", {}).get("size", 0),
            "active_workers": metrics.get("workers", {}).get("healthy", 0),
            "cpu_percent": metrics.get("system", {}).get("cpu_percent", 0),
            "memory_percent": metrics.get("system", {}).get("memory_percent", 0),
        }

        with self.lock:
            self.performance_history.append(performance_data)

        # Update baselines if we have enough samples
        if len(self.performance_history) >= self.baseline_calculation_samples:
            self._update_baselines()

    def _update_baselines(self) -> None:
        """Update baseline performance metrics"""
        try:
            recent_samples = list(self.performance_history)[
                -self.baseline_calculation_samples :
            ]

            for metric in [
                "throughput",
                "error_rate",
                "average_scan_time",
                "cpu_percent",
                "memory_percent",
            ]:
                values = [
                    sample[metric]
                    for sample in recent_samples
                    if sample[metric] is not None
                ]
                if values:
                    self.baseline_metrics[f"{metric}_baseline"] = statistics.median(
                        values
                    )

        except Exception as e:
            self.logger.error(f"Error updating baselines: {e}")

    def get_performance_trends(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance trends for specified time period"""
        cutoff_time = time.time() - (hours * 3600)

        with self.lock:
            recent_data = [
                sample
                for sample in self.performance_history
                if sample["timestamp"] >= cutoff_time
            ]

        if not recent_data:
            return {}

        trends = {}

        for metric in [
            "throughput",
            "error_rate",
            "average_scan_time",
            "queue_size",
            "cpu_percent",
            "memory_percent",
        ]:
            values = [
                sample[metric] for sample in recent_data if sample[metric] is not None
            ]

            if values:
                trends[metric] = {
                    "current": values[-1] if values else 0,
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "trend": self._calculate_trend_direction(values),
                    "baseline_deviation": self._calculate_baseline_deviation(
                        metric, values[-1]
                    ),
                }

        return trends

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 10:
            return "insufficient_data"

        # Compare recent third with earlier third
        third = len(values) // 3
        early_avg = statistics.mean(values[:third])
        recent_avg = statistics.mean(values[-third:])

        if early_avg == 0:
            return "stable"

        change_percent = ((recent_avg - early_avg) / early_avg) * 100

        if change_percent > 5:
            return "increasing"
        elif change_percent < -5:
            return "decreasing"
        else:
            return "stable"

    def _calculate_baseline_deviation(
        self, metric: str, current_value: float
    ) -> Optional[float]:
        """Calculate deviation from baseline"""
        baseline_key = f"{metric}_baseline"
        baseline = self.baseline_metrics.get(baseline_key)

        if baseline is None or baseline == 0:
            return None

        return ((current_value - baseline) / baseline) * 100


class HealthChecker:
    """Comprehensive health checker for the distributed system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("zeek_yara.monitoring.HealthChecker")

        # Health check configuration
        self.check_interval = config.get("HEALTH_CHECK_INTERVAL", 60)
        self.health_thresholds = {
            "error_rate_threshold": config.get("HEALTH_ERROR_RATE_THRESHOLD", 0.05),
            "response_time_threshold": config.get(
                "HEALTH_RESPONSE_TIME_THRESHOLD", 5.0
            ),
            "queue_size_threshold": config.get("HEALTH_QUEUE_SIZE_THRESHOLD", 1000),
            "worker_availability_threshold": config.get(
                "HEALTH_WORKER_AVAILABILITY_THRESHOLD", 0.8
            ),
        }

    def perform_health_check(self, system_status: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_results = {
            "overall_health": "healthy",
            "timestamp": time.time(),
            "component_health": {},
            "recommendations": [],
        }

        # Check message queue health
        queue_health = self._check_queue_health(system_status.get("message_queue", {}))
        health_results["component_health"]["message_queue"] = queue_health

        # Check worker health
        worker_health = self._check_worker_health(system_status.get("workers", {}))
        health_results["component_health"]["workers"] = worker_health

        # Check system resources
        system_health = self._check_system_health(system_status.get("system", {}))
        health_results["component_health"]["system"] = system_health

        # Determine overall health
        component_statuses = [
            health_results["component_health"][component]["status"]
            for component in health_results["component_health"]
        ]

        if "critical" in component_statuses:
            health_results["overall_health"] = "critical"
        elif "unhealthy" in component_statuses:
            health_results["overall_health"] = "unhealthy"
        elif "warning" in component_statuses:
            health_results["overall_health"] = "warning"

        return health_results

    def _check_queue_health(self, queue_status: Dict[str, Any]) -> Dict[str, Any]:
        """Check message queue health"""
        queue_size = queue_status.get("queue_size", 0)

        status = "healthy"
        issues = []

        if queue_size > self.health_thresholds["queue_size_threshold"]:
            status = "warning"
            issues.append(f"Queue size is high: {queue_size}")

        return {"status": status, "queue_size": queue_size, "issues": issues}

    def _check_worker_health(self, worker_status: Dict[str, Any]) -> Dict[str, Any]:
        """Check worker health"""
        total_workers = worker_status.get("total", 0)
        healthy_workers = worker_status.get("healthy", 0)

        status = "healthy"
        issues = []

        if total_workers == 0:
            status = "critical"
            issues.append("No workers available")
        else:
            availability = healthy_workers / total_workers
            if availability < self.health_thresholds["worker_availability_threshold"]:
                status = "warning" if availability > 0.5 else "critical"
                issues.append(f"Low worker availability: {availability:.1%}")

        return {
            "status": status,
            "total_workers": total_workers,
            "healthy_workers": healthy_workers,
            "availability": healthy_workers / total_workers if total_workers > 0 else 0,
            "issues": issues,
        }

    def _check_system_health(self, system_status: Dict[str, Any]) -> Dict[str, Any]:
        """Check system resource health"""
        cpu_percent = system_status.get("cpu_percent", 0)
        memory_percent = system_status.get("memory_percent", 0)
        disk_percent = system_status.get("disk_percent", 0)

        status = "healthy"
        issues = []

        if cpu_percent > 90:
            status = "critical"
            issues.append(f"Critical CPU usage: {cpu_percent:.1f}%")
        elif cpu_percent > 80:
            status = "warning"
            issues.append(f"High CPU usage: {cpu_percent:.1f}%")

        if memory_percent > 90:
            status = "critical"
            issues.append(f"Critical memory usage: {memory_percent:.1f}%")
        elif memory_percent > 80:
            status = "warning"
            issues.append(f"High memory usage: {memory_percent:.1f}%")

        if disk_percent > 95:
            status = "critical"
            issues.append(f"Critical disk usage: {disk_percent:.1f}%")
        elif disk_percent > 90:
            status = "warning"
            issues.append(f"High disk usage: {disk_percent:.1f}%")

        return {
            "status": status,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "issues": issues,
        }


class MonitoringSystem:
    """Main monitoring system that coordinates all monitoring components"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("zeek_yara.monitoring.MonitoringSystem")

        # Initialize components
        self.metrics_collector = MetricsCollector(config)
        self.alert_manager = AlertManager(config)
        self.performance_tracker = PerformanceTracker(config)
        self.health_checker = HealthChecker(config)

        # Monitoring thread
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        self.monitoring_interval = config.get("MONITORING_INTERVAL", 60)

    def start_monitoring(self) -> None:
        """Start the monitoring system"""
        try:
            # Start metrics collection
            self.metrics_collector.start_collection()

            # Start monitoring loop
            self.stop_event.clear()
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self.monitoring_thread.start()

            self.logger.info("Monitoring system started")

        except Exception as e:
            self.logger.error(f"Error starting monitoring system: {e}")

    def stop_monitoring(self) -> None:
        """Stop the monitoring system"""
        try:
            self.stop_event.set()

            # Stop metrics collection
            self.metrics_collector.stop_collection()

            # Wait for monitoring thread
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)

            self.logger.info("Monitoring system stopped")

        except Exception as e:
            self.logger.error(f"Error stopping monitoring system: {e}")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while not self.stop_event.is_set():
            try:
                # Get current metrics
                current_metrics = self.metrics_collector.get_current_metrics()

                # Record performance
                self.performance_tracker.record_performance(current_metrics)

                # Check for alerts
                self.alert_manager.check_metrics_for_alerts(current_metrics)

                # Sleep with responsive shutdown checking
                sleep_remaining = self.monitoring_interval
                while sleep_remaining > 0 and not self.stop_event.is_set():
                    sleep_time = min(1.0, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        return {
            "metrics": self.metrics_collector.get_current_metrics(),
            "alerts": self.alert_manager.get_alerts_summary(),
            "performance": self.performance_tracker.get_performance_trends(),
            "timestamp": time.time(),
        }

    def export_metrics(self, file_path: str, format: str = "json") -> bool:
        """Export metrics to file"""
        try:
            dashboard_data = self.get_monitoring_dashboard()

            if format.lower() == "json":
                with open(file_path, "w") as f:
                    json.dump(dashboard_data, f, indent=2, default=str)
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False

            self.logger.info(f"Metrics exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting metrics: {e}")
            return False
