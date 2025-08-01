#!/usr/bin/env python3
"""
Zeek-YARA Integration CLI
Created: April 24, 2025
Author: Security Team

Command-line interface for the Zeek-YARA scanner.
"""

import argparse
import json
import logging
import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.config import get_config, save_config
from core.scanner import MultiThreadScanner, SingleThreadScanner
from utils.logging_utils import setup_logging


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="YARA Scanner for Zeek file extraction",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Scanner type selection
    scanner_group = parser.add_argument_group("Scanner Options")
    scanner_group.add_argument(
        "--multi-threaded",
        "-mt",
        action="store_true",
        help="Use multi-threaded scanner instead of single-threaded",
    )
    scanner_group.add_argument(
        "--threads",
        "-t",
        type=int,
        default=2,
        help="Number of scanner threads (for multi-threaded scanner)",
    )

    # File and directory options
    file_group = parser.add_argument_group("File Options")
    file_group.add_argument("--extract-dir", "-d", help="Directory to monitor for extracted files")
    file_group.add_argument("--max-size", "-m", type=int, help="Maximum file size to scan in bytes")
    file_group.add_argument(
        "--scan-file", "-f", help="Scan a single file instead of monitoring a directory"
    )
    file_group.add_argument(
        "--scan-dir", "-s", help="Scan all files in a directory once (no monitoring)"
    )

    # YARA rule options
    rule_group = parser.add_argument_group("YARA Rule Options")
    rule_group.add_argument("--rules-dir", "-r", help="YARA rules directory")
    rule_group.add_argument("--rules-file", "-i", help="YARA rules index file")
    rule_group.add_argument(
        "--update-interval", type=int, help="YARA rules update interval in seconds"
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("--log-file", "-l", help="Log file path")
    output_group.add_argument("--db-file", "-b", help="SQLite database file path")
    output_group.add_argument("--quiet", "-q", action="store_true", help="Suppress console output")
    output_group.add_argument("--debug", action="store_true", help="Enable debug logging")
    output_group.add_argument("--json", action="store_true", help="Output logs in JSON format")

    # Config options
    config_group = parser.add_argument_group("Configuration Options")
    config_group.add_argument("--config", "-c", help="Load configuration from file")
    config_group.add_argument("--save-config", help="Save current configuration to file")

    return parser.parse_args()


def main():
    """Main entry point"""
    # Parse command-line arguments
    args = parse_args()

    # Load configuration
    config = get_config(args.config)

    # Override config with command-line arguments
    if args.extract_dir:
        config["EXTRACT_DIR"] = args.extract_dir
    if args.rules_dir:
        config["RULES_DIR"] = args.rules_dir
    if args.rules_file:
        config["RULES_INDEX"] = args.rules_file
    if args.log_file:
        config["LOG_FILE"] = args.log_file
    if args.db_file:
        config["DB_FILE"] = args.db_file
    if args.max_size:
        config["MAX_FILE_SIZE"] = args.max_size
    if args.update_interval:
        config["SCAN_INTERVAL"] = args.update_interval
    if args.threads:
        config["THREADS"] = args.threads
    if args.quiet:
        config["LOG_CONSOLE"] = False
    if args.debug:
        config["LOG_LEVEL"] = "DEBUG"
    if args.json:
        config["LOG_JSON"] = True

    # Save configuration if requested
    if args.save_config:
        if save_config(config, args.save_config):
            print(f"Configuration saved to {args.save_config}")
        else:
            print(f"Error saving configuration to {args.save_config}")

    # Set up logging
    logger = setup_logging(config)
    logger.info(f"Zeek-YARA Scanner starting")
    logger.debug(f"Using configuration: {json.dumps(config, indent=2)}")

    try:
        # Initialize appropriate scanner
        if args.multi_threaded:
            logger.info(f"Initializing multi-threaded scanner with {config['THREADS']} threads")
            scanner = MultiThreadScanner(config)
        else:
            logger.info("Initializing single-threaded scanner")
            scanner = SingleThreadScanner(config)

        # Handle different operating modes
        if args.scan_file:
            # Scan a single file
            logger.info(f"Scanning single file: {args.scan_file}")
            result = scanner.scan_file(args.scan_file)

            if result.get("matched", False):
                logger.info(f"YARA match found in {args.scan_file}")
                for match in result.get("matches", []):
                    logger.info(f"Rule: {match.get('namespace', '')}.{match.get('rule', '')}")
            else:
                logger.info(f"No YARA matches found in {args.scan_file}")

            if result.get("error"):
                logger.warning(f"Error scanning file: {result.get('error')}")

        elif args.scan_dir:
            # Scan all files in a directory (non-monitoring mode)
            logger.info(f"Scanning directory: {args.scan_dir}")
            results = scanner.scan_directory(args.scan_dir)

            logger.info(
                f"Directory scan complete: {results.get('scanned', 0)} files scanned, "
                f"{results.get('matched', 0)} matches found"
            )

            if results.get("error"):
                logger.warning(f"Error scanning directory: {results.get('error')}")

        else:
            # Start monitoring mode
            logger.info(f"Starting monitoring mode")

            if scanner.start_monitoring():
                try:
                    # Main event loop for monitoring
                    logger.info("Monitoring for files. Press Ctrl+C to stop.")

                    # Monitor for files
                    while True:
                        # Print status if multi-threaded
                        if args.multi_threaded and isinstance(scanner, MultiThreadScanner):
                            queue_size = scanner.get_queue_size()
                            if queue_size > 0:
                                logger.info(f"Current queue size: {queue_size} files")

                        # Check if rules need updating
                        if scanner.update_rules():
                            logger.info("YARA rules updated")

                        # Sleep before next check
                        time.sleep(10)

                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received, shutting down...")
                finally:
                    scanner.stop_monitoring()
            else:
                logger.error("Failed to start monitoring")

    except Exception as e:
        logger.error(f"Error running scanner: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
