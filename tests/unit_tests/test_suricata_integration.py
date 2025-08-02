"""
Zeek-YARA-Suricata Integration Unit Tests for Suricata Integration
Created: April 25, 2025
Author: Security Team

This module contains unit tests for the Suricata integration module.
"""

import json
import os
import sqlite3
import sys
import tempfile
from unittest.mock import patch

import pytest

from suricata.suricata_integration import SuricataConfig, SuricataRunner

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


@pytest.fixture
def suricata_config():
    """Fixture for Suricata configuration"""
    # Create temp directories for testing
    rules_dir = tempfile.mkdtemp()
    log_dir = tempfile.mkdtemp()
    config_file = os.path.join(tempfile.mkdtemp(), "suricata.yaml")

    # Create configuration
    config = SuricataConfig(config_file=config_file, rules_dir=rules_dir, log_dir=log_dir)

    yield config

    # Cleanup
    try:
        import shutil

        shutil.rmtree(rules_dir, ignore_errors=True)
        shutil.rmtree(log_dir, ignore_errors=True)
        shutil.rmtree(os.path.dirname(config_file), ignore_errors=True)
    except BaseException:
        pass


@pytest.fixture
def suricata_runner():
    """Fixture for Suricata runner"""
    # Create temporary files and directories
    db_file = os.path.join(tempfile.mkdtemp(), "alerts.db")
    rules_dir = tempfile.mkdtemp()
    log_dir = tempfile.mkdtemp()
    config_file = os.path.join(tempfile.mkdtemp(), "suricata.yaml")

    # Create configuration
    config = {
        "SURICATA_BIN": "suricata",
        "SURICATA_CONFIG": config_file,
        "SURICATA_RULES_DIR": rules_dir,
        "SURICATA_LOG_DIR": log_dir,
        "DB_FILE": db_file,
    }

    # Create runner
    runner = SuricataRunner(config)

    yield runner

    # Cleanup
    try:
        import shutil

        if os.path.exists(db_file):
            os.unlink(db_file)
        shutil.rmtree(os.path.dirname(db_file), ignore_errors=True)
        shutil.rmtree(rules_dir, ignore_errors=True)
        shutil.rmtree(log_dir, ignore_errors=True)
        shutil.rmtree(os.path.dirname(config_file), ignore_errors=True)
    except BaseException:
        pass


@pytest.mark.unit
class TestSuricataConfig:
    """Unit tests for SuricataConfig class"""

    def test_initialization(self, suricata_config):
        """Test initialization of Suricata configuration"""
        assert suricata_config is not None
        assert os.path.exists(suricata_config.config_file)
        assert os.path.exists(suricata_config.rules_dir)
        assert os.path.exists(suricata_config.log_dir)

    def test_default_config_creation(self, suricata_config):
        """Test creation of default Suricata configuration"""
        # Verify that the config file was created with default content
        with open(suricata_config.config_file, "r") as f:
            content = f.read()

        # Check for key configuration sections
        assert "%YAML 1.1" in content
        assert "vars:" in content
        assert "HOME-NET:" in content
        assert "outputs:" in content
        assert "rule-files:" in content

    def test_update_rules(self, suricata_config):
        """Test update_rules method without external dependencies"""
        # Test without downloading to avoid network dependency
        result = suricata_config.update_rules(download_emerging_threats=False)

        # Should succeed when not trying to download
        assert result is True


