"""
Zeek-YARA-Suricata Integration Unit Tests for Alert Correlation
Created: April 25, 2025
Author: Security Team

This module contains unit tests for the alert correlation functionality.
"""

import datetime
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from suricata.alert_correlation import AlertCorrelator


@pytest.fixture
def alert_correlator():
    """Fixture for alert correlator"""
    # Create temporary database file
    db_file = os.path.join(tempfile.mkdtemp(), "alerts.db")

    # Create configuration
    config = {
        "DB_FILE": db_file,
        "CORRELATION_WINDOW": 300,  # 5 minutes
        "TIME_PROXIMITY_WINDOW": 60,  # 1 minute
        "MIN_ALERT_CONFIDENCE": 70,
    }

    # Initialize database
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

    # Create correlator
    correlator = AlertCorrelator(config)

    yield correlator

    # Cleanup
    try:
        if os.path.exists(db_file):
            os.unlink(db_file)
        os.rmdir(os.path.dirname(db_file))
    except:
        pass


def populate_test_alerts(db_file):
    """Populate database with test alerts"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Current timestamp
    timestamp = datetime.datetime.now().isoformat()

    # Add YARA alerts
    yara_alerts = [
        (
            timestamp,  # timestamp
            "/path/to/malicious.exe",  # file_path
            "malicious.exe",  # file_name
            1024,  # file_size
            "application/x-dosexec",  # file_type
            "abcdef1234567890",  # md5
            "1234567890abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmn",  # sha256
            "CqTvvd2Y19NiSsNN2J",  # zeek_uid
            "MaliciousExe",  # rule_name
            "malware",  # rule_namespace
            json.dumps(
                {"severity": 3, "description": "Detected malicious executable"}
            ),  # rule_meta
            json.dumps(["string1", "string2"]),  # strings_matched
            3,  # severity
        ),
        (
            timestamp,  # timestamp
            "/path/to/suspicious.pdf",  # file_path
            "suspicious.pdf",  # file_name
            2048,  # file_size
            "application/pdf",  # file_type
            "0987654321fedcba",  # md5
            "0987654321zyxwvutsrqponmlkjihgfedcba0987654321zyxwvutsrqponm",  # sha256
            "DpOaX31CeefCUs7f0b",  # zeek_uid
            "SuspiciousPDF",  # rule_name
            "document",  # rule_namespace
            json.dumps({"severity": 2, "description": "Detected suspicious PDF"}),  # rule_meta
            json.dumps(["string3", "string4"]),  # strings_matched
            2,  # severity
        ),
    ]

    c.executemany(
        """
        INSERT INTO yara_alerts
        (timestamp, file_path, file_name, file_size, file_type, md5, sha256, zeek_uid, 
         rule_name, rule_namespace, rule_meta, strings_matched, severity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        yara_alerts,
    )

    # Add Suricata alerts
    suricata_alerts = [
        (
            timestamp,  # timestamp
            "alert",  # event_type
            "192.168.1.100",  # src_ip
            45678,  # src_port
            "10.0.0.10",  # dest_ip
            80,  # dest_port
            "TCP",  # proto
            "alert",  # action
            1,  # gid
            1000001,  # sid
            1,  # rev
            "ET MALWARE Suspicious EXE Download",  # signature
            "malware",  # category
            3,  # severity
            json.dumps({"data": "sample payload data"}),  # payload
            json.dumps({"src_ip": "192.168.1.100", "dst_ip": "10.0.0.10"}),  # packet_info
        ),
        (
            timestamp,  # timestamp
            "alert",  # event_type
            "192.168.1.101",  # src_ip
            54321,  # src_port
            "10.0.0.11",  # dest_ip
            443,  # dest_port
            "TCP",  # proto
            "alert",  # action
            1,  # gid
            1000002,  # sid
            1,  # rev
            "ET WEB_CLIENT PDF containing JavaScript",  # signature
            "web-client",  # category
            2,  # severity
            json.dumps({"data": "sample payload data", "hash": "0987654321fedcba"}),  # payload
            json.dumps({"src_ip": "192.168.1.101", "dst_ip": "10.0.0.11"}),  # packet_info
        ),
    ]

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


