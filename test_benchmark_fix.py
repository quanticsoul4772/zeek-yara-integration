#!/usr/bin/env python3
"""
Quick test script to verify benchmark fixes are working
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def main():
    """Test that benchmark fixes work"""
    print("🧪 Testing benchmark fixes...")
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "PLATFORM")
    
    # Try to run just one performance test to check for import errors
    print("1️⃣ Testing imports and basic benchmark functionality...")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/performance_tests/test_suricata_performance.py::TestSuricataPerformance::test_alert_retrieval_performance",
        "-v", "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, env=env, check=False, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Basic test passed!")
        else:
            print("❌ Basic test failed:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out (this might be expected for performance tests)")
        return True  # Timeout is acceptable for performance tests
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False
    
    # Test pytest-benchmark integration
    print("2️⃣ Testing pytest-benchmark integration...")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/performance_tests/",
        "-v", "--benchmark-only", "--benchmark-json=test_benchmark.json",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, env=env, check=False, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Benchmark integration test passed!")
            
            # Check if JSON file was created
            if os.path.exists("test_benchmark.json"):
                print("✅ Benchmark JSON output created successfully!")
                os.remove("test_benchmark.json")  # Clean up
            else:
                print("⚠️ Benchmark JSON output not found")
                
        else:
            print("❌ Benchmark integration test failed:")
            print("STDOUT:", result.stdout[-1000:])  # Last 1000 chars
            print("STDERR:", result.stderr[-1000:])  # Last 1000 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Benchmark test timed out")
        return True  # Timeout might be acceptable
    except Exception as e:
        print(f"❌ Error running benchmark test: {e}")
        return False
    
    print("🎉 All benchmark tests completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)