#!/usr/bin/env python3
"""
Test Worker Registration Security
Created: August 2025
Author: Security Team

This module tests the security enhancements for worker registration.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PLATFORM.core.schemas import SchemaValidator


class TestWorkerRegistrationSecurity(unittest.TestCase):
    """Test security features for worker registration"""

    def setUp(self):
        """Set up test environment"""
        self.schema_validator = SchemaValidator()

    def test_valid_worker_registration(self):
        """Test valid worker registration data"""
        valid_data = {
            "worker_id": "test-worker-01",
            "host": "localhost",
            "port": 8001,
            "max_tasks": 5,
            "capabilities": ["file_scan", "yara_analysis"],
            "metadata": {
                "threads": 2,
                "start_time": 1234567890.0,
                "version": "1.0.0",
                "platform": "linux",
            },
        }

        # Should not raise an exception
        self.schema_validator.validate("worker_registration", valid_data)
        self.assertTrue(
            self.schema_validator.is_valid("worker_registration", valid_data)
        )

    def test_invalid_worker_id(self):
        """Test invalid worker ID validation"""
        invalid_data = {
            "worker_id": "a",  # Too short
            "host": "localhost",
            "port": 8001,
            "max_tasks": 5,
            "capabilities": ["file_scan"],
        }

        self.assertFalse(
            self.schema_validator.is_valid("worker_registration", invalid_data)
        )
        errors = self.schema_validator.get_validation_errors(
            "worker_registration", invalid_data
        )
        self.assertTrue(len(errors) > 0)

    def test_invalid_capabilities(self):
        """Test invalid capabilities validation"""
        invalid_data = {
            "worker_id": "test-worker-01",
            "host": "localhost",
            "port": 8001,
            "max_tasks": 5,
            "capabilities": ["file_scan", "malicious_capability"],  # Invalid capability
        }

        self.assertFalse(
            self.schema_validator.is_valid("worker_registration", invalid_data)
        )

    def test_invalid_port_range(self):
        """Test invalid port range validation"""
        invalid_data = {
            "worker_id": "test-worker-01",
            "host": "localhost",
            "port": 80,  # Below minimum
            "max_tasks": 5,
            "capabilities": ["file_scan"],
        }

        self.assertFalse(
            self.schema_validator.is_valid("worker_registration", invalid_data)
        )

    def test_missing_required_fields(self):
        """Test missing required fields validation"""
        invalid_data = {
            "worker_id": "test-worker-01",
            "host": "localhost",
            # Missing port, max_tasks, capabilities
        }

        self.assertFalse(
            self.schema_validator.is_valid("worker_registration", invalid_data)
        )
        errors = self.schema_validator.get_validation_errors(
            "worker_registration", invalid_data
        )
        self.assertTrue(len(errors) > 0)

    def test_heartbeat_validation(self):
        """Test worker heartbeat data validation"""
        valid_heartbeat = {
            "current_tasks": 2,
            "total_processed": 150,
            "error_count": 1,
            "average_processing_time": 2.5,
            "memory_usage": 45.2,
            "cpu_usage": 30.1,
        }

        self.assertTrue(
            self.schema_validator.is_valid("worker_heartbeat", valid_heartbeat)
        )

        # Test invalid heartbeat
        invalid_heartbeat = {
            "current_tasks": -1,  # Invalid negative value
            "total_processed": 150,
            "error_count": 1,
            "average_processing_time": 2.5,
        }

        self.assertFalse(
            self.schema_validator.is_valid("worker_heartbeat", invalid_heartbeat)
        )


if __name__ == "__main__":
    unittest.main()
