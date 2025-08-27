#!/usr/bin/env python3
"""
Suricata API Module for Zeek-YARA Integration
Created: April 25, 2025
Author: Security Team

This module provides API endpoints for Suricata management and alerts.
"""

import logging
import os
from typing import Any, Dict, List, Optional

# Import FastAPI components
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from suricata.alert_correlation import AlertCorrelator
# Import application components
from suricata.suricata_integration import SuricataRunner


# Pydantic models for API
class SuricataAlertModel(BaseModel):
    """Suricata alert data model"""

    id: int
    timestamp: str
    src_ip: str
    src_port: int
    dest_ip: str
    dest_port: int
    proto: str
    signature: str
    category: str
    severity: int
    gid: int
    sid: int
    rev: int
    payload: Dict[str, Any] = {}
    packet_info: Dict[str, Any] = {}


class SuricataAlertsResponse(BaseModel):
    """Response model for Suricata alerts endpoint"""

    alerts: List[SuricataAlertModel]
    count: int
    total: int
    page: int
    page_size: int


class SuricataStatusModel(BaseModel):
    """Suricata status model"""

    running: bool
    pid: Optional[str] = None
    version: str
    alert_count: int
    rules_count: int
    interface: Optional[str] = None


class SuricataRunRequest(BaseModel):
    """Suricata run request model"""

    interface: str = Field(..., description="Network interface to monitor")
    duration: int = Field(0, description="Duration in seconds (0 for continuous)")


class SuricataPcapRequest(BaseModel):
    """Suricata PCAP analysis request model"""

    pcap_file: str = Field(..., description="Path to PCAP file to analyze")


class CorrelatedAlertModel(BaseModel):
    """Correlated alert data model"""

    id: int
    timestamp: str
    correlation_id: str
    alert_type: str
    alert_id: str
    correlation_confidence: int
    correlation_rationale: Optional[str] = None
    correlated_alerts: List[Dict[str, Any]] = []
    threat_intel: Dict[str, Any] = {}
    summary: str


class CorrelatedAlertsResponse(BaseModel):
    """Response model for correlated alerts endpoint"""

    alerts: List[CorrelatedAlertModel]
    count: int
    total: int
    page: int
    page_size: int


class CorrelateAlertsRequest(BaseModel):
    """Correlate alerts request model"""

    time_window: int = Field(300, description="Time window in seconds for correlation")


# Define Suricata API router
suricata_router = APIRouter(
    prefix="/suricata",
    tags=["Suricata"],
    responses={404: {"description": "Not found"}},
)


# Dependency for Suricata runner
def get_suricata_runner(config):
    """Get Suricata runner instance"""
    return SuricataRunner(config)


# Dependency for Alert correlator
def get_alert_correlator(config):
    """Get Alert correlator instance"""
    return AlertCorrelator(config)


# API Endpoints
@suricata_router.get("/status", response_model=SuricataStatusModel)
async def get_suricata_status(suricata_runner=Depends(get_suricata_runner)):
    """
    Get Suricata status information
    """
    try:
        status = suricata_runner.get_status()

        # Add interface information if running
        if status.get("running", False):
            status["interface"] = suricata_runner.config.get(
                "SURICATA_INTERFACE", "unknown"
            )

        return status

    except Exception as e:
        logging.error(f"Error getting Suricata status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting Suricata status: {str(e)}"
        )


@suricata_router.post("/start")
async def start_suricata(
    request: SuricataRunRequest,
    background_tasks: BackgroundTasks,
    suricata_runner=Depends(get_suricata_runner),
):
    """
    Start Suricata monitoring on a network interface
    """
    try:
        # Store current interface in config
        suricata_runner.config["SURICATA_INTERFACE"] = request.interface

        # Start in background task if continuous
        if request.duration == 0:
            background_tasks.add_task(suricata_runner.run_live, request.interface, 0)

            return {
                "success": True,
                "message": f"Started Suricata on interface {request.interface} in background mode",
                "interface": request.interface,
            }
        else:
            # Run for specific duration
            success = suricata_runner.run_live(request.interface, request.duration)

            if success:
                return {
                    "success": True,
                    "message": f"Completed Suricata monitoring on interface {request.interface} for {request.duration} seconds",
                    "interface": request.interface,
                }
            else:
                raise HTTPException(status_code=500, detail="Error starting Suricata")

    except Exception as e:
        logging.error(f"Error starting Suricata: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error starting Suricata: {str(e)}"
        )


