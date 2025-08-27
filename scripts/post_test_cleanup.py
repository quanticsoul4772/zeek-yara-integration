#!/usr/bin/env python3
"""
post_test_cleanup.py - Cleanup extracted files after Zeek-YARA testing

This script is designed to be called after a Zeek-YARA test run to clean up extracted files
while preserving any important test files. It provides options for automatic cleanup after
tests and can be integrated with your testing workflow.

Author: Russell Smith
Date: April 24, 2025
"""

import argparse
import logging
import os
import sqlite3
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/Users/russellsmith/zeek_yara_integration/logs/post_test_cleanup.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("post_test_cleanup")


def create_directory_if_not_exists(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")


def check_database_before_cleanup(db_path):
    """Check the YARA alerts database to ensure all alerts are properly stored."""
    if not os.path.exists(db_path):
        logger.warning(f"Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the database has the expected structure
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='yara_alerts'"
        )
        if not cursor.fetchone():
            logger.warning("Database doesn't contain the expected 'yara_alerts' table")
            conn.close()
            return False

        # Count recent alerts (last hour)
        cursor.execute(
            "SELECT COUNT(*) FROM yara_alerts WHERE timestamp > datetime('now', '-1 hour')"
        )
        recent_count = cursor.fetchone()[0]
        logger.info(f"Found {recent_count} recent alerts in database")

        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False


def run_cleanup_script():
    """Run the bash cleanup script."""
    cleanup_script = (
        "/Users/russellsmith/zeek_yara_integration/scripts/cleanup_extracted.sh"
    )

    if not os.path.exists(cleanup_script):
        logger.error(f"Cleanup script not found: {cleanup_script}")
        return False

    try:
        result = subprocess.run(
            [cleanup_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        logger.info(f"Cleanup script executed successfully")
        logger.debug(f"Cleanup output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Cleanup script failed with error code {e.returncode}")
        logger.error(f"Error: {e.stderr}")
        return False


def run_full_cleanup(args):
    """Run the complete cleanup process."""
    logger.info("Starting post-test cleanup process")

    # First, ensure all directories exist
    create_directory_if_not_exists("/Users/russellsmith/zeek_yara_integration/logs")

    # Verify database is intact before cleanup if requested
    if args.verify_db:
        logger.info("Verifying database before cleanup")
        db_path = args.db_path
        if not check_database_before_cleanup(db_path):
            if args.force:
                logger.warning(
                    "Database verification failed, but --force is enabled. Continuing with cleanup."
                )
            else:
                logger.error(
                    "Database verification failed. Cleanup aborted. Use --force to override."
                )
                return False

    # Add a delay if specified (useful to ensure all processes have completed)
    if args.delay > 0:
        logger.info(f"Delaying cleanup for {args.delay} seconds")
        time.sleep(args.delay)

    # Run the cleanup script
    success = run_cleanup_script()

    if success:
        logger.info("Post-test cleanup completed successfully")
    else:
        logger.error("Post-test cleanup encountered errors")

    return success


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean up extracted files after Zeek-YARA testing"
    )
    parser.add_argument(
        "--verify-db",
        action="store_true",
        help="Verify database integrity before cleanup",
    )
    parser.add_argument(
        "--db-path",
        default="/Users/russellsmith/zeek_yara_integration/logs/yara_alerts.db",
        help="Path to the YARA alerts database",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force cleanup even if verification fails"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=0,
        help="Delay in seconds before cleanup (default: 0)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    success = run_full_cleanup(args)
    sys.exit(0 if success else 1)
