#!/bin/bash

# CI Workflow Validation Script
# This script runs comprehensive tests to validate the CI workflow configuration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}=== CI Workflow Validation ===${NC}"
echo "Project root: $PROJECT_ROOT"
echo

# Function to print section headers
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if pytest is available
if ! command -v python -m pytest &> /dev/null; then
    print_error "pytest not found. Please install: pip install pytest"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/PLATFORM:$PYTHONPATH"

# Parse command line arguments
VERBOSE=""
MARKERS=""
SPECIFIC_TEST=""
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v -s"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=tests/ci_tests --cov-report=html --cov-report=term"
            shift
            ;;
        -m|--marker)
            MARKERS="-m $2"
            shift 2
            ;;
        -t|--test)
            SPECIFIC_TEST="tests/ci_tests/$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -v, --verbose     Verbose output"
            echo "  -c, --coverage    Generate coverage report"
            echo "  -m, --marker      Run tests with specific marker (ci, integration, slow)"
            echo "  -t, --test        Run specific test file"
            echo "  -h, --help        Show this help"
            echo
            echo "Examples:"
            echo "  $0                          # Run all CI validation tests"
            echo "  $0 -v                       # Run with verbose output"
            echo "  $0 -m integration           # Run integration tests only"
            echo "  $0 -t test_workflow_config.py  # Run specific test file"
            echo "  $0 -c                       # Run with coverage report"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Install dependencies if needed
print_header "Checking Dependencies"
python -c "import pytest" 2>/dev/null && print_success "pytest available" || {
    print_warning "Installing pytest..."
    pip install pytest
}

python -c "import yaml" 2>/dev/null && print_success "PyYAML available" || {
    print_warning "Installing PyYAML..."
    pip install PyYAML
}

# Create necessary directories
print_header "Setting Up Test Environment"
mkdir -p DATA/runtime/logs
mkdir -p DATA/runtime/extracted-files
mkdir -p DATA/runtime/alerts
mkdir -p DATA/samples/benign
print_success "Test directories created"

# Determine what to run
if [[ -n "$SPECIFIC_TEST" ]]; then
    TEST_TARGET="$SPECIFIC_TEST"
    print_header "Running Specific Test: $(basename $SPECIFIC_TEST)"
elif [[ -n "$MARKERS" ]]; then
    TEST_TARGET="tests/ci_tests/"
    print_header "Running Tests with Marker: ${MARKERS#-m }"
else
    TEST_TARGET="tests/ci_tests/"
    print_header "Running All CI Validation Tests"
fi

# Build pytest command
PYTEST_CMD="python -m pytest $TEST_TARGET $VERBOSE $MARKERS $COVERAGE --tb=short"

echo "Command: $PYTEST_CMD"
echo

# Run the tests
if eval "$PYTEST_CMD"; then
    echo
    print_success "CI validation tests completed successfully!"
    
    # Show coverage report if generated
    if [[ -n "$COVERAGE" ]] && [[ -d "htmlcov" ]]; then
        echo
        print_success "Coverage report generated in htmlcov/"
        echo "Open htmlcov/index.html in your browser to view the report"
    fi
    
else
    echo
    print_error "Some CI validation tests failed or had issues"
    echo
    echo "Common issues and solutions:"
    echo "• Missing tools: Install with 'pip install black isort flake8 mypy bandit safety'"
    echo "• Permission errors: Run 'chmod +x TOOLS/cli/zyi'"
    echo "• Import errors: Check PYTHONPATH is set correctly"
    echo
    echo "For detailed output, run with -v flag: $0 -v"
    exit 1
fi

# Show summary
echo
print_header "CI Validation Summary"
echo "✓ Workflow configuration validated"
echo "✓ Job dependencies checked"
echo "✓ Tool availability verified"
echo "✓ Environment simulation completed"
echo
echo "Your CI workflow is ready! 🚀"