@suricata_router.post("/stop")
async def stop_suricata(suricata_runner=Depends(get_suricata_runner)):
    """
    Stop Suricata if running
    """
    try:
        success = suricata_runner.stop()

        if success:
            return {"success": True, "message": "Suricata stopped successfully"}
        else:
            return {
                "success": False,
                "message": "Failed to stop Suricata, or Suricata was not running",
            }

    except Exception as e:
        logging.error(f"Error stopping Suricata: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error stopping Suricata: {str(e)}"
        )


@suricata_router.post("/pcap")
async def analyze_pcap(
    request: SuricataPcapRequest, suricata_runner=Depends(get_suricata_runner)
):
    """
    Analyze a PCAP file with Suricata
    """
    try:
        # Validate PCAP file path
        pcap_file = request.pcap_file
        if not os.path.exists(pcap_file):
            raise HTTPException(
                status_code=404, detail=f"PCAP file not found: {pcap_file}"
            )

        # Run analysis
        success = suricata_runner.run_pcap(pcap_file)

        if success:
            return {
                "success": True,
                "message": f"PCAP file {pcap_file} analyzed successfully",
                "file": pcap_file,
            }
        else:
            raise HTTPException(status_code=500, detail="Error analyzing PCAP file")

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error analyzing PCAP: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing PCAP: {str(e)}")


@suricata_router.get("/alerts", response_model=SuricataAlertsResponse)
async def get_suricata_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    severity: Optional[int] = Query(
        None, ge=0, le=10, description="Filter by severity"
    ),
    signature: Optional[str] = Query(None, description="Filter by signature"),
    src_ip: Optional[str] = Query(None, description="Filter by source IP"),
    dest_ip: Optional[str] = Query(None, description="Filter by destination IP"),
    start_date: Optional[str] = Query(
        None, description="Filter by start date (ISO format)"
    ),
    end_date: Optional[str] = Query(
        None, description="Filter by end date (ISO format)"
    ),
    suricata_runner=Depends(get_suricata_runner),
):
    """
    Get paginated Suricata alerts with optional filtering
    """
    try:
        # Calculate offset and limit
        offset = (page - 1) * page_size
        limit = page_size

        # Prepare filters
        filters = {}
        if severity is not None:
            filters["severity"] = severity
        if signature:
            filters["signature"] = signature
        if src_ip:
            filters["src_ip"] = src_ip
        if dest_ip:
            filters["dest_ip"] = dest_ip
        if start_date:
            filters["timestamp"] = (
                start_date  # This is a simplification, actual implementation might need more logic
            )

        # Get alerts
        alerts = suricata_runner.get_alerts(filters, limit, offset)

        # Count total alerts for pagination
        total_alerts = len(suricata_runner.get_alerts(filters))

        # Convert to API models
        alert_models = []
        for alert in alerts:
            alert_models.append(
                SuricataAlertModel(
                    id=alert.get("id", 0),
                    timestamp=alert.get("timestamp", ""),
                    src_ip=alert.get("src_ip", ""),
                    src_port=alert.get("src_port", 0),
                    dest_ip=alert.get("dest_ip", ""),
                    dest_port=alert.get("dest_port", 0),
                    proto=alert.get("proto", ""),
                    signature=alert.get("signature", ""),
                    category=alert.get("category", ""),
                    severity=alert.get("severity", 0),
                    gid=alert.get("gid", 0),
                    sid=alert.get("sid", 0),
                    rev=alert.get("rev", 0),
                    payload=alert.get("payload", {}),
                    packet_info=alert.get("packet_info", {}),
                )
            )

        # Return response
        return SuricataAlertsResponse(
            alerts=alert_models,
            count=len(alert_models),
            total=total_alerts,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logging.error(f"Error retrieving Suricata alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving Suricata alerts: {
                str(e)}",
        )


