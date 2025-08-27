"""
Test file demonstrating platform-specific test markers.

This file provides examples of how to use the new platform-specific markers
to handle cross-platform compatibility testing.
"""

import platform
import subprocess
import pytest


class TestPlatformMarkers:
    """Test class demonstrating platform-specific test markers."""

    @pytest.mark.linux
    def test_linux_specific_behavior(self):
        """Test that runs only on Linux systems."""
        assert platform.system() == "Linux", "This test should only run on Linux"

        # Test Linux-specific functionality
        result = subprocess.run(["which", "ls"], capture_output=True, text=True)
        assert result.returncode == 0, "ls command should be available on Linux"

    @pytest.mark.macos
    def test_macos_specific_behavior(self):
        """Test that runs only on macOS systems."""
        assert platform.system() == "Darwin", "This test should only run on macOS"

        # Test macOS-specific functionality
        result = subprocess.run(["which", "ls"], capture_output=True, text=True)
        assert result.returncode == 0, "ls command should be available on macOS"

    @pytest.mark.windows
    def test_windows_specific_behavior(self):
        """Test that runs only on Windows systems."""
        assert platform.system() == "Windows", "This test should only run on Windows"

        # Test Windows-specific functionality
        result = subprocess.run(
            ["where", "cmd"], capture_output=True, text=True, shell=True
        )
        assert result.returncode == 0, "cmd command should be available on Windows"

    @pytest.mark.unix
    def test_unix_like_behavior(self):
        """Test that runs on Unix-like systems (Linux and macOS)."""
        assert platform.system() in [
            "Linux",
            "Darwin",
        ], "This test should only run on Unix-like systems"

        # Test Unix-like functionality common to both Linux and macOS
        result = subprocess.run(["which", "grep"], capture_output=True, text=True)
        assert (
            result.returncode == 0
        ), "grep command should be available on Unix-like systems"

    @pytest.mark.posix
    def test_posix_compliance(self):
        """Test POSIX-compliant behavior."""
        assert platform.system() in [
            "Linux",
            "Darwin",
        ], "This test should only run on POSIX-compliant systems"

        # Test POSIX-compliant functionality
        result = subprocess.run(["test", "-d", "/"], capture_output=True)
        assert result.returncode == 0, "Root directory should exist on POSIX systems"


class TestTraditionalSkipIfApproach:
    """Examples using the traditional pytest.mark.skipif approach for comparison."""

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    def test_linux_with_skipif(self):
        """Traditional approach using skipif for Linux-specific tests."""
        assert platform.system() == "Linux"

        # Test Linux-specific grep behavior
        result = subprocess.run(["grep", "--version"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "GNU grep" in result.stdout or "grep" in result.stdout

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_macos_grep_behavior(self):
        """Traditional approach using skipif for macOS-specific tests."""
        assert platform.system() == "Darwin"

        # Test macOS-specific grep behavior
        result = subprocess.run(["grep", "--version"], capture_output=True, text=True)
        assert result.returncode == 0
        # macOS might have BSD grep or GNU grep via Homebrew
        assert "grep" in result.stdout.lower()

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_windows_with_skipif(self):
        """Traditional approach using skipif for Windows-specific tests."""
        assert platform.system() == "Windows"

        # Test Windows-specific behavior
        import os

        assert os.name == "nt"


class TestCombinedMarkers:
    """Examples of combining platform markers with other markers."""

    @pytest.mark.linux
    @pytest.mark.integration
    def test_linux_integration(self):
        """Test that combines Linux marker with integration marker."""
        assert platform.system() == "Linux"
        # This would run integration tests specific to Linux

    @pytest.mark.macos
    @pytest.mark.performance
    def test_macos_performance(self):
        """Test that combines macOS marker with performance marker."""
        assert platform.system() == "Darwin"
        # This would run performance tests specific to macOS

    @pytest.mark.unix
    @pytest.mark.unit
    def test_unix_unit_test(self):
        """Test that combines Unix marker with unit marker."""
        assert platform.system() in ["Linux", "Darwin"]
        # This would run unit tests for Unix-like systems

    @pytest.mark.windows
    @pytest.mark.slow
    def test_windows_slow_operation(self):
        """Test that combines Windows marker with slow marker."""
        assert platform.system() == "Windows"
        # This would run slow tests specific to Windows


class TestParametrizedPlatformTests:
    """Examples of parametrized tests for cross-platform compatibility."""

    @pytest.mark.parametrize("command", ["ls", "grep", "find"])
    @pytest.mark.unix
    def test_unix_commands_available(self, command):
        """Test that common Unix commands are available."""
        result = subprocess.run(["which", command], capture_output=True)
        assert (
            result.returncode == 0
        ), f"Command {command} should be available on Unix systems"

    @pytest.mark.parametrize("path_sep", ["/"])
    @pytest.mark.unix
    def test_unix_path_separator(self, path_sep):
        """Test Unix path separator behavior."""
        import os

        assert (
            os.path.sep == path_sep
        ), f"Path separator should be {path_sep} on Unix systems"

    @pytest.mark.parametrize("path_sep", ["\\"])
    @pytest.mark.windows
    def test_windows_path_separator(self, path_sep):
        """Test Windows path separator behavior."""
        import os

        assert (
            os.path.sep == path_sep
        ), f"Path separator should be {path_sep} on Windows"
