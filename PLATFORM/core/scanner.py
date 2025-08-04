#!/usr/bin/env python3
"""
Zeek-YARA Integration Scanner Module
Created: April 24, 2025
Author: Security Team

This module contains the core scanner functionality.
"""

import logging
import os
import statistics
import threading
import time
from collections import deque
from queue import Empty, Queue

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.database import DatabaseManager
from core.cleanup_manager import FileCleanupManager
from utils.file_utils import FileAnalyzer
from utils.yara_utils import RuleManager, YaraMatcher


class BaseScanner:
    """Base class for scanners with common functionality"""

    def __init__(self, config):
        """
        Initialize the base scanner.

        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.extract_dir = config.get("EXTRACT_DIR")
        self.logger = logging.getLogger("zeek_yara.scanner")

        # Initialize components
        self.file_analyzer = FileAnalyzer(max_file_size=config.get("MAX_FILE_SIZE"))
        self.rule_manager = RuleManager(
            rules_dir=config.get("RULES_DIR"), rules_index=config.get("RULES_INDEX")
        )
        self.yara_matcher = YaraMatcher(
            rule_manager=self.rule_manager, timeout=config.get("SCAN_TIMEOUT", 60)
        )
        self.db_manager = DatabaseManager(db_file=config.get("DB_FILE"))
        self.cleanup_manager = FileCleanupManager(config)

        # Callback for notifications
        self.scan_callback = None

        # Prepare rules
        self.rule_manager.compile_rules()

        # Recovery mechanism for interrupted scans
        self.recover_interrupted_scans()

    def scan_file(self, file_path):
        """
        Scan a single file with YARA and process the results.

        Args:
            file_path (str): Path to the file to scan

        Returns:
            dict: Scan result dictionary
        """
        scan_start_time = time.perf_counter()
        
        # Check if file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return {"matched": False, "error": "File not found"}

        # Check if file is too large
        if self.file_analyzer.is_file_too_large(file_path):
            self.logger.warning(f"File too large to scan: {file_path}")
            # Update state to failed due to size limit
            self.db_manager.update_file_state(file_path, 'failed', 'File too large to scan')
            return {"matched": False, "error": "File too large"}

        # Check if file has already been processed
        file_state = self.db_manager.get_file_state(file_path)
        if file_state:
            if file_state['state'] == 'completed':
                self.logger.info(f"File already processed: {file_path}")
                return {"matched": False, "error": "Already processed", "cached": True}
            elif file_state['state'] == 'scanning':
                self.logger.info(f"File currently being scanned: {file_path}")
                return {"matched": False, "error": "Currently scanning", "in_progress": True}
            elif file_state['state'] == 'quarantined':
                self.logger.info(f"File quarantined: {file_path}")
                return {"matched": False, "error": "File quarantined", "quarantined": True}

        # Get file metadata
        try:
            file_metadata = self.file_analyzer.get_file_metadata(file_path)
            self.logger.debug(f"File metadata: {file_metadata}")
        except Exception as e:
            self.logger.error(f"Error getting file metadata: {e}")
            file_metadata = {"file_path": file_path, "name": os.path.basename(file_path)}

        # Add file to state tracking if not already present
        if not file_state:
            self.db_manager.add_file_state(file_path, file_metadata)

        # Update state to scanning
        self.db_manager.update_file_state(file_path, 'scanning')

        # Log basic file info
        self.logger.info(f"Scanning: {file_path} ({file_metadata.get('size', 0)} bytes)")

        try:
            # Apply mime-type or extension filtering if configured
            if self.config.get("SCAN_MIME_TYPES") and not self.file_analyzer.filter_file_by_mime(
                file_path, self.config.get("SCAN_MIME_TYPES")
            ):
                self.logger.info(f"Skipping file with excluded MIME type: {file_path}")
                self.db_manager.update_file_state(file_path, 'completed', 'Excluded MIME type', 
                                                int((time.perf_counter() - scan_start_time) * 1000))
                return {"matched": False, "error": "Excluded MIME type"}

            if self.config.get("SCAN_EXTENSIONS") and not self.file_analyzer.filter_file_by_extension(
                file_path, self.config.get("SCAN_EXTENSIONS")
            ):
                self.logger.info(f"Skipping file with excluded extension: {file_path}")
                self.db_manager.update_file_state(file_path, 'completed', 'Excluded extension',
                                                int((time.perf_counter() - scan_start_time) * 1000))
                return {"matched": False, "error": "Excluded extension"}

            # Scan file with YARA
            scan_result = self.yara_matcher.scan_file(file_path)

            # Calculate scan duration
            scan_duration_ms = int((time.perf_counter() - scan_start_time) * 1000)

            # Process and store results
            if scan_result.get("matched", False):
                self.logger.info(f"YARA match found in {file_metadata.get('name', '')}")

                # Log match details
                for match in scan_result.get("matches", []):
                    rule_name = match.get("rule", "unknown")
                    rule_namespace = match.get("namespace", "unknown")
                    self.logger.info(f"  Rule Match: {rule_namespace}.{rule_name}")

                    # Log metadata if available
                    meta = match.get("meta", {})
                    for key, value in meta.items():
                        self.logger.info(f"    {key}: {value}")

                # Add to database
                try:
                    add_result = self.db_manager.add_alert(file_metadata, scan_result)
                    if add_result:
                        self.logger.info(
                            f"Added alert to database for file: {file_metadata.get('name', '')}"
                        )
                    else:
                        self.logger.error(
                            f"Failed to add alert to database for file: {file_metadata.get('name', '')}"
                        )
                except Exception as e:
                    self.logger.error(f"Exception adding alert to database: {e}")

                # Update state to completed (successful scan with matches)
                self.db_manager.update_file_state(file_path, 'completed', None, scan_duration_ms)
            else:
                if scan_result.get("error"):
                    self.logger.warning(f"Error scanning {file_path}: {scan_result.get('error')}")
                    # Update state to failed due to scan error
                    self.db_manager.update_file_state(file_path, 'failed', scan_result.get('error'), scan_duration_ms)
                else:
                    self.logger.info(f"No matches for file: {file_path}")
                    # Update state to completed (successful scan, no matches)
                    self.db_manager.update_file_state(file_path, 'completed', None, scan_duration_ms)

            # Call the scan callback if registered
            if self.scan_callback is not None:
                try:
                    self.scan_callback(file_path, scan_result)
                except Exception as e:
                    self.logger.error(f"Error in scan callback: {e}")

            return scan_result

        except Exception as e:
            # Handle any unexpected errors during scanning
            scan_duration_ms = int((time.perf_counter() - scan_start_time) * 1000)
            error_msg = f"Unexpected error during scan: {str(e)}"
            self.logger.error(f"Error scanning {file_path}: {error_msg}")
            
            # Update state to failed
            self.db_manager.update_file_state(file_path, 'failed', error_msg, scan_duration_ms)
            
            return {"matched": False, "error": error_msg}

    def scan_directory(self, directory=None):
        """
        Scan all files in a directory.

        Args:
            directory (str, optional): Directory to scan. Defaults to extract_dir.

        Returns:
            dict: Summary of scan results
        """
        directory = directory or self.extract_dir

        if not os.path.exists(directory) or not os.path.isdir(directory):
            self.logger.error(f"Directory not found: {directory}")
            return {"error": "Directory not found", "scanned": 0, "matched": 0}

        self.logger.info(f"Scanning files in directory: {directory}")

        results = {
            "scanned": 0,
            "matched": 0,
            "skipped": 0,
            "errors": 0,
            "start_time": time.time(),
            "matches": [],
        }

        try:
            # Iterate through files in the directory
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)

                # Skip directories
                if os.path.isdir(file_path):
                    continue

                # Scan the file
                scan_result = self.scan_file(file_path)

                # Check the result type
                if (
                    scan_result.get("error") == "Excluded MIME type"
                    or scan_result.get("error") == "Excluded extension"
                ):
                    results["skipped"] += 1
                else:
                    results["scanned"] += 1

                if scan_result.get("matched", False):
                    results["matched"] += 1
                    results["matches"].append(file_path)

                if scan_result.get("error"):
                    results["errors"] += 1

        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {str(e)}")
            results["error"] = str(e)

        # Calculate duration
        results["duration"] = time.time() - results["start_time"]

        self.logger.info(
            f"Directory scan complete: {results['scanned']} files scanned, "
            f"{results['skipped']} files skipped, "
            f"{results['matched']} matches found in {results['duration']:.2f} seconds"
        )

        return results

    def get_cleanup_statistics(self):
        """
        Get file cleanup statistics.

        Returns:
            dict: Cleanup statistics and configuration
        """
        return self.cleanup_manager.get_statistics()

    def force_cleanup(self):
        """
        Force an immediate cleanup operation.

        Returns:
            dict: Cleanup operation results
        """
        return self.cleanup_manager.force_cleanup()

    def recover_interrupted_scans(self, timeout_minutes=30):
        """
        Recover files that were interrupted during scanning.
        
        Args:
            timeout_minutes (int): Minutes after which a scanning state is considered interrupted
            
        Returns:
            int: Number of files recovered
        """
        try:
            recovered_count = self.db_manager.recover_interrupted_scans(timeout_minutes)
            if recovered_count > 0:
                self.logger.info(f"Recovered {recovered_count} interrupted scans on startup")
            return recovered_count
        except Exception as e:
            self.logger.error(f"Error recovering interrupted scans: {e}")
            return 0

    def get_processing_statistics(self):
        """
        Get file processing state statistics.
        
        Returns:
            dict: Processing statistics
        """
        try:
            return self.db_manager.get_state_statistics()
        except Exception as e:
            self.logger.error(f"Error getting processing statistics: {e}")
            return {}

    def quarantine_file(self, file_path, reason="Manual quarantine"):
        """
        Quarantine a file by updating its state.
        
        Args:
            file_path (str): Path to the file
            reason (str): Reason for quarantine
            
        Returns:
            bool: True if quarantined successfully
        """
        try:
            return self.db_manager.update_file_state(file_path, 'quarantined', reason)
        except Exception as e:
            self.logger.error(f"Error quarantining file {file_path}: {e}")
            return False

    def get_pending_files(self, limit=None):
        """
        Get files in pending state.
        
        Args:
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of pending files
        """
        try:
            return self.db_manager.get_files_by_state('pending', limit)
        except Exception as e:
            self.logger.error(f"Error getting pending files: {e}")
            return []


class SingleThreadScanner(BaseScanner):
    """Single-threaded scanner implementation"""

    def __init__(self, config):
        """Initialize the single-threaded scanner"""
        super().__init__(config)
        self.logger = logging.getLogger("zeek_yara.single_scanner")
        self.running = False
        self.observer = None

    def start_monitoring(self):
        """
        Start monitoring the extract directory for new files.

        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("Scanner is already running")
            return False

        try:
            # Set up file watching
            event_handler = FileEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.extract_dir, recursive=False)
            self.observer.start()

            self.running = True
            self.logger.info(f"Started monitoring directory: {self.extract_dir}")

            # Start cleanup manager
            if not self.cleanup_manager.start_cleanup_scheduler():
                self.logger.warning("Failed to start file cleanup scheduler")

            # Scan existing files in the directory
            self.scan_directory()

            return True

        except Exception as e:
            self.logger.error(f"Error starting monitoring: {str(e)}")
            return False

    def stop_monitoring(self):
        """
        Stop monitoring the extract directory.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("Scanner is not running")
            return False

        try:
            self.running = False

            # Stop cleanup manager
            if not self.cleanup_manager.stop_cleanup_scheduler():
                self.logger.warning("Failed to stop file cleanup scheduler")

            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None

            self.logger.info("Stopped monitoring")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {str(e)}")
            return False

    def update_rules(self):
        """
        Update YARA rules.

        Returns:
            bool: True if rules were updated, False otherwise
        """
        return self.rule_manager.compile_rules(force=True)


class MultiThreadScanner(BaseScanner):
    """Multi-threaded scanner implementation with enhanced performance monitoring"""

    def __init__(self, config):
        """Initialize the multi-threaded scanner"""
        super().__init__(config)
        self.logger = logging.getLogger("zeek_yara.multi_scanner")
        self.running = False
        self.observer = None

        # Threading components
        self.num_threads = config.get("THREADS", 2)
        self.max_queue_size = config.get("MAX_QUEUE_SIZE", 1000)
        self.queue_timeout_normal = config.get("QUEUE_TIMEOUT_NORMAL", 1.0)
        self.queue_timeout_priority = config.get("QUEUE_TIMEOUT_PRIORITY", 0.1)
        self.file_queue = Queue(maxsize=self.max_queue_size)
        self.worker_threads = []
        self.stop_event = threading.Event()

        # Performance monitoring
        self.performance_stats = {
            "files_processed": 0,
            "files_matched": 0,
            "files_failed": 0,
            "total_processing_time": 0.0,
            "scan_times": deque(maxlen=100),  # Keep last 100 scan times for statistics
            "queue_size_samples": deque(maxlen=50),  # Queue size monitoring
            "worker_stats": {},  # Per-worker statistics
            "start_time": None,
            "lock": threading.Lock()
        }

        # Worker health monitoring
        self.worker_health = {}
        self.health_check_interval = config.get("HEALTH_CHECK_INTERVAL", 30)
        self.max_worker_idle_time = config.get("MAX_WORKER_IDLE_TIME", 300)
        
        # Initialize worker stats
        for i in range(self.num_threads):
            worker_id = i + 1
            self.performance_stats["worker_stats"][worker_id] = {
                "files_processed": 0,
                "processing_time": 0.0,
                "errors": 0,
                "last_activity": None
            }
            self.worker_health[worker_id] = {
                "status": "idle",
                "last_heartbeat": time.time(),
                "current_file": None
            }

    def start_monitoring(self):
        """
        Start monitoring the extract directory with multiple threads.

        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("Scanner is already running")
            return False

        try:
            # Clear stop event and reset performance stats
            self.stop_event.clear()
            with self.performance_stats["lock"]:
                self.performance_stats["start_time"] = time.time()
                self.performance_stats["files_processed"] = 0
                self.performance_stats["files_matched"] = 0
                self.performance_stats["files_failed"] = 0
                self.performance_stats["total_processing_time"] = 0.0
                self.performance_stats["scan_times"].clear()
                self.performance_stats["queue_size_samples"].clear()

            # Start worker threads
            for i in range(self.num_threads):
                thread = threading.Thread(target=self._worker_thread, args=(i + 1,), daemon=True)
                thread.start()
                self.worker_threads.append(thread)
                self.logger.info(f"Started scanner thread {i + 1}")

            # Start performance monitoring thread
            monitor_thread = threading.Thread(target=self._performance_monitor, daemon=True)
            monitor_thread.start()
            self.worker_threads.append(monitor_thread)

            # Set up file watching
            event_handler = FileEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.extract_dir, recursive=False)
            self.observer.start()

            self.running = True
            self.logger.info(
                f"Started monitoring directory with {self.num_threads} threads (max queue: {self.max_queue_size}): {self.extract_dir}"
            )

            # Start cleanup manager
            if not self.cleanup_manager.start_cleanup_scheduler():
                self.logger.warning("Failed to start file cleanup scheduler")

            # Queue existing files for scanning
            queued_existing = 0
            for filename in os.listdir(self.extract_dir):
                file_path = os.path.join(self.extract_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        self.file_queue.put(file_path, timeout=self.queue_timeout_normal)
                        queued_existing += 1
                        self.logger.debug(f"Queued existing file: {file_path}")
                    except:
                        self.logger.warning(f"Queue full, skipping existing file: {file_path}")
                        break

            # Queue pending files from previous runs
            pending_files = self.get_pending_files()
            queued_pending = 0
            for file_record in pending_files:
                file_path = file_record['file_path']
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    try:
                        self.file_queue.put(file_path, timeout=self.queue_timeout_priority)
                        queued_pending += 1
                        self.logger.debug(f"Queued pending file: {file_path}")
                    except:
                        self.logger.debug(f"Queue full, will process pending file later: {file_path}")
                        break
                else:
                    # File no longer exists, mark as failed
                    self.db_manager.update_file_state(file_path, 'failed', 'File no longer exists')

            self.logger.info(f"Queued {queued_existing} existing files and {queued_pending} pending files for processing")
            return True

        except Exception as e:
            self.logger.error(f"Error starting monitoring: {str(e)}")
            # Clean up any started threads
            self.stop_monitoring()
            return False

    def stop_monitoring(self):
        """
        Stop monitoring and all worker threads gracefully.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("Scanner is not running")
            return False

        try:
            # Log final performance statistics
            final_stats = self.get_performance_statistics()
            self.logger.info(f"Final performance statistics: {final_stats}")

            # Signal threads to stop
            self.stop_event.set()

            # Stop cleanup manager
            if not self.cleanup_manager.stop_cleanup_scheduler():
                self.logger.warning("Failed to stop file cleanup scheduler")

            # Wait for threads to finish gracefully
            timeout_per_thread = 5.0
            for i, thread in enumerate(self.worker_threads):
                if thread.is_alive():
                    self.logger.debug(f"Waiting for thread {i+1} to complete...")
                    thread.join(timeout=timeout_per_thread)
                    if thread.is_alive():
                        self.logger.warning(f"Thread {i+1} did not shut down gracefully")

            # Clear thread list
            self.worker_threads = []

            # Stop the observer
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None

            self.running = False
            
            # Clean up worker_health dictionary to prevent memory leak
            self.worker_health.clear()
            self.logger.debug("Cleared worker_health dictionary")
            
            # Calculate final uptime
            uptime = 0
            with self.performance_stats["lock"]:
                if self.performance_stats["start_time"]:
                    uptime = time.time() - self.performance_stats["start_time"]
            
            self.logger.info(f"Stopped monitoring and all worker threads (uptime: {uptime:.1f}s)")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {str(e)}")
            return False

    def queue_file(self, file_path, priority=False):
        """
        Add a file to the scanning queue with optional priority.

        Args:
            file_path (str): Path to the file to scan
            priority (bool): If True, attempt to add to front of queue (not guaranteed in standard Queue)
            
        Returns:
            bool: True if file was queued successfully
        """
        try:
            # Use timeout to avoid blocking indefinitely if queue is full
            timeout = self.queue_timeout_priority if priority else self.queue_timeout_normal
            self.file_queue.put(file_path, timeout=timeout)
            return True
        except:
            self.logger.warning(f"Queue full, could not add file: {file_path}")
            return False

    def update_rules(self):
        """
        Update YARA rules.

        Returns:
            bool: True if rules were updated, False otherwise
        """
        return self.rule_manager.compile_rules(force=True)

    def get_queue_size(self):
        """
        Get the current size of the scanning queue.

        Returns:
            int: Number of files waiting to be scanned
        """
        return self.file_queue.qsize()
    
    def get_performance_statistics(self):
        """
        Get comprehensive performance statistics.
        
        Returns:
            dict: Performance statistics including throughput, timing, and worker health
        """
        with self.performance_stats["lock"]:
            stats = self.performance_stats.copy()
            
        # Calculate derived statistics
        uptime = 0
        if stats["start_time"]:
            uptime = time.time() - stats["start_time"]
            
        throughput = stats["files_processed"] / uptime if uptime > 0 else 0
        
        # Calculate timing statistics
        scan_times = list(stats["scan_times"])
        avg_scan_time = statistics.mean(scan_times) if scan_times else 0
        median_scan_time = statistics.median(scan_times) if scan_times else 0
        
        # Queue statistics
        queue_samples = list(stats["queue_size_samples"])
        avg_queue_size = statistics.mean(queue_samples) if queue_samples else 0
        
        return {
            "uptime_seconds": round(uptime, 1),
            "files_processed": stats["files_processed"],
            "files_matched": stats["files_matched"],
            "files_failed": stats["files_failed"],
            "throughput_files_per_second": round(throughput, 2),
            "average_scan_time_ms": round(avg_scan_time * 1000, 2),
            "median_scan_time_ms": round(median_scan_time * 1000, 2),
            "current_queue_size": self.get_queue_size(),
            "average_queue_size": round(avg_queue_size, 1),
            "active_threads": self.num_threads,
            "worker_stats": stats["worker_stats"].copy(),
            "worker_health": self.worker_health.copy()
        }
    
    def get_worker_health_status(self):
        """
        Get health status of all worker threads.
        
        Returns:
            dict: Health status of each worker
        """
        current_time = time.time()
        health_status = {}
        
        for worker_id, health in self.worker_health.items():
            time_since_heartbeat = current_time - health["last_heartbeat"]
            
            if time_since_heartbeat > self.max_worker_idle_time:
                status = "unhealthy"
            elif time_since_heartbeat > self.health_check_interval:
                status = "warning"
            else:
                status = "healthy"
                
            health_status[f"worker_{worker_id}"] = {
                "status": status,
                "last_heartbeat_ago": round(time_since_heartbeat, 1),
                "current_file": health["current_file"],
                "worker_status": health["status"]
            }
            
        return health_status

    def _worker_thread(self, thread_id):
        """
        Enhanced worker thread function with performance monitoring.

        Args:
            thread_id (int): Thread identifier
        """
        self.logger.info(f"Scanner thread {thread_id} started")
        
        # Initialize worker-specific statistics
        worker_stats = self.performance_stats["worker_stats"][thread_id]
        worker_health = self.worker_health[thread_id]

        while not self.stop_event.is_set():
            try:
                # Update heartbeat
                worker_health["last_heartbeat"] = time.time()
                worker_health["status"] = "idle"
                worker_health["current_file"] = None

                # Get file from queue with timeout
                try:
                    file_path = self.file_queue.get(timeout=1.0)
                except Empty:
                    # No files to scan, continue waiting
                    continue

                # Update worker status
                worker_health["status"] = "processing"
                worker_health["current_file"] = os.path.basename(file_path)
                worker_health["last_heartbeat"] = time.time()

                # Scan the file with timing
                scan_start_time = time.perf_counter()
                scan_result = None
                
                try:
                    scan_result = self.scan_file(file_path)
                    worker_stats["files_processed"] += 1
                    
                    # Update global statistics
                    with self.performance_stats["lock"]:
                        self.performance_stats["files_processed"] += 1
                        if scan_result and scan_result.get("matched", False):
                            self.performance_stats["files_matched"] += 1
                        elif scan_result and scan_result.get("error"):
                            self.performance_stats["files_failed"] += 1
                            worker_stats["errors"] += 1
                            
                except Exception as e:
                    self.logger.error(f"Thread {thread_id} error scanning {file_path}: {str(e)}")
                    worker_stats["errors"] += 1
                    
                    with self.performance_stats["lock"]:
                        self.performance_stats["files_failed"] += 1
                
                # Record timing statistics
                scan_duration = time.perf_counter() - scan_start_time
                worker_stats["processing_time"] += scan_duration
                worker_stats["last_activity"] = time.time()
                
                with self.performance_stats["lock"]:
                    self.performance_stats["total_processing_time"] += scan_duration
                    self.performance_stats["scan_times"].append(scan_duration)

                # Mark task as done
                self.file_queue.task_done()

            except Exception as e:
                self.logger.error(f"Thread {thread_id} error: {str(e)}")
                worker_stats["errors"] += 1
                # Sleep briefly to avoid tight loop in case of persistent error
                time.sleep(1.0)

        worker_health["status"] = "stopped"
        self.logger.info(f"Scanner thread {thread_id} stopped (processed {worker_stats['files_processed']} files)")
    
    def _performance_monitor(self):
        """
        Background thread for performance monitoring and health checks.
        """
        self.logger.info("Performance monitor thread started")
        
        while not self.stop_event.is_set():
            try:
                # Sample queue size for statistics
                queue_size = self.get_queue_size()
                with self.performance_stats["lock"]:
                    self.performance_stats["queue_size_samples"].append(queue_size)
                
                # Check worker health
                current_time = time.time()
                unhealthy_workers = 0
                
                for worker_id, health in self.worker_health.items():
                    time_since_heartbeat = current_time - health["last_heartbeat"]
                    if time_since_heartbeat > self.max_worker_idle_time:
                        unhealthy_workers += 1
                        self.logger.warning(f"Worker {worker_id} appears unhealthy (no heartbeat for {time_since_heartbeat:.1f}s)")
                
                # Log performance summary periodically
                if hasattr(self, '_last_perf_log'):
                    if current_time - self._last_perf_log > 300:  # Every 5 minutes
                        stats = self.get_performance_statistics()
                        self.logger.info(f"Performance: {stats['files_processed']} files processed, "
                                       f"{stats['throughput_files_per_second']} files/sec, "
                                       f"queue: {stats['current_queue_size']}, "
                                       f"avg scan: {stats['average_scan_time_ms']}ms")
                        self._last_perf_log = current_time
                else:
                    self._last_perf_log = current_time
                
                # Sleep until next check, but check stop_event frequently for responsive shutdown
                sleep_remaining = self.health_check_interval
                sleep_increment = 1.0  # Check stop_event every second
                while sleep_remaining > 0 and not self.stop_event.is_set():
                    sleep_time = min(sleep_increment, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time
                
            except Exception as e:
                self.logger.error(f"Performance monitor error: {e}")
                # Sleep with responsive shutdown checking after errors too
                sleep_remaining = self.health_check_interval
                sleep_increment = 1.0
                while sleep_remaining > 0 and not self.stop_event.is_set():
                    sleep_time = min(sleep_increment, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time
        
        self.logger.info("Performance monitor thread stopped")


class FileEventHandler(FileSystemEventHandler):
    """File event handler for watchdog"""

    def __init__(self, scanner):
        """
        Initialize file event handler.

        Args:
            scanner (BaseScanner): Scanner instance to use for processing
        """
        self.scanner = scanner
        self.logger = logging.getLogger("zeek_yara.file_handler")
        super().__init__()

    def on_created(self, event):
        """
        Handle file creation events.

        Args:
            event (FileCreatedEvent): File creation event
        """
        if event.is_directory:
            return

        # Wait a moment for file to be completely written
        time.sleep(1)

        self.logger.info(f"New file detected: {event.src_path}")

        # Add file to state tracking as pending
        try:
            file_metadata = self.scanner.file_analyzer.get_file_metadata(event.src_path)
        except Exception as e:
            self.logger.warning(f"Could not get metadata for {event.src_path}: {e}")
            file_metadata = None

        self.scanner.db_manager.add_file_state(event.src_path, file_metadata)

        # Process differently based on scanner type
        if isinstance(self.scanner, MultiThreadScanner):
            # Add to queue for multi-threaded scanner
            self.scanner.queue_file(event.src_path)
        else:
            # Scan directly for single-threaded scanner
            self.scanner.scan_file(event.src_path)


def main():
    """
    Main entry point for command-line scanner execution.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Zeek-YARA File Scanner")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--threads", "-t", type=int, default=2, help="Number of scanner threads")
    parser.add_argument("--directory", "-d", help="Directory to monitor")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        # Create scanner instance
        if args.threads > 1:
            scanner = MultiThreadScanner(num_threads=args.threads)
        else:
            scanner = SingleThreadScanner()

        print(f"Starting YARA scanner (threads: {args.threads})")
        print(f"Monitoring directory: {args.directory or 'extracted_files/'}")

        # Start scanning
        scanner.start()

        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down scanner...")
            scanner.stop()

    except Exception as e:
        print(f"Error starting scanner: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
