# Zeek-YARA Integration Testing Framework

## Overview

The Zeek-YARA Integration Testing Framework provides a comprehensive testing infrastructure for the project, offering unit, integration, and performance tests. This framework was developed as part of Phase 3 implementation to ensure the reliability, performance, and functionality of the entire system.

## Testing Framework Components

The testing framework consists of the following components:

1. **Test Framework Core** (`tests/frameworks/test_framework.py`)
   - Provides the foundation for organizing and running tests
   - Implements test results collection and reporting
   - Supports test suites, cases, and result metrics

2. **Predefined Test Cases** (`tests/frameworks/test_cases.py`)
   - Ready-to-use test cases for common testing scenarios
   - Helper functions for creating custom test cases

3. **Unit Tests**
   - `tests/test_file_analyzer.py` - Tests for file analyzer utilities
   - `tests/test_database.py` - Tests for database operations
   - `tests/test_scanner.py` - Tests for scanner functionality

4. **Integration Tests**
   - `tests/integration_test.py` - End-to-end testing of the Zeek-YARA workflow

5. **Performance Tests**
   - Performance benchmarks for Phase 2 optimizations
   - Comparative analysis between different implementation approaches

## Running Tests

### Using the Test Runner Script

The simplest way to run the tests is using the provided script:

```bash
bin/run_tests.sh [OPTIONS]
```

Options:
- `--unit` - Run only unit tests
- `--integration` - Run only integration tests
- `--performance` - Run only performance tests
- `--all` - Run all tests (default)
- `--verbose` - Enable verbose output
- `--output-dir DIR` - Specify output directory for test results (default: test_results)

### Using the Python Test Framework

For more control, you can use the Python test framework directly:

```bash
python tests/run_test_framework.py [OPTIONS]
```

Options:
- `--config CONFIG` - Path to configuration file
- `--output-dir DIR` - Directory for test results
- `--test-type TYPE` - Type of tests to run (unit, integration, performance, all)
- `--verbose` - Enable verbose output

### Using Pytest Directly

For even more control, you can use pytest directly:

```bash
python -m pytest tests/ [OPTIONS]
```

## Test Results

Test results are stored in the output directory (default: `test_results/`) in JSON format. The results include:

- Overall statistics (pass/fail/skip counts)
- Detailed results for each test case
- Performance metrics for performance tests
- Timestamp and execution duration

## Writing New Tests

### Creating Unit Tests

To add new unit tests, create a new test file in the `tests/` directory following the pytest conventions:

```python
import pytest

@pytest.mark.unit
class TestMyFeature:
    def test_something(self):
        # Test implementation
        assert True
```

### Creating Performance Tests

To add new performance tests, use the performance mark and timer fixture:

```python
@pytest.mark.performance
class TestPerformance:
    def test_my_performance(self, timer):
        # Start timing
        timer.start()
        
        # Perform the operation to test
        result = my_function()
        
        # Stop timing
        duration = timer.stop().duration
        
        # Assert performance requirements
        assert duration < 0.1  # Operation should take less than 100ms
```

## Continuous Integration

The testing framework is designed to be integrated with CI/CD pipelines. Use the `bin/run_tests.sh` script in your CI configuration with appropriate options.

Example for GitHub Actions:

```yaml
- name: Run Tests
  run: |
    ./bin/run_tests.sh --all --output-dir ${{ github.workspace }}/test_results
```

## Coverage Reports

Code coverage reports are generated when running the full test suite and stored in the output directory. The reports include:

- XML report for CI integration
- HTML report for visual inspection
- Console summary output
