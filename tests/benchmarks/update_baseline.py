#!/usr/bin/env python3
"""
Benchmark Baseline Management Script

This script manages performance benchmark baselines for the Zeek-YARA-Suricata 
Integration Platform. It can run benchmarks, update baselines, and compare current
performance against established baselines.

Usage:
    python update_baseline.py --run-benchmarks --update-baseline
    python update_baseline.py --run-benchmarks --compare
    python update_baseline.py --help

Created: August 1, 2025
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BenchmarkManager:
    """Manages performance benchmark baselines and comparisons."""
    
    def __init__(self, baseline_path: str = None):
        """Initialize the benchmark manager.
        
        Args:
            baseline_path: Path to the baseline JSON file. Defaults to tests/benchmarks/baseline.json
        """
        if baseline_path is None:
            # Default to baseline.json in the same directory as this script
            script_dir = Path(__file__).parent
            baseline_path = script_dir / "baseline.json"
        
        self.baseline_path = Path(baseline_path)
        self.project_root = Path(__file__).parent.parent.parent
        
    def run_benchmarks(self, output_file: Optional[str] = None) -> Dict:
        """Run performance benchmarks and return results.
        
        Args:
            output_file: Optional path to save benchmark results JSON
            
        Returns:
            Dictionary containing benchmark results
        """
        if output_file is None:
            output_file = tempfile.mktemp(suffix='.json')
        
        # Build pytest command for running benchmarks
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance_tests/",
            "-v",
            "--benchmark-only",
            f"--benchmark-json={output_file}",
            "--benchmark-min-rounds=5",
            "--benchmark-max-time=30",
            "--benchmark-warmup=on"
        ]
        
        print("Running performance benchmarks...")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            # Change to project root for running tests
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Benchmark execution failed with return code {result.returncode}")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return None
                
            # Load and return benchmark results
            with open(output_file, 'r') as f:
                results = json.load(f)
                
            print(f"Benchmarks completed successfully. Results saved to {output_file}")
            return results
            
        except Exception as e:
            print(f"Error running benchmarks: {e}")
            return None
    
    def update_baseline(self, benchmark_results: Dict) -> bool:
        """Update the baseline with new benchmark results.
        
        Args:
            benchmark_results: Results from run_benchmarks()
            
        Returns:
            True if baseline was updated successfully
        """
        try:
            # Ensure the directory exists
            self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata about the baseline update
            baseline_data = benchmark_results.copy()
            baseline_data['baseline_info'] = {
                'created': datetime.now().isoformat(),
                'source': 'update_baseline.py',
                'description': 'Performance baseline updated via management script'
            }
            
            # Write the baseline file
            with open(self.baseline_path, 'w') as f:
                json.dump(baseline_data, f, indent=2)
                
            print(f"Baseline updated successfully: {self.baseline_path}")
            return True
            
        except Exception as e:
            print(f"Error updating baseline: {e}")
            return False
    
    def load_baseline(self) -> Optional[Dict]:
        """Load the current baseline.
        
        Returns:
            Baseline data or None if not found
        """
        try:
            if not self.baseline_path.exists():
                print(f"Baseline file not found: {self.baseline_path}")
                return None
                
            with open(self.baseline_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading baseline: {e}")
            return None
    
    def compare_with_baseline(self, current_results: Dict, baseline: Dict = None) -> Dict:
        """Compare current benchmark results with baseline.
        
        Args:
            current_results: Current benchmark results
            baseline: Baseline data (loaded automatically if not provided)
            
        Returns:
            Dictionary containing comparison results
        """
        if baseline is None:
            baseline = self.load_baseline()
            if baseline is None:
                return {"error": "No baseline available for comparison"}
        
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "summary": {"total_tests": 0, "improved": 0, "degraded": 0, "similar": 0},
            "details": []
        }
        
        # Get current and baseline benchmarks
        current_benchmarks = {b['fullname']: b for b in current_results.get('benchmarks', [])}
        baseline_benchmarks = {b['fullname']: b for b in baseline.get('benchmarks', [])}
        
        # Compare each benchmark
        for test_name, current in current_benchmarks.items():
            comparison["summary"]["total_tests"] += 1
            
            if test_name not in baseline_benchmarks:
                comparison["details"].append({
                    "test": test_name,
                    "status": "new",
                    "current_mean": current['stats']['mean'],
                    "baseline_mean": None,
                    "change_percent": None
                })
                continue
            
            baseline_test = baseline_benchmarks[test_name]
            current_mean = current['stats']['mean']
            baseline_mean = baseline_test['stats']['mean']
            
            # Calculate percentage change
            change_percent = ((current_mean - baseline_mean) / baseline_mean) * 100
            
            # Classify the change (using 10% threshold)
            if abs(change_percent) < 10:
                status = "similar"
                comparison["summary"]["similar"] += 1
            elif change_percent < 0:
                status = "improved"  # Faster is better
                comparison["summary"]["improved"] += 1
            else:
                status = "degraded"  # Slower is worse
                comparison["summary"]["degraded"] += 1
            
            comparison["details"].append({
                "test": test_name,
                "status": status,
                "current_mean": current_mean,
                "baseline_mean": baseline_mean,
                "change_percent": change_percent
            })
        
        return comparison
    
    def print_comparison_report(self, comparison: Dict):
        """Print a formatted comparison report.
        
        Args:
            comparison: Results from compare_with_baseline()
        """
        if "error" in comparison:
            print(f"❌ {comparison['error']}")
            return
        
        summary = comparison["summary"]
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK COMPARISON REPORT")
        print("="*60)
        print(f"Timestamp: {comparison['timestamp']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Improved: {summary['improved']} | Similar: {summary['similar']} | Degraded: {summary['degraded']}")
        print()
        
        # Print details for each test
        for detail in comparison["details"]:
            test_name = detail["test"].split("::")[-1]  # Get just the test method name
            status = detail["status"]
            
            # Status emoji
            emoji = {"improved": "✅", "similar": "➡️", "degraded": "❌", "new": "🆕"}[status]
            
            print(f"{emoji} {test_name}")
            
            if detail["baseline_mean"] is not None:
                print(f"   Current:  {detail['current_mean']:.6f}s")
                print(f"   Baseline: {detail['baseline_mean']:.6f}s")
                if detail["change_percent"] is not None:
                    change_str = f"{detail['change_percent']:+.1f}%"
                    print(f"   Change:   {change_str}")
            else:
                print(f"   Current:  {detail['current_mean']:.6f}s")
                print(f"   Status:   New test (no baseline)")
            print()
        
        # Overall verdict
        if summary["degraded"] > 0:
            print("⚠️  WARNING: Some benchmarks show performance degradation!")
        elif summary["improved"] > 0:
            print("🎉 Great! Some benchmarks show performance improvements!")
        else:
            print("✅ All benchmarks are performing within expected ranges.")


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Manage performance benchmark baselines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run benchmarks and update baseline
  python update_baseline.py --run-benchmarks --update-baseline
  
  # Run benchmarks and compare with existing baseline  
  python update_baseline.py --run-benchmarks --compare
  
  # Just compare existing results with baseline
  python update_baseline.py --compare --input results.json
  
  # Update baseline from existing results file
  python update_baseline.py --update-baseline --input results.json
        """
    )
    
    parser.add_argument(
        "--run-benchmarks", 
        action="store_true",
        help="Run performance benchmarks"
    )
    
    parser.add_argument(
        "--update-baseline",
        action="store_true", 
        help="Update the baseline with benchmark results"
    )
    
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare benchmark results with baseline"
    )
    
    parser.add_argument(
        "--input",
        type=str,
        help="Input JSON file with benchmark results (instead of running benchmarks)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for benchmark results (when running benchmarks)"
    )
    
    parser.add_argument(
        "--baseline",
        type=str,
        help="Path to baseline file (default: tests/benchmarks/baseline.json)"
    )
    
    args = parser.parse_args()
    
    # Create benchmark manager
    manager = BenchmarkManager(args.baseline)
    
    # Determine the source of benchmark results
    benchmark_results = None
    
    if args.input:
        # Load results from file
        try:
            with open(args.input, 'r') as f:
                benchmark_results = json.load(f)
            print(f"Loaded benchmark results from {args.input}")
        except Exception as e:
            print(f"Error loading results from {args.input}: {e}")
            sys.exit(1)
    elif args.run_benchmarks:
        # Run benchmarks
        benchmark_results = manager.run_benchmarks(args.output)
        if benchmark_results is None:
            print("Failed to run benchmarks")
            sys.exit(1)
    elif args.update_baseline or args.compare:
        print("Error: --update-baseline or --compare requires either --run-benchmarks or --input")
        sys.exit(1)
    
    # Perform requested actions
    if args.update_baseline:
        if benchmark_results is None:
            print("Error: No benchmark results available for baseline update")
            sys.exit(1)
        
        success = manager.update_baseline(benchmark_results)
        if not success:
            sys.exit(1)
    
    if args.compare:
        if benchmark_results is None:
            print("Error: No benchmark results available for comparison")
            sys.exit(1)
        
        comparison = manager.compare_with_baseline(benchmark_results)
        manager.print_comparison_report(comparison)
        
        # Exit with error code if there are performance degradations
        if comparison.get("summary", {}).get("degraded", 0) > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()