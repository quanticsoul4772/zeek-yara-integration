#!/usr/bin/env python3
"""
Zeek-YARA Integration File Cleanup Manager
Created: August 3, 2025
Author: Security Team

This module manages automatic cleanup of processed files based on
configurable retention policies and processing status.
"""

import datetime
import logging
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.database import DatabaseManager


class FileCleanupManager:
    """
    Automated file cleanup manager with configurable retention policies.

    Provides safe deletion of processed files based on:
    - Processing status (clean vs matched files)
    - Configurable retention periods
    - Database verification of processing completion
    - Disk usage monitoring and alerting
    """

    def __init__(self, config: Dict):
        """
        Initialize the file cleanup manager.

        Args:
            config (Dict): Configuration dictionary containing cleanup settings
        """
        self.config = config
        self.logger = logging.getLogger("zeek_yara.cleanup_manager")

        # Extract directory and database configuration
        self.extract_dir = Path(config.get("EXTRACT_DIR", "./extracted_files"))
        self.db_manager = DatabaseManager(config.get("DB_FILE"))

        # Retention policies (in hours)
        self.retention_clean = config.get("CLEANUP_RETENTION_CLEAN_HOURS", 24)
        self.retention_matched = config.get(
            "CLEANUP_RETENTION_MATCHED_HOURS", 168
        )  # 7 days

        # Cleanup schedule (in minutes)
        self.cleanup_interval = config.get("CLEANUP_INTERVAL_MINUTES", 60)

        # Disk usage thresholds
        self.disk_usage_warning_threshold = config.get(
            "CLEANUP_DISK_WARNING_THRESHOLD", 80.0
        )
        self.disk_usage_critical_threshold = config.get(
            "CLEANUP_DISK_CRITICAL_THRESHOLD", 90.0
        )

        # Enable/disable cleanup
        self.cleanup_enabled = config.get("CLEANUP_ENABLED", True)

        # Threading components
        self.running = False
        self.cleanup_thread = None
        self.stop_event = threading.Event()

        # Statistics tracking
        self.stats = {
            "total_cleanups": 0,
            "files_deleted": 0,
            "space_freed_bytes": 0,
            "last_cleanup": None,
            "errors": 0,
        }

    def start_cleanup_scheduler(self) -> bool:
        """
        Start the automated cleanup scheduler.

        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("Cleanup scheduler is already running")
            return False

        if not self.cleanup_enabled:
            self.logger.info("File cleanup is disabled in configuration")
            return True

        try:
            self.stop_event.clear()
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_scheduler_loop,
                daemon=True,
                name="FileCleanupScheduler",
            )
            self.cleanup_thread.start()
            self.running = True

            self.logger.info(
                f"Started file cleanup scheduler with {self.cleanup_interval}min interval"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error starting cleanup scheduler: {e}")
            return False

    def stop_cleanup_scheduler(self) -> bool:
        """
        Stop the automated cleanup scheduler.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("Cleanup scheduler is not running")
            return False

        try:
            self.stop_event.set()
            if self.cleanup_thread:
                self.cleanup_thread.join(timeout=10.0)

            self.running = False
            self.logger.info("Stopped file cleanup scheduler")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping cleanup scheduler: {e}")
            return False

    def cleanup_processed_files(self) -> Dict:
        """
        Remove files older than retention period based on processing status.

        Returns:
            Dict: Cleanup operation results and statistics
        """
        if not self.cleanup_enabled:
            self.logger.info("File cleanup is disabled")
            return {"success": False, "reason": "cleanup_disabled"}

        self.logger.info("Starting file cleanup operation")
        start_time = time.time()

        cleanup_result = {
            "success": True,
            "start_time": datetime.datetime.now().isoformat(),
            "files_processed": 0,
            "files_deleted": 0,
            "space_freed_bytes": 0,
            "errors": [],
            "disk_usage_before": None,
            "disk_usage_after": None,
        }

        try:
            # Check disk usage before cleanup
            cleanup_result["disk_usage_before"] = self._get_disk_usage()

            # Get list of files to process
            files_to_check = self._get_files_for_cleanup()
            cleanup_result["files_processed"] = len(files_to_check)

            if not files_to_check:
                self.logger.info("No files found for cleanup")
                cleanup_result["success"] = True
                return cleanup_result

            # Process each file for potential cleanup
            for file_path in files_to_check:
                try:
                    file_result = self._process_file_for_cleanup(file_path)
                    if file_result["deleted"]:
                        cleanup_result["files_deleted"] += 1
                        cleanup_result["space_freed_bytes"] += file_result["size_freed"]

                except Exception as e:
                    error_msg = f"Error processing file {file_path}: {e}"
                    self.logger.error(error_msg)
                    cleanup_result["errors"].append(error_msg)
                    self.stats["errors"] += 1

            # Check disk usage after cleanup
            cleanup_result["disk_usage_after"] = self._get_disk_usage()

            # Update statistics
            self.stats["total_cleanups"] += 1
            self.stats["files_deleted"] += cleanup_result["files_deleted"]
            self.stats["space_freed_bytes"] += cleanup_result["space_freed_bytes"]
            self.stats["last_cleanup"] = cleanup_result["start_time"]

            duration = time.time() - start_time
            self.logger.info(
                f"Cleanup completed: {cleanup_result['files_deleted']} files deleted, "
                f"{cleanup_result['space_freed_bytes']} bytes freed in {duration:.2f}s"
            )

        except Exception as e:
            self.logger.error(f"Error during cleanup operation: {e}")
            cleanup_result["success"] = False
            cleanup_result["errors"].append(str(e))
            self.stats["errors"] += 1

        return cleanup_result

    def _cleanup_scheduler_loop(self):
        """
        Main loop for the cleanup scheduler thread.
        """
        self.logger.info("File cleanup scheduler started")

        while not self.stop_event.is_set():
            try:
                # Perform cleanup
                self.cleanup_processed_files()

                # Check disk usage and alert if necessary
                self._check_disk_usage_alerts()

                # Wait for next interval or stop signal
                if self.stop_event.wait(timeout=self.cleanup_interval * 60):
                    break  # Stop signal received

            except Exception as e:
                self.logger.error(f"Error in cleanup scheduler loop: {e}")
                self.stats["errors"] += 1
                # Wait before retrying to avoid tight error loop
                if self.stop_event.wait(timeout=60):
                    break

        self.logger.info("File cleanup scheduler stopped")

    def _get_files_for_cleanup(self) -> List[Path]:
        """
        Get list of files in extract directory eligible for cleanup.

        Returns:
            List[Path]: List of file paths to check for cleanup
        """
        files_to_check = []

        try:
            if not self.extract_dir.exists():
                self.logger.warning(
                    f"Extract directory does not exist: {self.extract_dir}"
                )
                return files_to_check

            for file_path in self.extract_dir.iterdir():
                if file_path.is_file():
                    files_to_check.append(file_path)

            self.logger.debug(f"Found {len(files_to_check)} files to check for cleanup")

        except Exception as e:
            self.logger.error(f"Error getting files for cleanup: {e}")

        return files_to_check

    def _process_file_for_cleanup(self, file_path: Path) -> Dict:
        """
        Process a single file for potential cleanup.

        Args:
            file_path (Path): Path to the file to process

        Returns:
            Dict: Processing result with deletion status and size freed
        """
        result = {"deleted": False, "size_freed": 0, "reason": None}

        try:
            # Get file stats
            file_stat = file_path.stat()
            file_age_hours = (time.time() - file_stat.st_mtime) / 3600
            file_size = file_stat.st_size

            # Check if file is in database (has been processed)
            processing_status = self._get_file_processing_status(file_path)

            # Determine retention policy based on processing status
            if processing_status["processed"]:
                if processing_status["matched"]:
                    retention_hours = self.retention_matched
                    file_type = "matched"
                else:
                    retention_hours = self.retention_clean
                    file_type = "clean"
            else:
                # File not yet processed - use clean retention for safety
                retention_hours = self.retention_clean
                file_type = "unprocessed"

            # Check if file is old enough for cleanup
            if file_age_hours >= retention_hours:
                try:
                    file_path.unlink()  # Delete the file
                    result["deleted"] = True
                    result["size_freed"] = file_size
                    result["reason"] = f"{file_type}_retention_exceeded"

                    self.logger.info(
                        f"Deleted {file_type} file: {file_path.name} "
                        f"(age: {file_age_hours:.1f}h, size: {file_size} bytes)"
                    )

                except OSError as e:
                    self.logger.error(f"Failed to delete file {file_path}: {e}")
                    result["reason"] = f"deletion_failed: {e}"

            else:
                result["reason"] = f"{file_type}_retention_not_exceeded"
                self.logger.debug(
                    f"Keeping {file_type} file: {file_path.name} "
                    f"(age: {file_age_hours:.1f}h < {retention_hours}h)"
                )

        except Exception as e:
            self.logger.error(f"Error processing file {file_path} for cleanup: {e}")
            result["reason"] = f"processing_error: {e}"

        return result

    def _get_file_processing_status(self, file_path: Path) -> Dict:
        """
        Check if file has been processed and determine match status.

        Args:
            file_path (Path): Path to the file to check

        Returns:
            Dict: Processing status with 'processed' and 'matched' booleans
        """
        status = {"processed": False, "matched": False}

        try:
            # Query database for alerts matching this file path
            alerts = self.db_manager.get_alerts(
                filters={"file_path": str(file_path.absolute())}, limit=1
            )

            if alerts:
                status["processed"] = True
                # Check if any YARA rules matched (rule_name != 'unknown')
                for alert in alerts:
                    if alert.get("rule_name") and alert["rule_name"] != "unknown":
                        status["matched"] = True
                        break

            self.logger.debug(
                f"File {file_path.name} processing status: "
                f"processed={status['processed']}, matched={status['matched']}"
            )

        except Exception as e:
            self.logger.error(f"Error checking processing status for {file_path}: {e}")
            # Default to processed=False for safety (longer retention)

        return status

    def _get_disk_usage(self) -> Optional[Dict]:
        """
        Get disk usage statistics for the extract directory.

        Returns:
            Optional[Dict]: Disk usage information or None if error
        """
        try:
            if not self.extract_dir.exists():
                return None

            stat = os.statvfs(str(self.extract_dir))

            total_bytes = stat.f_frsize * stat.f_blocks
            available_bytes = stat.f_frsize * stat.f_available
            used_bytes = total_bytes - available_bytes

            usage_percent = (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0

            return {
                "total_bytes": total_bytes,
                "used_bytes": used_bytes,
                "available_bytes": available_bytes,
                "usage_percent": usage_percent,
            }

        except Exception as e:
            self.logger.error(f"Error getting disk usage: {e}")
            return None

    def _check_disk_usage_alerts(self):
        """
        Check disk usage and log alerts if thresholds are exceeded.
        """
        try:
            disk_usage = self._get_disk_usage()
            if not disk_usage:
                return

            usage_percent = disk_usage["usage_percent"]

            if usage_percent >= self.disk_usage_critical_threshold:
                self.logger.critical(
                    f"CRITICAL: Disk usage at {usage_percent:.1f}% "
                    f"(threshold: {self.disk_usage_critical_threshold}%)"
                )
            elif usage_percent >= self.disk_usage_warning_threshold:
                self.logger.warning(
                    f"WARNING: Disk usage at {usage_percent:.1f}% "
                    f"(threshold: {self.disk_usage_warning_threshold}%)"
                )

        except Exception as e:
            self.logger.error(f"Error checking disk usage alerts: {e}")

    def get_statistics(self) -> Dict:
        """
        Get cleanup manager statistics.

        Returns:
            Dict: Statistics about cleanup operations
        """
        stats = self.stats.copy()
        stats["running"] = self.running
        stats["cleanup_enabled"] = self.cleanup_enabled
        stats["configuration"] = {
            "retention_clean_hours": self.retention_clean,
            "retention_matched_hours": self.retention_matched,
            "cleanup_interval_minutes": self.cleanup_interval,
            "disk_warning_threshold": self.disk_usage_warning_threshold,
            "disk_critical_threshold": self.disk_usage_critical_threshold,
        }
        stats["disk_usage"] = self._get_disk_usage()

        return stats

    def force_cleanup(self) -> Dict:
        """
        Force an immediate cleanup operation (bypass scheduler).

        Returns:
            Dict: Cleanup operation results
        """
        self.logger.info("Forcing immediate cleanup operation")
        return self.cleanup_processed_files()
