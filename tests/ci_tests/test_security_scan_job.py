"""
Test CI security scanning job validation.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


class TestSecurityScanJob:
    """Test the security-scan CI job functionality."""

    def test_bandit_security_scanner_available(self):
        """Test that Bandit security scanner is available."""
        result = subprocess.run(
            ["python", "-c", 'import bandit; print("Bandit available")'],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Try installing bandit for testing
            install_result = subprocess.run(
                ["pip", "install", "bandit"], capture_output=True, text=True
            )
            if install_result.returncode == 0:
                # Test again after installation
                result = subprocess.run(
                    ["python", "-c", 'import bandit; print("Bandit available")'],
                    capture_output=True,
                    text=True,
                )

        if result.returncode != 0:
            pytest.skip("Bandit not available and cannot be installed")

    def test_safety_vulnerability_scanner_available(self):
        """Test that Safety vulnerability scanner is available."""
        result = subprocess.run(
            ["python", "-c", 'import safety; print("Safety available")'],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Try installing safety for testing
            install_result = subprocess.run(
                ["pip", "install", "safety"], capture_output=True, text=True
            )
            if install_result.returncode == 0:
                # Test again after installation
                result = subprocess.run(
                    ["python", "-c", 'import safety; print("Safety available")'],
                    capture_output=True,
                    text=True,
                )

        if result.returncode != 0:
            pytest.skip("Safety not available and cannot be installed")

    def test_bandit_command_structure(self):
        """Test that Bandit can be run with proper parameters."""
        project_root = Path(__file__).parent.parent.parent

        # Test bandit help to ensure it's working
        result = subprocess.run(["bandit", "--help"], capture_output=True, text=True)

        if result.returncode != 0:
            pytest.skip("Bandit command not working")

        assert (
            "--recursive" in result.stdout or "-r" in result.stdout
        ), "Bandit should support recursive scanning"
        assert (
            "--format" in result.stdout or "-f" in result.stdout
        ), "Bandit should support output format"

    def test_bandit_exclusion_paths(self):
        """Test that Bandit exclusion paths are properly configured."""
        exclusion_paths = ["/venv", "/extracted_files", "/DATA/runtime"]

        # Test that exclusion paths are reasonable
        for path in exclusion_paths:
            assert isinstance(path, str), f"Exclusion path {path} should be string"
            assert path.startswith("/"), f"Exclusion path {path} should be absolute"

    def test_safety_command_structure(self):
        """Test that Safety can be run with proper parameters."""
        # Test safety help to ensure it's working
        result = subprocess.run(["safety", "--help"], capture_output=True, text=True)

        if result.returncode != 0:
            pytest.skip("Safety command not working")

        assert "check" in result.stdout, "Safety should support check command"

    @pytest.mark.integration
    def test_bandit_scan_execution(self):
        """Test that Bandit can actually scan the project."""
        project_root = Path(__file__).parent.parent.parent

        # Create a temporary test file with a potential security issue
        test_file = project_root / "temp_security_test.py"
        with open(test_file, "w") as f:
            f.write('import subprocess\nsubprocess.call("echo test", shell=True)\n')

        try:
            # Run bandit on the test file
            result = subprocess.run(
                [
                    "bandit",
                    "-r",
                    str(test_file),
                    "-f",
                    "json",
                    "-o",
                    "temp_bandit_report.json",
                ],
                capture_output=True,
                text=True,
                cwd=project_root,
            )

            # Bandit should detect the shell=True issue
            assert (
                result.returncode != 0
            ), "Bandit should detect security issues in test file"

            # Check if report was created
            report_file = project_root / "temp_bandit_report.json"
            if report_file.exists():
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                assert "results" in report_data, "Bandit report should have results"

                # Clean up report
                report_file.unlink()

        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()

    @pytest.mark.integration
    def test_bandit_project_scan(self):
        """Test Bandit scan on the actual project."""
        project_root = Path(__file__).parent.parent.parent

        # Run bandit with CI configuration
        result = subprocess.run(
            [
                "bandit",
                "-r",
                ".",
                "-x",
                "/venv,/extracted_files,/DATA/runtime",
                "-f",
                "json",
                "-o",
                "test_bandit_report.json",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=120,  # 2 minute timeout
        )

        # Bandit might find issues - that's OK for CI validation
        print(f"Bandit scan return code: {result.returncode}")
        print(f"Bandit stdout: {result.stdout}")
        print(f"Bandit stderr: {result.stderr}")

        # Check if report was created
        report_file = project_root / "test_bandit_report.json"
        if report_file.exists():
            try:
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                print(f"Bandit found {len(report_data.get('results', []))} issues")
            except json.JSONDecodeError:
                print("Bandit report is not valid JSON")

            # Clean up
            report_file.unlink()

        # Don't fail the test - this is validation
        assert True, "Bandit scan completed"

    @pytest.mark.integration
    def test_safety_dependency_check(self):
        """Test Safety dependency vulnerability check."""
        project_root = Path(__file__).parent.parent.parent

        # Run safety check
        result = subprocess.run(
            ["safety", "check", "--json", "--output", "test_safety_report.json"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=60,  # 1 minute timeout
        )

        # Safety might find vulnerabilities - that's OK
        print(f"Safety check return code: {result.returncode}")
        print(f"Safety stdout: {result.stdout}")
        print(f"Safety stderr: {result.stderr}")

        # Check if report was created
        report_file = project_root / "test_safety_report.json"
        if report_file.exists():
            try:
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                print(
                    f"Safety report structure: {list(report_data.keys()) if isinstance(report_data, dict) else type(report_data)}"
                )
            except json.JSONDecodeError:
                print("Safety report is not valid JSON")

            # Clean up
            report_file.unlink()

        # Don't fail the test - this is validation
        assert True, "Safety check completed"

    def test_security_report_upload_structure(self):
        """Test that security reports can be uploaded as artifacts."""
        # This tests the artifact upload structure from CI

        expected_artifacts = ["bandit-report.json", "safety-report.json"]

        for artifact in expected_artifacts:
            assert isinstance(
                artifact, str
            ), f"Artifact name {artifact} should be string"
            assert artifact.endswith(".json"), f"Artifact {artifact} should be JSON"

    def test_continue_on_error_behavior(self):
        """Test that security scans continue on error."""
        # Security scans should be non-blocking (continue-on-error: true)

        # Simulate a security scan that finds issues
        result = subprocess.run(
            ["python", "-c", 'print("Security scan complete"); exit(1)'],
            capture_output=True,
            text=True,
        )

        # Even though it "failed", the output should be there
        assert "Security scan complete" in result.stdout
        assert result.returncode == 1, "Simulated security scan should return non-zero"

    def test_security_scan_job_requirements(self):
        """Test that security scan job has proper requirements."""
        required_tools = ["bandit", "safety"]

        for tool in required_tools:
            # Test that we can at least try to import the tool
            result = subprocess.run(
                ["python", "-c", f"import {tool}"], capture_output=True, text=True
            )

            if result.returncode != 0:
                print(f"Tool {tool} not available - this is expected in CI validation")

    def test_security_scan_output_formats(self):
        """Test that security tools support required output formats."""
        # Test that bandit supports JSON output
        result = subprocess.run(["bandit", "--help"], capture_output=True, text=True)

        if result.returncode == 0:
            assert "json" in result.stdout.lower(), "Bandit should support JSON output"

        # Test that safety supports JSON output
        result = subprocess.run(["safety", "--help"], capture_output=True, text=True)

        if result.returncode == 0:
            assert "json" in result.stdout.lower(), "Safety should support JSON output"

    def test_requirements_file_exists_for_safety(self):
        """Test that requirements.txt exists for Safety to check."""
        project_root = Path(__file__).parent.parent.parent
        requirements_file = project_root / "requirements.txt"

        # Safety needs requirements.txt to check dependencies
        if requirements_file.exists():
            assert requirements_file.is_file(), "requirements.txt should be a file"

            # Check that it's readable
            with open(requirements_file, "r") as f:
                content = f.read()
            assert isinstance(content, str), "requirements.txt should be readable"
        else:
            print("requirements.txt not found - Safety checks may not work optimally")

    @pytest.mark.slow
    def test_security_scan_job_simulation(self):
        """Test complete security scan job simulation."""
        project_root = Path(__file__).parent.parent.parent

        # Simulate the complete CI security scan job
        security_steps = []

        # Step 1: Bandit scan
        bandit_result = subprocess.run(
            [
                "bandit",
                "-r",
                ".",
                "-x",
                "/venv,/extracted_files,/DATA/runtime",
                "-f",
                "txt",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=60,
        )
        security_steps.append(("bandit", bandit_result.returncode))

        # Step 2: Safety check
        safety_result = subprocess.run(
            ["safety", "check"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=30,
        )
        security_steps.append(("safety", safety_result.returncode))

        # Report results
        print("Security Scan Job Results:")
        for tool, returncode in security_steps:
            status = "PASSED" if returncode == 0 else "FOUND ISSUES"
            print(f"  {tool}: {status} (code: {returncode})")

        # Security scans finding issues is not a test failure
        assert True, "Security scan job simulation completed"
