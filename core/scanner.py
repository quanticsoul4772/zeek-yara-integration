#!/usr/bin/env python3
"""
Zeek-YARA Integration Scanner Module
Created: April 24, 2025
Author: Security Team

This module contains the core scanner functionality.
"""

import logging
import os
import threading
import time
from queue import Empty, Queue

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.database import DatabaseManager
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
        self.file_analyzer = FileAnalyzer(
            max_file_size=config.get("MAX_FILE_SIZE"))
        self.rule_manager = RuleManager(
            rules_dir=config.get("RULES_DIR"),
            rules_index=config.get("RULES_INDEX"))
        self.yara_matcher = YaraMatcher(
            rule_manager=self.rule_manager, timeout=config.get(
                "SCAN_TIMEOUT", 60)
        )
        self.db_manager = DatabaseManager(db_file=config.get("DB_FILE"))

        # Callback for notifications
        self.scan_callback = None

        # Prepare rules
        self.rule_manager.compile_rules()

    def scan_file(self, file_path):
        """
        Scan a single file with YARA and process the results.

        Args:
            file_path (str): Path to the file to scan

        Returns:
            dict: Scan result dictionary
        """
        # Check if file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return {"matched": False, "error": "File not found"}

        # Check if file is too large
        if self.file_analyzer.is_file_too_large(file_path):
            self.logger.warning(f"File too large to scan: {file_path}")
            return {"matched": False, "error": "File too large"}

        # Get file metadata
        try:
            file_metadata = self.file_analyzer.get_file_metadata(file_path)
            self.logger.debug(f"File metadata: {file_metadata}")
        except Exception as e:
            self.logger.error(f"Error getting file metadata: {e}")
            file_metadata = {"file_path": file_path,
                             "name": os.path.basename(file_path)}

        # Log basic file info
        self.logger.info(
            f"Scanning: {file_path} ({file_metadata.get('size', 0)} bytes)")

        # Apply mime-type or extension filtering if configured
        if self.config.get("SCAN_MIME_TYPES") and not self.file_analyzer.filter_file_by_mime(
                file_path, self.config.get("SCAN_MIME_TYPES")):
            self.logger.info(
                f"Skipping file with excluded MIME type: {file_path}")
            return {"matched": False, "error": "Excluded MIME type"}

        if self.config.get("SCAN_EXTENSIONS") and not self.file_analyzer.filter_file_by_extension(
                file_path, self.config.get("SCAN_EXTENSIONS")):
            self.logger.info(
                f"Skipping file with excluded extension: {file_path}")
            return {"matched": False, "error": "Excluded extension"}

        # Scan file with YARA
        scan_result = self.yara_matcher.scan_file(file_path)

        # Process and store results
        if scan_result.get("matched", False):
            self.logger.info(
                f"YARA match found in {file_metadata.get('name', '')}")

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
                add_result = self.db_manager.add_alert(
                    file_metadata, scan_result)
                if add_result:
                    self.logger.info(
                        f"Added alert to database for file: {file_metadata.get('name', '')}")
                else:
                    self.logger.error(
                        f"Failed to add alert to database for file: {file_metadata.get('name', '')}")
            except Exception as e:
                self.logger.error(f"Exception adding alert to database: {e}")
        else:
            if scan_result.get("error"):
                self.logger.warning(
                    f"Error scanning {file_path}: {scan_result.get('error')}")
            else:
                self.logger.info(f"No matches for file: {file_path}")

        # Call the scan callback if registered
        if self.scan_callback is not None:
            try:
                self.scan_callback(file_path, scan_result)
            except Exception as e:
                self.logger.error(f"Error in scan callback: {e}")

        return scan_result

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
            self.logger.error(
                f"Error scanning directory {directory}: {str(e)}")
            results["error"] = str(e)

        # Calculate duration
        results["duration"] = time.time() - results["start_time"]

        self.logger.info(
            f"Directory scan complete: {
                results['scanned']} files scanned, " f"{
                results['skipped']} files skipped, " f"{
                results['matched']} matches found in {
                    results['duration']:.2f} seconds")

        return results


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
            self.observer.schedule(
                event_handler, self.extract_dir, recursive=False)
            self.observer.start()

            self.running = True
            self.logger.info(
                f"Started monitoring directory: {self.extract_dir}")

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
    """Multi-threaded scanner implementation"""

    def __init__(self, config):
        """Initialize the multi-threaded scanner"""
        super().__init__(config)
        self.logger = logging.getLogger("zeek_yara.multi_scanner")
        self.running = False
        self.observer = None

        # Threading components
        self.num_threads = config.get("THREADS", 2)
        self.file_queue = Queue()
        self.worker_threads = []
        self.stop_event = threading.Event()

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
            # Clear stop event
            self.stop_event.clear()

            # Start worker threads
            for i in range(self.num_threads):
                thread = threading.Thread(
                    target=self._worker_thread, args=(i + 1,), daemon=True)
                thread.start()
                self.worker_threads.append(thread)
                self.logger.info(f"Started scanner thread {i + 1}")

            # Set up file watching
            event_handler = FileEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                event_handler, self.extract_dir, recursive=False)
            self.observer.start()

            self.running = True
            self.logger.info(
                f"Started monitoring directory with {
                    self.num_threads} threads: {
                    self.extract_dir}")

            # Queue existing files for scanning
            for filename in os.listdir(self.extract_dir):
                file_path = os.path.join(self.extract_dir, filename)
                if os.path.isfile(file_path):
                    self.file_queue.put(file_path)
                    self.logger.debug(f"Queued existing file: {file_path}")

            return True

        except Exception as e:
            self.logger.error(f"Error starting monitoring: {str(e)}")
            # Clean up any started threads
            self.stop_monitoring()
            return False

    def stop_monitoring(self):
        """
        Stop monitoring and all worker threads.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("Scanner is not running")
            return False

        try:
            # Signal threads to stop
            self.stop_event.set()

            # Wait for threads to finish
            for thread in self.worker_threads:
                thread.join(timeout=2.0)

            # Clear thread list
            self.worker_threads = []

            # Stop the observer
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None

            self.running = False
            self.logger.info("Stopped monitoring and all worker threads")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {str(e)}")
            return False

    def queue_file(self, file_path):
        """
        Add a file to the scanning queue.

        Args:
            file_path (str): Path to the file to scan
        """
        self.file_queue.put(file_path)

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

    def _worker_thread(self, thread_id):
        """
        Worker thread function for scanning files.

        Args:
            thread_id (int): Thread identifier
        """
        self.logger.info(f"Scanner thread {thread_id} started")

        while not self.stop_event.is_set():
            try:
                # Get file from queue with timeout
                try:
                    file_path = self.file_queue.get(timeout=1.0)
                except Empty:
                    # No files to scan, continue waiting
                    continue

                # Scan the file
                try:
                    self.scan_file(file_path)
                except Exception as e:
                    self.logger.error(
                        f"Thread {thread_id} error scanning {file_path}: {
                            str(e)}")

                # Mark task as done
                self.file_queue.task_done()

            except Exception as e:
                self.logger.error(f"Thread {thread_id} error: {str(e)}")
                # Sleep briefly to avoid tight loop in case of persistent error
                time.sleep(1.0)

        self.logger.info(f"Scanner thread {thread_id} stopped")


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

        # Process differently based on scanner type
        if isinstance(self.scanner, MultiThreadScanner):
            # Add to queue for multi-threaded scanner
            self.scanner.queue_file(event.src_path)
        else:
            # Scan directly for single-threaded scanner
            self.scanner.scan_file(event.src_path)
