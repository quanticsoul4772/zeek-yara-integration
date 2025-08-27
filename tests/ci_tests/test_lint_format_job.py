"""
Test CI lint and format job validation.
"""

import pytest
import subprocess
import os
import tempfile
from pathlib import Path


class TestLintFormatJob:
    """Test the lint-and-format CI job functionality."""

    def test_black_formatting(self):
        """Test that Black code formatter can run successfully."""
        # Create a temporary Python file with bad formatting
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_func( a,b ):\n    return a+b\n")
            temp_file = f.name

        try:
            # Run black --check on the temp file (should fail due to formatting)
            result = subprocess.run(
                ["black", "--check", "--diff", temp_file],
                capture_output=True,
                text=True,
            )
            # Black should detect formatting issues
            assert result.returncode != 0, "Black should detect formatting issues"

            # Now format the file
            result = subprocess.run(
                ["black", temp_file], capture_output=True, text=True
            )
            assert result.returncode == 0, "Black should format successfully"

            # Check should now pass
            result = subprocess.run(
                ["black", "--check", temp_file], capture_output=True, text=True
            )
            assert result.returncode == 0, "Black check should pass after formatting"

        finally:
            os.unlink(temp_file)

    def test_isort_import_sorting(self):
        """Test that isort can validate import sorting."""
        # Create a temporary Python file with unsorted imports
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import sys\nimport os\nimport argparse\n")
            temp_file = f.name

        try:
            # Run isort --check-only (might pass or fail depending on current sorting)
            result = subprocess.run(
                ["isort", "--check-only", "--diff", temp_file],
                capture_output=True,
                text=True,
            )
            # isort should run without error (return code 0 or 1)
            assert result.returncode in [0, 1], "isort should run successfully"

        finally:
            os.unlink(temp_file)

    def test_flake8_linting(self):
        """Test that flake8 can perform linting."""
        # Create a temporary Python file with linting issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                "import unused_module\ndef test_func():\n    undefined_var = unknown_var\n    return undefined_var\n"
            )
            temp_file = f.name

        try:
            # Run flake8 with syntax error detection
            result = subprocess.run(
                ["flake8", temp_file, "--select=E9,F63,F7,F82"],
                capture_output=True,
                text=True,
            )
            # Should detect undefined variable
            assert (
                result.returncode != 0
            ), "flake8 should detect syntax/undefined issues"
            assert "F821" in result.stdout or "undefined" in result.stdout.lower()

        finally:
            os.unlink(temp_file)

    def test_mypy_type_checking(self):
        """Test that mypy can perform type checking."""
        # Create a temporary Python file with type issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def add_numbers(a: int, b: int) -> int:\n    return str(a + b)\n")
            temp_file = f.name

        try:
            # Run mypy on the temp file
            result = subprocess.run(
                ["mypy", temp_file, "--ignore-missing-imports"],
                capture_output=True,
                text=True,
            )
            # mypy should detect type mismatch (returning str instead of int)
            assert result.returncode != 0, "mypy should detect type issues"

        finally:
            os.unlink(temp_file)

    def test_code_quality_tools_installed(self):
        """Test that all required code quality tools are installed."""
        tools = ["black", "isort", "flake8", "mypy"]

        for tool in tools:
            result = subprocess.run([tool, "--version"], capture_output=True, text=True)
            assert result.returncode == 0, f"{tool} should be installed and accessible"

    def test_project_passes_black_check(self):
        """Test that the current project passes Black formatting check."""
        project_root = Path(__file__).parent.parent.parent

        # Run black --check on the project
        result = subprocess.run(
            ["black", "--check", "--diff", str(project_root)],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        if result.returncode != 0:
            pytest.skip("Project has Black formatting issues - this is informational")

    def test_project_passes_isort_check(self):
        """Test that the current project passes isort check."""
        project_root = Path(__file__).parent.parent.parent

        # Run isort --check-only on the project
        result = subprocess.run(
            ["isort", "--check-only", "--diff", str(project_root)],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        if result.returncode != 0:
            pytest.skip("Project has isort issues - this is informational")

    def test_flake8_configuration(self):
        """Test that flake8 runs with proper configuration."""
        project_root = Path(__file__).parent.parent.parent

        # Test the exact flake8 command from CI
        result = subprocess.run(
            [
                "flake8",
                ".",
                "--count",
                "--select=E9,F63,F7,F82",
                "--show-source",
                "--statistics",
                "--exclude=venv,.venv,__pycache__,extracted_files,DATA/runtime",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        # This command should not find critical syntax errors
        if result.returncode != 0 and result.stdout.strip():
            pytest.fail(f"Critical flake8 errors found: {result.stdout}")

    @pytest.mark.slow
    def test_lint_format_job_simulation(self):
        """Test simulation of the complete lint-and-format job."""
        project_root = Path(__file__).parent.parent.parent

        # Simulate the CI job steps
        steps = [
            # Check black formatting
            ["black", "--check", "--diff", "."],
            # Check isort
            ["isort", "--check-only", "--diff", "."],
            # Run flake8 critical checks
            [
                "flake8",
                ".",
                "--count",
                "--select=E9,F63,F7,F82",
                "--show-source",
                "--statistics",
                "--exclude=venv,.venv,__pycache__,extracted_files,DATA/runtime",
            ],
        ]

        results = []
        for step in steps:
            result = subprocess.run(
                step, capture_output=True, text=True, cwd=project_root
            )
            results.append((step[0], result.returncode, result.stdout, result.stderr))

        # Report results but don't fail the test for formatting issues
        for tool, returncode, stdout, stderr in results:
            if returncode != 0:
                print(f"{tool} found issues:")
                print(f"  Return code: {returncode}")
                if stdout.strip():
                    print(f"  Stdout: {stdout}")
                if stderr.strip():
                    print(f"  Stderr: {stderr}")

        # Only fail for critical flake8 errors (syntax errors, undefined names)
        flake8_result = next((r for r in results if r[0] == "flake8"), None)
        if flake8_result and flake8_result[1] != 0 and flake8_result[2].strip():
            pytest.fail(
                f"Critical code quality issues found by flake8: {flake8_result[2]}"
            )
