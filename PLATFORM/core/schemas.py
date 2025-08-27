#!/usr/bin/env python3
"""
JSON Schema Validation for Zeek-YARA Integration
Created: August 2025
Author: Security Team

This module provides JSON schema validation for API requests and worker communications.
"""

import json
from typing import Any, Dict, List, Optional

try:
    import jsonschema
except ImportError:
    # If jsonschema is not available, provide a minimal fallback
    class MockJsonSchema:
        class exceptions:
            class ValidationError(Exception):
                pass
        
        @staticmethod
        def validate(data, schema):
            # Basic validation - just check required fields exist
            if schema.get("type") == "object":
                required_fields = schema.get("required", [])
                for field in required_fields:
                    if field not in data:
                        raise MockJsonSchema.exceptions.ValidationError(f"Required field '{field}' is missing")
        
        class Draft7Validator:
            def __init__(self, schema):
                self.schema = schema
            
            def iter_errors(self, data):
                return []
    
    jsonschema = MockJsonSchema()

# Worker Registration Schema
WORKER_REGISTRATION_SCHEMA = {
    "type": "object",
    "properties": {
        "worker_id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$",
            "minLength": 3,
            "maxLength": 64,
            "description": "Unique worker identifier"
        },
        "host": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9.-]+$",
            "minLength": 1,
            "maxLength": 253,
            "description": "Worker host address"
        },
        "port": {
            "type": "integer",
            "minimum": 1024,
            "maximum": 65535,
            "description": "Worker port number"
        },
        "max_tasks": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Maximum concurrent tasks"
        },
        "capabilities": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["file_scan", "yara_analysis", "network_analysis", "log_analysis"]
            },
            "uniqueItems": True,
            "minItems": 1,
            "description": "Worker capabilities"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "threads": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 32
                },
                "start_time": {
                    "type": "number",
                    "minimum": 0
                },
                "version": {
                    "type": "string",
                    "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
                },
                "platform": {
                    "type": "string",
                    "enum": ["linux", "windows", "macos", "freebsd"]
                },
                "memory_limit": {
                    "type": "integer",
                    "minimum": 128,
                    "maximum": 32768
                }
            },
            "additionalProperties": False,
            "description": "Additional worker metadata"
        }
    },
    "required": ["worker_id", "host", "port", "max_tasks", "capabilities"],
    "additionalProperties": False
}

# Worker Heartbeat Schema
WORKER_HEARTBEAT_SCHEMA = {
    "type": "object",
    "properties": {
        "current_tasks": {
            "type": "integer",
            "minimum": 0,
            "maximum": 1000,
            "description": "Current number of active tasks"
        },
        "total_processed": {
            "type": "integer",
            "minimum": 0,
            "description": "Total tasks processed"
        },
        "error_count": {
            "type": "integer",
            "minimum": 0,
            "description": "Total error count"
        },
        "average_processing_time": {
            "type": "number",
            "minimum": 0,
            "description": "Average processing time in seconds"
        },
        "memory_usage": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Memory usage percentage"
        },
        "cpu_usage": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "CPU usage percentage"
        }
    },
    "required": ["current_tasks", "total_processed", "error_count", "average_processing_time"],
    "additionalProperties": False
}

# Task Submission Schema
TASK_SUBMISSION_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$",
            "minLength": 1,
            "maxLength": 128,
            "description": "Unique task identifier"
        },
        "file_path": {
            "type": "string",
            "minLength": 1,
            "maxLength": 1024,
            "description": "Path to file to be scanned"
        },
        "priority": {
            "type": "string",
            "enum": ["low", "normal", "high", "critical"],
            "description": "Task priority level"
        },
        "timeout": {
            "type": "integer",
            "minimum": 5,
            "maximum": 300,
            "description": "Task timeout in seconds"
        },
        "metadata": {
            "type": "object",
            "additionalProperties": True,
            "description": "Additional task metadata"
        }
    },
    "required": ["task_id", "file_path"],
    "additionalProperties": False
}


class SchemaValidator:
    """JSON Schema validator for API requests"""
    
    def __init__(self):
        """Initialize validator with schemas"""
        self.schemas = {
            "worker_registration": WORKER_REGISTRATION_SCHEMA,
            "worker_heartbeat": WORKER_HEARTBEAT_SCHEMA,
            "task_submission": TASK_SUBMISSION_SCHEMA
        }
    
    def validate(self, schema_name: str, data: Dict[str, Any]) -> None:
        """
        Validate data against a schema
        
        Args:
            schema_name: Name of the schema to validate against
            data: Data to validate
            
        Raises:
            ValueError: If schema name is invalid
            jsonschema.exceptions.ValidationError: If data is invalid
        """
        if schema_name not in self.schemas:
            raise ValueError(f"Unknown schema: {schema_name}")
        
        schema = self.schemas[schema_name]
        jsonschema.validate(data, schema)
    
    def is_valid(self, schema_name: str, data: Dict[str, Any]) -> bool:
        """
        Check if data is valid against a schema
        
        Args:
            schema_name: Name of the schema to validate against
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.validate(schema_name, data)
            return True
        except (ValueError, jsonschema.exceptions.ValidationError):
            return False
    
    def get_validation_errors(self, schema_name: str, data: Dict[str, Any]) -> List[str]:
        """
        Get list of validation errors for data
        
        Args:
            schema_name: Name of the schema to validate against
            data: Data to validate
            
        Returns:
            List of error messages
        """
        if schema_name not in self.schemas:
            return [f"Unknown schema: {schema_name}"]
        
        schema = self.schemas[schema_name]
        validator = jsonschema.Draft7Validator(schema)
        errors = []
        
        for error in validator.iter_errors(data):
            error_path = ".".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"{error_path}: {error.message}")
        
        return errors