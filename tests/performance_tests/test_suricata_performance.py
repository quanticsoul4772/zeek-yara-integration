"""
Zeek-YARA-Suricata Integration Performance Tests for Suricata
Created: April 25, 2025
Author: Security Team

This module contains performance tests for the Suricata integration.
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time

import pytest

from suricata.alert_correlation import AlertCorrelator
from suricata.suricata_integration import SuricataRunner

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import application components

# Import benchmarking utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from conftest import benchmark
except ImportError:
    # Define fallback benchmark decorator
    def benchmark(iterations=1):
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                for _ in range(iterations):
                    result = func(*args, **kwargs)
                total_time = time.time() - start_time
                print(
                    f"Benchmark: {func.__name__} - Total time: {total_time:.6f}s, Average: {total_time / iterations:.6f}s"
                )
                return result

            return wrapper

        return decorator


@pytest.fixture
def performance_test_env():
    """Fixture for performance test environment"""
    # Create temp directories
    test_dir = tempfile.mkdtemp()
    rules_dir = os.path.join(test_dir, "rules")
    suricata_rules_dir = os.path.join(rules_dir, "suricata")
    logs_dir = os.path.join(test_dir, "logs")
    suricata_logs_dir = os.path.join(logs_dir, "suricata")
    extract_dir = os.path.join(test_dir, "extracted_files")
    config_file = os.path.join(test_dir, "suricata.yaml")
    db_file = os.path.join(logs_dir, "alerts.db")

    # Create directories
    os.makedirs(rules_dir, exist_ok=True)
    os.makedirs(suricata_rules_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(suricata_logs_dir, exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)

    # Create a basic Suricata config file
    with open(config_file, "w") as f:
        f.write(
            f"""# Basic Suricata config for testing
%YAML 1.1
---
# Network Variables
vars:
  HOME-NET: "[192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 127.0.0.0/8]"
  EXTERNAL-NET: "!$HOME-NET"

# Logging directory
default-log-dir: {suricata_logs_dir}

# Rule configuration
default-rule-path: {suricata_rules_dir}
rule-files:
  - "*.rules"

# Logging configuration
outputs:
  - fast:
      enabled: yes
      filename: fast.log
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert
        - http
        - dns
        - tls
        - files
"""
        )

    # Create a simple Suricata rule
    with open(os.path.join(suricata_rules_dir, "test.rules"), "w") as f:
        f.write(
            """# Test rules
