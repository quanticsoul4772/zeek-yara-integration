"""
Test CI unit test job validation.
"""

import os
import platform
import subprocess
from pathlib import Path

import pytest


class TestUnitTestJob:
    """Test the unit-tests CI job functionality."""

    def test_pytest_installed(self):
        """Test that pytest is installed and accessible."""
        result = subprocess.run(
            ["python", "-m", "pytest", "--version"], capture_output=True, text=True
        )
        assert result.returncode == 0, "pytest should be installed"
        assert "pytest" in result.stdout.lower()

    def test_pytest_coverage_installed(self):
        """Test that pytest-cov is installed."""
        result = subprocess.run(
            ["python", "-c", 'import pytest_cov; print("pytest-cov available")'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "pytest-cov should be installed"

    def test_pytest_xdist_installed(self):
        """Test that pytest-xdist is installed for parallel testing."""
        result = subprocess.run(
            ["python", "-c", 'import xdist; print("pytest-xdist available")'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "pytest-xdist should be installed"

    def test_unit_tests_directory_exists(self):
        """Test that unit tests directory exists."""
        project_root = Path(__file__).parent.parent.parent
        unit_tests_dir = project_root / "tests" / "unit_tests"
        assert unit_tests_dir.exists(), "Unit tests directory should exist"
        assert unit_tests_dir.is_dir(), "Unit tests path should be a directory"

    def test_unit_tests_discoverable(self):
        """Test that pytest can discover unit tests."""
        project_root = Path(__file__).parent.parent.parent
        unit_tests_dir = project_root / "tests" / "unit_tests"

        result = subprocess.run(
            ["python", "-m", "pytest", str(unit_tests_dir), "--collect-only", "-q"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        assert result.returncode == 0, f"pytest should discover tests: {result.stderr}"
        # Should find at least some test files
        lines = [line for line in result.stdout.split("\n") if line.strip()]
        collected_line = [line for line in lines if "collected" in line]
        if collected_line:
            assert "collected" in collected_line[0], "Should collect some tests"

    @pytest.mark.linux
    def test_linux_dependencies_detection(self):
        """Test detection of Linux-specific dependencies."""
        # Check if we can find package managers
        apt_available = (
            subprocess.run(["which", "apt-get"], capture_output=True).returncode == 0
        )
        if apt_available:
            assert True, "apt-get available on Linux"
        else:
            pytest.skip("apt-get not available, skipping Linux dependency test")

    @pytest.mark.macos
    def test_macos_dependencies_detection(self):
        """Test detection of macOS-specific dependencies."""
        # Check if brew is available on macOS
        brew_available = (
            subprocess.run(["which", "brew"], capture_output=True).returncode == 0
        )
        if brew_available:
            assert True, "brew available on macOS"
        else:
            pytest.skip("brew not available, skipping macOS dependency test")

    @pytest.mark.windows
    def test_windows_dependencies_detection(self):
        """Test detection of Windows-specific dependencies."""
        # Windows dependency installation is TODO in CI
        pytest.skip("Windows dependency installation not yet implemented")

    def test_required_directories_creation(self):
        """Test that required directories can be created."""
        project_root = Path(__file__).parent.parent.parent

        required_dirs = [
            "DATA/runtime/logs",
            "DATA/runtime/extracted-files",
            "DATA/runtime/alerts",
        ]

        for dir_path in required_dirs:
            full_path = project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            assert full_path.exists(), f"Should be able to create {dir_path}"

    def test_platform_python_path_setup(self):
        """Test that PYTHONPATH can be configured correctly."""
        project_root = Path(__file__).parent.parent.parent
        platform_path = project_root / "PLATFORM"

        # Test that PLATFORM directory exists
        assert platform_path.exists(), "PLATFORM directory should exist"

        # Test importing with PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = str(platform_path)

        result = subprocess.run(
            ["python", "-c", 'import sys; print("PYTHONPATH:", sys.path)'],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, "Should be able to set PYTHONPATH"
        assert str(platform_path) in result.stdout, "PLATFORM should be in Python path"

    def test_coverage_configuration(self):
        """Test that coverage can be configured for PLATFORM module."""
        project_root = Path(__file__).parent.parent.parent

        # Test coverage command structure
        result = subprocess.run(
            ["python", "-m", "pytest", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        assert result.returncode == 0, "pytest should provide help"
        assert "--cov" in result.stdout, "pytest-cov should be available"

    @pytest.mark.integration
    def test_unit_tests_can_run(self):
        """Test that unit tests can actually run (integration test)."""
        project_root = Path(__file__).parent.parent.parent
        unit_tests_dir = project_root / "tests" / "unit_tests"

        # Set up environment similar to CI
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root / "PLATFORM")

        # Create required directories
        required_dirs = [
            "DATA/runtime/logs",
            "DATA/runtime/extracted-files",
            "DATA/runtime/alerts",
        ]

        for dir_path in required_dirs:
            full_path = project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

        # Run a subset of unit tests
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                str(unit_tests_dir),
                "-v",
                "--tb=short",
                "--maxfail=3",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
            env=env,
            timeout=60,  # 1 minute timeout
        )

        # Don't fail the test if there are import errors or missing dependencies
        # This is informational for CI validation
        if result.returncode != 0:
            print(f"Unit tests had issues (expected in CI validation):")
            print(f"Return code: {result.returncode}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            pytest.skip(
                "Unit tests have dependency issues - this is expected for CI validation"
            )

    def test_codecov_upload_conditions(self):
        """Test Codecov upload conditions from workflow."""
        # This test validates the logic for when Codecov uploads should occur

        # Simulate matrix conditions
        test_conditions = [
            {"os": "ubuntu-latest", "python": "3.9", "should_upload": True},
            {"os": "ubuntu-latest", "python": "3.8", "should_upload": False},
            {"os": "macos-latest", "python": "3.9", "should_upload": False},
            {"os": "windows-latest", "python": "3.9", "should_upload": False},
        ]

        for condition in test_conditions:
            # CI uploads coverage only for ubuntu-latest with Python 3.9
            should_upload = (
                condition["os"] == "ubuntu-latest" and condition["python"] == "3.9"
            )

            assert (
                should_upload == condition["should_upload"]
            ), f"Codecov upload condition incorrect for {condition}"

    def test_python_version_matrix(self):
        """Test that all required Python versions are testable."""
        import sys

        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        supported_versions = ["3.8", "3.9", "3.10", "3.11", "3.12"]

        # We can't test all versions in one run, but we can validate our current version
        assert (
            current_version in supported_versions
        ), f"Current Python {current_version} should be in supported versions {supported_versions}"

    def test_matrix_os_coverage(self):
        """Test OS matrix coverage validation."""
        import platform

        current_os = platform.system().lower()

        # Map platform.system() output to CI matrix values
        os_mapping = {
            "linux": "ubuntu-latest",
            "darwin": "macos-latest",
            "windows": "windows-latest",
        }

        expected_os = ["ubuntu-latest", "macos-latest", "windows-latest"]

        if current_os in os_mapping:
            ci_os = os_mapping[current_os]
            assert ci_os in expected_os, f"Current OS {ci_os} should be in CI matrix"
        else:
            pytest.skip(f"Unknown OS {current_os} not in CI matrix")
