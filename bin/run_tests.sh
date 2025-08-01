#!/bin/bash
# Run the Zeek-YARA Integration Tests
# Created: April 24, 2025
# Author: Russell Smith

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT" || { echo "Error: Could not change to project root directory"; exit 1; }

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Default values
TEST_TYPE="all"
VERBOSE=false
TEST_OUTPUT_DIR="test_results"

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --unit)
        TEST_TYPE="unit"
        shift
        ;;
        --integration)
        TEST_TYPE="integration"
        shift
        ;;
        --performance)
        TEST_TYPE="performance"
        shift
        ;;
        --suricata)
        TEST_TYPE="suricata"
        shift
        ;;
        --all)
        TEST_TYPE="all"
        shift
        ;;
        --verbose)
        VERBOSE=true
        shift
        ;;
        --output-dir)
        TEST_OUTPUT_DIR="$2"
        shift
        shift
        ;;
        --help)
        echo "Usage: run_tests.sh [OPTIONS]"
        echo "Options:"
        echo "  --unit                Run only unit tests"
        echo "  --integration         Run only integration tests"
        echo "  --performance         Run only performance tests"
        echo "  --suricata            Run only Suricata integration tests"
        echo "  --all                 Run all tests (default)"
        echo "  --verbose             Enable verbose output"
        echo "  --output-dir DIR      Directory for test results (default: test_results)"
        echo "  --help                Show this help message"
        exit 0
        ;;
        *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
    esac
done

# Create output directory if it doesn't exist
mkdir -p "$TEST_OUTPUT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Set verbosity flag for Python
VERBOSE_FLAG=""
if [ "$VERBOSE" = true ]; then
    VERBOSE_FLAG="--verbose"
fi

# Select tests to run
case $TEST_TYPE in
    unit)
    echo "Running unit tests..."
    PYTEST_ARGS="-xvs tests/ -m unit"
    ;;
    integration)
    echo "Running integration tests..."
    PYTEST_ARGS="-xvs tests/ -m integration"
    ;;
    performance)
    echo "Running performance tests..."
    PYTEST_ARGS="-xvs tests/ -m performance"
    ;;
    suricata)
    echo "Running Suricata integration tests..."
    PYTEST_ARGS="-xvs tests/unit_tests/test_suricata_integration.py tests/unit_tests/test_alert_correlation.py tests/integration_tests/test_suricata_integration.py tests/performance_tests/test_suricata_performance.py"
    ;;
    all)
    echo "Running all tests..."
    PYTEST_ARGS="-xvs tests/"
    ;;
esac

# Run the tests
python -m pytest $PYTEST_ARGS --junitxml="$TEST_OUTPUT_DIR/test-results.xml" $VERBOSE_FLAG

# Collect code coverage if running all tests
if [ "$TEST_TYPE" = "all" ]; then
    echo "Collecting code coverage..."
    python -m pytest $PYTEST_ARGS --cov=core --cov=utils --cov=suricata --cov-report=xml:"$TEST_OUTPUT_DIR/coverage.xml" --cov-report=html:"$TEST_OUTPUT_DIR/coverage_html"
fi

# Generate test summary
echo "Generating test summary..."
python -c "
import os
import sys
import json
import datetime
from xml.etree import ElementTree

# Parse XML results
try:
    tree = ElementTree.parse('$TEST_OUTPUT_DIR/test-results.xml')
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
        'timestamp': datetime.datetime.now().isoformat(),
        'total': total,
        'passed': passed,
        'failures': failures,
        'errors': errors,
        'skipped': skipped,
        'success_rate': round(passed / total * 100, 2) if total > 0 else 0,
        'test_type': '$TEST_TYPE'
    }
    
    # Save summary to file
    with open('$TEST_OUTPUT_DIR/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print(f'\nTest Summary:')
    print(f'Total: {total}')
    print(f'Passed: {passed}')
    print(f'Failed: {failures}')
    print(f'Errors: {errors}')
    print(f'Skipped: {skipped}')
    print(f'Success Rate: {summary[\"success_rate\"]}%')
    
    # Set exit code
    sys.exit(1 if failures > 0 or errors > 0 else 0)
    
except Exception as e:
    print(f'Error generating test summary: {e}')
    sys.exit(1)
"

EXIT_CODE=$?

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate 2>/dev/null || true
fi

exit $EXIT_CODE
