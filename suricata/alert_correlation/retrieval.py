#!/usr/bin/env python3
"""
Alert Retrieval Strategies for different alert sources
"""

import json
import sqlite3
from typing import Any, Dict, List

from .base import AlertRetriever


class YaraAlertRetriever(AlertRetriever):
    """Retrieves YARA alerts from the database"""

    def get_alerts(self, conn: sqlite3.Connection,
                   start_time: str) -> List[Dict[str, Any]]:
        """
        Retrieve YARA alerts from database

        Args:
            conn (sqlite3.Connection): Database connection
            start_time (str): Start time for retrieving alerts

        Returns:
            List of YARA alerts
        """
        try:
            # Set row factory to get results as dictionaries
            original_row_factory = conn.row_factory
            conn.row_factory = sqlite3.Row
            
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
                        alert["strings_matched"] = json.loads(
                            alert["strings_matched"])
                except BaseException:
                    # Set defaults if JSON parsing fails
                    if isinstance(alert.get("rule_meta"), str):
                        alert["rule_meta"] = {}
                    if isinstance(alert.get("strings_matched"), str):
                        alert["strings_matched"] = []

                # Add alert source
                alert["source"] = "yara"
                alerts.append(alert)

            # Restore original row factory
            conn.row_factory = original_row_factory
            return alerts

        except Exception as e:
            raise RuntimeError(f"Error retrieving YARA alerts: {e}")


class SuricataAlertRetriever(AlertRetriever):
    """Retrieves Suricata alerts from the database"""

    def get_alerts(self, conn: sqlite3.Connection,
                   start_time: str) -> List[Dict[str, Any]]:
        """
        Retrieve Suricata alerts from database

        Args:
            conn (sqlite3.Connection): Database connection
            start_time (str): Start time for retrieving alerts

        Returns:
            List of Suricata alerts
        """
        try:
            # Set row factory to get results as dictionaries
            original_row_factory = conn.row_factory
            conn.row_factory = sqlite3.Row
            
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

            # Restore original row factory
            conn.row_factory = original_row_factory
            return alerts

        except Exception as e:
            raise RuntimeError(f"Error retrieving Suricata alerts: {e}")
