# Performance Benchmarks

This directory contains performance benchmark baselines and results for the Zeek-YARA Integration platform.

## Overview

Performance benchmarks are used to track system performance over time and identify performance regressions. The benchmarks cover key areas:

- **Alert Retrieval**: Database query performance for retrieving alerts
- **Alert Filtering**: Performance of filtered alert queries 
- **Alert Correlation**: Cross-system alert correlation performance
- **Database Operations**: Write performance for storing alerts and correlations
- **Alert Processing**: Suricata alert processing pipeline performance

## Running Benchmarks

To run performance benchmarks:

```bash
# Run all performance tests with benchmarking
bin/run_tests.sh --performance

# Run with pytest-benchmark directly
python -m pytest tests/performance_tests/ -v --benchmark-json=benchmark_results.json

# Run benchmark-only mode (skip non-benchmark tests)
python -m pytest tests/performance_tests/ -v --benchmark-only --benchmark-json=benchmark_results.json
```

## Baseline Files

- `baseline.json` - Current performance baseline for comparison
- `historical/` - Historical benchmark results for trend analysis

## Interpreting Results

Each benchmark measures:
- **Mean time**: Average execution time across multiple runs  
- **Std dev**: Standard deviation indicating consistency
- **Min/Max**: Fastest and slowest execution times
- **Ops/sec**: Operations per second (higher is better)

## Performance Targets

Current performance targets:
- Alert retrieval: < 100ms for 1000 alerts
- Alert filtering: < 50ms for filtered queries
- Alert correlation: < 5 seconds for 100 alert pairs
- Database writes: < 2 seconds for 100 correlation groups
- Alert processing: < 10 seconds for 500 alerts

## Regression Detection

Benchmarks will fail if performance degrades significantly from baseline:
- > 50% slower than baseline for critical operations
- > 100% slower than baseline for non-critical operations

Updates to baselines should be done consciously when:
1. Performance improvements are implemented
2. Functionality changes that affect performance characteristics
3. Infrastructure changes that impact timing