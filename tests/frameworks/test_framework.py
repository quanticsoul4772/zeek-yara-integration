#!/usr/bin/env python3
"""
Zeek-YARA Integration Multi-Level Testing Framework
Created: April 24, 2025
Author: Russell Smith

This module provides a comprehensive testing framework for the Zeek-YARA integration.
It implements multi-level testing including unit tests, integration tests, and
performance tests with detailed reporting.
"""

import datetime
import json
import logging
import os
import sys
import time
import unittest
from typing import Any, Callable, Dict, List, Optional

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(os.path.join("logs", "tests.log")), logging.StreamHandler()],
)

logger = logging.getLogger("zeek_yara.test_framework")


class CustomTestResult:
    """Container for test results with detailed metrics"""

    def __init__(self, name: str, test_type: str):
        """
        Initialize test result.

        Args:
            name (str): Test name
            test_type (str): Type of test (unit, integration, performance)
        """
        self.name = name
        self.test_type = test_type
        self.start_time = time.time()
        self.end_time = None
        self.duration = None
        self.passed = False
        self.skipped = False
        self.error = None
        self.metrics = {}

    def complete(self, passed: bool, error: Optional[str] = None) -> None:
        """
        Complete the test and record results.

        Args:
            passed (bool): Whether the test passed
            error (str, optional): Error message if test failed
        """
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.passed = passed
        self.error = error

    def skip(self) -> None:
        """Mark test as skipped"""
        self.skipped = True
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def add_metric(self, name: str, value: Any) -> None:
        """
        Add a performance or test metric.

        Args:
            name (str): Metric name
            value (Any): Metric value
        """
        self.metrics[name] = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert test result to dictionary.

        Returns:
            Dict[str, Any]: Test result dictionary
        """
        return {
            "name": self.name,
            "type": self.test_type,
            "duration": self.duration,
            "passed": self.passed,
            "skipped": self.skipped,
            "error": self.error,
            "metrics": self.metrics,
            "timestamp": datetime.datetime.now().isoformat(),
        }


class CustomTestCase:
    """Base class for all test cases"""

    def __init__(self, name: str, test_type: str):
        """
        Initialize test case.

        Args:
            name (str): Test name
            test_type (str): Type of test (unit, integration, performance)
        """
        self.name = name
        self.test_type = test_type
        self.logger = logging.getLogger(f"zeek_yara.tests.{test_type}.{name}")

    def setup(self) -> None:
        """Set up test environment"""

    def teardown(self) -> None:
        """Clean up test environment"""

    def run(self) -> CustomTestResult:
        """
        Run the test.

        Returns:
            TestResult: Test result
        """
        result = CustomTestResult(self.name, self.test_type)

        try:
            self.setup()
            self.execute(result)
            result.complete(passed=True)
        except unittest.SkipTest:
            result.skip()
            self.logger.info(f"Test {self.name} skipped")
        except Exception as e:
            result.complete(passed=False, error=str(e))
            self.logger.error(f"Test {self.name} failed: {str(e)}", exc_info=True)
        finally:
            try:
                self.teardown()
            except Exception as cleanup_error:
                self.logger.error(f"Error in teardown: {str(cleanup_error)}")

        return result

    def execute(self, result: CustomTestResult) -> None:
        """
        Execute the test case.

        Args:
            result (TestResult): Test result to populate

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement execute()")