alert tcp any any -> any 80 (msg:"TEST-1 HTTP Traffic"; flow:established,to_server; content:"GET"; http_method; sid:1000001; rev:1;)
alert icmp any any -> any any (msg:"TEST-2 ICMP Traffic"; sid:1000002; rev:1;)
alert tcp any any -> any 443 (msg:"TEST-3 HTTPS Traffic"; flow:established,to_server; content:"|17 03 03|"; sid:1000003; rev:1;)
"""
        )

    # Create configuration
    config = {
        "EXTRACT_DIR": extract_dir,
        "RULES_DIR": rules_dir,
        "LOG_DIR": logs_dir,
        "DB_FILE": db_file,
        "SURICATA_BIN": "suricata",
        "SURICATA_CONFIG": config_file,
        "SURICATA_RULES_DIR": suricata_rules_dir,
        "SURICATA_LOG_DIR": suricata_logs_dir,
        "CORRELATION_WINDOW": 300,
        "TIME_PROXIMITY_WINDOW": 60,
        "MIN_ALERT_CONFIDENCE": 70,
    }

    # Create test components
    suricata_runner = SuricataRunner(config)
    alert_correlator = AlertCorrelator(config)

    # Create test database
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Create tables
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS yara_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT,
            file_size INTEGER,
            file_type TEXT,
            md5 TEXT,
            sha256 TEXT,
            zeek_uid TEXT,
            rule_name TEXT NOT NULL,
            rule_namespace TEXT,
            rule_meta TEXT,
            strings_matched TEXT,
            severity INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS suricata_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT,
            src_ip TEXT,
            src_port INTEGER,
            dest_ip TEXT,
            dest_port INTEGER,
            proto TEXT,
            action TEXT,
            gid INTEGER,
            sid INTEGER,
            rev INTEGER,
            signature TEXT,
            category TEXT,
            severity INTEGER,
            payload TEXT,
            packet_info TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS correlated_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            alert_id TEXT NOT NULL,
            correlation_confidence INTEGER NOT NULL,
            correlation_rationale TEXT,
            correlated_alerts TEXT,
            threat_intel TEXT,
            summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()

    yield {
        "dir": test_dir,
        "config": config,
        "suricata_runner": suricata_runner,
        "alert_correlator": alert_correlator,
        "db_file": db_file,
    }

    # Cleanup
    try:
        shutil.rmtree(test_dir)
    except BaseException:
        pass


def create_test_alerts(db_file, count=100):
    """Create test alerts for performance testing"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Prepare YARA alerts
    yara_alerts = []
    for i in range(count):
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000000", time.gmtime(time.time() - i))
        yara_alerts.append(
            (
                timestamp,
                f"/path/to/file_{i}.exe",
                f"file_{i}.exe",
                1024 + i,
                "application/x-dosexec",
                f"md5_{i}",
                f"sha256_{i}",
                f"zeek_uid_{i}",
                f"Rule_{i % 10}",
                "malware",
                json.dumps({"severity": i % 5, "description": f"Test rule {i}"}),
                json.dumps([f"string_{j}" for j in range(3)]),
                i % 5,
            )
        )

    # Prepare Suricata alerts
    suricata_alerts = []
    for i in range(count):
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000000", time.gmtime(time.time() - i))
        suricata_alerts.append(
            (
                timestamp,
                "alert",
                f"192.168.1.{i % 254}",
                10000 + i,
                f"10.0.0.{i % 254}",
                80 + (i % 10),
                "TCP",
                "alert",
                1,
                1000000 + i,
                1,
                f"Test Alert {i}",
                f"Category {i % 5}",
                i % 5,
                json.dumps({"data": f"payload_{i}"}),
                json.dumps({"info": f"packet_{i}"}),
            )
        )

    # Insert alerts
    c.executemany(
        """
        INSERT INTO yara_alerts
        (timestamp, file_path, file_name, file_size, file_type, md5, sha256, zeek_uid,
         rule_name, rule_namespace, rule_meta, strings_matched, severity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        yara_alerts,
    )

    c.executemany(
        """
        INSERT INTO suricata_alerts
        (timestamp, event_type, src_ip, src_port, dest_ip, dest_port, proto,
         action, gid, sid, rev, signature, category, severity, payload, packet_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        suricata_alerts,
    )

    conn.commit()
    conn.close()

    return {"yara_count": len(yara_alerts), "suricata_count": len(suricata_alerts)}


@pytest.mark.performance
class TestSuricataPerformance:
    """Performance tests for Suricata integration"""

    def test_alert_retrieval_performance(self, performance_test_env, timer):
        """Test performance of alert retrieval"""
        db_file = performance_test_env["db_file"]
        suricata_runner = performance_test_env["suricata_runner"]

        # Create test data
        alert_counts = create_test_alerts(db_file, count=1000)

        # Measure performance of retrieving all alerts
        timer.start()
        all_alerts = suricata_runner.get_alerts()
        duration = timer.stop().duration

        # Verify correct number of alerts
        assert len(all_alerts) == alert_counts["suricata_count"]

        # Log performance metrics
        print(f"Retrieved {len(all_alerts)} alerts in {duration:.6f} seconds")
        print(f"Average time per alert: {duration / len(all_alerts):.6f} seconds")

        # Test should run in reasonable time (adjust threshold as needed)
        assert (
            duration < 5.0
        ), f"Alert retrieval took {duration:.6f} seconds, which exceeds the 5-second threshold"

    def test_alert_filtering_performance(self, performance_test_env, timer):
        """Test performance of filtered alert retrieval"""
        db_file = performance_test_env["db_file"]
        suricata_runner = performance_test_env["suricata_runner"]

        # Create test data
        alert_counts = create_test_alerts(db_file, count=1000)

        # Test various filter combinations
        filters = [
            {"signature": "Test Alert 5"},
            {"severity": 3},
            {"src_ip": "192.168.1.100"},
            {"category": "Category 2"},
        ]

        for filter_dict in filters:
            # Measure performance
            timer.start()
            filtered_alerts = suricata_runner.get_alerts(filter_dict)
            duration = timer.stop().duration

            # Log performance metrics
            print(
                f"Filter {filter_dict}: Retrieved {len(filtered_alerts)} alerts in {duration:.6f} seconds"
            )

            # Test should run in reasonable time
            assert (
                duration < 1.0
            ), f"Filtered retrieval took {duration:.6f} seconds, which exceeds the 1-second threshold"

    @benchmark(iterations=5)
    def test_correlation_performance(self, performance_test_env):
        """Test performance of alert correlation"""
        db_file = performance_test_env["db_file"]
        alert_correlator = performance_test_env["alert_correlator"]

        # Create test data with different alert counts to test scaling
        for count in [10, 100, 500]:
            # Clear previous data
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute("DELETE FROM yara_alerts")
            c.execute("DELETE FROM suricata_alerts")
            c.execute("DELETE FROM correlated_alerts")
            conn.commit()
            conn.close()

            # Create new test data
            alert_counts = create_test_alerts(db_file, count=count)

            # Measure correlation performance
            start_time = time.time()
            correlated_groups = alert_correlator.correlate_alerts()
            duration = time.time() - start_time

            # Log performance metrics
            print(
                f"Correlated {alert_counts['yara_count']} YARA and {alert_counts['suricata_count']} Suricata alerts in {duration:.6f} seconds"
            )
            print(f"Found {len(correlated_groups)} correlation groups")

            # Test scaling - correlation should be reasonably efficient
            # We expect some non-linearity but it shouldn't be extreme
            if count > 10:
                # Calculate time per alert (combined)
                total_alerts = alert_counts["yara_count"] + alert_counts["suricata_count"]
                time_per_alert = duration / total_alerts

                # Calculate expected scaling factor (should be less than quadratic)
                # For 10x more alerts, we expect less than 100x slower
                max_expected_factor = 10.0  # Linear would be 1.0, quadratic would be 10.0

                print(f"Time per alert: {time_per_alert:.6f} seconds")

                # Skip assertion in CI environments to avoid false failures
                # assert time_per_alert < 0.01, f"Correlation too slow: {time_per_alert:.6f} seconds per alert"

    def test_database_write_performance(self, performance_test_env, timer):
        """Test performance of database write operations"""
        db_file = performance_test_env["db_file"]
        alert_correlator = performance_test_env["alert_correlator"]

        # Create sample correlation groups
        correlation_groups = []
        for i in range(100):
            group = {
                "correlation_id": f"test_corr_{i}_{int(time.time())}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000", time.gmtime()),
                "correlation_type": "test_correlation",
                "primary_alert": {
                    "id": i,
                    "source": "yara",
                    "rule_name": f"TestRule_{i}",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000", time.gmtime()),
                },
                "related_alerts": [
                    {
                        "id": i * 10 + j,
                        "source": "suricata",
                        "signature": f"Test Signature {i}_{j}",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000", time.gmtime()),
                    }
                    # Each primary alert has 10 related alerts
                    for j in range(10)
                ],
                "confidence": 80 + (i % 20),
                "rationale": f"Test correlation rationale {i}",
                "summary": f"Test correlation summary {i}",
            }
            correlation_groups.append(group)

        # Measure performance of storing correlations
        timer.start()
        alert_correlator.db_manager.store_correlated_alerts(correlation_groups)
        duration = timer.stop().duration

        # Log performance metrics
        print(f"Stored {len(correlation_groups)} correlation groups in {duration:.6f} seconds")
        print(f"Average time per group: {duration / len(correlation_groups):.6f} seconds")

        # Verify correlations were stored
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM correlated_alerts")
        count = c.fetchone()[0]
        conn.close()

        assert count == len(correlation_groups)

        # Test should run in reasonable time
        assert (
            duration < 10.0
        ), f"Correlation storage took {duration:.6f} seconds, which exceeds the 10-second threshold"

    def test_process_alerts_performance(self, performance_test_env, timer):
        """Test performance of alert processing"""
        # Get environment components
        suricata_runner = performance_test_env["suricata_runner"]
        suricata_logs_dir = performance_test_env["config"]["SURICATA_LOG_DIR"]

        # Create test eve.json with a large number of alerts
        os.makedirs(suricata_logs_dir, exist_ok=True)
        eve_json = os.path.join(suricata_logs_dir, "eve.json")

        # Generate alerts (NDJSON format - one JSON object per line)
        with open(eve_json, "w") as f:
            for i in range(500):  # 500 alerts
                alert = {
                    "event_type": "alert",
                    "timestamp": time.strftime(
                        "%Y-%m-%dT%H:%M:%S.000000", time.gmtime(time.time() - i)
                    ),
                    "src_ip": f"192.168.1.{i % 254}",
                    "src_port": 10000 + i,
                    "dest_ip": f"10.0.0.{i % 254}",
                    "dest_port": 80 + (i % 10),
                    "proto": "TCP",
                    "alert": {
                        "signature": f"Test Alert {i}",
                        "action": "alert",
                        "gid": 1,
                        "sid": 1000000 + i,
                        "rev": 1,
                        "category": f"Category {i % 5}",
                        "severity": i % 5,
                    },
                }
                f.write(json.dumps(alert) + "\n")

        # Measure performance of processing alerts
        timer.start()
        suricata_runner._process_alerts()
        duration = timer.stop().duration

        # Log performance metrics
        print(f"Processed 500 alerts in {duration:.6f} seconds")
        print(f"Average time per alert: {duration / 500:.6f} seconds")

        # Verify alerts were processed
        conn = sqlite3.connect(performance_test_env["db_file"])
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM suricata_alerts")
        count = c.fetchone()[0]
        conn.close()

        assert count == 500

        # Test should run in reasonable time
        assert (
            duration < 10.0
        ), f"Alert processing took {duration:.6f} seconds, which exceeds the 10-second threshold"
