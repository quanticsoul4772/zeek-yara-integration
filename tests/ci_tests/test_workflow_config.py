"""
Test CI workflow configuration and structure.
"""

import pytest
import yaml
import os
from pathlib import Path


class TestWorkflowConfiguration:
    """Test the CI workflow YAML configuration."""

    def test_workflow_file_exists(self):
        """Test that the CI workflow file exists."""
        workflow_path = (
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        )
        assert workflow_path.exists(), "CI workflow file should exist"

    def test_workflow_yaml_valid(self):
        """Test that the workflow YAML is valid."""
        workflow_path = (
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        )

        with open(workflow_path, "r") as f:
            try:
                workflow_config = yaml.safe_load(f)
                assert workflow_config is not None
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in CI workflow: {e}")

    def test_workflow_triggers(self):
        """Test that workflow has proper triggers configured."""
        workflow_path = (
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        )

        with open(workflow_path, "r") as f:
            workflow_config = yaml.safe_load(f)

        assert "on" in workflow_config, "Workflow should have triggers"

        triggers = workflow_config["on"]
        assert "push" in triggers, "Should trigger on push"
        assert "pull_request" in triggers, "Should trigger on pull requests"
        assert "schedule" in triggers, "Should have scheduled runs"

        # Check branch configurations
        assert triggers["push"]["branches"] == ["main", "develop"]
        assert triggers["pull_request"]["branches"] == ["main", "develop"]

        # Check schedule configuration
        assert len(triggers["schedule"]) == 1
        assert triggers["schedule"][0]["cron"] == "0 2 * * *"

    def test_required_jobs_exist(self):
        """Test that all required jobs are defined."""
        workflow_path = (
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        )

        with open(workflow_path, "r") as f:
            workflow_config = yaml.safe_load(f)

        jobs = workflow_config.get("jobs", {})

        required_jobs = [
            "lint-and-format",
            "unit-tests",
            "integration-tests",
            "educational-content-tests",
            "cli-tool-tests",
            "security-scan",
            "docker-build",
            "performance-benchmarks",
            "documentation-build",
            "notification",
        ]

        for job in required_jobs:
            assert job in jobs, f"Job '{job}' should be defined in workflow"

    def test_job_dependencies(self):
        """Test that job dependencies are correctly configured."""
        workflow_path = (
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        )

        with open(workflow_path, "r") as f:
            workflow_config = yaml.safe_load(f)

        jobs = workflow_config.get("jobs", {})

        # Integration tests should depend on unit tests
        integration_job = jobs.get("integration-tests", {})
        assert "needs" in integration_job, "Integration tests should have dependencies"
        assert integration_job["needs"] == "unit-tests"

        # Notification job should depend on core jobs
        notification_job = jobs.get("notification-job", {})
        # Note: The actual workflow uses 'notification' not 'notification-job'
        notification_job = jobs.get("notification", {})
        if "needs" in notification_job:
            expected_deps = [
                "lint-and-format",
                "unit-tests",
                "integration-tests",
                "educational-content-tests",
                "cli-tool-tests",
                "security-scan",
            ]
            for dep in expected_deps:
                assert (
                    dep in notification_job["needs"]
                ), f"Notification should depend on {dep}"

    def test_matrix_strategy(self):
        """Test that unit tests have proper matrix strategy."""
        workflow_path = (
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        )

        with open(workflow_path, "r") as f:
            workflow_config = yaml.safe_load(f)

        jobs = workflow_config.get("jobs", {})
        unit_tests_job = jobs.get("unit-tests", {})

        assert "strategy" in unit_tests_job, "Unit tests should have strategy"
        strategy = unit_tests_job["strategy"]
        assert "matrix" in strategy, "Strategy should have matrix"

        matrix = strategy["matrix"]
        assert "os" in matrix, "Matrix should include OS variants"
        assert "python-version" in matrix, "Matrix should include Python versions"

        # Check OS coverage
        expected_os = ["ubuntu-latest", "macos-latest", "windows-latest"]
        assert matrix["os"] == expected_os, f"Should test on {expected_os}"

        # Check Python version coverage
        expected_python = ["3.8", "3.9", "3.10", "3.11"]
        assert (
            matrix["python-version"] == expected_python
        ), f"Should test Python {expected_python}"

    def test_performance_benchmarks_conditions(self):
        """Test that performance benchmarks have proper conditions."""
        workflow_path = (
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        )

        with open(workflow_path, "r") as f:
            workflow_config = yaml.safe_load(f)

        jobs = workflow_config.get("jobs", {})
        perf_job = jobs.get("performance-benchmarks", {})

        assert "if" in perf_job, "Performance benchmarks should have conditions"
        condition = perf_job["if"]
        assert "github.event_name == 'push'" in condition
        assert "github.ref == 'refs/heads/main'" in condition
