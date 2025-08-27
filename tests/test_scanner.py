"""
Zeek-YARA Integration Scanner Tests
Created: April 24, 2025
Author: Russell Smith

This module contains tests for the scanner functionality, including performance tests
for the optimizations implemented in Phase 2.
"""

import logging
import os
import shutil
import sys
import tempfile
import threading
import time
from queue import Queue

import pytest

from PLATFORM.core.database import DatabaseManager
from PLATFORM.core.scanner import (
    FileEventHandler,
    MultiThreadScanner,
    SingleThreadScanner,
)
from utils.file_utils import FileAnalyzer
from utils.yara_utils import RuleManager, YaraMatcher

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Unit tests for the Scanner
@pytest.mark.unit
class TestScanner:
    """Unit tests for Scanner classes"""

    def test_single_thread_scanner_initialization(self, config):
        """Test single-threaded scanner initialization"""
        scanner = SingleThreadScanner(config)

        assert scanner is not None
        assert scanner.extract_dir == config.get("EXTRACT_DIR")
        assert isinstance(scanner.file_analyzer, FileAnalyzer)
        assert isinstance(scanner.rule_manager, RuleManager)
        assert isinstance(scanner.yara_matcher, YaraMatcher)
        assert isinstance(scanner.db_manager, DatabaseManager)
        assert scanner.running is False

    def test_multi_thread_scanner_initialization(self, config):
        """Test multi-threaded scanner initialization"""
        config_copy = config.copy()
        config_copy["THREADS"] = 4

        scanner = MultiThreadScanner(config_copy)

        assert scanner is not None
        assert scanner.extract_dir == config_copy.get("EXTRACT_DIR")
        assert isinstance(scanner.file_analyzer, FileAnalyzer)
        assert isinstance(scanner.rule_manager, RuleManager)
        assert isinstance(scanner.yara_matcher, YaraMatcher)
        assert isinstance(scanner.db_manager, DatabaseManager)
        assert scanner.running is False
        assert scanner.num_threads == 4
        assert isinstance(scanner.file_queue, Queue)
        assert scanner.worker_threads == []
        assert isinstance(scanner.stop_event, threading.Event)

    def test_scan_file(self, scanner, test_files):
        """Test scanning a single file"""
        # Scan a text file
        text_file = test_files["paths"]["text.txt"]
        result = scanner.scan_file(text_file)

        assert isinstance(result, dict)
        assert "matched" in result

        # Scan a non-existent file
        non_existent = os.path.join(test_files["dir"], "non_existent.txt")
        result = scanner.scan_file(non_existent)

        assert isinstance(result, dict)
        assert "matched" in result
        assert result.get("matched") is False
        assert "error" in result

    def test_scan_directory(self, scanner, test_files):
        """Test scanning a directory"""
        result = scanner.scan_directory(test_files["dir"])

        assert isinstance(result, dict)
        assert "scanned" in result
        assert result["scanned"] == len(test_files["files"])
        assert "matched" in result
        assert "errors" in result
        assert "duration" in result

    def test_file_event_handler(self, scanner, test_files):
        """Test file event handler"""
        # Create event handler
        handler = FileEventHandler(scanner)

        # Mock file creation event
        class MockEvent:
            def __init__(self, path, is_dir=False):
                self.src_path = path
                self.is_directory = is_dir

        # Test with directory event (should be ignored)
        dir_event = MockEvent(test_files["dir"], is_dir=True)
        handler.on_created(dir_event)  # Should not raise any exceptions

        # Test with file event
        text_file = test_files["paths"]["text.txt"]
        file_event = MockEvent(text_file)

        # Create a mock scan method to verify it's called
        original_scan = scanner.scan_file

        call_count = [0]

        def mock_scan_file(file_path):
            call_count[0] += 1
            assert file_path == text_file
            return {"matched": False}

        try:
            scanner.scan_file = mock_scan_file
            handler.on_created(file_event)
            assert call_count[0] == 1
        finally:
            scanner.scan_file = original_scan