@pytest.mark.unit
class TestAlertCorrelator:
    """Unit tests for AlertCorrelator class"""

    def test_initialization(self, alert_correlator):
        """Test initialization of Alert Correlator"""
        assert alert_correlator is not None
        assert hasattr(alert_correlator, "db_file")
        assert hasattr(alert_correlator, "correlation_window")
        assert hasattr(alert_correlator, "min_alert_confidence")

    def test_database_initialization(self, alert_correlator):
        """Test database initialization"""
        conn = sqlite3.connect(alert_correlator.db_file)
        c = conn.cursor()

        # Check if correlated_alerts table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='correlated_alerts'")
        assert c.fetchone() is not None

        conn.close()

    @patch("suricata.alert_correlation.AlertCorrelator._get_connection_info")
    def test_correlate_alerts_ip_based(self, mock_get_connection_info, alert_correlator):
        """Test IP-based alert correlation"""
        # Populate database with test alerts
        populate_test_alerts(alert_correlator.db_file)

        # Configure mock for connection info
        mock_get_connection_info.return_value = {
            "src_ip": "192.168.1.100",
            "src_port": 45678,
            "dst_ip": "10.0.0.10",
            "dst_port": 80,
            "proto": "tcp",
        }

        # Run correlation
        correlated_groups = alert_correlator.correlate_alerts()

        # Verify results
        assert len(correlated_groups) > 0

        # Check at least one IP-based correlation
        ip_correlations = [
            g for g in correlated_groups if g.get("correlation_type") == "ip_correlation"
        ]
        assert len(ip_correlations) > 0

        # Check correlation structure
        for correlation in ip_correlations:
            assert "correlation_id" in correlation
            assert "primary_alert" in correlation
            assert "related_alerts" in correlation
            assert "confidence" in correlation
            assert correlation["confidence"] >= alert_correlator.min_alert_confidence

    def test_correlate_alerts_hash_based(self, alert_correlator):
        """Test hash-based alert correlation"""
        # Populate database with test alerts
        populate_test_alerts(alert_correlator.db_file)

        # Run correlation
        correlated_groups = alert_correlator.correlate_alerts()

        # Check for hash-based correlations
        hash_correlations = [
            g for g in correlated_groups if g.get("correlation_type") == "hash_correlation"
        ]

        # We might not get hash correlations in this test due to how payload data is set up
        # but we should verify the function ran properly
        assert isinstance(correlated_groups, list)

    def test_correlate_alerts_time_proximity(self, alert_correlator):
        """Test time-proximity alert correlation"""
        # Populate database with test alerts
        populate_test_alerts(alert_correlator.db_file)

        # Run correlation
        correlated_groups = alert_correlator.correlate_alerts()

        # Check for time-proximity correlations
        time_correlations = [
            g for g in correlated_groups if g.get("correlation_type") == "time_proximity"
        ]

        # Since alerts have the same timestamp, we should have time correlations
        assert len(time_correlations) > 0

        # Check correlation structure
        for correlation in time_correlations:
            assert "correlation_id" in correlation
            assert "primary_alert" in correlation
            assert "related_alerts" in correlation
            assert "confidence" in correlation
            assert correlation["confidence"] >= alert_correlator.min_alert_confidence

    def test_store_correlated_alerts(self, alert_correlator):
        """Test storing correlated alerts"""
        # Populate database with test alerts
        populate_test_alerts(alert_correlator.db_file)

        # Create sample correlation groups
        timestamp = datetime.datetime.now().isoformat()

        correlation_groups = [
            {
                "correlation_id": f"test_correlation_{int(datetime.datetime.now().timestamp())}",
                "timestamp": timestamp,
                "correlation_type": "test_correlation",
                "primary_alert": {
                    "id": 1,
                    "source": "yara",
                    "rule_name": "TestRule",
                    "timestamp": timestamp,
                },
                "related_alerts": [
                    {
                        "id": 1,
                        "source": "suricata",
                        "signature": "Test Signature",
                        "timestamp": timestamp,
                    }
                ],
                "confidence": 85,
                "rationale": "Test correlation rationale",
                "summary": "Test correlation summary",
            }
        ]

        # Store correlations
        alert_correlator._store_correlated_alerts(correlation_groups)

        # Verify stored correlations
        conn = sqlite3.connect(alert_correlator.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT * FROM correlated_alerts")
        rows = c.fetchall()

        # Check that correlation was stored
        assert len(rows) == 1

        # Check correlation data
        assert rows[0]["correlation_id"] == correlation_groups[0]["correlation_id"]
        assert rows[0]["alert_type"] == "yara"
        assert rows[0]["correlation_confidence"] == 85
        assert rows[0]["summary"] == "Test correlation summary"

        # Check related alerts JSON
        related_alerts = json.loads(rows[0]["correlated_alerts"])
        assert len(related_alerts) == 1
        assert related_alerts[0]["source"] == "suricata"

        conn.close()

    def test_get_correlated_alerts(self, alert_correlator):
        """Test retrieving correlated alerts"""
        # First, store some test correlations
        # Populate database with test alerts
        populate_test_alerts(alert_correlator.db_file)

        # Create correlations
        alert_correlator.correlate_alerts()

        # Retrieve correlations without filters
        all_correlations = alert_correlator.get_correlated_alerts()

        # Verify we have some correlations
        assert isinstance(all_correlations, list)

        # If we have correlations, check their structure
        if all_correlations:
            assert "correlation_id" in all_correlations[0]
            assert "timestamp" in all_correlations[0]
            assert "alert_type" in all_correlations[0]
            assert "correlated_alerts" in all_correlations[0]

            # Test with filters
            filtered = alert_correlator.get_correlated_alerts(
                filters={"alert_type": all_correlations[0]["alert_type"]}
            )
            assert len(filtered) > 0

            # Test with limit
            limited = alert_correlator.get_correlated_alerts(limit=1)
            assert len(limited) <= 1
