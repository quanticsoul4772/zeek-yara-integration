#!/usr/bin/env python3
"""
Alert Correlation Orchestrator
Manages the overall alert correlation process
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import AlertDatabaseManager
from .correlation import (
    HashCorrelationStrategy,
    IPCorrelationStrategy,
    TimeProximityCorrelationStrategy,
)
from .retrieval import SuricataAlertRetriever, YaraAlertRetriever


class AlertCorrelator:
    """
    Main alert correlation orchestrator
    Coordinates different correlation strategies and manages the correlation process
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the alert correlator

        Args:
            config (dict): Configuration dictionary
        """
        # Configure logging
        self.logger = logging.getLogger("zeek_yara.alert_correlation")

        # Database configuration
        self.db_file = config.get("DB_FILE", "logs/alerts.db")
        self.correlation_window = config.get(
            "CORRELATION_WINDOW", 300)  # 5 minutes by default
        self.min_alert_confidence = config.get("MIN_ALERT_CONFIDENCE", 70)

        # Initialize database manager
        self.db_manager = AlertDatabaseManager(self.db_file)

        # Initialize alert retrievers
        self.yara_retriever = YaraAlertRetriever()
        self.suricata_retriever = SuricataAlertRetriever()

        # Initialize correlation strategies
        self.correlation_strategies = [
            IPCorrelationStrategy(connection_info_resolver=self._get_connection_info),
            HashCorrelationStrategy(),
            TimeProximityCorrelationStrategy(
                time_window=config.get("TIME_PROXIMITY_WINDOW", 60)),
        ]

    def correlate_alerts(
            self, time_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Correlate alerts from different sources based on various correlation factors

        Args:
            time_window (int, optional): Time window in seconds for correlation

        Returns:
            List of correlated alert groups
        """
        # Use provided time window or default
        window = time_window or self.correlation_window

        try:
            # Calculate the start time for correlation window
            start_time = (datetime.now() -
                          timedelta(seconds=window)).isoformat()

            # Connect to database
            with sqlite3.connect(self.db_file) as conn:
                # Get recent alerts within the time window
                yara_alerts = self.yara_retriever.get_alerts(conn, start_time)
                suricata_alerts = self.suricata_retriever.get_alerts(
                    conn, start_time)

            # Start correlation
            correlated_groups = []

            # Apply all correlation strategies
            for strategy in self.correlation_strategies:
                strategy_groups = strategy.correlate(
                    yara_alerts, suricata_alerts)
                correlated_groups.extend(strategy_groups)

            # Store correlated alerts in database
            self.db_manager.store_correlated_alerts(correlated_groups)

            return correlated_groups

        except Exception as e:
            self.logger.error(f"Error correlating alerts: {e}")
            return []

    def get_correlated_alerts(self,
                              filters: Optional[Dict[str,
                                                     Any]] = None,
                              limit: Optional[int] = None,
                              offset: int = 0) -> List[Dict[str,
                                                            Any]]:
        """
        Retrieve correlated alerts from database

        Args:
            filters (dict, optional): Filtering conditions
            limit (int, optional): Maximum number of results
            offset (int, optional): Number of results to skip

        Returns:
            List of correlated alert dictionaries
        """
        return self.db_manager.get_correlated_alerts(filters, limit, offset)

    def _get_connection_info(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract connection information from an alert
        
        Args:
            alert (Dict): Alert data
            
        Returns:
            Dict containing connection information (IPs, ports, protocol)
        """
        connection_info = {}
        
        # Extract from YARA alerts (via Zeek UID if available)
        if alert.get("source") == "yara" or "zeek_uid" in alert:
            # For YARA alerts, we might need to correlate with Zeek logs
            # For now, return basic info if available
            connection_info = {
                "zeek_uid": alert.get("zeek_uid", ""),
                "file_path": alert.get("file_path", ""),
                "md5": alert.get("md5", ""),
                "sha256": alert.get("sha256", "")
            }
        
        # Extract from Suricata alerts
        elif alert.get("source") == "suricata" or any(key in alert for key in ["src_ip", "dest_ip"]):
            connection_info = {
                "src_ip": alert.get("src_ip", ""),
                "src_port": alert.get("src_port", 0),
                "dest_ip": alert.get("dest_ip", ""),
                "dest_port": alert.get("dest_port", 0),
                "proto": alert.get("proto", "").lower()
            }
        
        return connection_info
    
    def _store_correlated_alerts(self, correlated_groups: List[Dict[str, Any]]):
        """
        Store correlated alerts using the database manager
        
        Args:
            correlated_groups (List[Dict]): List of correlated alert groups
        """
        try:
            self.db_manager.store_correlated_alerts(correlated_groups)
            self.logger.info(f"Stored {len(correlated_groups)} correlated alert groups")
        except Exception as e:
            self.logger.error(f"Error storing correlated alerts: {e}")
            raise

    def initialize(self):
        """
        Initialize the alert correlator
        Sets up database and any necessary configurations
        """
        try:
            # Initialize database
            self.db_manager.initialize_database()

            self.logger.info("Alert Correlator initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing Alert Correlator: {e}")
            raise
