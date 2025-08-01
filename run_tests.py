#!/usr/bin/env python3
"""
Cross-platform test runner for Zeek-YARA Integration
Created: August 1, 2025
Author: Claude

This script provides cross-platform test execution for Python 3.8-3.11
on Windows, macOS, and Linux.
"""

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def activate_venv():
    """
    Activate virtual environment if it exists.
    Returns the Python executable to use.
    """
    venv_dir = Path("venv")
    if venv_dir.exists():
        if os.name == "nt":  # Windows
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:  # Unix-like (Linux, macOS)
            python_exe = venv_dir / "bin" / "python"
        
        if python_exe.exists():
            return str(python_exe)
    
    return sys.executable


def run_tests(test_type, verbose, output_dir, python_exe):
    """Run the specified tests using pytest."""
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Build pytest arguments
    pytest_args = [python_exe, "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        pytest_args.extend(["-xvs"])
    else:
        pytest_args.extend(["-x"])
    
    # Add test selection
    if test_type == "unit":
        pytest_args.extend(["tests/", "-m", "unit"])
    elif test_type == "integration":
        pytest_args.extend(["tests/", "-m", "integration"])
    elif test_type == "performance":
        pytest_args.extend(["tests/", "-m", "performance"])
    elif test_type == "suricata":
        pytest_args.extend([
            "tests/unit_tests/test_suricata_integration.py",
            "tests/unit_tests/test_alert_correlation.py",
            "tests/integration_tests/test_suricata_integration.py",
            "tests/performance_tests/test_suricata_performance.py"
        ])
    else:  # all
        pytest_args.append("tests/")
    
    # Add JUnit XML output
    pytest_args.extend([
        "--junitxml", os.path.join(output_dir, "test-results.xml")
    ])
    
    # Run tests
    print(f"Running {test_type} tests...")
    result = subprocess.run(pytest_args, capture_output=False)
    
    # Run coverage if all tests
    if test_type == "all":
        print("Collecting code coverage...")
        coverage_args = pytest_args.copy()
        coverage_args.extend([
            "--cov=core",
            "--cov=utils", 
            "--cov=suricata",
            f"--cov-report=xml:{os.path.join(output_dir, 'coverage.xml')}",
            f"--cov-report=html:{os.path.join(output_dir, 'coverage_html')}"
        ])
        subprocess.run(coverage_args, capture_output=False)
    
    return result.returncode


def generate_summary(output_dir, test_type):
    """Generate test summary from XML results."""
    try:
        xml_path = os.path.join(output_dir, "test-results.xml")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Get the testsuite element
        testsuite = root.find('.//testsuite')
        if testsuite is None:
            testsuite = root  # Fallback to root if structure is different
        
        # Extract test stats
        total = int(testsuite.attrib.get('tests', 0))
        failures = int(testsuite.attrib.get('failures', 0))
        errors = int(testsuite.attrib.get('errors', 0))
        skipped = int(testsuite.attrib.get('skipped', 0))
        passed = total - failures - errors - skipped
        
        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total': total,
            'passed': passed,
            'failures': failures,
            'errors': errors,
            'skipped': skipped,
            'success_rate': round(passed / total * 100, 2) if total > 0 else 0,
            'test_type': test_type
        }
        
        # Save summary to file
        summary_path = os.path.join(output_dir, "summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print(f'\nTest Summary:')
        print(f'Total: {total}')
        print(f'Passed: {passed}')
        print(f'Failed: {failures}')
        print(f'Errors: {errors}')
        print(f'Skipped: {skipped}')
        print(f'Success Rate: {summary["success_rate"]}%')
        
        # Return exit code
        return 1 if failures > 0 or errors > 0 else 0
        
    except Exception as e:
        print(f'Error generating test summary: {e}')
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Zeek-YARA Integration tests")
    parser.add_argument(
        "--unit", action="store_const", const="unit", dest="test_type",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration", action="store_const", const="integration", dest="test_type",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--performance", action="store_const", const="performance", dest="test_type",
        help="Run only performance tests"
    )
    parser.add_argument(
        "--suricata", action="store_const", const="suricata", dest="test_type",
        help="Run only Suricata integration tests"
    )
    parser.add_argument(
        "--all", action="store_const", const="all", dest="test_type",
        help="Run all tests (default)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--output-dir", default="test_results",
        help="Directory for test results (default: test_results)"
    )
    
    args = parser.parse_args()
    
    # Default to all tests
    if args.test_type is None:
        args.test_type = "all"
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Get Python executable
    python_exe = activate_venv()
    print(f"Using Python: {python_exe}")
    
    # Run tests
    exit_code = run_tests(args.test_type, args.verbose, args.output_dir, python_exe)
    
    # Generate summary
    summary_exit_code = generate_summary(args.output_dir, args.test_type)
    
    # Use the worse of the two exit codes
    final_exit_code = max(exit_code, summary_exit_code)
    
    sys.exit(final_exit_code)


if __name__ == "__main__":
    main()