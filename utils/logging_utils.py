#!/usr/bin/env python3
"""
Zeek-YARA Integration Logging Utilities Module
Created: April 24, 2025
Author: Security Team

This module provides enhanced logging capabilities.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """
    Format logs as JSON for easier parsing and integration with log analysis tools.
    """

    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            ]:
                try:
                    # Try to make value JSON serializable
                    json.dumps({key: value})
                    log_data[key] = value
                except (TypeError, OverflowError):
                    # If value can't be serialized, convert to string
                    log_data[key] = str(value)

        return json.dumps(log_data)


def setup_logging(config, logger_name="zeek_yara"):
    """
    Configure logging with file and console handlers.

    Args:
        config (dict): Configuration dictionary containing logging settings
        logger_name (str): Name for the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(logger_name)

    # Determine log level from config
    log_level_name = config.get("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Configure handlers
    handlers = []

    # File handler
    if "LOG_FILE" in config:
        log_file = config["LOG_FILE"]

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Create handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB
        )

        # Check if JSON logging is enabled
        if config.get("LOG_JSON", False):
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(config.get("LOG_FORMAT")))

        handlers.append(file_handler)

    # Console handler
    if config.get("LOG_CONSOLE", True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(config.get("LOG_FORMAT")))
        handlers.append(console_handler)

    # Add all handlers to logger
    for handler in handlers:
        logger.addHandler(handler)

    # Optionally log initialization message
    if not config.get("SUPPRESS_INIT_LOG", False):
        logger.info("Logging initialized")
    return logger


def add_scan_context(logger, file_data=None, scan_result=None):
    """
    Create a child logger with context data for a specific scan.

    Args:
        logger (logging.Logger): Parent logger
        file_data (dict): File metadata
        scan_result (dict): Scan result data

    Returns:
        logging.LoggerAdapter: Logger with contextual data
    """
    context = {}

    # Add file context if provided
    if file_data:
        # Only include essential fields for performance
        for key in ["name", "size", "md5", "zeek_uid"]:
            if key in file_data:
                context[f"file_{key}"] = file_data[key]

    # Add scan result context if provided
    if scan_result:
        if "rule_name" in scan_result:
            context["rule_name"] = scan_result["rule_name"]
        if "matched" in scan_result:
            context["matched"] = scan_result["matched"]

    # Create and return logger adapter with context
    return logging.LoggerAdapter(logger, context)
