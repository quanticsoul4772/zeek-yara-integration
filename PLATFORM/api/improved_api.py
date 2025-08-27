"""
Enhanced API Server with Better Error Handling and Validation
Created: 2025
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


# Custom error classes
class APIError(Exception):
    """Base API exception"""

    def __init__(self, message: str, status_code: int = 500, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# Pydantic models with validation
class ScanRequest(BaseModel):
    """Validated scan request model"""

    target: str = Field(..., min_length=1, max_length=4096)
    rules_dir: Optional[str] = Field(None, max_length=4096)
    recursive: bool = Field(True)
    max_file_size: int = Field(104857600, ge=1024, le=1073741824)  # 1KB to 1GB
    threads: int = Field(4, ge=1, le=32)

    @validator("target")
    def validate_target_path(cls, v):
        """Validate target path doesn't contain dangerous patterns"""
        dangerous_patterns = ["..", "~", "${", "$(", "`"]
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError(f"Invalid path: contains '{pattern}'")
        return v

    @validator("rules_dir")
    def validate_rules_dir(cls, v):
        """Validate rules directory path"""
        if v and ".." in v:
            raise ValueError("Invalid rules directory path")
        return v


class AlertQuery(BaseModel):
    """Validated alert query parameters"""

    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    severity: Optional[str] = Field(None, regex="^(low|medium|high|critical)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @validator("end_time")
    def validate_time_range(cls, v, values):
        """Ensure end_time is after start_time"""
        start = values.get("start_time")
        if start and v and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class ScannerControl(BaseModel):
    """Scanner control commands"""

    command: str = Field(..., regex="^(start|stop|restart|status)$")
    directory: Optional[str] = Field(None, max_length=4096)
    threads: int = Field(4, ge=1, le=32)


# Create limiter for rate limiting
limiter = Limiter(key_func=get_remote_address)

# Security
security = HTTPBearer(auto_error=False)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger = logging.getLogger("api")
    logger.info("Starting API server...")

    # Initialize services
    app.state.scanner = None  # Initialize scanner here
    app.state.metrics = {"requests": 0, "errors": 0}

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    if hasattr(app.state, "scanner") and app.state.scanner:
        # Cleanup scanner resources
        pass


# Create FastAPI app with lifespan
app = FastAPI(
    title="Zeek-YARA Integration API",
    description="Enhanced security monitoring platform API",
    version="2.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)

# Add rate limit handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    """Handle custom API errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "message": str(exc),
                "type": "validation_error",
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected errors"""
    logger = logging.getLogger("api")
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "An unexpected error occurred",
                "type": "internal_error",
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


# Dependency for optional authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    """Validate authentication token (optional)"""
    if not credentials:
        return None  # Anonymous access allowed

    # In production, validate the token here
    # For now, just return a mock user
    return {"username": "authenticated_user"}


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check various components
        checks = {
            "api": "healthy",
            "database": "healthy",  # Add actual database check
            "scanner": "healthy" if app.state.scanner else "not_initialized",
        }

        # Overall health
        overall_health = all(v == "healthy" for v in checks.values())

        return {
            "status": "healthy" if overall_health else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": checks,
            "metrics": app.state.metrics,
        }
    except Exception as e:
        raise APIError(
            "Health check failed", status_code=503, details={"error": str(e)}
        )


# Scanner endpoints with validation and error handling
@app.post("/scan", tags=["Scanner"])
@limiter.limit("10/minute")
async def scan_target(
    request: ScanRequest, current_user: Optional[Dict] = Security(get_current_user)
):
    """Scan a file or directory with YARA rules"""
    try:
        # Log the scan request
        logger = logging.getLogger("api")
        logger.info(
            f"Scan request from {current_user or 'anonymous'}: {request.target}"
        )

        # Validate scanner is available
        if not app.state.scanner:
            raise APIError(
                "Scanner not initialized",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Perform scan (mock implementation)
        result = {
            "status": "completed",
            "target": request.target,
            "files_scanned": 10,
            "threats_detected": 0,
            "scan_time": 1.23,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Update metrics
        app.state.metrics["requests"] += 1

        return result

    except APIError:
        raise
    except Exception as e:
        app.state.metrics["errors"] += 1
        logger.error(f"Scan failed: {e}", exc_info=True)
        raise APIError(
            "Scan operation failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)},
        )


@app.get("/alerts", tags=["Alerts"])
@limiter.limit("100/minute")
async def get_alerts(
    query: AlertQuery = Query(),
    current_user: Optional[Dict] = Security(get_current_user),
):
    """Retrieve alerts with advanced filtering"""
    try:
        # Mock alert data
        alerts = [
            {
                "id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "medium",
                "rule_name": f"Rule_{i}",
                "file_path": f"/path/to/file_{i}",
            }
            for i in range(1, min(11, query.limit + 1))
        ]

        return {
            "alerts": alerts,
            "total": 100,
            "page": query.offset // query.limit + 1,
            "page_size": query.limit,
        }

    except Exception as e:
        raise APIError(
            "Failed to retrieve alerts",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)},
        )


@app.post("/scanner/control", tags=["Scanner"])
@limiter.limit("5/minute")
async def control_scanner(
    control: ScannerControl, current_user: Optional[Dict] = Security(get_current_user)
):
    """Control scanner service (start/stop/restart/status)"""
    try:
        if control.command == "status":
            return {
                "status": "running" if app.state.scanner else "stopped",
                "uptime": 3600,
                "files_processed": 1000,
            }

        elif control.command == "start":
            if app.state.scanner:
                raise APIError("Scanner already running", status_code=400)

            # Initialize scanner (mock)
            app.state.scanner = {"started_at": datetime.utcnow()}
            return {"status": "started", "message": "Scanner started successfully"}

        elif control.command == "stop":
            if not app.state.scanner:
                raise APIError("Scanner not running", status_code=400)

            app.state.scanner = None
            return {"status": "stopped", "message": "Scanner stopped successfully"}

        elif control.command == "restart":
            app.state.scanner = None
            await asyncio.sleep(0.1)  # Brief pause
            app.state.scanner = {"started_at": datetime.utcnow()}
            return {"status": "restarted", "message": "Scanner restarted successfully"}

    except APIError:
        raise
    except Exception as e:
        raise APIError(
            f"Scanner control failed: {control.command}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)},
        )


@app.get("/metrics", tags=["System"])
async def get_metrics(current_user: Optional[Dict] = Security(get_current_user)):
    """Get system metrics and statistics"""
    try:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "api_metrics": app.state.metrics,
            "scanner_metrics": {
                "files_scanned": 10000,
                "threats_detected": 50,
                "avg_scan_time": 0.25,
            },
            "system_metrics": {
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "disk_usage": 60.0,
            },
        }
    except Exception as e:
        raise APIError(
            "Failed to retrieve metrics",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)},
        )


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket):
    """WebSocket endpoint for real-time alerts"""
    await websocket.accept()
    try:
        # Send initial connection message
        await websocket.send_json(
            {
                "type": "connection",
                "message": "Connected to alert stream",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Stream alerts (mock implementation)
        while True:
            await asyncio.sleep(5)  # Send alert every 5 seconds
            await websocket.send_json(
                {
                    "type": "alert",
                    "data": {
                        "id": 1,
                        "severity": "medium",
                        "rule_name": "Test_Rule",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
            )

    except Exception as e:
        logger = logging.getLogger("api")
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# Run with: uvicorn improved_api:app --reload --port 8000