@suricata_router.post("/rules/update")
async def update_suricata_rules(suricata_runner=Depends(get_suricata_runner)):
    """
    Update Suricata rules
    """
    try:
        success = suricata_runner.update_rules()

        if success:
            return {"success": True, "message": "Suricata rules updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Error updating Suricata rules")

    except Exception as e:
        logging.error(f"Error updating Suricata rules: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error updating Suricata rules: {str(e)}"
        )


@suricata_router.post("/correlate", response_model=CorrelatedAlertsResponse)
async def correlate_alerts(
    request: CorrelateAlertsRequest,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    alert_correlator=Depends(get_alert_correlator),
):
    """
    Correlate alerts from different sources (Suricata, YARA, Zeek)
    """
    try:
        # Perform correlation
        alert_correlator.correlate_alerts(request.time_window)

        # Calculate offset and limit
        offset = (page - 1) * page_size
        limit = page_size

        # Get correlated alerts
        correlated_alerts = alert_correlator.get_correlated_alerts(
            filters=None, limit=limit, offset=offset
        )

        # Count total alerts for pagination
        total_alerts = len(alert_correlator.get_correlated_alerts())

        # Convert to API models
        alert_models = []
        for alert in correlated_alerts:
            alert_models.append(
                CorrelatedAlertModel(
                    id=alert.get("id", 0),
                    timestamp=alert.get("timestamp", ""),
                    correlation_id=alert.get("correlation_id", ""),
                    alert_type=alert.get("alert_type", ""),
                    alert_id=alert.get("alert_id", ""),
                    correlation_confidence=alert.get("correlation_confidence", 0),
                    correlation_rationale=alert.get("correlation_rationale", ""),
                    correlated_alerts=alert.get("correlated_alerts", []),
                    threat_intel=alert.get("threat_intel", {}),
                    summary=alert.get("summary", ""),
                )
            )

        # Return response
        return CorrelatedAlertsResponse(
            alerts=alert_models,
            count=len(alert_models),
            total=total_alerts,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logging.error(f"Error correlating alerts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error correlating alerts: {str(e)}"
        )


@suricata_router.get("/correlation", response_model=CorrelatedAlertsResponse)
async def get_correlated_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    confidence: Optional[int] = Query(
        None, ge=0, le=100, description="Filter by confidence level"
    ),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    alert_correlator=Depends(get_alert_correlator),
):
    """
    Get paginated correlated alerts with optional filtering
    """
    try:
        # Calculate offset and limit
        offset = (page - 1) * page_size
        limit = page_size

        # Prepare filters
        filters = {}
        if confidence is not None:
            filters["correlation_confidence"] = confidence
        if alert_type:
            filters["alert_type"] = alert_type

        # Get correlated alerts
        correlated_alerts = alert_correlator.get_correlated_alerts(
            filters=filters, limit=limit, offset=offset
        )

        # Count total alerts for pagination
        total_alerts = len(alert_correlator.get_correlated_alerts(filters=filters))

        # Convert to API models
        alert_models = []
        for alert in correlated_alerts:
            alert_models.append(
                CorrelatedAlertModel(
                    id=alert.get("id", 0),
                    timestamp=alert.get("timestamp", ""),
                    correlation_id=alert.get("correlation_id", ""),
                    alert_type=alert.get("alert_type", ""),
                    alert_id=alert.get("alert_id", ""),
                    correlation_confidence=alert.get("correlation_confidence", 0),
                    correlation_rationale=alert.get("correlation_rationale", ""),
                    correlated_alerts=alert.get("correlated_alerts", []),
                    threat_intel=alert.get("threat_intel", {}),
                    summary=alert.get("summary", ""),
                )
            )

        # Return response
        return CorrelatedAlertsResponse(
            alerts=alert_models,
            count=len(alert_models),
            total=total_alerts,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logging.error(f"Error retrieving correlated alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving correlated alerts: {
                str(e)}",
        )