class CustomTestSuite:
    """Collection of test cases"""

    def __init__(self, name: str):
        """
        Initialize test suite.

        Args:
            name (str): Suite name
        """
        self.name = name
        self.tests: List[CustomTestCase] = []
        self.logger = logging.getLogger(f"zeek_yara.tests.suite.{name}")

    def add_test(self, test: CustomTestCase) -> None:
        """
        Add a test case to the suite.

        Args:
            test (CustomTestCase): Test case to add
        """
        self.tests.append(test)

    def run(self) -> Dict[str, Any]:
        """
        Run all tests in the suite.

        Returns:
            Dict[str, Any]: Test suite results
        """
        self.logger.info(f"Running test suite: {self.name}")

        start_time = time.time()
        results = []
        passed = 0
        failed = 0
        skipped = 0

        for test in self.tests:
            result = test.run()
            results.append(result.to_dict())

            if result.passed:
                passed += 1
            elif result.skipped:
                skipped += 1
            else:
                failed += 1

        duration = time.time() - start_time

        suite_result = {
            "name": self.name,
            "tests": len(self.tests),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "results": results,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        self.logger.info(
            f"Suite {self.name} completed: {passed} passed, "
            f"{failed} failed, {skipped} skipped in {duration:.2f}s"
        )

        return suite_result


class CustomTestRunner:
    """Test runner for executing test suites"""

    def __init__(self, output_dir: str = "test_results"):
        """
        Initialize test runner.

        Args:
            output_dir (str, optional): Directory for test results
        """
        self.suites: List[CustomTestSuite] = []
        self.output_dir = output_dir
        self.logger = logging.getLogger("zeek_yara.tests.runner")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

    def add_suite(self, suite: CustomTestSuite) -> None:
        """
        Add a test suite to the runner.

        Args:
            suite (TestSuite): Test suite to add
        """
        self.suites.append(suite)

    def run_all(self) -> Dict[str, Any]:
        """
        Run all test suites.

        Returns:
            Dict[str, Any]: Overall test results
        """
        self.logger.info("Starting test run")

        start_time = time.time()
        suite_results = []
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for suite in self.suites:
            result = suite.run()
            suite_results.append(result)

            total_tests += result["tests"]
            total_passed += result["passed"]
            total_failed += result["failed"]
            total_skipped += result["skipped"]

        duration = time.time() - start_time

        overall_result = {
            "suites": len(self.suites),
            "tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "duration": duration,
            "suite_results": suite_results,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Save results
        self._save_results(overall_result)

        self.logger.info(
            f"Test run completed: {total_passed}/{total_tests} passed, "
            f"{total_failed} failed, {total_skipped} skipped in {duration:.2f}s"
        )

        return overall_result

    def _save_results(self, results: Dict[str, Any]) -> None:
        """
        Save test results to file.

        Args:
            results (Dict[str, Any]): Test results
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.output_dir, f"test_results_{timestamp}.json")

        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"Test results saved to {result_file}")


# Helper functions for creating test cases
def create_unit_test_case(
    name: str, test_func: Callable[[CustomTestResult], None]
) -> CustomTestCase:
    """
    Create a unit test case with a custom test function.

    Args:
        name (str): Test name
        test_func (Callable): Test function that accepts a TestResult

    Returns:
        CustomTestCase: Configured test case
    """

    class CustomUnitTest(CustomTestCase):
        def __init__(self):
            super().__init__(name, "unit")
            self._test_func = test_func

        def execute(self, result: CustomTestResult) -> None:
            self._test_func(result)

    return CustomUnitTest()


def create_integration_test_case(
    name: str, test_func: Callable[[CustomTestResult], None]
) -> CustomTestCase:
    """
    Create an integration test case with a custom test function.

    Args:
        name (str): Test name
        test_func (Callable): Test function that accepts a TestResult

    Returns:
        CustomTestCase: Configured test case
    """

    class CustomIntegrationTest(CustomTestCase):
        def __init__(self):
            super().__init__(name, "integration")
            self._test_func = test_func

        def execute(self, result: CustomTestResult) -> None:
            self._test_func(result)

    return CustomIntegrationTest()


def create_performance_test_case(
    name: str, test_func: Callable[[CustomTestResult], None]
) -> CustomTestCase:
    """
    Create a performance test case with a custom test function.

    Args:
        name (str): Test name
        test_func (Callable): Test function that accepts a TestResult

    Returns:
        CustomTestCase: Configured test case
    """

    class CustomPerformanceTest(CustomTestCase):
        def __init__(self):
            super().__init__(name, "performance")
            self._test_func = test_func

        def execute(self, result: CustomTestResult) -> None:
            self._test_func(result)

    return CustomPerformanceTest()


# Main function to run all tests
def run_tests() -> int:
    """
    Run all tests and return exit code.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        runner = CustomTestRunner()

        # Create and add test suites
        # This would be populated with actual test cases

        results = runner.run_all()

        # Return 0 for success, 1 for failure
        return 0 if results["failed"] == 0 else 1

    except Exception as e:
        logger.error(f"Error running tests: {str(e)}", exc_info=True)
        return 1


# CLI entry point
if __name__ == "__main__":
    sys.exit(run_tests())
