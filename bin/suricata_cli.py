#!/usr/bin/env python3
"""
Suricata CLI Tool for Zeek-YARA Integration
Created: April 25, 2025
Author: Security Team

This script provides a command-line interface for Suricata management.
"""

import argparse
import logging
import os
import sys
import time

from config.config import Config
from suricata.alert_correlation import AlertCorrelator
from suricata.suricata_integration import SuricataRunner

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import application components

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("suricata_cli")


# Parse arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Suricata CLI for Zeek-YARA Integration")

    # Main operation modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--interface", "-i", help="Monitor network interface")
    mode_group.add_argument("--pcap", "-r", help="Analyze PCAP file")
    mode_group.add_argument("--status", action="store_true", help="Show Suricata status")
    mode_group.add_argument("--update-rules", action="store_true", help="Update Suricata rules")
    mode_group.add_argument("--stop", action="store_true", help="Stop running Suricata instance")
    mode_group.add_argument("--correlate", action="store_true", help="Correlate alerts")

    # Additional options
    parser.add_argument("--config", help="Custom configuration file")
    parser.add_argument(
        "--duration", type=int, default=0, help="Monitoring duration in seconds (0 = continuous)"
    )
    parser.add_argument(
        "--correlation-window",
        type=int,
        default=300,
        help="Alert correlation time window in seconds",
    )

    return parser.parse_args()


# Main function
def main():
    args = parse_args()

    # Load configuration
    if args.config:
        config = Config.load_config(args.config)
    else:
        config = Config.load_config()

    # Initialize components
    suricata_runner = SuricataRunner(config)
    alert_correlator = AlertCorrelator(config)

    try:
        # Handle different operation modes
        if args.interface:
            logger.info(f"Starting Suricata on interface: {args.interface}")
            success = suricata_runner.run_live(args.interface, args.duration)

            if success:
                if args.duration > 0:
                    logger.info(
                        f"Completed monitoring on {args.interface} for {args.duration} seconds"
                    )
                else:
                    logger.info(f"Suricata started in background mode on {args.interface}")
                    logger.info("Press Ctrl+C to stop when finished")

                    try:
                        while True:
                            time.sleep(10)
                    except KeyboardInterrupt:
                        logger.info("Stopping Suricata...")
                        suricata_runner.stop()
            else:
                logger.error("Failed to start Suricata")
                return 1

        elif args.pcap:
            logger.info(f"Analyzing PCAP file: {args.pcap}")

            if not os.path.exists(args.pcap):
                logger.error(f"PCAP file not found: {args.pcap}")
                return 1

            success = suricata_runner.run_pcap(args.pcap)

            if success:
                logger.info(f"PCAP analysis completed: {args.pcap}")

                # Get alert count
                alerts = suricata_runner.get_alerts()
                logger.info(f"Found {len(alerts)} alerts")

                # Print summary of top alerts
                if alerts:
                    logger.info("Top alerts:")
                    alert_counts = {}

                    for alert in alerts:
                        signature = alert.get("signature", "Unknown")
                        if signature in alert_counts:
                            alert_counts[signature] += 1
                        else:
                            alert_counts[signature] = 1

                    for signature, count in sorted(
                        alert_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]:
                        logger.info(f"  {signature}: {count}")
            else:
                logger.error("Failed to analyze PCAP file")
                return 1

        elif args.status:
            status = suricata_runner.get_status()

            logger.info("Suricata Status:")
            logger.info(f"  Running: {status.get('running', False)}")
            logger.info(f"  Version: {status.get('version', 'Unknown')}")
            logger.info(f"  PID: {status.get('pid', 'None')}")
            logger.info(f"  Alert count: {status.get('alert_count', 0)}")
            logger.info(f"  Rules count: {status.get('rules_count', 0)}")

        elif args.update_rules:
            logger.info("Updating Suricata rules...")
            success = suricata_runner.update_rules()

            if success:
                logger.info("Suricata rules updated successfully")
            else:
                logger.error("Failed to update Suricata rules")
                return 1

        elif args.stop:
            logger.info("Stopping Suricata...")
            success = suricata_runner.stop()

            if success:
                logger.info("Suricata stopped successfully")
            else:
                logger.error("Failed to stop Suricata or Suricata was not running")
                return 1

        elif args.correlate:
            logger.info(
                 f"Correlating alerts with time window: {args.correlation_window} seconds"
            )
            correlated_groups = alert_correlator.correlate_alerts(args.correlation_window)

            if correlated_groups:
                logger.info(f"Found {len(correlated_groups)} correlated alert groups")

                # Print summary of correlated alerts
                for i, group in enumerate(correlated_groups[:5], 1):
                    logger.info(f"Group {i}:")
                    logger.info(
                         f" Correlation type: {group.get( 'correlation_type', 'unknown')}"
                    )
                    logger.info(f"  Confidence: {group.get('confidence', 0)}%")
                    logger.info(
                         f" Primary alert: {group.get( 'primary_alert', {}).get( 'source', 'unknown')} - {group.get( 'primary_alert', {}).get( 'rule_name', 'unknown')}"
                    )
                    logger.info(f"  Related alerts: {len(group.get('related_alerts', []))}")

                if len(correlated_groups) > 5:
                    logger.info(f"And {len(correlated_groups) - 5} more groups...")
            else:
                logger.info("No correlated alert groups found")

        return 0

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
