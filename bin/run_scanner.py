#!/usr/bin/env python3
"""
Standalone YARA Scanner Script
Created: April 25, 2025
Author: Security Team

This script starts the YARA scanner for monitoring extracted files.
"""

import argparse
import logging
import os
import sys
import time

from config.config import Config
from core.scanner import MultiThreadScanner, SingleThreadScanner

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import application components

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.expanduser("~/zeek_yara_integration/logs/yara_scan.log")
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("yara_scanner")


def main():
    parser = argparse.ArgumentParser(description="YARA Scanner for Zeek Integration")
    parser.add_argument("--config", default=None, help="Path to configuration file")
    parser.add_argument(
        "--multi-threaded", action="store_true", help="Use multi-threaded scanning"
    )
    parser.add_argument(
        "--threads", type=int, default=2, help="Number of scanner threads"
    )
    args = parser.parse_args()

    # Load configuration
    if args.config:
        config = Config.load_config(args.config)
    else:
        config = Config.load_config()

    # Set thread count if multi-threaded
    if args.multi_threaded:
        config["THREADS"] = args.threads

    # Initialize appropriate scanner
    if args.multi_threaded or config.get("MULTI_THREADED", False):
        logger.info(
            f"Starting multi-threaded scanner with {config.get('THREADS', 2)} threads"
        )
        scanner = MultiThreadScanner(config)
    else:
        logger.info("Starting single-threaded scanner")
        scanner = SingleThreadScanner(config)

    # Start monitoring
    try:
        logger.info(f"Monitoring directory: {config.get('EXTRACT_DIR')}")
        scanner.start_monitoring()

        # Keep running until interrupted
        while True:
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("Stopping scanner...")
        scanner.stop_monitoring()
        logger.info("Scanner stopped")

    except Exception as e:
        logger.error(f"Error running scanner: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
