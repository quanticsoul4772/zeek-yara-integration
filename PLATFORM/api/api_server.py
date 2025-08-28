#!/usr/bin/env python3
"""
Zeek-YARA Integration API Server
Created: April 24, 2025
Author: Russell Smith

This module implements a RESTful API for the Zeek-YARA integration system using FastAPI.
It provides endpoints for retrieving alerts, system status, and basic control operations.
"""

import datetime
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

import uvicorn

# Import FastAPI components
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi import Path as PathParam
from fastapi import Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from PLATFORM.api.suricata_api import get_alert_correlator, get_suricata_runner, suricata_router
from config.config import Config
from core.database import DatabaseManager
from core.distributed import DistributedScanner, TaskPriority, WorkerNode
from core.monitoring import AlertLevel, MonitoringSystem
from core.scanner import MultiThreadScanner, SingleThreadScanner
from core.schemas import SchemaValidator
from suricata.alert_correlation import AlertCorrelator
from suricata.suricata_integration import SuricataRunner
from utils.file_utils import FileAnalyzer
from utils.yara_utils import RuleManager

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Import application components

# Import Suricata components

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("logs", "api.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("zeek_yara.api")

# Load configuration
config = Config.load_config()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Get worker registration rate limit from config
worker_registration_rate_limit = config.get("SECURITY", {}).get(
    "WORKER_REGISTRATION_RATE_LIMIT", "10/minute"
)

# Initialize API application
app = FastAPI(
    title="Zeek-YARA-Suricata Integration API",
    description="RESTful API for the Zeek-YARA-Suricata integration system",
    version="1.0.0",
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize application components
db_manager = DatabaseManager(db_file=config.get("DB_FILE"))
file_analyzer = FileAnalyzer(max_file_size=config.get("MAX_FILE_SIZE"))
rule_manager = RuleManager(
    rules_dir=config.get("RULES_DIR"), rules_index=config.get("RULES_INDEX")
)
schema_validator = SchemaValidator()

# Initialize Suricata components
suricata_runner = SuricataRunner(config)
alert_correlator = AlertCorrelator(config)

# API security - optional API key
API_KEY_NAME = "X-API-Key"
API_KEY = config.get("API_KEY", "")  # If not set, API key auth is disabled
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Scanner instance (for on-demand scanning)
scanner = None

# Distributed components (initialized if distributed mode is enabled)
distributed_scanner = None
monitoring_system = None

# Initialize distributed components if enabled
if config.get("DISTRIBUTED_ENABLED", False):
    distributed_scanner = DistributedScanner(config)
    if config.get("MONITORING_ENABLED", True):
        monitoring_system = MonitoringSystem(config)


# Pydantic models for API
class AlertModel(BaseModel):
    """Alert data model"""

    id: int
    timestamp: str
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    md5: str
    sha256: str
    zeek_uid: str
    rule_name: str
    rule_namespace: str
    rule_meta: Dict[str, Any]
    strings_matched: List[str]
    severity: int


class AlertsResponse(BaseModel):
    """Response model for alerts endpoint"""

    alerts: List[AlertModel]
    count: int
    total: int
    page: int
    page_size: int


class SystemStatusModel(BaseModel):
    """System status model"""

    status: str
    uptime: float
    scanner_type: str
    scanner_running: bool
    extracted_files_count: int
    rules_count: int
    alerts_count: int
    alerts_last_24h: int
    version: str
    suricata: Dict[str, Any]
    config: Dict[str, Any]


class ScanRequestModel(BaseModel):
    """Scan request model"""

    file_path: str = Field(..., description="Path to file or directory to scan")
    recursive: bool = Field(False, description="Recursively scan directories")


class ScanResultModel(BaseModel):
    """Scan result model"""

    success: bool
    matched: bool = False
    error: Optional[str] = None
    alerts: List[AlertModel] = []
    scan_time: float
    scanned_files: int = 0


class WebhookConfigModel(BaseModel):
    """Webhook configuration model"""

    url: str = Field(..., description="Webhook URL to send alerts to")
    secret: Optional[str] = Field(None, description="Secret for webhook authentication")
    events: List[str] = Field(
        ["alert"],
        description="Events to trigger webhook (alert, scan, startup, shutdown)",
    )
    enabled: bool = Field(True, description="Whether webhook is enabled")


class CleanupStatsModel(BaseModel):
    """File cleanup statistics model"""

    running: bool = Field(..., description="Whether cleanup scheduler is running")
    cleanup_enabled: bool = Field(..., description="Whether cleanup is enabled")
    total_cleanups: int = Field(..., description="Total number of cleanup operations")
    files_deleted: int = Field(..., description="Total files deleted")
    space_freed_bytes: int = Field(..., description="Total space freed in bytes")
    last_cleanup: Optional[str] = Field(None, description="Last cleanup timestamp")
    errors: int = Field(..., description="Number of cleanup errors")
    configuration: Dict[str, Any] = Field(..., description="Cleanup configuration")
    disk_usage: Optional[Dict[str, Any]] = Field(None, description="Current disk usage")


class CleanupResultModel(BaseModel):
    """File cleanup operation result model"""

    success: bool = Field(..., description="Whether cleanup was successful")
    start_time: str = Field(..., description="Cleanup start time")
    files_processed: int = Field(..., description="Number of files processed")
    files_deleted: int = Field(..., description="Number of files deleted")
    space_freed_bytes: int = Field(..., description="Space freed in bytes")
    errors: List[str] = Field(..., description="List of error messages")
    disk_usage_before: Optional[Dict[str, Any]] = Field(
        None, description="Disk usage before cleanup"
    )


# Distributed scanning models
class WorkerRegistrationModel(BaseModel):
    """Worker node registration model"""

    worker_id: str = Field(..., description="Unique worker identifier")
    host: str = Field(..., description="Worker host address")
    port: int = Field(..., description="Worker port number")
    max_tasks: int = Field(5, description="Maximum concurrent tasks")
    capabilities: List[str] = Field([], description="Worker capabilities")
    metadata: Dict[str, Any] = Field({}, description="Additional worker metadata")


class WorkerHeartbeatModel(BaseModel):
    """Worker heartbeat model"""

    current_tasks: int = Field(0, description="Current number of active tasks")
    total_processed: int = Field(0, description="Total tasks processed")
    error_count: int = Field(0, description="Number of errors encountered")
    average_processing_time: float = Field(
        0.0, description="Average processing time in seconds"
    )


class DistributedScanRequestModel(BaseModel):
    """Distributed scan request model"""

    file_path: str = Field(..., description="Path to file to scan")
    priority: int = Field(5, description="Task priority (1-10)")
    metadata: Dict[str, Any] = Field({}, description="Additional metadata")


class DistributedSystemStatusModel(BaseModel):
    """Distributed system status model"""

    running: bool = Field(..., description="Whether distributed system is running")
    message_queue: Dict[str, Any] = Field(..., description="Message queue status")
    workers: Dict[str, Any] = Field(..., description="Worker status information")
    load_balancer: Dict[str, Any] = Field(
        ..., description="Load balancer configuration"
    )
    config: Dict[str, Any] = Field(..., description="System configuration")


class MetricsExportModel(BaseModel):
    """Metrics export request model"""

    file_path: str = Field(..., description="Path to export metrics file")
    format: str = Field("json", description="Export format (json)")
    time_window: int = Field(3600, description="Time window in seconds")
    disk_usage_after: Optional[Dict[str, Any]] = Field(
        None, description="Disk usage after cleanup"
    )


# API key dependency
async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key if configured"""
    if API_KEY and api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API key required"},
        )
    return True


async def verify_api_key_required(api_key: str = Depends(api_key_header)):
    """Verify API key - always required for sensitive endpoints"""
    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="API authentication is required but not configured. Please set API_KEY in configuration.",
            headers={"WWW-Authenticate": "API key required"},
        )
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "API key required"},
        )
    return True


# Include Suricata API router
app.include_router(suricata_router)

# Add dependencies to Suricata router

app.dependency_overrides[get_suricata_runner] = lambda: suricata_runner
app.dependency_overrides[get_alert_correlator] = lambda: alert_correlator

# Start time for uptime calculation
start_time = time.time()


def get_public_config() -> Dict[str, Any]:
    """
    Get public configuration values safe for API exposure.
    Filters out sensitive configuration that should not be exposed externally.
    """
    # Define which config values are safe to expose publicly
    public_config_keys = [
        "EXTRACT_DIR",
        "RULES_DIR",
        "MAX_FILE_SIZE",
        "SCAN_INTERVAL",
        "LOG_LEVEL",
        "SCAN_MIME_TYPES",
        "SCAN_EXTENSIONS",
        "CORRELATION_ENABLED",
        "CORRELATION_WINDOW",
        "TIME_PROXIMITY_WINDOW",
        "MIN_ALERT_CONFIDENCE",
        "CLEANUP_ENABLED",
        "CLEANUP_RETENTION_CLEAN_HOURS",
        "CLEANUP_RETENTION_MATCHED_HOURS",
        "CLEANUP_INTERVAL_MINUTES",
        "CLEANUP_DISK_WARNING_THRESHOLD",
        "CLEANUP_DISK_CRITICAL_THRESHOLD",
    ]

    # Build filtered config dictionary
    public_config = {}
    for key in public_config_keys:
        value = config.get(key)
        if value is not None:
            public_config[key.lower()] = value

    return public_config


# Endpoints
@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Zeek-YARA Integration API",
        "version": "1.0.0",
        "documentation": "/docs",
    }


@app.get("/status", response_model=SystemStatusModel, tags=["System"])
async def get_status(_: bool = Depends(verify_api_key)):
    """Get system status information"""

    # Get scanner status
    scanner_running = False
    scanner_type = "None"

    if scanner:
        scanner_running = getattr(scanner, "running", False)
        scanner_type = (
            "Multi-threaded"
            if isinstance(scanner, MultiThreadScanner)
            else "Single-threaded"
        )

    # Count extracted files
    extract_dir = config.get("EXTRACT_DIR")
    extracted_files_count = 0

    if os.path.exists(extract_dir) and os.path.isdir(extract_dir):
        extracted_files_count = len(
            [
                f
                for f in os.listdir(extract_dir)
                if os.path.isfile(os.path.join(extract_dir, f))
            ]
        )

    # Get alert counts
    all_alerts = db_manager.get_alerts(limit=1000000)
    recent_cutoff = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    recent_alerts = [a for a in all_alerts if a.get("timestamp", "") >= recent_cutoff]

    # Get rule count
    rules_count = len(rule_manager.get_rule_list())

    # Get Suricata status
    suricata_status = suricata_runner.get_status()

    # Build status response
    status = {
        "status": "operational",
        "uptime": time.time() - start_time,
        "scanner_type": scanner_type,
        "scanner_running": scanner_running,
        "extracted_files_count": extracted_files_count,
        "rules_count": rules_count,
        "alerts_count": len(all_alerts),
        "alerts_last_24h": len(recent_alerts),
        "version": "1.0.0",
        "suricata": {
            "running": suricata_status.get("running", False),
            "version": suricata_status.get("version", "Unknown"),
            "alert_count": suricata_status.get("alert_count", 0),
            "rules_count": suricata_status.get("rules_count", 0),
        },
        "config": get_public_config(),
    }

    return status


# Performance monitoring endpoints
class PerformanceMetricsModel(BaseModel):
    """Performance metrics model"""

    uptime_seconds: float
    files_processed: int
    files_matched: int
    files_failed: int
    throughput_files_per_second: float
    average_scan_time_ms: float
    median_scan_time_ms: float
    current_queue_size: int
    average_queue_size: float
    active_threads: int
    worker_stats: Dict[str, Any]
    worker_health: Dict[str, Any]


class WorkerHealthModel(BaseModel):
    """Worker health status model"""

    worker_health: Dict[str, Dict[str, Any]]


@app.get("/performance", response_model=PerformanceMetricsModel, tags=["Performance"])
@limiter.limit("10/minute")
async def get_performance_metrics(
    request: Request, _: bool = Depends(verify_api_key_required)
):
    """Get detailed performance metrics for multi-threaded scanner"""
    if not scanner or not isinstance(scanner, MultiThreadScanner):
        raise HTTPException(
            status_code=400, detail="Multi-threaded scanner not available"
        )

    if not scanner.running:
        raise HTTPException(status_code=400, detail="Scanner is not running")

    try:
        metrics = scanner.get_performance_statistics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve performance metrics"
        )


@app.get("/performance/workers", response_model=WorkerHealthModel, tags=["Performance"])
@limiter.limit("10/minute")
async def get_worker_health(
    request: Request, _: bool = Depends(verify_api_key_required)
):
    """Get health status of all worker threads"""
    if not scanner or not isinstance(scanner, MultiThreadScanner):
        raise HTTPException(
            status_code=400, detail="Multi-threaded scanner not available"
        )

    if not scanner.running:
        raise HTTPException(status_code=400, detail="Scanner is not running")

    try:
        health_status = scanner.get_worker_health_status()
        return {"worker_health": health_status}
    except Exception as e:
        logger.error(f"Error getting worker health: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve worker health status"
        )


@app.get("/alerts", response_model=AlertsResponse, tags=["Alerts"])
async def get_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    severity: Optional[int] = Query(
        None, ge=0, le=10, description="Filter by severity"
    ),
    rule_name: Optional[str] = Query(None, description="Filter by rule name"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    zeek_uid: Optional[str] = Query(None, description="Filter by Zeek UID"),
    start_date: Optional[str] = Query(
        None, description="Filter by start date (ISO format)"
    ),
    end_date: Optional[str] = Query(
        None, description="Filter by end date (ISO format)"
    ),
    _: bool = Depends(verify_api_key),
):
    """
    Get paginated alerts with optional filtering
    """
    try:
        # Calculate offset and limit
        offset = (page - 1) * page_size
        limit = page_size

        # Get all alerts (for total count)
        all_alerts = db_manager.get_alerts(limit=1000000)

        # Apply filters
        filtered_alerts = all_alerts

        if severity is not None:
            filtered_alerts = [
                a for a in filtered_alerts if a.get("severity") == severity
            ]

        if rule_name:
            filtered_alerts = [
                a
                for a in filtered_alerts
                if rule_name.lower() in a.get("rule_name", "").lower()
            ]

        if file_type:
            filtered_alerts = [
                a
                for a in filtered_alerts
                if file_type.lower() in a.get("file_type", "").lower()
            ]

        if zeek_uid:
            filtered_alerts = [
                a for a in filtered_alerts if zeek_uid == a.get("zeek_uid")
            ]

        if start_date:
            filtered_alerts = [
                a for a in filtered_alerts if a.get("timestamp", "") >= start_date
            ]

        if end_date:
            filtered_alerts = [
                a for a in filtered_alerts if a.get("timestamp", "") <= end_date
            ]

        # Apply pagination
        paginated_alerts = filtered_alerts[offset : offset + limit]

        # Convert to API models
        alerts = []
        for alert in paginated_alerts:
            # Parse JSON fields
            rule_meta = alert.get("rule_meta", {})
            if isinstance(rule_meta, str):
                try:
                    rule_meta = json.loads(rule_meta)
                except BaseException:
                    rule_meta = {}

            strings_matched = alert.get("strings_matched", [])
            if isinstance(strings_matched, str):
                try:
                    strings_matched = json.loads(strings_matched)
                except BaseException:
                    strings_matched = []

            # Create alert model
            alerts.append(
                AlertModel(
                    id=alert.get("id", 0),
                    timestamp=alert.get("timestamp", ""),
                    file_path=alert.get("file_path", ""),
                    file_name=alert.get("file_name", ""),
                    file_size=alert.get("file_size", 0),
                    file_type=alert.get("file_type", ""),
                    md5=alert.get("md5", ""),
                    sha256=alert.get("sha256", ""),
                    zeek_uid=alert.get("zeek_uid", ""),
                    rule_name=alert.get("rule_name", ""),
                    rule_namespace=alert.get("rule_namespace", ""),
                    rule_meta=rule_meta,
                    strings_matched=strings_matched,
                    severity=alert.get("severity", 0),
                )
            )

        # Return response
        return AlertsResponse(
            alerts=alerts,
            count=len(alerts),
            total=len(filtered_alerts),
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Error retrieving alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving alerts: {str(e)}"
        )


@app.get("/alerts/{alert_id}", response_model=AlertModel, tags=["Alerts"])
async def get_alert(
    alert_id: int = PathParam(..., description="Alert ID"),
    _: bool = Depends(verify_api_key),
):
    """
    Get a specific alert by ID
    """
    try:
        # Get all alerts (not efficient, but works for prototype)
        all_alerts = db_manager.get_alerts(limit=1000000)

        # Find alert by ID
        alert = next((a for a in all_alerts if a.get("id") == alert_id), None)

        if not alert:
            raise HTTPException(
                status_code=404, detail=f"Alert with ID {alert_id} not found"
            )

        # Parse JSON fields
        rule_meta = alert.get("rule_meta", {})
        if isinstance(rule_meta, str):
            try:
                rule_meta = json.loads(rule_meta)
            except BaseException:
                rule_meta = {}

        strings_matched = alert.get("strings_matched", [])
        if isinstance(strings_matched, str):
            try:
                strings_matched = json.loads(strings_matched)
            except BaseException:
                strings_matched = []

        # Return alert model
        return AlertModel(
            id=alert.get("id", 0),
            timestamp=alert.get("timestamp", ""),
            file_path=alert.get("file_path", ""),
            file_name=alert.get("file_name", ""),
            file_size=alert.get("file_size", 0),
            file_type=alert.get("file_type", ""),
            md5=alert.get("md5", ""),
            sha256=alert.get("sha256", ""),
            zeek_uid=alert.get("zeek_uid", ""),
            rule_name=alert.get("rule_name", ""),
            rule_namespace=alert.get("rule_namespace", ""),
            rule_meta=rule_meta,
            strings_matched=strings_matched,
            severity=alert.get("severity", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving alert: {str(e)}")


@app.post("/scan", response_model=ScanResultModel, tags=["Scanning"])
async def scan_file(scan_request: ScanRequestModel, _: bool = Depends(verify_api_key)):
    """
    Scan a file or directory on demand
    """
    try:
        # Validate file path
        file_path = scan_request.file_path
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, detail=f"File or directory not found: {file_path}"
            )

        # Initialize scanner if not already done
        global scanner
        if not scanner:
            scanner = SingleThreadScanner(config)

        # Start timing
        start_time = time.time()

        # Scan file or directory
        if os.path.isfile(file_path):
            # Scan single file
            result = scanner.scan_file(file_path)
            scanned_files = 1

            # Check for matches
            matched = result.get("matched", False)
            error = result.get("error", None)

            # Get alerts for this file
            all_alerts = db_manager.get_alerts(limit=1000)

            # Find alerts by file path (simple match, can be improved)
            alerts = []
            for alert in all_alerts:
                if alert.get("file_path") == file_path:
                    # Parse JSON fields
                    rule_meta = alert.get("rule_meta", {})
                    if isinstance(rule_meta, str):
                        try:
                            rule_meta = json.loads(rule_meta)
                        except BaseException:
                            rule_meta = {}

                    strings_matched = alert.get("strings_matched", [])
                    if isinstance(strings_matched, str):
                        try:
                            strings_matched = json.loads(strings_matched)
                        except BaseException:
                            strings_matched = []

                    # Create alert model
                    alerts.append(
                        AlertModel(
                            id=alert.get("id", 0),
                            timestamp=alert.get("timestamp", ""),
                            file_path=alert.get("file_path", ""),
                            file_name=alert.get("file_name", ""),
                            file_size=alert.get("file_size", 0),
                            file_type=alert.get("file_type", ""),
                            md5=alert.get("md5", ""),
                            sha256=alert.get("sha256", ""),
                            zeek_uid=alert.get("zeek_uid", ""),
                            rule_name=alert.get("rule_name", ""),
                            rule_namespace=alert.get("rule_namespace", ""),
                            rule_meta=rule_meta,
                            strings_matched=strings_matched,
                            severity=alert.get("severity", 0),
                        )
                    )

        else:
            # Scan directory
            if scan_request.recursive:
                # Recursive scanning - walk directory tree
                result = {"matched": False, "errors": []}
                files_to_scan = []

                # Get all files
                for root, _, files in os.walk(file_path):
                    for file in files:
                        files_to_scan.append(os.path.join(root, file))

                # Scan each file
                for file in files_to_scan:
                    file_result = scanner.scan_file(file)
                    if file_result.get("matched", False):
                        result["matched"] = True

                scanned_files = len(files_to_scan)

                # Get all alerts
                all_alerts = db_manager.get_alerts(limit=1000)

                # Find alerts for files in this directory
                alerts = []
                for alert in all_alerts:
                    if alert.get("file_path", "").startswith(file_path):
                        # Parse JSON fields
                        rule_meta = alert.get("rule_meta", {})
                        if isinstance(rule_meta, str):
                            try:
                                rule_meta = json.loads(rule_meta)
                            except BaseException:
                                rule_meta = {}

                        strings_matched = alert.get("strings_matched", [])
                        if isinstance(strings_matched, str):
                            try:
                                strings_matched = json.loads(strings_matched)
                            except BaseException:
                                strings_matched = []

                        # Create alert model
                        alerts.append(
                            AlertModel(
                                id=alert.get("id", 0),
                                timestamp=alert.get("timestamp", ""),
                                file_path=alert.get("file_path", ""),
                                file_name=alert.get("file_name", ""),
                                file_size=alert.get("file_size", 0),
                                file_type=alert.get("file_type", ""),
                                md5=alert.get("md5", ""),
                                sha256=alert.get("sha256", ""),
                                zeek_uid=alert.get("zeek_uid", ""),
                                rule_name=alert.get("rule_name", ""),
                                rule_namespace=alert.get("rule_namespace", ""),
                                rule_meta=rule_meta,
                                strings_matched=strings_matched,
                                severity=alert.get("severity", 0),
                            )
                        )

                # Set error if any
                error = None
                if result.get("errors"):
                    error = "; ".join(result["errors"])

            else:
                # Non-recursive - just scan files in top directory
                dir_result = scanner.scan_directory(directory=file_path)

                matched = dir_result.get("matched", 0) > 0
                error = dir_result.get("error", None)
                scanned_files = dir_result.get("scanned", 0)

                # Get all alerts
                all_alerts = db_manager.get_alerts(limit=1000)

                # Find alerts for files in this directory
                alerts = []
                for alert in all_alerts:
                    # Simple check - can be improved
                    alert_path = alert.get("file_path", "")
                    if (
                        alert_path.startswith(file_path)
                        and alert_path.count("/") <= file_path.count("/") + 1
                    ):
                        # Parse JSON fields
                        rule_meta = alert.get("rule_meta", {})
                        if isinstance(rule_meta, str):
                            try:
                                rule_meta = json.loads(rule_meta)
                            except BaseException:
                                rule_meta = {}

                        strings_matched = alert.get("strings_matched", [])
                        if isinstance(strings_matched, str):
                            try:
                                strings_matched = json.loads(strings_matched)
                            except BaseException:
                                strings_matched = []

                        # Create alert model
                        alerts.append(
                            AlertModel(
                                id=alert.get("id", 0),
                                timestamp=alert.get("timestamp", ""),
                                file_path=alert.get("file_path", ""),
                                file_name=alert.get("file_name", ""),
                                file_size=alert.get("file_size", 0),
                                file_type=alert.get("file_type", ""),
                                md5=alert.get("md5", ""),
                                sha256=alert.get("sha256", ""),
                                zeek_uid=alert.get("zeek_uid", ""),
                                rule_name=alert.get("rule_name", ""),
                                rule_namespace=alert.get("rule_namespace", ""),
                                rule_meta=rule_meta,
                                strings_matched=strings_matched,
                                severity=alert.get("severity", 0),
                            )
                        )

        # Calculate scan time
        scan_time = time.time() - start_time

        # Return result
        return ScanResultModel(
            success=True,
            matched=matched,
            error=error,
            alerts=alerts,
            scan_time=scan_time,
            scanned_files=scanned_files,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error scanning {scan_request.file_path}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Error scanning file: {str(e)}")


@app.post("/scanner/start", tags=["Scanner Control"])
async def start_scanner(
    threads: int = Query(
        0, ge=0, description="Number of threads (0 for single-threaded)"
    ),
    background_tasks: BackgroundTasks = None,
    _: bool = Depends(verify_api_key),
):
    """
    Start the scanner in monitoring mode
    """
    try:
        global scanner

        # Stop existing scanner if running
        if scanner and getattr(scanner, "running", False):
            scanner.stop_monitoring()

        # Initialize scanner
        if threads > 0:
            # Multi-threaded scanner
            thread_config = config.copy()
            thread_config["THREADS"] = threads
            scanner = MultiThreadScanner(thread_config)
        else:
            # Single-threaded scanner
            scanner = SingleThreadScanner(config)

        # Start scanner in background task to avoid blocking
        if background_tasks:
            background_tasks.add_task(scanner.start_monitoring)

            # Wait briefly for startup
            time.sleep(0.5)

            return {
                "success": True,
                "scanner_type": "Multi-threaded" if threads > 0 else "Single-threaded",
                "threads": threads if threads > 0 else 1,
                "status": "starting",
            }
        else:
            # Start directly (may block)
            success = scanner.start_monitoring()

            return {
                "success": success,
                "scanner_type": "Multi-threaded" if threads > 0 else "Single-threaded",
                "threads": threads if threads > 0 else 1,
                "status": "running" if success else "error",
            }

    except Exception as e:
        logger.error(f"Error starting scanner: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting scanner: {str(e)}")


@app.post("/scanner/stop", tags=["Scanner Control"])
async def stop_scanner(_: bool = Depends(verify_api_key)):
    """
    Stop the scanner if running
    """
    try:
        if not scanner:
            return {"success": True, "status": "not_running"}

        if not getattr(scanner, "running", False):
            return {"success": True, "status": "not_running"}

        # Stop scanner
        success = scanner.stop_monitoring()

        return {"success": success, "status": "stopped" if success else "error"}

    except Exception as e:
        logger.error(f"Error stopping scanner: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error stopping scanner: {str(e)}")


@app.post("/rules/update", tags=["Rules Management"])
async def update_rules(_: bool = Depends(verify_api_key)):
    """
    Update and recompile YARA rules
    """
    try:
        # Update rules
        success = rule_manager.compile_rules(force=True)

        # Update scanner rules if running
        if scanner:
            scanner.rule_manager = rule_manager
            if hasattr(scanner, "yara_matcher"):
                scanner.yara_matcher.rule_manager = rule_manager

        return {
            "success": success,
            "rule_count": len(rule_manager.get_rule_list()),
            "status": "updated" if success else "error",
        }

    except Exception as e:
        logger.error(f"Error updating rules: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating rules: {str(e)}")


@app.get("/rules", tags=["Rules Management"])
async def get_rules(_: bool = Depends(verify_api_key)):
    """
    Get list of available YARA rules
    """
    try:
        rules = rule_manager.get_rule_list()

        # Get rule information
        rule_info = []

        for rule in rules:
            info = {
                "name": rule.get("name", "unknown"),
                "namespace": rule.get("namespace", "default"),
                "tags": rule.get("tags", []),
                "meta": rule.get("meta", {}),
            }
            rule_info.append(info)

        return {"rules": rule_info, "count": len(rule_info)}

    except Exception as e:
        logger.error(f"Error retrieving rules: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving rules: {str(e)}")


@app.get("/cleanup/stats", response_model=CleanupStatsModel, tags=["File Cleanup"])
async def get_cleanup_statistics(_: bool = Depends(verify_api_key)):
    """
    Get file cleanup statistics and configuration
    """
    try:
        if not scanner:
            raise HTTPException(status_code=503, detail="Scanner not available")

        stats = scanner.get_cleanup_statistics()
        return CleanupStatsModel(**stats)

    except Exception as e:
        logger.error(f"Error retrieving cleanup statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving cleanup statistics: {str(e)}"
        )


@app.post("/cleanup/force", response_model=CleanupResultModel, tags=["File Cleanup"])
async def force_cleanup(_: bool = Depends(verify_api_key)):
    """
    Force an immediate cleanup operation
    """
    try:
        if not scanner:
            raise HTTPException(status_code=503, detail="Scanner not available")

        result = scanner.force_cleanup()
        return CleanupResultModel(**result)

    except Exception as e:
        logger.error(f"Error forcing cleanup: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error forcing cleanup: {str(e)}")


@app.post("/webhook/config", tags=["Webhooks"])
async def configure_webhook(
    webhook_config: WebhookConfigModel, _: bool = Depends(verify_api_key)
):
    """
    Configure webhook for alert notifications
    """
    try:
        # Save webhook configuration
        webhook_file = os.path.join("config", "webhook.json")

        with open(webhook_file, "w") as f:
            json.dump(webhook_config.dict(), f, indent=2)

        return {"success": True, "webhook": webhook_config.dict()}

    except Exception as e:
        logger.error(f"Error configuring webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error configuring webhook: {str(e)}"
        )


@app.get("/webhook/config", tags=["Webhooks"])
async def get_webhook_config(_: bool = Depends(verify_api_key)):
    """
    Get current webhook configuration
    """
    try:
        webhook_file = os.path.join("config", "webhook.json")

        if not os.path.exists(webhook_file):
            return {"configured": False, "webhook": None}

        with open(webhook_file, "r") as f:
            webhook_config = json.load(f)

        return {"configured": True, "webhook": webhook_config}

    except Exception as e:
        logger.error(f"Error retrieving webhook config: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving webhook config: {str(e)}",
        )


# Distributed scanning endpoints
@app.post("/distributed/start", tags=["Distributed"])
async def start_distributed_system(_: bool = Depends(verify_api_key)):
    """
    Start the distributed scanning system
    """
    if not distributed_scanner:
        raise HTTPException(
            status_code=400, detail="Distributed scanning is not enabled"
        )

    try:
        success = distributed_scanner.start()
        if monitoring_system:
            monitoring_system.start_monitoring()

        return {
            "success": success,
            "message": (
                "Distributed system started"
                if success
                else "Failed to start distributed system"
            ),
        }
    except Exception as e:
        logger.error(f"Error starting distributed system: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error starting distributed system: {str(e)}"
        )


@app.post("/distributed/stop", tags=["Distributed"])
async def stop_distributed_system(_: bool = Depends(verify_api_key)):
    """
    Stop the distributed scanning system
    """
    if not distributed_scanner:
        raise HTTPException(
            status_code=400, detail="Distributed scanning is not enabled"
        )

    try:
        distributed_scanner.stop()
        if monitoring_system:
            monitoring_system.stop_monitoring()

        return {"success": True, "message": "Distributed system stopped"}
    except Exception as e:
        logger.error(f"Error stopping distributed system: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error stopping distributed system: {str(e)}"
        )


@app.get(
    "/distributed/status",
    response_model=DistributedSystemStatusModel,
    tags=["Distributed"],
)
async def get_distributed_status(_: bool = Depends(verify_api_key)):
    """
    Get comprehensive distributed system status
    """
    if not distributed_scanner:
        raise HTTPException(
            status_code=400, detail="Distributed scanning is not enabled"
        )

    try:
        status = distributed_scanner.get_system_status()
        return DistributedSystemStatusModel(**status)
    except Exception as e:
        logger.error(f"Error getting distributed status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting distributed status: {str(e)}"
        )


@app.post("/distributed/workers/register", tags=["Distributed"])
@limiter.limit(worker_registration_rate_limit)
async def register_worker(
    worker_data: WorkerRegistrationModel,
    request: Request,
    _: bool = Depends(verify_api_key),
):
    """
    Register a new worker node with enhanced security validation
    """
    if not distributed_scanner:
        raise HTTPException(
            status_code=400, detail="Distributed scanning is not enabled"
        )

    # Security checks
    environment = config.get("ENVIRONMENT", "development").lower()

    # Enforce HTTPS in production
    if environment == "production" and request.url.scheme != "https":
        logger.warning(
            f"Rejected worker registration from {request.client.host} - HTTPS required in production"
        )
        raise HTTPException(
            status_code=400,
            detail="HTTPS is required for worker registration in production",
        )

    # Rate limiting is enforced by the @limiter.limit decorator above
    client_ip = request.client.host
    logger.info(
        f"Worker registration attempt from {client_ip} for worker {worker_data.worker_id}"
    )

    try:
        # Additional JSON schema validation beyond Pydantic model
        worker_dict = worker_data.dict()
        try:
            schema_validator.validate("worker_registration", worker_dict)
        except Exception as validation_error:
            logger.error(
                f"Worker registration schema validation failed: {validation_error}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid worker registration data: {str(validation_error)}",
            )

        # Security validation of worker data
        worker_id = worker_dict.get("worker_id", "")
        if not worker_id or len(worker_id) < 3 or len(worker_id) > 64:
            raise HTTPException(
                status_code=400, detail="Worker ID must be between 3 and 64 characters"
            )

        # Validate capabilities
        capabilities = worker_dict.get("capabilities", [])
        allowed_capabilities = [
            "file_scan",
            "yara_analysis",
            "network_analysis",
            "log_analysis",
        ]
        invalid_capabilities = [
            cap for cap in capabilities if cap not in allowed_capabilities
        ]
        if invalid_capabilities:
            raise HTTPException(
                status_code=400, detail=f"Invalid capabilities: {invalid_capabilities}"
            )

        # Validate port range
        port = worker_dict.get("port", 0)
        if port < 1024 or port > 65535:
            raise HTTPException(
                status_code=400, detail="Worker port must be between 1024 and 65535"
            )

        # Validate max_tasks reasonable limit
        max_tasks = worker_dict.get("max_tasks", 0)
        if max_tasks < 1 or max_tasks > 100:
            raise HTTPException(
                status_code=400, detail="max_tasks must be between 1 and 100"
            )

        # Check for duplicate worker registration
        existing_workers = distributed_scanner.worker_manager.get_workers()
        for existing_worker in existing_workers:
            if existing_worker.worker_id == worker_id:
                logger.warning(f"Attempt to register duplicate worker ID: {worker_id}")
                raise HTTPException(
                    status_code=409,
                    detail=f"Worker ID {worker_id} is already registered",
                )

        # Register the worker
        success = distributed_scanner.worker_manager.register_worker(worker_dict)

        if success:
            logger.info(f"Successfully registered worker {worker_id} from {client_ip}")
            return {
                "success": True,
                "worker_id": worker_data.worker_id,
                "message": "Worker registered successfully",
                "timestamp": time.time(),
            }
        else:
            logger.error(f"Failed to register worker {worker_id}")
            return {
                "success": False,
                "worker_id": worker_data.worker_id,
                "message": "Failed to register worker - internal error",
            }

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        logger.error(f"Error registering worker: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during worker registration"
        )


@app.delete("/distributed/workers/{worker_id}", tags=["Distributed"])
async def unregister_worker(worker_id: str, _: bool = Depends(verify_api_key)):
    """
    Unregister a worker node
    """
    if not distributed_scanner:
        raise HTTPException(
            status_code=400, detail="Distributed scanning is not enabled"
        )

    try:
        success = distributed_scanner.worker_manager.unregister_worker(worker_id)
        return {
            "success": success,
            "worker_id": worker_id,
            "message": "Worker unregistered" if success else "Worker not found",
        }
    except Exception as e:
        logger.error(f"Error unregistering worker: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error unregistering worker: {str(e)}"
        )


@app.get("/distributed/workers", tags=["Distributed"])
async def get_workers(_: bool = Depends(verify_api_key)):
    """
    Get list of all registered workers
    """
    if not distributed_scanner:
        raise HTTPException(
            status_code=400, detail="Distributed scanning is not enabled"
        )

    try:
        workers = distributed_scanner.worker_manager.get_workers()
        return {"workers": [worker.to_dict() for worker in workers]}
    except Exception as e:
        logger.error(f"Error getting workers: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting workers: {str(e)}")


@app.put("/distributed/workers/{worker_id}/heartbeat", tags=["Distributed"])
async def worker_heartbeat(
    worker_id: str,
    heartbeat_data: WorkerHeartbeatModel,
    _: bool = Depends(verify_api_key),
):
    """
    Update worker heartbeat
    """
    if not distributed_scanner:
        raise HTTPException(
            status_code=400, detail="Distributed scanning is not enabled"
        )

    try:
        success = distributed_scanner.worker_manager.update_worker_heartbeat(
            worker_id, heartbeat_data.dict()
        )
        return {
            "success": success,
            "worker_id": worker_id,
            "message": "Heartbeat updated" if success else "Worker not found",
        }
    except Exception as e:
        logger.error(f"Error updating worker heartbeat: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error updating worker heartbeat: {str(e)}"
        )


@app.post("/distributed/scan", tags=["Distributed"])
async def submit_distributed_scan(
    scan_request: DistributedScanRequestModel, _: bool = Depends(verify_api_key)
):
    """
    Submit a file scan task to the distributed system
    """
    if not distributed_scanner:
        raise HTTPException(
            status_code=400, detail="Distributed scanning is not enabled"
        )

    try:
        task_id = distributed_scanner.submit_scan_task(
            file_path=scan_request.file_path,
            priority=scan_request.priority,
            metadata=scan_request.metadata,
        )

        if task_id:
            return {
                "success": True,
                "task_id": task_id,
                "message": "Scan task submitted",
            }
        else:
            return {"success": False, "message": "Failed to submit scan task"}
    except Exception as e:
        logger.error(f"Error submitting distributed scan: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error submitting distributed scan: {str(e)}"
        )


# Monitoring endpoints
@app.get("/monitoring/metrics", tags=["Monitoring"])
async def get_current_metrics(_: bool = Depends(verify_api_key)):
    """
    Get current system metrics
    """
    if not monitoring_system:
        raise HTTPException(status_code=400, detail="Monitoring is not enabled")

    try:
        metrics = monitoring_system.metrics_collector.get_current_metrics()
        return {"metrics": metrics, "timestamp": time.time()}
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@app.get("/monitoring/metrics/summary", tags=["Monitoring"])
async def get_metrics_summary(
    time_window: int = Query(3600, description="Time window in seconds"),
    _: bool = Depends(verify_api_key),
):
    """
    Get metrics summary for a time window
    """
    if not monitoring_system:
        raise HTTPException(status_code=400, detail="Monitoring is not enabled")

    try:
        summary = monitoring_system.metrics_collector.get_metrics_summary(time_window)
        return {
            "summary": summary,
            "time_window": time_window,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting metrics summary: {str(e)}"
        )


@app.get("/monitoring/alerts", tags=["Monitoring"])
async def get_alerts(_: bool = Depends(verify_api_key)):
    """
    Get active alerts and alert history
    """
    if not monitoring_system:
        raise HTTPException(status_code=400, detail="Monitoring is not enabled")

    try:
        active_alerts = monitoring_system.alert_manager.get_active_alerts()
        alert_history = monitoring_system.alert_manager.get_alert_history(50)
        summary = monitoring_system.alert_manager.get_alerts_summary()

        return {
            "active_alerts": [alert.__dict__ for alert in active_alerts],
            "alert_history": [alert.__dict__ for alert in alert_history],
            "summary": summary,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")


@app.post("/monitoring/alerts/{alert_id}/resolve", tags=["Monitoring"])
async def resolve_alert(alert_id: str, _: bool = Depends(verify_api_key)):
    """
    Resolve an alert
    """
    if not monitoring_system:
        raise HTTPException(status_code=400, detail="Monitoring is not enabled")

    try:
        success = monitoring_system.alert_manager.resolve_alert(alert_id)
        return {
            "success": success,
            "alert_id": alert_id,
            "message": "Alert resolved" if success else "Alert not found",
        }
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")


@app.post("/monitoring/export", tags=["Monitoring"])
async def export_metrics(
    export_request: MetricsExportModel, _: bool = Depends(verify_api_key)
):
    """
    Export metrics to file
    """
    if not monitoring_system:
        raise HTTPException(status_code=400, detail="Monitoring is not enabled")

    try:
        success = monitoring_system.export_metrics(
            export_request.file_path, export_request.format
        )
        return {
            "success": success,
            "file_path": export_request.file_path,
            "message": "Metrics exported" if success else "Failed to export metrics",
        }
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error exporting metrics: {str(e)}"
        )


@app.get("/monitoring/dashboard", tags=["Monitoring"])
async def get_monitoring_dashboard(_: bool = Depends(verify_api_key)):
    """
    Get comprehensive monitoring dashboard data
    """
    if not monitoring_system:
        raise HTTPException(status_code=400, detail="Monitoring is not enabled")

    try:
        dashboard = monitoring_system.get_monitoring_dashboard()
        return dashboard
    except Exception as e:
        logger.error(f"Error getting monitoring dashboard: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting monitoring dashboard: {str(e)}"
        )


# Main entry point for running the API server
def main():
    """Run the API server"""
    # Load configuration
    port = config.get("API_PORT", 8000)
    host = config.get("API_HOST", "127.0.0.1")

    # Initialize scanner
    global scanner
    if config.get("AUTO_START_SCANNER", False):
        if config.get("MULTI_THREADED", False):
            scanner = MultiThreadScanner(config)
        else:
            scanner = SingleThreadScanner(config)

        # Start scanner in background
        scanner.start_monitoring()

    # Auto-start Suricata if configured
    if config.get("SURICATA_AUTO_START", False):
        interface = config.get("SURICATA_INTERFACE", "en0")
        suricata_runner.run_live(interface, 0)

    # Start API server
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
