"""
Zeek-YARA Integration Test Configuration
Created: April 24, 2025
Author: Russell Smith

This module contains pytest fixtures and configuration for testing.
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import pytest

from config.config import Config
from core.database import DatabaseManager
from core.scanner import MultiThreadScanner, SingleThreadScanner
from tests.helpers.db_setup import initialize_test_db
from utils.file_utils import FileAnalyzer
from utils.yara_utils import RuleManager, YaraMatcher

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import application components

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(os.path.join("logs", "tests.log")), logging.StreamHandler()],
)


@pytest.fixture
def config():
    """Fixture for test configuration"""
    # Load default config
    config = Config.load_config()

    # Override with test-specific values
    test_config = config.copy()
    test_dir = tempfile.mkdtemp()
    test_config.update(
        {
            "EXTRACT_DIR": os.path.join(test_dir, "zeek_yara_test_extract"),
            "DB_FILE": os.path.join(test_dir, "zeek_yara_test.db"),
            "SCAN_TIMEOUT": 10,
            "MAX_FILE_SIZE": 1024 * 1024,  # 1MB for tests
            "THREADS": 2,
        }
    )

    # Initialize test database with schema and optional seed data
    initialize_test_db(test_config["DB_FILE"])

    # Create test directories
    os.makedirs(test_config["EXTRACT_DIR"], exist_ok=True)

    yield test_config

    # Clean up test directories
    try:
        if os.path.exists(test_config["EXTRACT_DIR"]):
            shutil.rmtree(test_config["EXTRACT_DIR"])

        if os.path.exists(test_config["DB_FILE"]):
            os.unlink(test_config["DB_FILE"])
    except Exception as e:
        print(f"Error cleaning up test environment: {e}")


@pytest.fixture
def file_analyzer():
    """Fixture for file analyzer"""
    return FileAnalyzer(max_file_size=1024 * 1024)


@pytest.fixture
def rule_manager():
    """Fixture for rule manager"""
    rules_dir = os.path.join(os.path.dirname(__file__), "..", "rules")
    return RuleManager(rules_dir=rules_dir)


@pytest.fixture
def yara_matcher(rule_manager):
    """Fixture for YARA matcher"""
    return YaraMatcher(rule_manager=rule_manager)


@pytest.fixture
def db_manager():
    """Fixture for database manager"""
    db_file = os.path.join(tempfile.gettempdir(), "zeek_yara_test.db")

    # Remove existing database file if it exists
    if os.path.exists(db_file):
        os.unlink(db_file)

    # Create a new database manager
    db = DatabaseManager(db_file=db_file)

    # Initialize database with no seed data
    try:
        db.initialize_database()
    except Exception:
        pass  # This might be expected in some tests

    yield db

    # Clean up database
    if os.path.exists(db_file):
        os.unlink(db_file)


@pytest.fixture
def scanner(config):
    """Fixture for scanner"""
    return SingleThreadScanner(config)


@pytest.fixture
def multi_scanner(config):
    """Fixture for multi-threaded scanner"""
    test_config = config.copy()
    test_config["THREADS"] = 2
    return MultiThreadScanner(test_config)


@pytest.fixture
def test_files():
    """Fixture for test files"""
    temp_dir = tempfile.mkdtemp()
    test_files = []

    # Create test files
    file_contents = {
        "text.txt": "This is a test file.\n",
        "binary.bin": b"\x00\x01\x02\x03\x04\x05",
        "eicar.txt": "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*",
        "empty.dat": "",
    }

    for filename, content in file_contents.items():
        file_path = os.path.join(temp_dir, filename)

        if isinstance(content, str):
            with open(file_path, "w") as f:
                f.write(content)
        else:
            with open(file_path, "wb") as f:
                f.write(content)

        test_files.append(file_path)

    yield {
        "dir": temp_dir,
        "files": test_files,
        "paths": {filename: os.path.join(temp_dir, filename) for filename in file_contents.keys()},
    }

    # Clean up test files
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error cleaning up test files: {e}")


# Timer fixture for performance testing
@pytest.fixture
def timer():
    """Timer fixture for measuring performance"""

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()
            return self

        def stop(self):
            self.end_time = time.perf_counter()
            return self

        @property
        def duration(self):
            if self.start_time is None:
                return 0
            end = self.end_time if self.end_time is not None else time.perf_counter()
            return end - self.start_time

    return Timer()


# Performance benchmark decorator
def benchmark(iterations=1):
    """
    Performance benchmarking decorator.

    Args:
        iterations (int): Number of iterations to run
    """

    def decorator(func):
        def wrapper(self, performance_test_env, *args, **kwargs):
            # Run benchmark
            start_time = time.perf_counter()

            results = []
            for _ in range(iterations):
                iter_start = time.perf_counter()
                result = func(self, performance_test_env, *args, **kwargs)
                iter_end = time.perf_counter()
                results.append(result)

                # Calculate iteration time
                iter_time = iter_end - iter_start
                print(f"Iteration completed in {iter_time:.6f} seconds")

            # Calculate overall time
            end_time = time.perf_counter()
            total_time = end_time - start_time
            avg_time = total_time / iterations

            # Print benchmark results
            print(f"\nBenchmark Results for {func.__name__}:")
            print(f"Total Time: {total_time:.6f} seconds")
            print(f"Iterations: {iterations}")
            print(f"Average Time: {avg_time:.6f} seconds per iteration")

            # Return the results from the last iteration
            return results[-1]

        return wrapper

    return decorator
