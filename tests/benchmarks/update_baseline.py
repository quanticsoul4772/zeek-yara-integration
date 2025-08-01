#!/usr/bin/env python3
"""
Benchmark Baseline Management Script

This script helps maintain performance benchmark baselines for the 
Zeek-YARA Integration platform.

Usage:
    python update_baseline.py --run-benchmarks  # Run benchmarks and update baseline
    python update_baseline.py --compare         # Compare current results with baseline
    python update_baseline.py --archive         # Archive current baseline to historical/
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_benchmarks(output_file="benchmark_results.json"):
    """Run performance benchmarks and save results"""
    print("🚀 Running performance benchmarks...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Run benchmarks with pytest-benchmark
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/performance_tests/", 
        "-v", 
        "--benchmark-only",
        f"--benchmark-json={output_file}"
    ]
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "PLATFORM")
    
    try:
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        print(f"✅ Benchmarks completed successfully")
        print(f"📊 Results saved to {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Benchmarks failed with exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def compare_with_baseline(results_file="benchmark_results.json", baseline_file="tests/benchmarks/baseline.json"):
    """Compare benchmark results with baseline"""
    print("📈 Comparing benchmark results with baseline...")
    
    if not os.path.exists(results_file):
        print(f"❌ Results file {results_file} not found")
        return False
        
    if not os.path.exists(baseline_file):
        print(f"❌ Baseline file {baseline_file} not found")
        return False
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    with open(baseline_file, 'r') as f:
        baseline = json.load(f)
    
    # Create lookup for baseline benchmarks
    baseline_lookup = {}
    for bench in baseline.get('benchmarks', []):
        baseline_lookup[bench['name']] = bench
    
    print("\n📊 Performance Comparison:")
    print("-" * 60)
    
    for bench in results.get('benchmarks', []):
        name = bench['name']
        current_mean = bench['stats']['mean']
        
        if name in baseline_lookup:
            baseline_mean = baseline_lookup[name]['stats']['mean']
            change_pct = ((current_mean - baseline_mean) / baseline_mean) * 100
            
            status = "🟢" if change_pct < 10 else "🟡" if change_pct < 50 else "🔴"
            print(f"{status} {name:40} {current_mean:8.4f}s ({change_pct:+6.1f}%)")
        else:
            print(f"🆕 {name:40} {current_mean:8.4f}s (new)")
    
    return True


def archive_baseline():
    """Archive current baseline to historical directory"""
    print("📚 Archiving current baseline...")
    
    baseline_file = Path("tests/benchmarks/baseline.json")
    if not baseline_file.exists():
        print(f"❌ Baseline file {baseline_file} not found")
        return False
    
    # Create historical directory
    historical_dir = Path("tests/benchmarks/historical")
    historical_dir.mkdir(exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_file = historical_dir / f"baseline_{timestamp}.json"
    
    # Copy baseline to historical
    shutil.copy2(baseline_file, archived_file)
    print(f"✅ Baseline archived to {archived_file}")
    
    return True


def update_baseline(results_file="benchmark_results.json"):
    """Update baseline with new benchmark results"""
    print("🔄 Updating baseline with new results...")
    
    if not os.path.exists(results_file):
        print(f"❌ Results file {results_file} not found")
        return False
    
    baseline_file = Path("tests/benchmarks/baseline.json")
    
    # Archive existing baseline if it exists
    if baseline_file.exists():
        archive_baseline()
    
    # Copy new results as baseline
    shutil.copy2(results_file, baseline_file)
    print(f"✅ Baseline updated from {results_file}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Manage performance benchmark baselines')
    parser.add_argument('--run-benchmarks', action='store_true', 
                       help='Run performance benchmarks')
    parser.add_argument('--compare', action='store_true',
                       help='Compare results with baseline')
    parser.add_argument('--archive', action='store_true',
                       help='Archive current baseline')
    parser.add_argument('--update-baseline', action='store_true',
                       help='Update baseline with new results')
    parser.add_argument('--results-file', default='benchmark_results.json',
                       help='Benchmark results file')
    parser.add_argument('--baseline-file', default='tests/benchmarks/baseline.json',
                       help='Baseline file path')
    
    args = parser.parse_args()
    
    if args.run_benchmarks:
        success = run_benchmarks(args.results_file)
        if success and args.update_baseline:
            update_baseline(args.results_file)
        elif success and args.compare:
            compare_with_baseline(args.results_file, args.baseline_file)
    elif args.compare:
        compare_with_baseline(args.results_file, args.baseline_file)
    elif args.archive:
        archive_baseline()
    elif args.update_baseline:
        update_baseline(args.results_file)
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python update_baseline.py --run-benchmarks --compare")
        print("  python update_baseline.py --run-benchmarks --update-baseline")
        print("  python update_baseline.py --archive")


if __name__ == "__main__":
    main()