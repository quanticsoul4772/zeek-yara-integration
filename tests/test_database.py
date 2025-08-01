"""
Zeek-YARA Integration Database Tests
Created: April 24, 2025
Author: Russell Smith

This module contains tests for the database functionality, including performance tests
for the optimizations implemented in Phase 2.
"""

from core.database import ConnectionPool, DatabaseManager, performance_track
import datetime
import json
import os
import sqlite3
import sys
import time

import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


# Unit tests for the DatabaseManager
@pytest.mark.unit
class TestDatabaseManager:
    """Unit tests for DatabaseManager class"""

    def test_initialization(self, db_manager):
        """Test database initialization"""
        assert db_manager is not None
        assert os.path.exists(db_manager.db_file)

    def test_add_alert(self, db_manager):
        """Test adding an alert to the database"""
        # Create test alert data
        alert_data = {
            "file_path": "/tmp/test.txt",
            "file_name": "test.txt",
            "file_size": 100,
            "file_type": "text/plain",
            "md5": "test_md5",
            "sha256": "test_sha256",
            "zeek_uid": "test_uid",
        }

        match_data = {
            "matched": True,
            "matches": [
                {
                    "rule": "test_rule",
                    "namespace": "test",
                    "meta": {"description": "Test rule", "severity": 3},
                    "strings": ["test_string"],
                }
            ],
        }

        # Add alert
        result = db_manager.add_alert(alert_data, match_data)
        assert result == True

        # Verify alert was added
        alerts = db_manager.get_alerts(limit=10)
        assert len(alerts) == 1

        # Check alert fields
        alert = alerts[0]
        assert alert["file_name"] == "test.txt"
        assert alert["file_size"] == 100
        assert alert["rule_name"] == "test_rule"
        assert alert["rule_namespace"] == "test"
        assert alert["severity"] == 3

    def test_bulk_insert_alerts(self, db_manager):
        """Test bulk insertion of alerts"""
        # Create test alert data (10 alerts)
        alerts_data = []
        for i in range(10):
            alert = {
                "timestamp": datetime.datetime.now().isoformat(),
                "file_path": f"/tmp/test_{i}.txt",
                "file_name": f"test_{i}.txt",
                "file_size": 100 + i,
                "file_type": "text/plain",
                "md5": f"md5_{i}",
                "sha256": f"sha256_{i}",
                "zeek_uid": f"uid_{i}",
                "rule_name": "test_rule",
                "rule_namespace": "test",
                "rule_meta": json.dumps({"description": "Test rule", "severity": 3}),
                "strings_matched": json.dumps([f"string_{i}"]),
                "severity": 3,
            }
            alerts_data.append(alert)

        # Bulk insert
        result = db_manager.bulk_insert_alerts(alerts_data)
        assert result == 10

        # Verify alerts were added
        alerts = db_manager.get_alerts(limit=100)
        assert len(alerts) == 10

    def test_get_alerts_with_limit(self, db_manager):
        """Test retrieving alerts with a limit"""
        # Create test alert data (20 alerts)
        alerts_data = []
        for i in range(20):
            alert = {
                "timestamp": datetime.datetime.now().isoformat(),
                "file_path": f"/tmp/test_{i}.txt",
                "file_name": f"test_{i}.txt",
                "file_size": 100 + i,
                "file_type": "text/plain",
                "md5": f"md5_{i}",
                "sha256": f"sha256_{i}",
                "zeek_uid": f"uid_{i}",
                "rule_name": "test_rule",
                "rule_namespace": "test",
                "rule_meta": json.dumps({"description": "Test rule", "severity": 3}),
                "strings_matched": json.dumps([f"string_{i}"]),
                "severity": 3,
            }
            alerts_data.append(alert)

        # Bulk insert
        db_manager.bulk_insert_alerts(alerts_data)

        # Get alerts with limit
        alerts_5 = db_manager.get_alerts(limit=5)
        assert len(alerts_5) == 5

        alerts_10 = db_manager.get_alerts(limit=10)
        assert len(alerts_10) == 10

        # Default should be all alerts
        alerts_all = db_manager.get_alerts()
        assert len(alerts_all) == 20

    def test_connection_pool(self):
        """Test the connection pool functionality"""
        # Create a temporary database file
        db_file = os.path.join(os.path.dirname(__file__), "test_pool.db")

        # Clean up if exists
        if os.path.exists(db_file):
            os.unlink(db_file)

        # Create connection pool
        pool = ConnectionPool(db_file, max_connections=3)

        # Get connections from pool
        connections = []
        for _ in range(3):
            with pool.connection() as conn:
                assert isinstance(conn, sqlite3.Connection)
                # Execute a simple query to verify connection works
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result == (1,)

                # Store connection object for verification
                connections.append(conn)

        # Clean up
        if os.path.exists(db_file):
            os.unlink(db_file)


