"""
Zeek-YARA Integration Test Configuration
Minimal version for CI
"""

import os
import platform
import shutil
import tempfile

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers for platform-specific tests."""
    config.addinivalue_line("markers", "linux: mark test to run only on Linux")
    config.addinivalue_line("markers", "macos: mark test to run only on macOS")
    config.addinivalue_line("markers", "windows: mark test to run only on Windows")
    config.addinivalue_line(
        "markers", "unix: mark test to run only on Unix-like systems (Linux/macOS)"
    )
    config.addinivalue_line(
        "markers", "posix: mark test to run only on POSIX-compliant systems"
    )


def pytest_collection_modifyitems(config, items):
    """Skip platform-specific tests on incompatible platforms."""
    current_platform = platform.system()
    
    for item in items:
        # Skip Linux-specific tests on non-Linux platforms
        if item.get_closest_marker("linux") and current_platform != "Linux":
            item.add_marker(pytest.mark.skip(reason="Linux only test"))
        
        # Skip macOS-specific tests on non-macOS platforms
        if item.get_closest_marker("macos") and current_platform != "Darwin":
            item.add_marker(pytest.mark.skip(reason="macOS only test"))
        
        # Skip Windows-specific tests on non-Windows platforms
        if item.get_closest_marker("windows") and current_platform != "Windows":
            item.add_marker(pytest.mark.skip(reason="Windows only test"))
        
        # Skip Unix-specific tests on non-Unix platforms
        if item.get_closest_marker("unix") and current_platform not in ["Linux", "Darwin"]:
            item.add_marker(pytest.mark.skip(reason="Unix-like systems only test"))
        
        # Skip POSIX-specific tests on non-POSIX platforms
        if item.get_closest_marker("posix") and current_platform not in ["Linux", "Darwin"]:
            item.add_marker(pytest.mark.skip(reason="POSIX-compliant systems only test"))


@pytest.fixture
def config():
    """Fixture for test configuration"""
    test_dir = tempfile.mkdtemp()
    test_config = {
        "EXTRACT_DIR": os.path.join(test_dir, "zeek_yara_test_extract"),
        "DB_FILE": os.path.join(test_dir, "zeek_yara_test.db"),
        "SCAN_TIMEOUT": 10,
        "MAX_FILE_SIZE": 1024 * 1024,  # 1MB for tests
        "THREADS": 2,
    }

    # Create test directories
    os.makedirs(test_config["EXTRACT_DIR"], exist_ok=True)

    yield test_config

    # Clean up
    try:
        shutil.rmtree(test_dir)
    except Exception:
        pass


@pytest.fixture
def test_files():
    """Fixture for test files"""
    temp_dir = tempfile.mkdtemp()

    # Create a simple test file
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("Test content")

    yield {"dir": temp_dir, "files": [test_file]}

    # Clean up
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


@pytest.fixture
def timer(benchmark):
    """Timer fixture that wraps pytest-benchmark for performance tests"""
    return benchmark
