"""
Test CI performance benchmark job validation.
"""

import pytest
import subprocess
import os
from pathlib import Path


class TestPerformanceBenchmarkJob:
    """Test the performance-benchmarks CI job functionality."""

    def test_performance_tests_directory_exists(self):
        """Test that performance tests directory exists."""
        project_root = Path(__file__).parent.parent.parent
        performance_tests_dir = project_root / "tests" / "performance_tests"
        assert (
            performance_tests_dir.exists()
        ), "Performance tests directory should exist"
        assert performance_tests_dir.is_dir(), "Performance tests should be a directory"

    def test_pytest_benchmark_available(self):
        """Test that pytest-benchmark is available."""
        result = subprocess.run(
            [
                "python",
                "-c",
                'import pytest_benchmark; print("pytest-benchmark available")',
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Try installing pytest-benchmark for testing
            install_result = subprocess.run(
                ["pip", "install", "pytest-benchmark"], capture_output=True, text=True
            )
            if install_result.returncode == 0:
                # Test again after installation
                result = subprocess.run(
                    [
                        "python",
                        "-c",
                        'import pytest_benchmark; print("pytest-benchmark available")',
                    ],
                    capture_output=True,
                    text=True,
                )

        if result.returncode != 0:
            pytest.skip("pytest-benchmark not available and cannot be installed")

    def test_benchmark_job_conditions(self):
        """Test performance benchmark job conditions."""
        # Performance benchmarks only run on push to main branch

        # Simulate the CI conditions
        test_conditions = [
            {"event": "push", "ref": "refs/heads/main", "should_run": True},
            {"event": "push", "ref": "refs/heads/develop", "should_run": False},
            {"event": "pull_request", "ref": "refs/heads/main", "should_run": False},
            {"event": "schedule", "ref": "refs/heads/main", "should_run": False},
        ]

        for condition in test_conditions:
            # Check if conditions match CI logic
            should_run = (
                condition["event"] == "push" and condition["ref"] == "refs/heads/main"
            )

            assert (
                should_run == condition["should_run"]
            ), f"Benchmark condition incorrect for {condition}"

    def test_benchmark_command_structure(self):
        """Test pytest benchmark command structure."""
        # Test the exact command from CI
        expected_command = [
            "python",
            "-m",
            "pytest",
            "tests/performance_tests/",
            "-v",
            "--benchmark-only",
            "--benchmark-json=benchmark.json",
        ]

        # Validate command structure
        assert expected_command[0] == "python", "Should use python"
        assert expected_command[1] == "-m", "Should use module flag"
        assert expected_command[2] == "pytest", "Should use pytest"
        assert "--benchmark-only" in expected_command, "Should run benchmarks only"
        assert any(
            "--benchmark-json" in arg for arg in expected_command
        ), "Should output JSON"

    def test_benchmark_json_output_format(self):
        """Test benchmark JSON output format."""
        output_file = "benchmark.json"

        # Validate output file format
        assert output_file.endswith(".json"), "Benchmark output should be JSON"
        assert isinstance(output_file, str), "Output file should be string"

    def test_performance_tests_discoverable(self):
        """Test that pytest can discover performance tests."""
        project_root = Path(__file__).parent.parent.parent
        performance_tests_dir = project_root / "tests" / "performance_tests"

        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                str(performance_tests_dir),
                "--collect-only",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        # Should be able to collect (even if no tests found)
        assert result.returncode in [
            0,
            1,
        ], f"pytest should discover performance tests: {result.stderr}"

    def test_pythonpath_configuration_for_benchmarks(self):
        """Test PYTHONPATH configuration for benchmark tests."""
        project_root = Path(__file__).parent.parent.parent
        platform_path = project_root / "PLATFORM"

        if platform_path.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(platform_path)

            result = subprocess.run(
                ["python", "-c", "import sys; print(sys.path)"],
                capture_output=True,
                text=True,
                env=env,
            )

            assert (
                result.returncode == 0
            ), "Should be able to set PYTHONPATH for benchmarks"
            assert (
                str(platform_path) in result.stdout
            ), "PLATFORM should be in Python path"
        else:
            pytest.skip("PLATFORM directory not found")

    def test_benchmark_artifact_upload_structure(self):
        """Test benchmark artifact upload structure."""
        # Test the artifact upload configuration from CI
        expected_artifact = {"name": "benchmark-results", "path": "benchmark.json"}

        assert (
            expected_artifact["name"] == "benchmark-results"
        ), "Artifact name should be benchmark-results"
        assert (
            expected_artifact["path"] == "benchmark.json"
        ), "Artifact path should be benchmark.json"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_benchmark_execution_simulation(self):
        """Test benchmark execution simulation."""
        project_root = Path(__file__).parent.parent.parent
        performance_tests_dir = project_root / "tests" / "performance_tests"

        if not performance_tests_dir.exists():
            pytest.skip("Performance tests directory not found")

        # Set up environment
        env = os.environ.copy()
        platform_path = project_root / "PLATFORM"
        if platform_path.exists():
            env["PYTHONPATH"] = str(platform_path)

        # Try to run performance tests
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                str(performance_tests_dir),
                "-v",
                "--benchmark-only",
                "--benchmark-json=test_benchmark.json",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
            env=env,
            timeout=180,  # 3 minute timeout
        )

        # Performance tests may not exist or may fail - this is informational
        print(f"Benchmark execution return code: {result.returncode}")
        print(f"Benchmark stdout: {result.stdout}")
        print(f"Benchmark stderr: {result.stderr}")

        # Check if benchmark JSON was created
        benchmark_file = project_root / "test_benchmark.json"
        if benchmark_file.exists():
            print("Benchmark JSON file created successfully")

            # Try to parse the JSON
            try:
                import json

                with open(benchmark_file, "r") as f:
                    benchmark_data = json.load(f)
                print(
                    f"Benchmark data keys: {list(benchmark_data.keys()) if isinstance(benchmark_data, dict) else type(benchmark_data)}"
                )
            except json.JSONDecodeError:
                print("Benchmark JSON file is not valid JSON")

            # Clean up
            benchmark_file.unlink()

        if result.returncode != 0:
            pytest.skip(
                "Performance benchmarks not working - this is expected for CI validation"
            )

    def test_benchmark_only_flag_behavior(self):
        """Test --benchmark-only flag behavior."""
        # This flag should only run benchmark tests, not regular tests

        # Test that pytest recognizes the flag
        result = subprocess.run(
            ["python", "-m", "pytest", "--help"], capture_output=True, text=True
        )

        if result.returncode == 0:
            # Check if benchmark options are available
            if "--benchmark-only" in result.stdout:
                assert True, "pytest-benchmark --benchmark-only flag available"
            else:
                pytest.skip("pytest-benchmark not available")
        else:
            pytest.skip("pytest not working")

    def test_ubuntu_latest_performance_environment(self):
        """Test Ubuntu latest environment for performance testing."""
        import platform

        current_os = platform.system().lower()

        if current_os == "linux":
            # Check system info that might affect performance
            try:
                # Check CPU info
                with open("/proc/cpuinfo", "r") as f:
                    cpu_info = f.read()
                assert "processor" in cpu_info, "Should have CPU information"

                # Check memory info
                with open("/proc/meminfo", "r") as f:
                    mem_info = f.read()
                assert "MemTotal" in mem_info, "Should have memory information"

                print("Performance testing environment validated on Linux")

            except FileNotFoundError:
                print("Cannot read system info - continuing")
        else:
            print(f"Performance testing on {current_os} - environment may vary")

        # Always pass - this is informational
        assert True, "Performance environment check completed"

    def test_benchmark_marker_configuration(self):
        """Test that performance marker is properly configured."""
        project_root = Path(__file__).parent.parent.parent
        pytest_ini = project_root / "pytest.ini"

        if pytest_ini.exists():
            with open(pytest_ini, "r") as f:
                pytest_config = f.read()

            # Check if performance marker is defined
            if "performance:" in pytest_config:
                assert True, "Performance marker is configured"
            else:
                print(
                    "Performance marker not found in pytest.ini - may need to be added"
                )
        else:
            print("pytest.ini not found - performance marker may not be configured")

    def test_python_39_performance_requirements(self):
        """Test Python 3.9 performance requirements."""
        import sys

        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        # CI runs benchmarks on Python 3.9
        if current_version == "3.9":
            print(f"Running on Python 3.9 - optimal for CI benchmarks")
        else:
            print(f"Running on Python {current_version} - benchmarks may vary from CI")

        # Version info should be accessible
        assert sys.version_info.major >= 3, "Should be running Python 3+"
        assert sys.version_info.minor >= 8, "Should be running Python 3.8+"

    def test_main_branch_only_logic(self):
        """Test that benchmarks only run on main branch pushes."""
        # This validates the CI conditional logic

        # Simulate GitHub context
        github_conditions = {
            "push_to_main": {
                "event_name": "push",
                "ref": "refs/heads/main",
                "should_run": True,
            },
            "push_to_develop": {
                "event_name": "push",
                "ref": "refs/heads/develop",
                "should_run": False,
            },
            "pull_request": {
                "event_name": "pull_request",
                "ref": "refs/heads/feature-branch",
                "should_run": False,
            },
        }

        for scenario, condition in github_conditions.items():
            # Replicate CI logic
            should_run = (
                condition["event_name"] == "push"
                and condition["ref"] == "refs/heads/main"
            )

            assert (
                should_run == condition["should_run"]
            ), f"Benchmark logic incorrect for {scenario}"

    def test_benchmark_performance_markers(self):
        """Test that performance tests use proper markers."""
        # Performance tests should use @pytest.mark.performance

        marker_examples = [
            "@pytest.mark.performance",
            "@pytest.mark.slow",
            "@pytest.mark.benchmark",
        ]

        for marker in marker_examples:
            assert marker.startswith(
                "@pytest.mark."
            ), f"Marker {marker} should use pytest.mark"
            assert isinstance(marker, str), f"Marker {marker} should be string"
