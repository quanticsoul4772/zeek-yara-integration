#!/usr/bin/env python3
"""
Zeek-YARA Integration Test Framework Runner
Created: April 24, 2025
Author: Russell Smith

This script runs the testing framework for the Zeek-YARA integration.
"""

import argparse
import json
import logging
import os
import sys
import time

from config.config import Config
from tests.frameworks.test_cases import (
    create_test_suites,
)
from tests.frameworks.test_framework import CustomTestRunner

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import configuration

# Import testing framework


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Zeek-YARA Integration Test Framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--config", "-c", help="Path to config file")

    parser.add_argument(
        "--output-dir", "-o", default="test_results", help="Directory for test results"
    )

    parser.add_argument(
        "--test-type",
        choices=["unit", "integration", "performance", "all"],
        default="all",
        help="Type of tests to run",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def setup_logging(verbose=False):
    """Set up logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join("logs", "test_framework.log")),
            logging.StreamHandler(),
        ],
    )

    return logging.getLogger("test_framework")


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_args()

    # Set up logging
    logger = setup_logging(args.verbose)

    # Load configuration
    if args.config:
        config = Config.load_config(args.config)
    else:
        config = Config.load_config()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Run tests
    test_runner = CustomTestRunner(output_dir=args.output_dir)

    # Create test suites
    for suite in create_test_suites(config):
        # Filter suites by test type if specified
        if args.test_type != "all" and suite.name.lower() != f"{args.test_type} tests":
            continue

        # Add suite to runner
        test_runner.add_suite(suite)

    # Run all test suites
    logger.info(f"Running {args.test_type} tests...")
    start_time = time.time()

    results = test_runner.run_all()

    end_time = time.time()
    duration = end_time - start_time

    # Print summary
    logger.info("=" * 80)
    logger.info(f"Test Run Summary ({args.test_type.capitalize()} Tests)")
    logger.info("=" * 80)
    logger.info(f"Total Tests: {results['tests']}")
    logger.info(f"Passed: {results['passed']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Skipped: {results['skipped']}")
    logger.info(f"Success Rate: {(results['passed'] / results['tests'] * 100):.2f}%")
    logger.info(f"Total Duration: {duration:.2f} seconds")
    logger.info("=" * 80)

    # Save detailed results
    result_file = os.path.join(args.output_dir, f"{args.test_type}_test_results.json")
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Detailed results saved to {result_file}")

    # Return success if all tests passed
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