# Performance tests for the DatabaseManager
@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database optimizations"""

    def test_single_vs_bulk_insert_performance(self, db_manager, timer):
        """Test performance comparison between single and bulk inserts"""
        # Create test data
        single_inserts = 50
        bulk_size = 50

        # Prepare alert data
        alert_template = {
            "file_path": "/tmp/test.txt",
            "file_name": "test.txt",
            "file_size": 100,
            "file_type": "text/plain",
            "md5": "test_md5",
            "sha256": "test_sha256",
            "zeek_uid": "test_uid",
        }

        match_template = {
            "matched": True,
            "matches": [
                {
                    "rule": "test_rule",
                    "namespace": "test",
                    "meta": {"description": "Test rule", "severity": 3},
                    "strings": ["test_string"],
                }
            ],
        }

        # Prepare bulk data
        bulk_data = []
        for i in range(bulk_size):
            alert = {
                "timestamp": datetime.datetime.now().isoformat(),
                "file_path": f"/tmp/test_{i}.txt",
                "file_name": f"test_{i}.txt",
                "file_size": 100 + i,
                "file_type": "text/plain",
                "md5": f"md5_{i}",
                "sha256": f"sha256_{i}",
                "zeek_uid": f"uid_{i}",
                "rule_name": "test_rule",
                "rule_namespace": "test",
                "rule_meta": json.dumps({"description": "Test rule", "severity": 3}),
                "strings_matched": json.dumps([f"string_{i}"]),
                "severity": 3,
            }
            bulk_data.append(alert)

        # Measure single insert performance
        timer.start()
        for i in range(single_inserts):
            alert_data = alert_template.copy()
            alert_data["file_path"] = f"/tmp/single_{i}.txt"
            alert_data["file_name"] = f"single_{i}.txt"
            alert_data["md5"] = f"single_md5_{i}"
            alert_data["sha256"] = f"single_sha256_{i}"
            alert_data["zeek_uid"] = f"single_uid_{i}"

            db_manager.add_alert(alert_data, match_template)
        single_time = timer.stop().duration

        # Clean database
        os.unlink(db_manager.db_file)
        db_manager = DatabaseManager(db_file=db_manager.db_file)

        # Measure bulk insert performance
        timer.start()
        db_manager.bulk_insert_alerts(bulk_data)
        bulk_time = timer.stop().duration

        # Calculate speedup
        speedup = single_time / bulk_time if bulk_time > 0 else float("inf")

        # Print results
        print(
            f"Single insert time: {
                single_time:.6f}s for {single_inserts} inserts")
        print(f"Bulk insert time: {bulk_time:.6f}s for {bulk_size} inserts")
        print(f"Speedup: {speedup:.2f}x")

        # Verify performance improvement
        assert speedup > 1.5, "Bulk insert should be at least 50% faster than single inserts"

    def test_query_performance(self, db_manager, timer):
        """Test query performance with different database sizes"""
        # Insert different numbers of alerts
        sizes = [10, 100, 1000]
        query_times = []

        for size in sizes:
            # Clean database
            os.unlink(db_manager.db_file)
            db_manager = DatabaseManager(db_file=db_manager.db_file)

            # Generate alerts
            alerts_data = []
            for i in range(size):
                alert = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "file_path": f"/tmp/test_{i}.txt",
                    "file_name": f"test_{i}.txt",
                    "file_size": 100 + i,
                    "file_type": "text/plain",
                    "md5": f"md5_{i}",
                    "sha256": f"sha256_{i}",
                    "zeek_uid": f"uid_{i}",
                    "rule_name": f"rule_{i % 10}",  # 10 different rules
                    # 5 different namespaces
                    "rule_namespace": f"namespace_{i % 5}",
                    "rule_meta": json.dumps({"description": f"Test rule {i}", "severity": i % 10}),
                    "strings_matched": json.dumps([f"string_{i}"]),
                    "severity": i % 10,
                }
                alerts_data.append(alert)

            # Insert alerts
            db_manager.bulk_insert_alerts(alerts_data)

            # Measure query time for all alerts
            timer.start()
            all_alerts = db_manager.get_alerts()
            all_time = timer.stop().duration
            assert len(all_alerts) == size

            # Measure query time with filter
            timer.start()
            filtered_alerts = db_manager.get_alerts(
                filters={"rule_namespace": "namespace_1"})
            filter_time = timer.stop().duration

            # Record results
            query_times.append(
                {
                    "size": size,
                    "all_time": all_time,
                    "filter_time": filter_time,
                    "all_per_row": all_time /
                    size if size > 0 else 0,
                    "filter_per_row": filter_time /
                    len(filtered_alerts) if filtered_alerts else 0,
                })

        # Print results
        for result in query_times:
            print(f"Database size: {result['size']} alerts")
            print(
                f"  All alerts query: {
                    result['all_time']:.6f}s ({
                    result['all_per_row'] *
                    1000:.2f}ms per row)")
            print(
                f"  Filtered query: {
                    result['filter_time']:.6f}s ({
                    result['filter_per_row'] *
                    1000:.2f}ms per row)")

        # Verify performance is acceptable
        assert query_times[-1]["all_per_row"] < 0.001, "Query time per row should be less than 1ms"

    def test_performance_tracking_decorator(self, db_manager):
        """Test the performance tracking decorator"""
        # Create a logger that captures logs
        import io
        import logging

        log_stream = io.StringIO()
        test_logger = logging.getLogger("test_performance_tracking")
        test_logger.setLevel(logging.DEBUG)

        # Add a stream handler
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)

        # Create a test method with performance tracking
        @performance_track(logger=test_logger)
        def test_method():
            # Simulate work
            time.sleep(0.1)
            return True

        # Run the decorated method
        result = test_method()
        assert result == True

        # Check if performance logs were captured
        log_contents = log_stream.getvalue()
        assert "Method test_method executed in" in log_contents
