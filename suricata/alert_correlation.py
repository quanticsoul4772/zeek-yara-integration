#!/usr/bin/env python3
"""
Alert Correlation Module for Zeek-YARA-Suricata Integration
Created: April 25, 2025
Author: Security Team

This module correlates alerts from different security tools (Zeek, YARA, Suricata)
to provide comprehensive threat detection.
"""

import ipaddress
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class AlertCorrelator:
    """Alert correlation engine for multi-source security alerts"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the alert correlator.

        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.db_file = config.get("DB_FILE", "logs/alerts.db")
        self.correlation_window = config.get("CORRELATION_WINDOW", 300)  # 5 minutes by default
        self.min_alert_confidence = config.get("MIN_ALERT_CONFIDENCE", 70)
        self.logger = logging.getLogger("zeek_yara.alert_correlation")

        # Initialize database for correlated alerts
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database for correlated alerts"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()

            # Create correlated alerts table
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

            # Create YARA alerts table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS yara_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    file_path TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    file_type TEXT,
                    md5 TEXT,
                    sha256 TEXT,
                    zeek_uid TEXT,
                    rule_name TEXT,
                    rule_namespace TEXT,
                    rule_meta TEXT,
                    strings_matched TEXT,
                    severity INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_correlation_id ON correlated_alerts(correlation_id)"
            )
            c.execute("CREATE INDEX IF NOT EXISTS idx_alert_type ON correlated_alerts(alert_type)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_yara_timestamp ON yara_alerts(timestamp)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_yara_rule_name ON yara_alerts(rule_name)")

            conn.commit()
            conn.close()

            self.logger.info("Correlated alerts database initialized")

        except Exception as e:
            self.logger.error(f"Error initializing correlated alerts database: {e}")

    def correlate_alerts(self, time_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Correlate alerts from different sources based on various correlation factors.

        Args:
            time_window (int, optional): Time window in seconds for correlation

        Returns:
            list: List of correlated alert groups
        """
        # Use provided time window or default
        window = time_window or self.correlation_window

        try:
            # Calculate the start time for correlation window
            start_time = (datetime.now() - timedelta(seconds=window)).isoformat()

            # Connect to database
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row

            # Get recent alerts within the time window
            yara_alerts = self._get_yara_alerts(conn, start_time)
            suricata_alerts = self._get_suricata_alerts(conn, start_time)

            # Start correlation
            correlated_groups = []

            # Correlation steps:
            # 1. IP-based correlation
            ip_groups = self._correlate_by_ip(yara_alerts, suricata_alerts)
            correlated_groups.extend(ip_groups)

            # 2. File hash correlation
            hash_groups = self._correlate_by_hash(yara_alerts, suricata_alerts)
            correlated_groups.extend(hash_groups)

            # 3. Time-proximity correlation
            time_groups = self._correlate_by_time_proximity(yara_alerts, suricata_alerts)
            correlated_groups.extend(time_groups)

            # Store correlated alerts in database
            self._store_correlated_alerts(correlated_groups)

            conn.close()
            return correlated_groups

        except Exception as e:
            self.logger.error(f"Error correlating alerts: {e}")
            return []

    def _get_yara_alerts(self, conn: sqlite3.Connection, start_time: str) -> List[Dict[str, Any]]:
        """
        Get recent YARA alerts from database.

        Args:
            conn (sqlite3.Connection): Database connection
            start_time (str): Start time in ISO format

        Returns:
            list: List of YARA alerts
        """
        try:
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM yara_alerts
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (start_time,),
            )

            alerts = []
            for row in c.fetchall():
                alert = dict(row)

                # Parse JSON fields
                try:
                    if isinstance(alert.get("rule_meta"), str):
                        alert["rule_meta"] = json.loads(alert["rule_meta"])
                    if isinstance(alert.get("strings_matched"), str):
                        alert["strings_matched"] = json.loads(alert["strings_matched"])
                except BaseException:
                    # Set defaults if JSON parsing fails
                    if isinstance(alert.get("rule_meta"), str):
                        alert["rule_meta"] = {}
                    if isinstance(alert.get("strings_matched"), str):
                        alert["strings_matched"] = []

                # Add alert source
                alert["source"] = "yara"
                alerts.append(alert)

            return alerts

        except Exception as e:
            self.logger.error(f"Error retrieving YARA alerts: {e}")
            return []

    def _get_suricata_alerts(
        self, conn: sqlite3.Connection, start_time: str
    ) -> List[Dict[str, Any]]:
        """
        Get recent Suricata alerts from database.

        Args:
            conn (sqlite3.Connection): Database connection
            start_time (str): Start time in ISO format

        Returns:
            list: List of Suricata alerts
        """
        try:
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM suricata_alerts
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (start_time,),
            )

            alerts = []
            for row in c.fetchall():
                alert = dict(row)

                # Parse JSON fields
                try:
                    if isinstance(alert.get("payload"), str):
                        alert["payload"] = json.loads(alert["payload"])
                    if isinstance(alert.get("packet_info"), str):
                        alert["packet_info"] = json.loads(alert["packet_info"])
                except BaseException:
                    # Set defaults if JSON parsing fails
                    if isinstance(alert.get("payload"), str):
                        alert["payload"] = {}
                    if isinstance(alert.get("packet_info"), str):
                        alert["packet_info"] = {}

                # Add alert source
                alert["source"] = "suricata"
                alerts.append(alert)

            return alerts

        except Exception as e:
            self.logger.error(f"Error retrieving Suricata alerts: {e}")
            return []