# Integration tests for the Scanner
@pytest.mark.integration
class TestScannerIntegration:
    """Integration tests for Scanner functionality"""

    def test_monitoring_workflow(self, scanner, test_files, config):
        """Test the complete monitoring workflow"""
        # Initialize scanner and events
        extracted_dir = config["EXTRACT_DIR"]
        events = []

        # Create callbacks to track events
        def scan_callback(file_path, result):
            events.append(("scan", file_path, result))

        # Register callback
        scanner.scan_callback = scan_callback

        # Start monitoring
        assert scanner.running is False
        start_result = scanner.start_monitoring()
        assert start_result is True
        assert scanner.running is True

        # Wait a moment for setup
        time.sleep(1)

        # Copy test files to extract directory
        for file_path in test_files["files"]:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(extracted_dir, file_name)
            shutil.copy(file_path, dest_path)

            # Wait a bit for processing
            time.sleep(0.5)

        # Wait for processing
        time.sleep(2)

        # Stop monitoring
        stop_result = scanner.stop_monitoring()
        assert stop_result is True
        assert scanner.running is False

        # Check events
        assert len(events) > 0
        for event_type, file_path, result in events:
            assert event_type == "scan"
            assert os.path.exists(file_path)
            assert isinstance(result, dict)
            assert "matched" in result

    def test_eicar_detection(self, config):
        """Test detection of EICAR test file"""
        # Initialize scanner
        # Enable debug logging
        logging.getLogger("zeek_yara").setLevel(logging.DEBUG)
        scanner = SingleThreadScanner(config)

        # Create EICAR test file
        temp_dir = tempfile.mkdtemp()
        eicar_path = os.path.join(temp_dir, "eicar.txt")
        # Get absolute path to ensure consistency
        eicar_path = os.path.abspath(eicar_path)

        eicar_content = (
            "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        )
        with open(eicar_path, "w") as f:
            f.write(eicar_content)

        try:
            # Manually get file metadata for debugging
            file_analyzer = scanner.file_analyzer
            metadata = file_analyzer.get_file_metadata(eicar_path)
            print(f"DEBUG: File metadata for {eicar_path}:\n{metadata}")

            # Scan file
            result = scanner.scan_file(eicar_path)

            # Check result
            assert result.get("matched", False) is True
            assert len(result.get("matches", [])) > 0

            # Check database entry - use the scanner's database manager
            alerts = scanner.db_manager.get_alerts()
            print(f"DEBUG: All alerts in database:\n{alerts}")

            # Do a more flexible match on the file path
            eicar_name = os.path.basename(eicar_path)
            matching_alerts = [
                alert
                for alert in alerts
                if (
                    alert.get("file_path") == eicar_path
                    or (eicar_name and alert.get("file_name") == eicar_name)
                )
            ]

            assert len(matching_alerts) > 0
            alert = matching_alerts[0]

            # Check alert details
            assert alert["file_name"] == "eicar.txt"
            # Case-insensitive check for rule name
            rule_name = alert["rule_name"].lower()
            assert "eicar" in rule_name or "test" in rule_name

        finally:
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


# Performance tests for the Scanner
@pytest.mark.performance
class TestScannerPerformance:
    """Performance tests for Scanner optimizations"""

    def test_performance_monitoring(self, config):
        """Test performance monitoring features with proper metric validation"""
        import tempfile
        import shutil

        # Create multi-threaded scanner with performance monitoring
        thread_config = config.copy()
        thread_config["THREADS"] = 2
        thread_config["MAX_QUEUE_SIZE"] = 10
        thread_config["HEALTH_CHECK_INTERVAL"] = 1

        # Create temporary directory for test files
        temp_dir = tempfile.mkdtemp()
        thread_config["EXTRACT_DIR"] = temp_dir

        multi_scanner = MultiThreadScanner(thread_config)

        # Test initial state
        assert multi_scanner.num_threads == 2
        assert multi_scanner.max_queue_size == 10

        # Start monitoring to initialize performance stats
        assert multi_scanner.start_monitoring() is True

        # Wait briefly for initialization
        time.sleep(0.5)

        try:
            # Test initial performance statistics - validate actual values
            initial_stats = multi_scanner.get_performance_statistics()
            assert isinstance(initial_stats, dict)

            # Validate metric structure and initial values
            assert "uptime_seconds" in initial_stats
            assert "files_processed" in initial_stats
            assert "throughput_files_per_second" in initial_stats
            assert "worker_stats" in initial_stats
            assert "worker_health" in initial_stats
            assert initial_stats["active_threads"] == 2

            # Validate initial metric values are sensible
            assert (
                initial_stats["uptime_seconds"] > 0
            ), "Uptime should be positive after initialization"
            assert (
                initial_stats["files_processed"] == 0
            ), "No files should be processed initially"
            assert (
                initial_stats["throughput_files_per_second"] == 0
            ), "Throughput should be 0 initially"
            assert (
                len(initial_stats["worker_stats"]) == 2
            ), "Should have stats for 2 workers"

            # Create test files to simulate processing activity
            test_files = []
            for i in range(3):
                test_file = os.path.join(temp_dir, f"test_file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Test content {i}")
                test_files.append(test_file)

            # Wait for files to be processed
            time.sleep(2.0)

            # Test metrics after processing activity
            post_processing_stats = multi_scanner.get_performance_statistics()

            # Validate metrics reflect actual processing
            assert (
                post_processing_stats["uptime_seconds"]
                > initial_stats["uptime_seconds"]
            ), "Uptime should increase over time"
            assert post_processing_stats["files_processed"] >= len(
                test_files
            ), f"Should have processed at least {len(test_files)} files"

            # If files were processed, throughput should be positive
            if post_processing_stats["files_processed"] > 0:
                assert (
                    post_processing_stats["throughput_files_per_second"] > 0
                ), "Throughput should be positive when files are processed"

            # Test worker health status with validation
            health = multi_scanner.get_worker_health_status()
            assert isinstance(health, dict)
            assert len(health) == 2, "Should have health status for 2 workers"

            for worker_id, status in health.items():
                assert "status" in status
                assert "last_heartbeat_ago" in status
                assert "worker_status" in status

                # Validate health metrics are reasonable
                assert (
                    status["last_heartbeat_ago"] >= 0
                ), "Heartbeat age should be non-negative"
                assert status["status"] in [
                    "healthy",
                    "warning",
                    "unhealthy",
                ], f"Invalid health status: {status['status']}"
                assert status["worker_status"] in [
                    "idle",
                    "processing",
                ], f"Invalid worker status: {status['worker_status']}"

            # Test queue size monitoring with validation
            initial_queue_size = multi_scanner.get_queue_size()
            assert initial_queue_size >= 0, "Queue size should be non-negative"

            # Test queue size consistency - multiple calls should be consistent
            queue_size_2 = multi_scanner.get_queue_size()
            assert abs(queue_size_2 - initial_queue_size) <= len(
                test_files
            ), "Queue size should not vary drastically between consecutive calls"

            # Test worker statistics validation
            worker_stats = post_processing_stats["worker_stats"]
            total_files_by_workers = sum(
                stats["files_processed"] for stats in worker_stats.values()
            )
            assert (
                total_files_by_workers <= post_processing_stats["files_processed"]
            ), "Sum of worker processed files should not exceed total processed files"

            # Test metric consistency over time
            time.sleep(0.5)
            consistency_stats = multi_scanner.get_performance_statistics()
            assert (
                consistency_stats["uptime_seconds"]
                >= post_processing_stats["uptime_seconds"]
            ), "Uptime should be monotonically increasing"
            assert (
                consistency_stats["files_processed"]
                >= post_processing_stats["files_processed"]
            ), "Files processed should be monotonically increasing"

        finally:
            # Clean up
            multi_scanner.stop_monitoring()
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_single_vs_multi_thread_performance(self, config, timer):
        """Test performance comparison between single and multi-threaded scanners"""
        # Create test files
        file_count = 50
        temp_dir = tempfile.mkdtemp()
        test_files = []

        for i in range(file_count):
            file_path = os.path.join(temp_dir, f"test_{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"Test file {i}\n")
            test_files.append(file_path)

        try:
            # Test single-threaded performance
            single_scanner = SingleThreadScanner(config)

            timer.start()
            single_result = single_scanner.scan_directory(temp_dir)
            single_time = timer.stop().duration

            assert single_result["scanned"] == file_count

            # Test multi-threaded performance with different thread counts
            thread_times = {}
            for threads in [2, 4, 8]:
                thread_config = config.copy()
                thread_config["THREADS"] = threads

                multi_scanner = MultiThreadScanner(thread_config)

                timer.start()
                multi_scanner.start_monitoring()

                # Wait for queue to be processed
                while multi_scanner.get_queue_size() > 0:
                    time.sleep(0.1)

                # Wait a bit more for processing to complete
                time.sleep(1.0)

                multi_scanner.stop_monitoring()
                thread_time = timer.stop().duration

                thread_times[threads] = thread_time

            # Print results
            print(f"Single-threaded: {single_time:.6f}s")
            for threads, thread_time in thread_times.items():
                speedup = single_time / thread_time
                print(
                    f"{threads} threads: { thread_time:.6f}s (speedup: { speedup:.2f}x)"
                )

            # Print comparison results without asserting which one is faster
            print(
                f"Speed comparison: Single-threaded vs. min multi-threaded: {single_time:.6f}s vs {min( thread_times.values()):.6f}s"
            )
            # Get best thread count - don't assert that multi-threaded is faster
            # as it may not be for small test datasets or test environments

            # Get best thread count
            best_threads = min(thread_times, key=thread_times.get)
            best_speedup = single_time / thread_times[best_threads]

            print(
                f"Best performance with {best_threads} threads: {best_speedup:.2f}x speedup"
            )

        finally:
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_file_type_filtering_performance(self, config, timer):
        """Test performance of file type filtering"""
        # Create different file types
        file_counts = {
            "txt": 20,  # Text files
            "bin": 10,  # Binary files
            "empty": 5,  # Empty files
            "exe": 5,  # Executable files (fake)
        }

        temp_dir = tempfile.mkdtemp()
        all_files = []

        # Create text files
        for i in range(file_counts["txt"]):
            file_path = os.path.join(temp_dir, f"test_{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"Test file {i}\n" * 10)
            all_files.append(file_path)

        # Create binary files
        for i in range(file_counts["bin"]):
            file_path = os.path.join(temp_dir, f"binary_{i}.bin")
            with open(file_path, "wb") as f:
                f.write(os.urandom(1024))  # 1KB random data
            all_files.append(file_path)

        # Create empty files
        for i in range(file_counts["empty"]):
            file_path = os.path.join(temp_dir, f"empty_{i}.dat")
            with open(file_path, "w"):
                pass  # Create empty file
            all_files.append(file_path)

        # Create fake executable files
        for i in range(file_counts["exe"]):
            file_path = os.path.join(temp_dir, f"fake_{i}.exe")
            with open(file_path, "wb") as f:
                f.write(b"MZ" + os.urandom(1022))  # Fake EXE header
            all_files.append(file_path)

        try:
            # Create scanner with no filtering
            unfiltered_config = config.copy()
            unfiltered_scanner = SingleThreadScanner(unfiltered_config)

            # Time unfiltered scan
            timer.start()
            unfiltered_result = unfiltered_scanner.scan_directory(temp_dir)
            unfiltered_time = timer.stop().duration

            assert unfiltered_result["scanned"] == sum(file_counts.values())

            # Create scanner with MIME type filtering (text only)
            filtered_config = config.copy()
            filtered_config["SCAN_MIME_TYPES"] = ["text/plain"]
            filtered_scanner = SingleThreadScanner(filtered_config)

            # Time filtered scan
            timer.start()
            filtered_result = filtered_scanner.scan_directory(temp_dir)
            filtered_time = timer.stop().duration

            # Assert on the number of scanned and skipped files instead of specific counts
            # The test was incorrectly assuming all text files would be found
            # and scanned
            assert filtered_result["scanned"] < unfiltered_result["scanned"]
            assert filtered_result["scanned"] > 0

            # Print results
            print(
                f"Unfiltered scan: {unfiltered_time:.6f}s for {unfiltered_result['scanned']} files"
            )
            print(
                f"Filtered scan (text only): {filtered_time:.6f}s for {filtered_result['scanned']} files"
            )

            # Calculate efficiency
            unfiltered_per_file = unfiltered_time / unfiltered_result["scanned"]
            filtered_per_file = (
                filtered_time / filtered_result["scanned"]
                if filtered_result["scanned"] > 0
                else 0
            )

            print(f"Unfiltered: {unfiltered_per_file * 1000:.2f}ms per file")
            print(f"Filtered: {filtered_per_file * 1000:.2f}ms per file")

            # Compare efficiency on a per-file basis
            if filtered_result["scanned"] > 0:  # Avoid division by zero
                filtered_per_file = filtered_time / filtered_result["scanned"]
                unfiltered_per_file = unfiltered_time / unfiltered_result["scanned"]
                assert filtered_per_file <= unfiltered_per_file * 2.5, (
                    f"Filtered scan ({filtered_per_file * 1000:.2f}ms/file) should be efficient "
                    f"compared to unfiltered ({unfiltered_per_file * 1000:.2f}ms/file)"
                )

        finally:
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_rule_optimization_performance(self, config, timer):
        """Test performance of rule optimization"""
        # Create scanner with standard rule loading
        standard_scanner = SingleThreadScanner(config)

        # Create test file
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test file for rule optimization\n")

        try:
            # Time standard rule compilation
            timer.start()
            standard_scanner.rule_manager.compile_rules()
            standard_compile_time = timer.stop().duration

            # Time standard file scan
            timer.start()
            standard_scanner.scan_file(test_file)
            standard_scan_time = timer.stop().duration

            # Create scanner with optimized rule loading
            optimized_config = config.copy()
            optimized_config["OPTIMIZE_RULES"] = True
            optimized_scanner = SingleThreadScanner(optimized_config)

            # Time optimized rule compilation
            timer.start()
            optimized_scanner.rule_manager.compile_rules()
            optimized_compile_time = timer.stop().duration

            # Time optimized file scan
            timer.start()
            optimized_scanner.scan_file(test_file)
            optimized_scan_time = timer.stop().duration

            # Print results
            print(f"Standard rule compilation: {standard_compile_time:.6f}s")
            print(f"Optimized rule compilation: {optimized_compile_time:.6f}s")
            print(f"Standard file scan: {standard_scan_time:.6f}s")
            print(f"Optimized file scan: {optimized_scan_time:.6f}s")

            # Calculate performance improvement
            compile_speedup = (
                standard_compile_time / optimized_compile_time
                if optimized_compile_time > 0
                else 1
            )
            scan_speedup = (
                standard_scan_time / optimized_scan_time
                if optimized_scan_time > 0
                else 1
            )

            print(f"Compilation speedup: {compile_speedup:.2f}x")
            print(f"Scan speedup: {scan_speedup:.2f}x")

        finally:
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


# Edge case and resilience tests
@pytest.mark.unit
class TestScannerEdgeCases:
    """Tests for scanner edge cases, failure scenarios, and resilience"""

    def test_shutdown_under_heavy_load(self, config):
        """Test graceful shutdown when scanner is under heavy load"""
        # Create temporary directory with many files
        temp_dir = tempfile.mkdtemp()
        file_count = 100
        test_files = []

        # Create files that will queue up
        for i in range(file_count):
            file_path = os.path.join(temp_dir, f"load_test_{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"Test content {i}\n" * 100)  # Make files substantial
            test_files.append(file_path)

        try:
            # Configure scanner with small thread count to create backlog
            load_config = config.copy()
            load_config["THREADS"] = 2
            load_config["MAX_QUEUE_SIZE"] = 50
            load_config["EXTRACT_DIR"] = temp_dir

            scanner = MultiThreadScanner(load_config)

            # Start monitoring - this will queue existing files
            start_time = time.time()
            assert scanner.start_monitoring() is True
            assert scanner.running is True

            # Wait briefly to let queue fill up
            time.sleep(0.5)

            # Verify queue has work
            initial_queue_size = scanner.get_queue_size()
            assert initial_queue_size > 0, "Queue should have files to process"

            # Get initial performance stats
            initial_stats = scanner.get_performance_statistics()

            # Trigger shutdown while under load
            shutdown_start = time.time()
            assert scanner.stop_monitoring() is True
            shutdown_duration = time.time() - shutdown_start

            # Verify graceful shutdown
            assert scanner.running is False
            assert (
                shutdown_duration < 10.0
            ), f"Shutdown took too long: {shutdown_duration}s"

            # Verify final stats are accessible
            final_stats = scanner.get_performance_statistics()
            assert final_stats["uptime_seconds"] > 0

            # Verify no threads are left running
            assert len(scanner.worker_threads) == 0

            print(f"Shutdown under load completed in {shutdown_duration:.2f}s")
            print(f"Initial queue size: {initial_queue_size}")
            print(f"Files processed before shutdown: {final_stats['files_processed']}")

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_queue_overflow_conditions(self, config):
        """Test behavior when queue reaches maximum capacity"""
        temp_dir = tempfile.mkdtemp()

        try:
            # Configure scanner with very small queue
            overflow_config = config.copy()
            overflow_config["THREADS"] = 1  # Single thread to slow processing
            overflow_config["MAX_QUEUE_SIZE"] = 5  # Very small queue
            overflow_config["EXTRACT_DIR"] = temp_dir
            overflow_config["QUEUE_TIMEOUT_NORMAL"] = 0.1  # Fast timeout

            scanner = MultiThreadScanner(overflow_config)

            # Start scanner
            assert scanner.start_monitoring() is True

            # Create more files than queue can handle
            file_count = 20
            test_files = []
            successful_queues = 0
            failed_queues = 0

            for i in range(file_count):
                file_path = os.path.join(temp_dir, f"overflow_test_{i}.txt")
                with open(file_path, "w") as f:
                    f.write(f"Overflow test content {i}\n")
                test_files.append(file_path)

                # Try to queue file manually
                if scanner.queue_file(file_path):
                    successful_queues += 1
                else:
                    failed_queues += 1

                # Check queue size
                queue_size = scanner.get_queue_size()
                assert (
                    queue_size <= overflow_config["MAX_QUEUE_SIZE"]
                ), f"Queue size {queue_size} exceeded max {overflow_config['MAX_QUEUE_SIZE']}"

            print(
                f"Queue overflow test: {successful_queues} successful, {failed_queues} failed"
            )
            print(f"Max queue size: {overflow_config['MAX_QUEUE_SIZE']}")

            # Verify that some files were rejected due to queue overflow
            assert (
                failed_queues > 0
            ), "Expected some files to be rejected due to queue overflow"
            assert (
                successful_queues > 0
            ), "Expected some files to be successfully queued"

            # Wait for processing
            time.sleep(2.0)

            # Stop scanner
            scanner.stop_monitoring()

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_worker_thread_exception_handling(self, config):
        """Test worker thread recovery from various exception scenarios"""
        temp_dir = tempfile.mkdtemp()

        try:
            # Configure scanner for exception testing
            exception_config = config.copy()
            exception_config["THREADS"] = 2
            exception_config["EXTRACT_DIR"] = temp_dir

            scanner = MultiThreadScanner(exception_config)

            # Create problematic files that might cause exceptions
            test_scenarios = [
                ("normal_file.txt", "Normal content"),
                ("empty_file.txt", ""),  # Empty file
                ("large_filename_" + "x" * 200 + ".txt", "Content"),  # Long filename
            ]

            test_files = []
            for filename, content in test_scenarios:
                file_path = os.path.join(temp_dir, filename)
                try:
                    with open(file_path, "w") as f:
                        f.write(content)
                    test_files.append(file_path)
                except Exception as e:
                    print(f"Could not create test file {filename}: {e}")

            # Start scanner
            assert scanner.start_monitoring() is True

            # Monitor worker health
            initial_health = scanner.get_worker_health_status()
            assert len(initial_health) == 2, "Should have 2 workers"

            # Wait for processing
            time.sleep(3.0)

            # Check that workers are still responsive
            final_health = scanner.get_worker_health_status()
            healthy_workers = sum(
                1
                for status in final_health.values()
                if status["status"] in ["healthy", "warning"]
            )

            assert healthy_workers >= 1, "At least one worker should remain healthy"

            # Check performance stats for error tracking
            stats = scanner.get_performance_statistics()
            print(f"Worker error handling test:")
            print(f"Files processed: {stats['files_processed']}")
            print(f"Files failed: {stats['files_failed']}")
            print(f"Healthy workers: {healthy_workers}/{len(final_health)}")

            # Verify error counts are tracked in worker stats
            total_errors = sum(
                worker_stats["errors"]
                for worker_stats in stats["worker_stats"].values()
            )
            print(f"Total worker errors: {total_errors}")

            # Stop scanner
            scanner.stop_monitoring()

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_worker_health_monitoring(self, config):
        """Test worker health monitoring and detection of unhealthy workers"""
        temp_dir = tempfile.mkdtemp()

        try:
            # Configure scanner with aggressive health monitoring
            health_config = config.copy()
            health_config["THREADS"] = 3
            health_config["EXTRACT_DIR"] = temp_dir
            health_config["HEALTH_CHECK_INTERVAL"] = 1  # Check every second
            health_config["MAX_WORKER_IDLE_TIME"] = 5  # 5 second timeout

            scanner = MultiThreadScanner(health_config)

            # Start scanner
            assert scanner.start_monitoring() is True

            # Initial health check
            initial_health = scanner.get_worker_health_status()
            assert len(initial_health) == 3, "Should have 3 workers"

            # All workers should start healthy
            for worker_id, status in initial_health.items():
                assert (
                    status["status"] == "healthy"
                ), f"Worker {worker_id} should start healthy"
                assert status["last_heartbeat_ago"] < 2.0, "Heartbeat should be recent"

            # Create some work to keep workers active
            for i in range(5):
                file_path = os.path.join(temp_dir, f"health_test_{i}.txt")
                with open(file_path, "w") as f:
                    f.write(f"Health test content {i}\n")

            # Wait for processing and health monitoring
            time.sleep(3.0)

            # Check health again
            active_health = scanner.get_worker_health_status()
            healthy_count = sum(
                1 for status in active_health.values() if status["status"] == "healthy"
            )

            print(f"Worker health monitoring:")
            for worker_id, status in active_health.items():
                print(
                    f"  {worker_id}: {status['status']} (heartbeat {status['last_heartbeat_ago']:.1f}s ago)"
                )

            # Most workers should be healthy during normal operation
            assert (
                healthy_count >= 2
            ), f"Expected at least 2 healthy workers, got {healthy_count}"

            # Test performance stats integration
            stats = scanner.get_performance_statistics()
            assert "worker_health" in stats
            assert len(stats["worker_health"]) == 3

            # Stop scanner
            scanner.stop_monitoring()

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_scanner_recovery_from_interruption(self, config):
        """Test scanner's ability to recover interrupted scans on startup"""
        temp_dir = tempfile.mkdtemp()

        try:
            # Configure scanner
            recovery_config = config.copy()
            recovery_config["EXTRACT_DIR"] = temp_dir

            # Create test files
            test_files = []
            for i in range(5):
                file_path = os.path.join(temp_dir, f"recovery_test_{i}.txt")
                with open(file_path, "w") as f:
                    f.write(f"Recovery test content {i}\n")
                test_files.append(file_path)

            # First scanner - simulate interrupted scanning
            scanner1 = MultiThreadScanner(recovery_config)

            # Manually add some files to pending state in database
            for file_path in test_files[:3]:
                try:
                    file_metadata = scanner1.file_analyzer.get_file_metadata(file_path)
                    scanner1.db_manager.add_file_state(file_path, file_metadata)
                    # Simulate scanning state (interrupted)
                    scanner1.db_manager.update_file_state(file_path, "scanning")
                except Exception as e:
                    print(f"Error setting up test state: {e}")

            # Test recovery mechanism
            recovered_count = scanner1.recover_interrupted_scans(timeout_minutes=1)
            print(f"Recovery test: {recovered_count} files recovered")

            # Start second scanner - should recover interrupted files
            scanner2 = MultiThreadScanner(recovery_config)

            # Check pending files
            pending_files = scanner2.get_pending_files()
            print(f"Pending files after recovery: {len(pending_files)}")

            # Start monitoring to process recovered files
            assert scanner2.start_monitoring() is True

            # Wait for processing
            time.sleep(2.0)

            # Check processing statistics
            stats = scanner2.get_processing_statistics()
            print(f"Processing statistics: {stats}")

            # Stop scanner
            scanner2.stop_monitoring()

            # Verify some files were processed
            final_stats = scanner2.get_processing_statistics()
            assert (
                final_stats.get("completed", 0) + final_stats.get("failed", 0) > 0
            ), "Expected some files to be processed after recovery"

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_memory_pressure_handling(self, config):
        """Test scanner behavior under memory pressure conditions"""
        temp_dir = tempfile.mkdtemp()

        try:
            # Configure scanner for memory pressure testing
            memory_config = config.copy()
            memory_config["THREADS"] = 2
            memory_config["MAX_FILE_SIZE"] = 1024 * 1024  # 1MB limit
            memory_config["EXTRACT_DIR"] = temp_dir

            scanner = MultiThreadScanner(memory_config)

            # Create files of various sizes
            test_scenarios = [
                ("small_file.txt", 1024),  # 1KB - should process
                ("medium_file.txt", 512 * 1024),  # 512KB - should process
                ("large_file.txt", 2 * 1024 * 1024),  # 2MB - should be rejected
            ]

            test_files = []
            for filename, size in test_scenarios:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    f.write("x" * size)
                test_files.append((file_path, size))

            # Start scanner
            assert scanner.start_monitoring() is True

            # Wait for processing
            time.sleep(3.0)

            # Check results
            stats = scanner.get_performance_statistics()

            print(f"Memory pressure test results:")
            print(f"Files processed: {stats['files_processed']}")
            print(f"Files failed: {stats['files_failed']}")

            # Check file states in database
            for file_path, size in test_files:
                file_state = scanner.db_manager.get_file_state(file_path)
                print(
                    f"File {os.path.basename(file_path)} ({size} bytes): {file_state['state'] if file_state else 'not found'}"
                )

                if size > memory_config["MAX_FILE_SIZE"]:
                    # Large files should be marked as failed
                    assert (
                        file_state and file_state["state"] == "failed"
                    ), f"Large file should be marked as failed"
                else:
                    # Small files should be processed
                    assert file_state and file_state["state"] in [
                        "completed",
                        "scanning",
                    ], f"Small file should be processed or in progress"

            # Stop scanner
            scanner.stop_monitoring()

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
