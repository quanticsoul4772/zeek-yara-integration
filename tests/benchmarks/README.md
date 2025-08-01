# Performance Benchmarks

This directory contains performance benchmark tests and management tools for the Zeek-YARA-Suricata Integration Platform.

## Overview

The performance benchmarking system uses `pytest-benchmark` to measure and track the performance of critical system components over time. This helps detect performance regressions and track improvements.

## Files

- **`baseline.json`** - Performance baseline data for comparison
- **`update_baseline.py`** - Management script for running benchmarks and updating baselines  
- **`README.md`** - This documentation file

## Quick Start

### Running Benchmarks

```bash
# Using the test script (recommended)
bin/run_tests.sh --benchmark

# Direct pytest-benchmark usage
python -m pytest tests/performance_tests/ -v --benchmark-only --benchmark-json=results.json

# Compare with baseline
python -m pytest tests/performance_tests/ -v --benchmark-compare=tests/benchmarks/baseline.json
```

### Managing Baselines

```bash
# Update baseline after performance improvements
python tests/benchmarks/update_baseline.py --run-benchmarks --update-baseline

# Compare current performance with baseline
python tests/benchmarks/update_baseline.py --run-benchmarks --compare

# Update baseline from existing results file
python tests/benchmarks/update_baseline.py --update-baseline --input results.json
```

## Benchmark Tests

The following performance tests are included:

### `test_alert_retrieval_performance`
- **Purpose**: Measures database query performance for retrieving alerts
- **Baseline**: ~0.005 seconds for 1000 alerts
- **Key Metric**: Time to retrieve all Suricata alerts from database

### `test_alert_filtering_performance`  
- **Purpose**: Measures filtered query performance
- **Baseline**: ~0.002 seconds for filtered queries
- **Key Metric**: Time to retrieve alerts with specific filters

### `test_correlation_performance`
- **Purpose**: Measures alert correlation algorithm performance
- **Baseline**: ~0.05 seconds for 100 alerts
- **Key Metric**: Time to correlate YARA and Suricata alerts

### `test_database_write_performance`
- **Purpose**: Measures database write performance for correlations
- **Baseline**: ~0.1 seconds for 100 correlation groups
- **Key Metric**: Time to store correlated alert data

### `test_process_alerts_performance`
- **Purpose**: Measures Suricata log processing performance
- **Baseline**: ~0.2 seconds for 100 alerts
- **Key Metric**: Time to parse and store Suricata eve.json logs

## Baseline Management

### Creating a New Baseline

When you make performance improvements or significant changes:

1. **Run benchmarks**: Ensure your changes are working correctly
2. **Verify improvements**: Compare against current baseline to see improvements
3. **Update baseline**: Create new baseline to track future regressions

```bash
# Complete workflow
python tests/benchmarks/update_baseline.py --run-benchmarks --compare
# Review the comparison report
python tests/benchmarks/update_baseline.py --run-benchmarks --update-baseline
```

### Baseline File Structure

The `baseline.json` file contains:

```json
{
  "machine_info": {
    "node": "system-info",
    "processor": "CPU details",
    "python_version": "3.x"
  },
  "commit_info": {
    "id": "commit-hash",
    "time": "timestamp",
    "branch": "branch-name"
  },
  "benchmarks": [
    {
      "name": "test_name",
      "fullname": "full.test.path",
      "stats": {
        "min": 0.001,
        "max": 0.01,
        "mean": 0.005,
        "stddev": 0.002,
        "median": 0.005
      }
    }
  ]
}
```

## CI Integration

### GitHub Actions

For continuous integration, add these steps to your workflow:

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install pytest pytest-benchmark
    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    if [ -f test-requirements.txt ]; then pip install -r test-requirements.txt; fi

- name: Create necessary directories
  run: |
    mkdir -p DATA/runtime/logs DATA/runtime/extracted-files DATA/runtime/alerts

- name: Run performance benchmarks
  run: |
    python -m pytest tests/performance_tests/ -v --benchmark-only --benchmark-json=benchmark.json --benchmark-compare=tests/benchmarks/baseline.json --benchmark-compare-fail=min:10% --benchmark-compare-fail=mean:20%
```

### Failure Thresholds

The CI is configured to fail if:
- **Minimum time** increases by more than 10%
- **Mean time** increases by more than 20%

## Performance Analysis

### Understanding Results

**Benchmark Output Metrics:**
- **Min**: Fastest execution time (best case)
- **Max**: Slowest execution time (worst case) 
- **Mean**: Average execution time (primary metric)
- **Median**: Middle value (less affected by outliers)
- **StdDev**: Standard deviation (consistency measure)

**Performance Categories:**
- **✅ Improved**: Mean time decreased (faster performance)
- **➡️ Similar**: Mean time within ±10% (stable performance)
- **❌ Degraded**: Mean time increased >10% (performance regression)

### Interpreting Trends

Monitor these patterns over time:
- **Gradual increases**: May indicate memory leaks or inefficient algorithms
- **Sudden spikes**: Usually indicate specific code changes causing regression
- **High variance**: May indicate system load or non-deterministic behavior

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Install missing dependencies
pip install pytest-benchmark
```

**2. Missing Dependencies**
```bash
# Check if test environment is properly set up
python -c "import suricata.suricata_integration"
```

**3. Database Connection Issues**
```bash
# Ensure test database can be created
mkdir -p tests/temp
sqlite3 tests/temp/test.db "SELECT 1;"
```

**4. Permission Issues**
```bash
# Make scripts executable
chmod +x tests/benchmarks/update_baseline.py
```

### Performance Debugging

If benchmarks show degradation:

1. **Profile the code**: Use `cProfile` or `line_profiler`
2. **Check system resources**: Monitor CPU, memory, and disk I/O
3. **Review recent changes**: Look at git history for performance-impacting changes
4. **Test isolated components**: Run individual benchmark tests

```bash
# Profile a specific test
python -m cProfile -o profile.stats -m pytest tests/performance_tests/test_suricata_performance.py::TestSuricataPerformance::test_correlation_performance -v --benchmark-only

# Analyze profile results
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

## Best Practices

### Writing Benchmark Tests

1. **Use representative data**: Test with realistic data sizes
2. **Minimize setup overhead**: Keep setup out of the benchmark loop
3. **Test one thing**: Each benchmark should focus on a single operation
4. **Use consistent data**: Ensure repeatable test conditions

### Managing Performance

1. **Regular monitoring**: Run benchmarks in CI/CD pipelines
2. **Baseline updates**: Update baselines after confirmed improvements
3. **Performance budgets**: Set acceptable performance thresholds
4. **Documentation**: Document performance expectations and trade-offs

## Advanced Usage

### Custom Benchmark Options

```bash
# Increase benchmark rounds for more accuracy
python -m pytest tests/performance_tests/ --benchmark-min-rounds=10 --benchmark-max-time=60

# Save detailed benchmark data
python -m pytest tests/performance_tests/ --benchmark-json=detailed_results.json --benchmark-verbose

# Run only specific benchmark groups
python -m pytest tests/performance_tests/ -k "alert_retrieval"
```

### Historical Analysis

```bash
# Compare multiple benchmark files
python tests/benchmarks/update_baseline.py --compare --input old_results.json
python tests/benchmarks/update_baseline.py --compare --input new_results.json

# Generate performance trends
python -c "
import json
import matplotlib.pyplot as plt
# Load multiple benchmark files and plot trends
"
```

---

For more information about pytest-benchmark, visit: https://pytest-benchmark.readthedocs.io/