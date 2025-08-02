# CI Workflow Validation Tests

This directory contains comprehensive tests to validate the GitHub Actions CI workflow configuration and ensure all CI jobs can run correctly.

## Overview

The CI validation tests are designed to:

1. **Validate workflow configuration** - Check that the CI YAML is properly structured
2. **Test individual job functionality** - Ensure each CI job can execute successfully
3. **Simulate CI environment** - Replicate CI conditions locally for testing
4. **Verify dependencies** - Check that all required tools and packages are available
5. **Validate job interdependencies** - Ensure jobs run in the correct order

## Test Structure

### Core Test Files

- `test_workflow_config.py` - Validates the CI workflow YAML structure and configuration
- `test_lint_format_job.py` - Tests the lint-and-format job (Black, isort, flake8, mypy)
- `test_unit_test_job.py` - Validates unit test job functionality and matrix strategy
- `test_integration_job.py` - Tests integration test job setup and execution
- `test_educational_content_job.py` - Validates educational content testing
- `test_cli_tool_job.py` - Tests CLI tool functionality and commands
- `test_security_scan_job.py` - Validates security scanning (Bandit, Safety)
- `test_docker_build_job.py` - Tests Docker build job functionality
- `test_performance_benchmark_job.py` - Validates performance benchmark job
- `test_documentation_build_job.py` - Tests documentation build (MkDocs)
- `test_ci_environment_simulation.py` - End-to-end CI workflow simulation

## Running CI Validation Tests

### Run All CI Tests
```bash
# From project root
python -m pytest tests/ci_tests/ -v
```

### Run Specific Job Tests
```bash
# Test workflow configuration
python -m pytest tests/ci_tests/test_workflow_config.py -v

# Test lint and format job
python -m pytest tests/ci_tests/test_lint_format_job.py -v

# Test unit test job
python -m pytest tests/ci_tests/test_unit_test_job.py -v
```

### Run by Test Markers
```bash
# Run CI validation tests
python -m pytest -m ci -v

# Run integration tests (CI simulation)
python -m pytest tests/ci_tests/ -m integration -v

# Run slow tests (full simulations)
python -m pytest tests/ci_tests/ -m slow -v
```

## Test Categories

### ✅ Configuration Tests
- YAML syntax validation
- Job dependency verification
- Matrix strategy validation
- Trigger condition testing

### ✅ Tool Availability Tests
- Code quality tools (Black, isort, flake8, mypy)
- Testing frameworks (pytest, pytest-cov, pytest-xdist)
- Security scanners (Bandit, Safety)
- Documentation tools (MkDocs, Material theme)
- CLI framework (Click)

### ✅ Environment Simulation Tests
- GitHub Actions environment variables
- Python version matrix testing
- OS compatibility testing
- Directory structure creation
- Dependency installation simulation

### ✅ Job Integration Tests
- Unit test discovery and execution
- Integration test setup and running
- CLI tool command execution
- Security scan execution
- Documentation build process

## Expected Test Behavior

### ✅ Passing Tests
These tests should always pass:
- Configuration validation
- Tool availability checks (for installed tools)
- Command structure validation
- Directory creation tests

### ⚠️ Conditional Tests
These tests may skip or provide warnings:
- Tool execution tests (if tools not installed)
- System dependency tests (if packages not available)
- Platform-specific tests (if running on different OS)

### 📊 Informational Tests
These tests provide information but don't fail:
- CI environment simulation
- Performance benchmark validation
- Security scan results
- Documentation build attempts

## CI Test Markers

The tests use pytest markers for organization:

- `@pytest.mark.ci` - CI workflow validation tests
- `@pytest.mark.integration` - Integration tests that actually run CI components
- `@pytest.mark.slow` - Tests that take longer to run (full simulations)
- `@pytest.mark.performance` - Performance-related tests

## Dependencies

### Required Python Packages
```
pytest
pytest-cov
pytest-xdist
pytest-benchmark
PyYAML
```

### Optional Tools (for full validation)
```
black
isort
flake8
mypy
bandit
safety
mkdocs
mkdocs-material
click
docker
```

### System Dependencies
- Git (for repository operations)
- Python 3.8+ (for compatibility testing)

## Troubleshooting

### Common Issues

1. **Tool not found errors**
   - Install missing tools: `pip install black isort flake8 mypy bandit safety`
   - Tests will skip if tools are not available

2. **Permission errors**
   - Ensure proper file permissions for CLI tools
   - Run: `chmod +x TOOLS/cli/zyi`

3. **Import errors**
   - Set PYTHONPATH: `export PYTHONPATH=$PWD/PLATFORM:$PYTHONPATH`
   - Install project in development mode: `pip install -e .`

4. **Docker errors**
   - Install Docker if testing Docker build functionality
   - Tests will skip if Docker is not available

### Debug Mode

Run tests with verbose output and no capture:
```bash
python -m pytest tests/ci_tests/ -v -s --tb=long
```

## Integration with CI

These tests are designed to:

1. **Validate CI configuration** before workflow runs
2. **Test CI components** in development environment
3. **Ensure compatibility** across different Python versions and OS
4. **Catch configuration errors** early in development process

## Contributing

When adding new CI jobs or modifying existing ones:

1. Add corresponding validation tests in this directory
2. Update test markers and documentation
3. Ensure tests handle missing dependencies gracefully
4. Include both positive and negative test cases
5. Document expected behavior and requirements