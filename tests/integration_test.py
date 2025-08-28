#!/usr/bin/env python3
"""
Zeek-YARA Integration Test
Created: April 24, 2025
Author: Security Team

This script performs an end-to-end test of the Zeek-YARA integration.
"""

import argparse
import logging
import os
import shutil
import sys
import time

from PLATFORM.config.config import get_config
from PLATFORM.core.database import DatabaseManager
from PLATFORM.core.scanner import MultiThreadScanner, SingleThreadScanner
from PLATFORM.utils.logging_utils import setup_logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Zeek-YARA Integration Test",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--config", "-c", help="Config file to use")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--multi-threaded", "-m", action="store_true", help="Use multi-threaded scanner"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean extracted files directory before testing",
    )

    return parser.parse_args()


def run_test(config, use_multi_threaded=False, verbose=False):
    """Run the integration test"""
    logger = logging.getLogger("integration_test")

    # Set up paths
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    extract_dir = config["EXTRACT_DIR"]
    test_file = os.path.join(project_dir, "tests", "test_eicar.txt")

    # Ensure test file exists
    if not os.path.exists(test_file):
        logger.error(f"Test file not found: {test_file}")
        return False

    # Create scanner
    if use_multi_threaded:
        logger.info("Using multi-threaded scanner")
        scanner = MultiThreadScanner(config)
    else:
        logger.info("Using single-threaded scanner")
        scanner = SingleThreadScanner(config)

    # Copy test file to extract directory
    test_file_dest = os.path.join(extract_dir, "test_eicar.txt")
    logger.info(f"Copying test file to {test_file_dest}")
    shutil.copy(test_file, test_file_dest)

    # Give a moment for the file system events to propagate
    time.sleep(1)

    # Scan the file
    logger.info("Scanning test file")
    result = scanner.scan_file(test_file_dest)

    if result.get("matched", False):
        logger.info("Test file successfully matched")

        # Check database
        db_manager = DatabaseManager(config["DB_FILE"])
        alerts = db_manager.get_alerts(filters={"file_name": "test_eicar.txt"})

        if alerts:
            logger.info(f"Database alert created successfully - ID: {alerts[0]['id']}")

            if verbose:
                logger.info("Alert details:")
                for key, value in alerts[0].items():
                    logger.info(f"  {key}: {value}")

            return True
        else:
            logger.error("No database alert found for test file")
            return False
    else:
        if result.get("error"):
            logger.error(f"Error scanning test file: {result.get('error')}")
        else:
            logger.error("Test file did not match any rules")
        return False


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_args()

    # Load configuration
    config = get_config(args.config)

    # Set up logging
    config["LOG_LEVEL"] = "DEBUG" if args.verbose else "INFO"
    logger = setup_logging(config, "integration_test")

    # Clean extracted files directory if requested
    if args.clean and os.path.exists(config["EXTRACT_DIR"]):
        logger.info(f"Cleaning extract directory: {config['EXTRACT_DIR']}")
        for filename in os.listdir(config["EXTRACT_DIR"]):
            file_path = os.path.join(config["EXTRACT_DIR"], filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"Error deleting {file_path}: {e}")

    # Run the test
    logger.info("Starting integration test")
    success = run_test(
        config, use_multi_threaded=args.multi_threaded, verbose=args.verbose
    )

    if success:
        logger.info("Integration test passed!")
        return 0
    else:
        logger.error("Integration test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
