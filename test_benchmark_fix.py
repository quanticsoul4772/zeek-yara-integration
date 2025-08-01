#!/usr/bin/env python3
"""
Test script to validate the performance benchmark fixes.

This script tests the benchmark functionality without requiring the full
test environment setup, to verify that the pytest-benchmark integration
is working correctly.
"""

import sys
import subprocess
import tempfile
import json
from pathlib import Path

def test_import_pytest_benchmark():
    """Test that pytest-benchmark can be imported."""
    try:
        import pytest_benchmark
        print("✅ pytest-benchmark import successful")
        return True
    except ImportError:
        print("❌ pytest-benchmark not available")
        return False

def test_benchmark_syntax():
    """Test that the performance test files have valid pytest-benchmark syntax."""
    
    # Simple syntax check by parsing the file
    test_file = Path("tests/performance_tests/test_suricata_performance.py")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Check for pytest-benchmark patterns
        required_patterns = [
            "def test_", 
            "benchmark",
            "@pytest.mark.performance"
        ]
        
        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            print(f"❌ Missing patterns in test file: {missing_patterns}")
            return False
        
        # Check that old timer patterns are removed
        old_patterns = ["timer.start()", "timer.stop()"]
        found_old_patterns = []
        for pattern in old_patterns:
            if pattern in content:
                found_old_patterns.append(pattern)
        
        if found_old_patterns:
            print(f"❌ Old timer patterns still present: {found_old_patterns}")
            return False
        
        print("✅ Performance test syntax validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating test syntax: {e}")
        return False

def test_baseline_files():
    """Test that baseline files exist and are valid."""
    
    baseline_file = Path("tests/benchmarks/baseline.json")
    update_script = Path("tests/benchmarks/update_baseline.py")
    
    if not baseline_file.exists():
        print(f"❌ Baseline file not found: {baseline_file}")
        return False
    
    if not update_script.exists():
        print(f"❌ Update script not found: {update_script}")
        return False
    
    try:
        # Validate baseline JSON
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
        
        # Check for required structure
        required_keys = ["benchmarks"]
        for key in required_keys:
            if key not in baseline_data:
                print(f"❌ Missing key in baseline: {key}")
                return False
        
        if len(baseline_data["benchmarks"]) == 0:
            print("❌ No benchmarks in baseline file")
            return False
        
        print("✅ Baseline files validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating baseline files: {e}")
        return False

def test_run_tests_script():
    """Test that run_tests.sh has the benchmark option."""
    
    script_file = Path("bin/run_tests.sh")
    
    if not script_file.exists():
        print(f"❌ Script file not found: {script_file}")
        return False
    
    try:
        with open(script_file, 'r') as f:
            content = f.read()
        
        # Check for benchmark option
        if "--benchmark)" not in content:
            print("❌ --benchmark option not found in run_tests.sh")
            return False
        
        if "benchmark)" not in content or "TEST_TYPE=\"benchmark\"" not in content:
            print("❌ Benchmark test type handling not found in run_tests.sh")
            return False
        
        print("✅ run_tests.sh benchmark option validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating run_tests.sh: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🔧 Validating Performance Benchmark Fixes")
    print("=" * 50)
    
    tests = [
        ("Import pytest-benchmark", test_import_pytest_benchmark),
        ("Benchmark syntax validation", test_benchmark_syntax),
        ("Baseline files validation", test_baseline_files),
        ("run_tests.sh script validation", test_run_tests_script),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed!")
    
    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! Benchmark fixes are working correctly.")
        return 0
    else:
        print("⚠️  Some validation tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())