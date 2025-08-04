#!/usr/bin/env python3
"""
Multi-threaded Scanner Performance Demonstration
Created: December 4, 2024

This script demonstrates the enhanced multi-threaded file scanning capabilities
with performance monitoring and health checking features.
"""

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "PLATFORM"))

from config.config import Config
from core.scanner import MultiThreadScanner, SingleThreadScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("performance_demo")


def create_test_files(directory, count=20):
    """Create test files for scanning demonstration"""
    test_files = []
    
    for i in range(count):
        file_path = os.path.join(directory, f"test_file_{i:03d}.txt")
        
        # Create varying file sizes and content
        if i % 10 == 0:
            # Include EICAR test string in every 10th file
            content = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        else:
            # Regular test content
            content = f"Test file {i}\n" + "Sample data line\n" * (i % 5 + 1)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        test_files.append(file_path)
    
    logger.info(f"Created {len(test_files)} test files in {directory}")
    return test_files


def demonstrate_single_threaded_performance(config, test_dir):
    """Demonstrate single-threaded scanner performance"""
    logger.info("=== Single-threaded Scanner Performance ===")
    
    scanner = SingleThreadScanner(config)
    
    start_time = time.time()
    result = scanner.scan_directory(test_dir)
    duration = time.time() - start_time
    
    logger.info(f"Single-threaded Results:")
    logger.info(f"  Files scanned: {result['scanned']}")
    logger.info(f"  Files matched: {result['matched']}")
    logger.info(f"  Total time: {duration:.2f} seconds")
    logger.info(f"  Throughput: {result['scanned'] / duration:.2f} files/second")
    
    return {
        "type": "single-threaded",
        "files_scanned": result['scanned'],
        "files_matched": result['matched'],
        "duration": duration,
        "throughput": result['scanned'] / duration
    }


def demonstrate_multithreaded_performance(config, test_dir, threads=4):
    """Demonstrate multi-threaded scanner performance with monitoring"""
    logger.info(f"=== Multi-threaded Scanner Performance ({threads} threads) ===")
    
    # Configure multi-threaded scanner
    mt_config = config.copy()
    mt_config.update({
        "THREADS": threads,
        "MAX_QUEUE_SIZE": 100,
        "HEALTH_CHECK_INTERVAL": 5,
        "MAX_WORKER_IDLE_TIME": 30
    })
    
    scanner = MultiThreadScanner(mt_config)
    
    # Start monitoring
    start_time = time.time()
    scanner.start_monitoring()
    
    try:
        # Wait for initial setup
        time.sleep(1)
        
        # Queue all files for scanning
        test_files = [f for f in os.listdir(test_dir) 
                     if os.path.isfile(os.path.join(test_dir, f))]
        
        for filename in test_files:
            file_path = os.path.join(test_dir, filename)
            scanner.queue_file(file_path)
        
        logger.info(f"Queued {len(test_files)} files for processing")
        
        # Monitor processing
        processed_files = 0
        while True:
            stats = scanner.get_performance_statistics()
            queue_size = stats['current_queue_size']
            processed_files = stats['files_processed']
            
            logger.info(f"Progress: {processed_files}/{len(test_files)} processed, "
                       f"queue: {queue_size}, "
                       f"throughput: {stats['throughput_files_per_second']:.2f} files/sec")
            
            if queue_size == 0 and processed_files >= len(test_files):
                break
                
            time.sleep(2)
        
        # Get final statistics
        final_stats = scanner.get_performance_statistics()
        health_status = scanner.get_worker_health_status()
        
        duration = time.time() - start_time
        
        logger.info(f"Multi-threaded Results:")
        logger.info(f"  Files processed: {final_stats['files_processed']}")
        logger.info(f"  Files matched: {final_stats['files_matched']}")
        logger.info(f"  Files failed: {final_stats['files_failed']}")
        logger.info(f"  Total time: {duration:.2f} seconds")
        logger.info(f"  Average scan time: {final_stats['average_scan_time_ms']:.2f} ms")
        logger.info(f"  Median scan time: {final_stats['median_scan_time_ms']:.2f} ms")
        logger.info(f"  Final throughput: {final_stats['throughput_files_per_second']:.2f} files/sec")
        
        # Show worker statistics
        logger.info("Worker Statistics:")
        for worker_id, stats in final_stats['worker_stats'].items():
            logger.info(f"  Worker {worker_id}: {stats['files_processed']} files, "
                       f"{stats['errors']} errors")
        
        # Show worker health
        logger.info("Worker Health:")
        for worker_name, health in health_status.items():
            logger.info(f"  {worker_name}: {health['status']}")
        
        return {
            "type": f"multi-threaded ({threads} threads)",
            "files_processed": final_stats['files_processed'],
            "files_matched": final_stats['files_matched'],
            "files_failed": final_stats['files_failed'],
            "duration": duration,
            "throughput": final_stats['throughput_files_per_second'],
            "avg_scan_time_ms": final_stats['average_scan_time_ms'],
            "worker_stats": final_stats['worker_stats'],
            "worker_health": health_status
        }
        
    finally:
        scanner.stop_monitoring()


def main():
    """Main demonstration function"""
    logger.info("Multi-threaded File Scanner Performance Demonstration")
    logger.info("=" * 60)
    
    # Load configuration
    try:
        config = Config.load_config()
        logger.info("Loaded configuration successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temporary directory: {temp_dir}")
        
        # Update config to use temp directory
        config["EXTRACT_DIR"] = temp_dir
        
        # Create test files
        test_files = create_test_files(temp_dir, count=25)
        
        # Run performance comparison
        results = []
        
        # Test single-threaded performance
        single_result = demonstrate_single_threaded_performance(config, temp_dir)
        results.append(single_result)
        
        # Test multi-threaded performance with different thread counts
        for thread_count in [2, 4, 6]:
            mt_result = demonstrate_multithreaded_performance(config, temp_dir, thread_count)
            results.append(mt_result)
        
        # Performance comparison summary
        logger.info("\n" + "=" * 60)
        logger.info("PERFORMANCE COMPARISON SUMMARY")
        logger.info("=" * 60)
        
        baseline_throughput = results[0]['throughput']
        
        for result in results:
            speedup = result['throughput'] / baseline_throughput
            logger.info(f"{result['type']:25} | "
                       f"Throughput: {result['throughput']:6.2f} files/sec | "
                       f"Speedup: {speedup:4.2f}x")
        
        # Show best performing configuration
        best_result = max(results, key=lambda r: r['throughput'])
        logger.info(f"\nBest Performance: {best_result['type']} "
                   f"({best_result['throughput']:.2f} files/sec)")
        
        logger.info("\nDemonstration completed successfully!")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())