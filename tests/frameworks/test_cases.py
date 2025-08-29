#!/usr/bin/env python3
"""
Zeek-YARA Integration Test Cases
Created: April 24, 2025
Author: Russell Smith

This module contains predefined test cases for the Zeek-YARA integration testing framework.
"""

import os
import shutil
import sys
import tempfile
import time
from typing import Any, Dict, List

from PLATFORM.config.config import Config
from PLATFORM.core.database import DatabaseManager
from PLATFORM.core.scanner import MultiThreadScanner, SingleThreadScanner
from PLATFORM.utils.file_utils import FileAnalyzer, FileTypeCategories
from PLATFORM.utils.yara_utils import RuleManager, YaraMatcher
from tests.frameworks.test_framework import (
    CustomTestCase,
    CustomTestResult,
    CustomTestRunner,
    CustomTestSuite,
)

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# Unit Tests for File Utilities
class FileUtilsTestCase(CustomTestCase):
    """Tests for file utilities module"""

    def __init__(self):
        super().__init__("file_utils", "unit")
        self.temp_dir = None
        self.temp_files = []

    def setup(self):
        """Set up temporary test files"""
        self.temp_dir = tempfile.mkdtemp()

        # Create test files
        # Text file
        text_file = os.path.join(self.temp_dir, "test.txt")
        with open(text_file, "w") as f:
            f.write("This is a test file.")
        self.temp_files.append(text_file)

        # Empty file
        empty_file = os.path.join(self.temp_dir, "empty.dat")
        with open(empty_file, "w"):
            pass
        self.temp_files.append(empty_file)

        # Binary file
        binary_file = os.path.join(self.temp_dir, "binary.bin")
        with open(binary_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04")
        self.temp_files.append(binary_file)

    def teardown(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def execute(self, result: CustomTestResult):
        """Execute file utilities tests"""
        # Initialize file analyzer
        analyzer = FileAnalyzer(max_file_size=1024 * 1024)

        # Test file detection
        for file_path in self.temp_files:
            mime_type = analyzer.get_mime_type(file_path)
            file_type = analyzer.get_file_type(file_path)

            # Verify file exists
            assert os.path.exists(file_path), f"File does not exist: {file_path}"

            # Verify mime type detection
            assert mime_type, f"No MIME type detected for {file_path}"

            # Verify file type detection
            assert file_type, f"No file type detected for {file_path}"

            # Verify file metadata extraction
            metadata = analyzer.get_file_metadata(file_path)
            assert "path" in metadata, "File path missing from metadata"
            assert "size" in metadata, "File size missing from metadata"
            assert "mime_type" in metadata, "MIME type missing from metadata"

            # Record results
            result.add_metric(f"mime_type_{os.path.basename(file_path)}", mime_type)
            result.add_metric(f"file_type_{os.path.basename(file_path)}", file_type)

        # Test file categorization
        categories = [
            ("application/pdf", "document"),
            ("image/jpeg", "image"),
            ("application/x-executable", "executable"),
            ("application/zip", "archive"),
            ("text/x-python", "script"),
            ("text/plain", "text"),
            ("video/mp4", "video"),
            ("application/octet-stream", "unknown"),
        ]

        for mime_type, expected_category in categories:
            category = FileTypeCategories.categorize_mime(mime_type)
            assert (
                category == expected_category
            ), f"Expected {expected_category} for {mime_type}, got {category}"

            result.add_metric(f"category_{mime_type}", category)

        # Test LRU cache
        # Call repeatedly to test cache
        for _ in range(10):
            for file_path in self.temp_files:
                analyzer.get_mime_type(file_path)
                analyzer.get_file_type(file_path)

        # All tests passed
        result.add_metric("total_tests", len(self.temp_files) + len(categories))


# Unit Tests for YARA Rules
class YaraRulesTestCase(CustomTestCase):
    """Tests for YARA rules management"""

    def __init__(self, rules_dir: str):
        super().__init__("yara_rules", "unit")
        self.rules_dir = rules_dir
        self.temp_dir = None

    def setup(self):
        """Set up temporary test files"""
        self.temp_dir = tempfile.mkdtemp()

        # Create a simple test rule
        rule_content = """
        rule test_rule {
            meta:
                description = "Test rule"
                author = "Test Author"
                severity = 3

            strings:
                $s1 = "EICAR" nocase

            condition:
                any of them
        }
        """

        # Write test rule
        rule_file = os.path.join(self.temp_dir, "test_rule.yar")
        with open(rule_file, "w") as f:
            f.write(rule_content)

        # Create test file
        test_file = os.path.join(self.temp_dir, "test_eicar.txt")
        with open(test_file, "w") as f:
            f.write("This is a test file containing EICAR test string.")

    def teardown(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def execute(self, result: CustomTestResult):
        """Execute YARA rules tests"""
        # Initialize rule manager
        rule_manager = RuleManager(rules_dir=self.rules_dir, rules_index=None)

        # Test rule compilation
        compile_success = rule_manager.compile_rules()
        assert compile_success, "Rule compilation failed"

        # Test rule count
        assert rule_manager.rules is not None, "Rules not compiled"
        result.add_metric("rule_count", len(rule_manager.get_rule_list()))

        # Initialize YARA matcher
        yara_matcher = YaraMatcher(rule_manager=rule_manager)

        # Test scanning
        test_file = os.path.join(self.temp_dir, "test_eicar.txt")
        scan_result = yara_matcher.scan_file(test_file)

        # Validate scan results
        assert "matched" in scan_result, "Scan result missing 'matched' field"
        result.add_metric("scan_matched", scan_result.get("matched", False))

        # If using a custom rule, it should match
        if os.path.exists(os.path.join(self.temp_dir, "test_rule.yar")):
            # Test custom rule manager
            custom_manager = RuleManager(rules_dir=self.temp_dir, rules_index=None)
            custom_manager.compile_rules()

            # Test custom matcher
            custom_matcher = YaraMatcher(rule_manager=custom_manager)
            custom_result = custom_matcher.scan_file(test_file)

            assert custom_result.get("matched", False), "Custom rule did not match"
            result.add_metric("custom_rule_matched", True)

        # All tests passed
        result.add_metric("total_tests", 5)


# Integration Tests for Scanner
class ScannerIntegrationTestCase(CustomTestCase):
    """Integration tests for scanner functionality"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("scanner_integration", "integration")
        self.config = config
        self.temp_dir = None
        self.test_files = []

    def setup(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()

        # Create extract directory
        extract_dir = os.path.join(self.temp_dir, "extracted_files")
        os.makedirs(extract_dir, exist_ok=True)

        # Create logs directory
        logs_dir = os.path.join(self.temp_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # Copy test EICAR file
        eicar_source = os.path.join("tests", "test_eicar.txt")
        if os.path.exists(eicar_source):
            eicar_dest = os.path.join(extract_dir, "test_eicar.txt")
            shutil.copy(eicar_source, eicar_dest)
            self.test_files.append(eicar_dest)

        # Create blank test files
        for i in range(5):
            file_path = os.path.join(extract_dir, f"test_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"Test file {i}\n")
            self.test_files.append(file_path)

        # Update config
        self.config["EXTRACT_DIR"] = extract_dir
        self.config["DB_FILE"] = os.path.join(logs_dir, "test_alerts.db")

    def teardown(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def execute(self, result: CustomTestResult):
        """Execute scanner integration tests"""
        # Initialize scanner
        scanner = SingleThreadScanner(self.config)

        # Test directory scan
        scan_results = scanner.scan_directory()

        # Validate scan results
        assert "scanned" in scan_results, "Scan results missing 'scanned' field"
        assert scan_results["scanned"] >= len(
            self.test_files
        ), "Not all files were scanned"

        # Record metrics
        result.add_metric("files_scanned", scan_results["scanned"])
        result.add_metric("files_matched", scan_results["matched"])
        result.add_metric("scan_duration", scan_results["duration"])

        # Test database
        db_manager = DatabaseManager(db_file=self.config["DB_FILE"])
        alerts = db_manager.get_alerts(limit=100)

        # Record database metrics
        result.add_metric("alert_count", len(alerts))

        # Test EICAR detection
        has_eicar_match = False
        for alert in alerts:
            if "eicar" in alert.get("file_name", "").lower():
                has_eicar_match = True
                break

        if os.path.exists(os.path.join("tests", "test_eicar.txt")):
            assert has_eicar_match, "EICAR test file not detected"

        # All tests passed
        result.add_metric("total_tests", 4)


# Performance Tests for Scanning
class ScannerPerformanceTestCase(CustomTestCase):
    """Performance tests for scanner functionality"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("scanner_performance", "performance")
        self.config = config
        self.temp_dir = None
        self.test_files = []
        self.file_count = 100  # Number of test files to create

    def setup(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()

        # Create extract directory
        extract_dir = os.path.join(self.temp_dir, "extracted_files")
        os.makedirs(extract_dir, exist_ok=True)

        # Create logs directory
        logs_dir = os.path.join(self.temp_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # Create test files
        for i in range(self.file_count):
            file_path = os.path.join(extract_dir, f"test_file_{i}.txt")
            file_size = 1024 * (i % 10 + 1)  # Varying file sizes

            with open(file_path, "w") as f:
                f.write("A" * file_size)

            self.test_files.append(file_path)

        # Update config
        self.config["EXTRACT_DIR"] = extract_dir
        self.config["DB_FILE"] = os.path.join(logs_dir, "test_alerts.db")

    def teardown(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def execute(self, result: CustomTestResult):
        """Execute scanner performance tests"""
        # Configure performance metrics
        metrics = {"single_threaded": {}, "multi_threaded": {}}

        # Test single-threaded scanner
        single_scanner = SingleThreadScanner(self.config)

        start_time = time.time()
        single_results = single_scanner.scan_directory()
        single_duration = time.time() - start_time

        metrics["single_threaded"] = {
            "duration": single_duration,
            "files_per_second": single_results["scanned"] / single_duration,
            "scanned": single_results["scanned"],
        }

        # Test multi-threaded scanner with different thread counts
        for threads in [2, 4, 8]:
            thread_config = self.config.copy()
            thread_config["THREADS"] = threads

            multi_scanner = MultiThreadScanner(thread_config)

            start_time = time.time()
            multi_scanner.start_monitoring()

            # Wait for queue to empty
            while multi_scanner.get_queue_size() > 0:
                time.sleep(0.1)

            # Allow time for processing
            time.sleep(1.0)

            multi_scanner.stop_monitoring()
            multi_duration = time.time() - start_time

            # Get database stats
            db_manager = DatabaseManager(db_file=self.config["DB_FILE"])
            alerts = db_manager.get_alerts(limit=1000)

            metrics[f"multi_threaded_{threads}"] = {
                "duration": multi_duration,
                "files_per_second": self.file_count / multi_duration,
                "threads": threads,
                "alert_count": len(alerts),
            }

            # Clear database for next test
            if os.path.exists(self.config["DB_FILE"]):
                os.remove(self.config["DB_FILE"])

        # Record all metrics
        for category, category_metrics in metrics.items():
            for metric_name, metric_value in category_metrics.items():
                result.add_metric(f"{category}_{metric_name}", metric_value)

        # Calculate improvement ratio
        if "duration" in metrics["single_threaded"] and "multi_threaded_4" in metrics:
            single_duration = metrics["single_threaded"]["duration"]
            multi_duration = metrics["multi_threaded_4"]["duration"]

            if single_duration > 0 and multi_duration > 0:
                speedup = single_duration / multi_duration
                result.add_metric("speedup_ratio_4_threads", speedup)

        # Check if any multi-threaded version is faster
        is_multi_faster = False
        for key in metrics.keys():
            if key.startswith("multi_threaded_") and "duration" in metrics[key]:
                if metrics[key]["duration"] < metrics["single_threaded"]["duration"]:
                    is_multi_faster = True
                    break

        result.add_metric("multi_threaded_faster", is_multi_faster)

        # All tests passed
        result.add_metric("total_tests", 5 + len([2, 4, 8]))


# Database Performance Test
class DatabasePerformanceTestCase(CustomTestCase):
    """Performance tests for database operations"""

    def __init__(self):
        super().__init__("database_performance", "performance")
        self.temp_dir = None
        self.db_file = None
        self.alert_counts = [10, 100, 1000]  # Batch sizes to test

    def setup(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "test_alerts.db")

    def teardown(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def execute(self, result: CustomTestResult):
        """Execute database performance tests"""
        # Initialize database manager
        db_manager = DatabaseManager(db_file=self.db_file)

        # Generate test alerts
        base_alert = {
            "file_path": "/path/to/file.txt",
            "file_name": "file.txt",
            "file_size": 1024,
            "file_type": "text/plain",
            "md5": "abcdef1234567890",
            "sha256": "abcdef1234567890" * 2,
            "zeek_uid": "UID12345",
            "rule_name": "test_rule",
            "rule_namespace": "test",
            "rule_meta": {"description": "Test rule", "severity": 1},
            "strings_matched": ["test_string"],
            "timestamp": time.time(),
        }

        # Test individual inserts
        metrics = {}

        start_time = time.time()
        for i in range(100):
            alert = base_alert.copy()
            alert["file_name"] = f"file_{i}.txt"
            alert["md5"] = f"md5_{i}"
            db_manager.add_alert(alert, {"matched": True, "matches": []})

        single_insert_duration = time.time() - start_time

        metrics["single_insert"] = {
            "duration": single_insert_duration,
            "inserts_per_second": 100 / single_insert_duration,
            "count": 100,
        }

        # Test bulk inserts with different batch sizes
        for count in self.alert_counts:
            # Clear database
            if os.path.exists(self.db_file):
                os.remove(self.db_file)

            # Re-initialize database
            db_manager = DatabaseManager(db_file=self.db_file)

            # Generate batch of alerts
            alerts = []
            for i in range(count):
                alert = base_alert.copy()
                alert["file_name"] = f"bulk_file_{i}.txt"
                alert["md5"] = f"bulk_md5_{i}"
                alerts.append(alert)

            # Measure bulk insert performance
            start_time = time.time()
            inserted = db_manager.bulk_insert_alerts(alerts)
            bulk_duration = time.time() - start_time

            metrics[f"bulk_insert_{count}"] = {
                "duration": bulk_duration,
                "inserts_per_second": inserted / bulk_duration,
                "count": inserted,
            }

            # Test query performance
            query_start = time.time()
            retrieved = db_manager.get_alerts(limit=count * 2)
            query_duration = time.time() - query_start

            metrics[f"query_{count}"] = {
                "duration": query_duration,
                "items_per_second": len(retrieved) / query_duration,
                "count": len(retrieved),
            }

        # Record all metrics
        for category, category_metrics in metrics.items():
            for metric_name, metric_value in category_metrics.items():
                result.add_metric(f"{category}_{metric_name}", metric_value)

        # Calculate bulk insert vs single insert speedup
        if "single_insert" in metrics and "bulk_insert_100" in metrics:
            single_ips = metrics["single_insert"]["inserts_per_second"]
            bulk_ips = metrics["bulk_insert_100"]["inserts_per_second"]

            if single_ips > 0:
                speedup = bulk_ips / single_ips
                result.add_metric("bulk_vs_single_speedup", speedup)

        # All tests passed
        result.add_metric("total_tests", 2 + (len(self.alert_counts) * 2))


# Create test runner with predefined tests
def create_test_suites(config: Dict[str, Any]) -> List[CustomTestSuite]:
    """
    Create test suites with predefined tests.

    Args:
        config (Dict[str, Any]): Application configuration

    Returns:
        List[TestSuite]: Test suites
    """
    suites = []

    # Unit tests suite
    unit_suite = CustomTestSuite("Unit Tests")
    unit_suite.add_test(FileUtilsTestCase())
    unit_suite.add_test(YaraRulesTestCase(rules_dir=config.get("RULES_DIR", "rules")))
    suites.append(unit_suite)

    # Integration tests suite
    integration_suite = CustomTestSuite("Integration Tests")
    integration_suite.add_test(ScannerIntegrationTestCase(config))
    suites.append(integration_suite)

    # Performance tests suite
    performance_suite = CustomTestSuite("Performance Tests")
    performance_suite.add_test(ScannerPerformanceTestCase(config))
    performance_suite.add_test(DatabasePerformanceTestCase())
    suites.append(performance_suite)

    return suites


# Run tests with a configuration
def run_tests_with_config(config: Dict[str, Any]) -> int:
    """
    Run all tests with a specific configuration.

    Args:
        config (Dict[str, Any]): Application configuration

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        runner = CustomTestRunner()

        # Create and add test suites
        for suite in create_test_suites(config):
            runner.add_suite(suite)

        # Run tests
        results = runner.run_all()

        # Return 0 for success, 1 for failure
        return 0 if results["failed"] == 0 else 1

    except Exception as e:
        print(f"Error running tests: {str(e)}")
        return 1


# CLI entry point
if __name__ == "__main__":
    config = Config.load_config()
    sys.exit(run_tests_with_config(config))
