#!/usr/bin/env python3
"""
Correlation Strategy Implementations for Alert Correlation
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import CorrelationStrategy


class IPCorrelationStrategy(CorrelationStrategy):
    """
    Correlation strategy based on IP address matching
    """

    def __init__(self, connection_info_resolver=None):
        """
        Initialize IP correlation strategy

        Args:
            connection_info_resolver (callable, optional): Function to resolve connection info
        """
        self._connection_info_resolver = connection_info_resolver or self._default_connection_info

    def correlate(
        self, yara_alerts: List[Dict[str, Any]], suricata_alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Correlate alerts based on IP addresses

        Args:
            yara_alerts (List[Dict]): List of YARA alerts
            suricata_alerts (List[Dict]): List of Suricata alerts

        Returns:
            List of correlated alert groups
        """
        correlated_groups = []

        # Create lookup for Suricata alerts by source and destination IP
        suricata_by_src_ip = {}
        suricata_by_dst_ip = {}

        for alert in suricata_alerts:
            src_ip = alert.get("src_ip")
            dst_ip = alert.get("dest_ip")

            if src_ip:
                suricata_by_src_ip.setdefault(src_ip, []).append(alert)

            if dst_ip:
                suricata_by_dst_ip.setdefault(dst_ip, []).append(alert)

        # Cross-reference YARA alerts with Suricata alerts
        for yara_alert in yara_alerts:
            # Extract Zeek UID
            zeek_uid = yara_alert.get("zeek_uid")

            # Skip if no Zeek UID is available
            if not zeek_uid or zeek_uid == "unknown_uid":
                continue

            # Look up connection information
            conn_info = self._connection_info_resolver(yara_alert)

            if not conn_info:
                continue

            src_ip = conn_info.get("src_ip")
            dst_ip = conn_info.get("dst_ip")

            matching_alerts = []

            # Match by source IP
            if src_ip and src_ip in suricata_by_src_ip:
                matching_alerts.extend(suricata_by_src_ip[src_ip])

            # Match by destination IP
            if dst_ip and dst_ip in suricata_by_dst_ip:
                matching_alerts.extend(suricata_by_dst_ip[dst_ip])

            # If matches found, create a correlation group
            if matching_alerts:
                # Deduplicate alerts
                unique_alerts = {
                    f"{alert['source']}_{alert['id']}": alert for alert in matching_alerts
                }

                # Create correlation group
                group = {
                    "correlation_id": f"ip_{zeek_uid}_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "correlation_type": "ip_correlation",
                    "primary_alert": yara_alert,
                    "related_alerts": list(unique_alerts.values()),
                    "confidence": 85,
                    "rationale": f"IP correlation between YARA detection and Suricata alerts from same connection {zeek_uid}",
                    "summary": f"Malicious file detected by YARA with correlated network activity from same IP(s)",
                }

                correlated_groups.append(group)

        return correlated_groups

    def _default_connection_info(
            self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Default method to generate connection information

        Args:
            alert (Dict): Alert data

        Returns:
            Optional connection information dictionary
        """
        zeek_uid = alert.get("zeek_uid", "")
        if not zeek_uid or zeek_uid == "unknown_uid":
            return None

        # Generate dummy connection info for testing based on UID
        return {
            "src_ip": f"192.168.1.{hash(zeek_uid) % 254 + 1}",
            "src_port": hash(zeek_uid) % 65535,
            "dst_ip": f"10.0.0.{(hash(zeek_uid) // 256) % 254 + 1}",
            "dst_port": (hash(zeek_uid) // 65536) % 65535,
            "proto": "tcp",
        }


class HashCorrelationStrategy(CorrelationStrategy):
    """
    Correlation strategy based on file hash matching
    """

    def correlate(
        self, yara_alerts: List[Dict[str, Any]], suricata_alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Correlate alerts based on file hashes

        Args:
            yara_alerts (List[Dict]): List of YARA alerts
            suricata_alerts (List[Dict]): List of Suricata alerts

        Returns:
            List of correlated alert groups
        """
        correlated_groups = []

        # Create lookup for YARA alerts by MD5 and SHA256
        yara_by_md5 = {}
        yara_by_sha256 = {}

        for alert in yara_alerts:
            md5 = alert.get("md5")
            sha256 = alert.get("sha256")

            if md5:
                yara_by_md5.setdefault(md5, []).append(alert)

            if sha256:
                yara_by_sha256.setdefault(sha256, []).append(alert)

        # Look for file hash references in Suricata alerts
        for suricata_alert in suricata_alerts:
            # Extract potential file hashes from signature and payload
            signature = suricata_alert.get("signature", "")
            payload_text = json.dumps(suricata_alert.get("payload", {}))

            # Combine text for hash search
            search_text = f"{signature} {payload_text}"

            # Find potential hash matches
            matching_alerts = []

            # Check all MD5 hashes
            matching_alerts.extend(
                alert
                for md5, alerts in yara_by_md5.items()
                if md5 in search_text
                for alert in alerts
            )

            # Check all SHA256 hashes
            matching_alerts.extend(
                alert
                for sha256, alerts in yara_by_sha256.items()
                if sha256 in search_text
                for alert in alerts
            )

            # If matches found, create a correlation group
            if matching_alerts:
                # Deduplicate alerts
                unique_alerts = {
                    f"{alert['source']}_{alert['id']}": alert for alert in matching_alerts
                }

                # Create correlation group
                group = {
                    "correlation_id": f"hash_{suricata_alert['id']}_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "correlation_type": "hash_correlation",
                    "primary_alert": suricata_alert,
                    "related_alerts": list(unique_alerts.values()),
                    "confidence": 90,
                    "rationale": "File hash found in Suricata alert matches YARA detection",
                    "summary": "Suricata detected traffic related to file identified as malicious by YARA",
                }

                correlated_groups.append(group)

        return correlated_groups


class TimeProximityCorrelationStrategy(CorrelationStrategy):
    """
    Correlation strategy based on time proximity
    """

    def __init__(self, time_window: int = 60):
        """
        Initialize time proximity correlation strategy

        Args:
            time_window (int, optional): Time window in seconds. Defaults to 60.
        """
        self.time_window = time_window

    def correlate(
        self, yara_alerts: List[Dict[str, Any]], suricata_alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Correlate alerts based on time proximity

        Args:
            yara_alerts (List[Dict]): List of YARA alerts
            suricata_alerts (List[Dict]): List of Suricata alerts

        Returns:
            List of correlated alert groups
        """
        correlated_groups = []

        # Parse timestamps and sort alerts
        for alert in yara_alerts:
            try:
                alert["datetime"] = datetime.fromisoformat(alert["timestamp"])
            except BaseException:
                alert["datetime"] = datetime.now()

        for alert in suricata_alerts:
            try:
                alert["datetime"] = datetime.fromisoformat(alert["timestamp"])
            except BaseException:
                alert["datetime"] = datetime.now()

        # Sort alerts by timestamp
        yara_alerts.sort(key=lambda x: x["datetime"])
        suricata_alerts.sort(key=lambda x: x["datetime"])

        # Find clusters of alerts within the time window
        for yara_alert in yara_alerts:
            yara_time = yara_alert["datetime"]

            # Find Suricata alerts within the time window
            matching_alerts = [suricata_alert for suricata_alert in suricata_alerts if abs(
                (yara_time - suricata_alert["datetime"]).total_seconds()) <= self.time_window]

            # If matches found, create a correlation group
            if matching_alerts:
                # Create correlation group
                group = {
                    "correlation_id": f"time_{yara_alert['id']}_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "correlation_type": "time_proximity",
                    "primary_alert": yara_alert,
                    "related_alerts": matching_alerts,
                    "confidence": 75,  # Lower confidence for time-based correlation
                    "rationale": f"Temporal correlation between YARA detection and Suricata alerts within {self.time_window} seconds",
                    "summary": "Malicious file detected by YARA with correlated network activity in close temporal proximity",
                }

                correlated_groups.append(group)

        return correlated_groups
