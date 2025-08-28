#!/usr/bin/env python3
"""
Alert Correlation Module for Zeek-YARA-Suricata Integration
Created: April 25, 2025
Author: Security Team

This module correlates alerts from different security tools (Zeek, YARA, Suricata)
to provide comprehensive threat detection.
"""

# Import the orchestrator implementation as the main AlertCorrelator
from .alert_correlation.orchestrator import AlertCorrelator

# Re-export for backward compatibility
__all__ = ["AlertCorrelator"]