@pytest.mark.unit
class TestSuricataRunner:
    """Unit tests for SuricataRunner class"""

    def test_initialization(self, suricata_runner):
        """Test initialization of Suricata runner"""
        assert suricata_runner is not None
        assert hasattr(suricata_runner, "suricata_bin")
        assert hasattr(suricata_runner, "suricata_config")
        assert hasattr(suricata_runner, "output_dir")
        assert hasattr(suricata_runner, "db_file")

        # Check if database was initialized
        conn = sqlite3.connect(suricata_runner.db_file)
        c = conn.cursor()

        # Check if suricata_alerts table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suricata_alerts'")
        assert c.fetchone() is not None

        conn.close()

    @patch("subprocess.Popen")
    def test_run_live(self, mock_popen, suricata_runner):
        """Test run_live method"""
        # Set up subprocess mock
        mock_popen.return_value.poll.return_value = None  # Process running

        # Call run_live for a short duration
        result = suricata_runner.run_live("eth0", duration=1)

        # Check result
        assert result is True

        # Verify subprocess was called with correct arguments
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert "suricata" in args
        assert "-i" in args
        assert "eth0" in args

    @patch("subprocess.run")
    def test_run_pcap(self, mock_subprocess, suricata_runner):
        """Test run_pcap method"""
        # Create a temporary pcap file
        pcap_file = os.path.join(tempfile.mkdtemp(), "test.pcap")
        with open(pcap_file, "wb") as f:
            f.write(b"PCAPDATA")

        # Set up subprocess mock
        mock_subprocess.return_value.returncode = 0

        # Call run_pcap
        result = suricata_runner.run_pcap(pcap_file)

        # Check result
        assert result is True

        # Verify subprocess was called with correct arguments
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert "suricata" in args
        assert "-r" in args
        assert pcap_file in args

        # Clean up
        os.unlink(pcap_file)
        os.rmdir(os.path.dirname(pcap_file))

    def test_process_alerts(self, suricata_runner):
        """Test _process_alerts method"""
        # Create a temporary eve.json file with test alerts
        eve_json = os.path.join(suricata_runner.output_dir, "eve.json")
        os.makedirs(os.path.dirname(eve_json), exist_ok=True)

        alerts = [
            {
                "event_type": "alert",
                "timestamp": "2025-04-25T12:00:00.000000",
                "src_ip": "192.168.1.1",
                "src_port": 12345,
                "dest_ip": "10.0.0.1",
                "dest_port": 80,
                "proto": "TCP",
                "alert": {
                    "signature": "Test Alert 1",
                    "action": "alert",
                    "gid": 1,
                    "sid": 1000001,
                    "rev": 1,
                    "category": "Test Category",
                    "severity": 2,
                },
            },
            {
                "event_type": "alert",
                "timestamp": "2025-04-25T12:01:00.000000",
                "src_ip": "192.168.1.2",
                "src_port": 23456,
                "dest_ip": "10.0.0.2",
                "dest_port": 443,
                "proto": "TCP",
                "alert": {
                    "signature": "Test Alert 2",
                    "action": "alert",
                    "gid": 1,
                    "sid": 1000002,
                    "rev": 1,
                    "category": "Test Category",
                    "severity": 1,
                },
            },
        ]

        # Write alerts to eve.json (one per line in NDJSON format)
        with open(eve_json, "w") as f:
            for alert in alerts:
                f.write(json.dumps(alert) + "\n")

        # Process alerts
        suricata_runner._process_alerts()

        # Verify alerts were added to database
        conn = sqlite3.connect(suricata_runner.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM suricata_alerts")
        rows = c.fetchall()

        # Check results
        assert len(rows) == 2

        # Check first alert
        assert rows[0]["signature"] == "Test Alert 1"
        assert rows[0]["src_ip"] == "192.168.1.1"
        assert rows[0]["severity"] == 2

        # Check second alert
        assert rows[1]["signature"] == "Test Alert 2"
        assert rows[1]["src_ip"] == "192.168.1.2"
        assert rows[1]["severity"] == 1

        conn.close()

        # Clean up
        os.unlink(eve_json)

    def test_get_alerts(self, suricata_runner):
        """Test get_alerts method"""
        # First, add some test alerts to the database
        conn = sqlite3.connect(suricata_runner.db_file)
        c = conn.cursor()

        # Sample alerts
        alerts = [
            (
                "2025-04-25T12:00:00.000000",
                "alert",
                "192.168.1.1",
                12345,
                "10.0.0.1",
                80,
                "TCP",
                "alert",
                1,
                1000001,
                1,
                "SSH Brute Force Attempt",
                "Attempted Security",
                3,
                "{}",
                "{}",
            ),
            (
                "2025-04-25T12:01:00.000000",
                "alert",
                "192.168.1.2",
                23456,
                "10.0.0.2",
                443,
                "TCP",
                "alert",
                1,
                1000002,
                1,
                "SQL Injection Attempt",
                "Web Attack",
                2,
                "{}",
                "{}",
            ),
        ]

        # Insert sample alerts
        c.executemany(
            """
            INSERT INTO suricata_alerts
            (timestamp, event_type, src_ip, src_port, dest_ip, dest_port, proto,
             action, gid, sid, rev, signature, category, severity, payload, packet_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            alerts,
        )

        conn.commit()
        conn.close()

        # Test get_alerts without filters
        all_alerts = suricata_runner.get_alerts()
        assert len(all_alerts) == 2

        # Test get_alerts with filters
        ssh_alerts = suricata_runner.get_alerts({"signature": "SSH"})
        assert len(ssh_alerts) == 1
        assert ssh_alerts[0]["signature"] == "SSH Brute Force Attempt"

        # Test with severity filter
        high_severity = suricata_runner.get_alerts({"severity": 3})
        assert len(high_severity) == 1
        assert high_severity[0]["severity"] == 3

        # Test with pagination
        limited_alerts = suricata_runner.get_alerts(limit=1)
        assert len(limited_alerts) == 1

    @patch("subprocess.check_output")
    @patch("subprocess.run")
    def test_stop(self, mock_run, mock_check_output, suricata_runner):
        """Test stop method"""
        # Set up mocks
        mock_check_output.return_value = """
        russellsmith  1234  0.0 /usr/bin/suricata -c /etc/suricata/suricata.yaml -i eth0
        russellsmith  5678  0.0 grep suricata
        """

        # Call stop
        result = suricata_runner.stop()

        # Check result
        assert result is True

        # Verify subprocess calls
        assert mock_check_output.call_count == 1
        assert mock_run.call_count == 1

        # Verify kill command
        kill_args = mock_run.call_args[0][0]
        assert "kill" in kill_args
        assert "1234" in kill_args

    def test_get_status(self, suricata_runner):
        """Test get_status method"""
        # Get status
        status = suricata_runner.get_status()

        # Check status structure
        assert "running" in status
        assert "alert_count" in status
        assert "rules_count" in status
        assert "version" in status
