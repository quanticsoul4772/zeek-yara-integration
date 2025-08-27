#!/usr/bin/env python3
"""
Unit tests for FileCleanupManager
Created: August 3, 2025
Author: Security Team

Tests for the automated file cleanup functionality.
"""

import datetime
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Import project modules

import pytest

from PLATFORM.core.cleanup_manager import FileCleanupManager
from PLATFORM.core.database import DatabaseManager


class TestFileCleanupManager(unittest.TestCase):
    """Test cases for FileCleanupManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.extract_dir = Path(self.temp_dir.name) / "extracted_files"
        self.extract_dir.mkdir()

        self.db_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.db_temp.name
        self.db_temp.close()

        self.config = {
            "EXTRACT_DIR": str(self.extract_dir),
            "DB_FILE": self.db_path,
            "CLEANUP_ENABLED": True,
            "CLEANUP_RETENTION_CLEAN_HOURS": 1,
            "CLEANUP_RETENTION_MATCHED_HOURS": 24,
            "CLEANUP_INTERVAL_MINUTES": 1,
            "CLEANUP_DISK_WARNING_THRESHOLD": 80.0,
            "CLEANUP_DISK_CRITICAL_THRESHOLD": 90.0,
        }

        self.cleanup_manager = FileCleanupManager(self.config)

    def tearDown(self):
        """Clean up test fixtures"""
        if self.cleanup_manager.running:
            self.cleanup_manager.stop_cleanup_scheduler()

        self.temp_dir.cleanup()

        # Clean up database file
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    @pytest.mark.unit
    def test_init_with_defaults(self):
        """Test initialization with default configuration"""
        default_config = {"EXTRACT_DIR": str(self.extract_dir), "DB_FILE": self.db_path}

        manager = FileCleanupManager(default_config)

        self.assertEqual(manager.retention_clean, 24)  # Default
        self.assertEqual(manager.retention_matched, 168)  # Default
        self.assertEqual(manager.cleanup_interval, 60)  # Default
        self.assertTrue(manager.cleanup_enabled)  # Default

    @pytest.mark.unit
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration"""
        self.assertEqual(self.cleanup_manager.retention_clean, 1)
        self.assertEqual(self.cleanup_manager.retention_matched, 24)
        self.assertEqual(self.cleanup_manager.cleanup_interval, 1)
        self.assertTrue(self.cleanup_manager.cleanup_enabled)

    @pytest.mark.unit
    def test_start_stop_scheduler(self):
        """Test starting and stopping the cleanup scheduler"""
        # Test start
        self.assertTrue(self.cleanup_manager.start_cleanup_scheduler())
        self.assertTrue(self.cleanup_manager.running)

        # Test start when already running
        self.assertFalse(self.cleanup_manager.start_cleanup_scheduler())

        # Test stop
        self.assertTrue(self.cleanup_manager.stop_cleanup_scheduler())
        self.assertFalse(self.cleanup_manager.running)

        # Test stop when not running
        self.assertFalse(self.cleanup_manager.stop_cleanup_scheduler())

    @pytest.mark.unit
    def test_scheduler_disabled(self):
        """Test scheduler behavior when cleanup is disabled"""
        config = self.config.copy()
        config["CLEANUP_ENABLED"] = False

        manager = FileCleanupManager(config)

        # Should return True but not actually start
        self.assertTrue(manager.start_cleanup_scheduler())
        self.assertFalse(manager.running)

    @pytest.mark.unit
    def test_get_files_for_cleanup(self):
        """Test getting files for cleanup from extract directory"""
        # Create test files
        test_files = []
        for i in range(3):
            file_path = self.extract_dir / f"test_file_{i}.txt"
            file_path.write_text(f"Test content {i}")
            test_files.append(file_path)

        # Create a subdirectory (should be ignored)
        subdir = self.extract_dir / "subdir"
        subdir.mkdir()

        files = self.cleanup_manager._get_files_for_cleanup()

        self.assertEqual(len(files), 3)
        self.assertTrue(all(f.is_file() for f in files))
        self.assertTrue(all(f.name.startswith("test_file_") for f in files))

    @pytest.mark.unit
    def test_get_files_nonexistent_directory(self):
        """Test getting files when extract directory doesn't exist"""
        # Remove the directory
        self.extract_dir.rmdir()

        files = self.cleanup_manager._get_files_for_cleanup()
        self.assertEqual(len(files), 0)

    @pytest.mark.unit
    @patch("PLATFORM.core.cleanup_manager.time.time")
    def test_process_file_for_cleanup_old_unprocessed(self, mock_time):
        """Test processing an old unprocessed file for cleanup"""
        # Mock current time to make file appear old
        current_time = time.time()
        mock_time.return_value = current_time

        # Create test file and make it old
        test_file = self.extract_dir / "old_file.txt"
        test_content = "Test content"
        test_file.write_text(test_content)

        # Set file modification time to be older than retention period
        old_time = current_time - (2 * 3600)  # 2 hours ago
        os.utime(test_file, (old_time, old_time))

        # Mock database to return no results (unprocessed file)
        with patch.object(
            self.cleanup_manager.db_manager, "get_alerts", return_value=[]
        ):
            result = self.cleanup_manager._process_file_for_cleanup(test_file)

        self.assertTrue(result["deleted"])
        self.assertEqual(result["size_freed"], len(test_content))
        self.assertEqual(result["reason"], "unprocessed_retention_exceeded")
        self.assertFalse(test_file.exists())

    @pytest.mark.unit
    @patch("PLATFORM.core.cleanup_manager.time.time")
    def test_process_file_for_cleanup_old_matched(self, mock_time):
        """Test processing an old matched file for cleanup"""
        current_time = time.time()
        mock_time.return_value = current_time

        test_file = self.extract_dir / "matched_file.txt"
        test_content = "Malware content"
        test_file.write_text(test_content)

        # Set file modification time to be older than matched retention period
        old_time = current_time - (25 * 3600)  # 25 hours ago
        os.utime(test_file, (old_time, old_time))

        # Mock database to return a matched alert
        mock_alert = {
            "file_path": str(test_file.absolute()),
            "rule_name": "test_malware_rule",
        }

        with patch.object(
            self.cleanup_manager.db_manager, "get_alerts", return_value=[mock_alert]
        ):
            result = self.cleanup_manager._process_file_for_cleanup(test_file)

        self.assertTrue(result["deleted"])
        self.assertEqual(result["size_freed"], len(test_content))
        self.assertEqual(result["reason"], "matched_retention_exceeded")
        self.assertFalse(test_file.exists())

    @pytest.mark.unit
    @patch("PLATFORM.core.cleanup_manager.time.time")
    def test_process_file_for_cleanup_old_clean(self, mock_time):
        """Test processing an old clean file for cleanup"""
        current_time = time.time()
        mock_time.return_value = current_time

        test_file = self.extract_dir / "clean_file.txt"
        test_content = "Clean content"
        test_file.write_text(test_content)

        # Set file modification time to be older than clean retention period
        old_time = current_time - (2 * 3600)  # 2 hours ago
        os.utime(test_file, (old_time, old_time))

        # Mock database to return a clean alert (rule_name = "unknown")
        mock_alert = {"file_path": str(test_file.absolute()), "rule_name": "unknown"}

        with patch.object(
            self.cleanup_manager.db_manager, "get_alerts", return_value=[mock_alert]
        ):
            result = self.cleanup_manager._process_file_for_cleanup(test_file)

        self.assertTrue(result["deleted"])
        self.assertEqual(result["size_freed"], len(test_content))
        self.assertEqual(result["reason"], "clean_retention_exceeded")
        self.assertFalse(test_file.exists())

    @pytest.mark.unit
    @patch("PLATFORM.core.cleanup_manager.time.time")
    def test_process_file_for_cleanup_recent_file(self, mock_time):
        """Test processing a recent file that should not be cleaned up"""
        current_time = time.time()
        mock_time.return_value = current_time

        test_file = self.extract_dir / "recent_file.txt"
        test_content = "Recent content"
        test_file.write_text(test_content)

        # File is recent (within retention period)
        recent_time = current_time - (0.5 * 3600)  # 30 minutes ago
        os.utime(test_file, (recent_time, recent_time))

        with patch.object(
            self.cleanup_manager.db_manager, "get_alerts", return_value=[]
        ):
            result = self.cleanup_manager._process_file_for_cleanup(test_file)

        self.assertFalse(result["deleted"])
        self.assertEqual(result["size_freed"], 0)
        self.assertEqual(result["reason"], "unprocessed_retention_not_exceeded")
        self.assertTrue(test_file.exists())

    @pytest.mark.unit
    def test_get_file_processing_status_unprocessed(self):
        """Test getting processing status for unprocessed file"""
        test_file = self.extract_dir / "unprocessed.txt"
        test_file.write_text("test")

        with patch.object(
            self.cleanup_manager.db_manager, "get_alerts", return_value=[]
        ):
            status = self.cleanup_manager._get_file_processing_status(test_file)

        self.assertFalse(status["processed"])
        self.assertFalse(status["matched"])

    @pytest.mark.unit
    def test_get_file_processing_status_processed_clean(self):
        """Test getting processing status for processed clean file"""
        test_file = self.extract_dir / "clean.txt"
        test_file.write_text("test")

        mock_alert = {"file_path": str(test_file.absolute()), "rule_name": "unknown"}

        with patch.object(
            self.cleanup_manager.db_manager, "get_alerts", return_value=[mock_alert]
        ):
            status = self.cleanup_manager._get_file_processing_status(test_file)

        self.assertTrue(status["processed"])
        self.assertFalse(status["matched"])

    @pytest.mark.unit
    def test_get_file_processing_status_processed_matched(self):
        """Test getting processing status for processed matched file"""
        test_file = self.extract_dir / "matched.txt"
        test_file.write_text("test")

        mock_alert = {
            "file_path": str(test_file.absolute()),
            "rule_name": "malware_rule",
        }

        with patch.object(
            self.cleanup_manager.db_manager, "get_alerts", return_value=[mock_alert]
        ):
            status = self.cleanup_manager._get_file_processing_status(test_file)

        self.assertTrue(status["processed"])
        self.assertTrue(status["matched"])

    @pytest.mark.unit
    @patch("PLATFORM.core.cleanup_manager.os.statvfs")
    def test_get_disk_usage(self, mock_statvfs):
        """Test getting disk usage statistics"""
        # Mock statvfs return value
        mock_stat = Mock()
        mock_stat.f_frsize = 4096  # 4KB blocks
        mock_stat.f_blocks = 1000  # 1000 blocks total
        mock_stat.f_available = 200  # 200 blocks available
        mock_statvfs.return_value = mock_stat

        usage = self.cleanup_manager._get_disk_usage()

        self.assertIsNotNone(usage)
        self.assertEqual(usage["total_bytes"], 4096 * 1000)
        self.assertEqual(usage["available_bytes"], 4096 * 200)
        self.assertEqual(usage["used_bytes"], 4096 * 800)
        self.assertEqual(usage["usage_percent"], 80.0)

    @pytest.mark.unit
    def test_get_disk_usage_nonexistent_directory(self):
        """Test getting disk usage for nonexistent directory"""
        self.extract_dir.rmdir()

        usage = self.cleanup_manager._get_disk_usage()
        self.assertIsNone(usage)

    @pytest.mark.unit
    @patch("PLATFORM.core.cleanup_manager.os.statvfs")
    def test_check_disk_usage_alerts(self, mock_statvfs):
        """Test disk usage alerting"""
        # Mock critical usage
        mock_stat = Mock()
        mock_stat.f_frsize = 4096
        mock_stat.f_blocks = 1000
        mock_stat.f_available = 50  # 95% usage
        mock_statvfs.return_value = mock_stat

        with patch.object(
            self.cleanup_manager.logger, "critical"
        ) as mock_critical, patch.object(
            self.cleanup_manager.logger, "warning"
        ) as mock_warning:
            self.cleanup_manager._check_disk_usage_alerts()

            # Should trigger critical alert
            mock_critical.assert_called_once()
            mock_warning.assert_not_called()

    @pytest.mark.unit
    def test_cleanup_processed_files_disabled(self):
        """Test cleanup operation when disabled"""
        self.cleanup_manager.cleanup_enabled = False

        result = self.cleanup_manager.cleanup_processed_files()

        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "cleanup_disabled")

    @pytest.mark.unit
    @patch("PLATFORM.core.cleanup_manager.time.time")
    def test_cleanup_processed_files_success(self, mock_time):
        """Test successful cleanup operation"""
        current_time = time.time()
        mock_time.return_value = current_time

        # Create old test files
        old_files = []
        for i in range(3):
            file_path = self.extract_dir / f"old_file_{i}.txt"
            file_path.write_text(f"Content {i}")
            old_time = current_time - (2 * 3600)  # 2 hours ago
            os.utime(file_path, (old_time, old_time))
            old_files.append(file_path)

        # Mock database calls
        with patch.object(
            self.cleanup_manager.db_manager, "get_alerts", return_value=[]
        ), patch.object(
            self.cleanup_manager,
            "_get_disk_usage",
            return_value={"usage_percent": 50.0},
        ):
            result = self.cleanup_manager.cleanup_processed_files()

        self.assertTrue(result["success"])
        self.assertEqual(result["files_processed"], 3)
        self.assertEqual(result["files_deleted"], 3)
        self.assertGreater(result["space_freed_bytes"], 0)
        self.assertEqual(len(result["errors"]), 0)

        # Files should be deleted
        for file_path in old_files:
            self.assertFalse(file_path.exists())

    @pytest.mark.unit
    def test_get_statistics(self):
        """Test getting cleanup statistics"""
        stats = self.cleanup_manager.get_statistics()

        self.assertIn("running", stats)
        self.assertIn("cleanup_enabled", stats)
        self.assertIn("configuration", stats)
        self.assertIn("disk_usage", stats)
        self.assertIn("total_cleanups", stats)
        self.assertIn("files_deleted", stats)
        self.assertIn("space_freed_bytes", stats)

    @pytest.mark.unit
    def test_force_cleanup(self):
        """Test forcing immediate cleanup"""
        # Create a test file
        test_file = self.extract_dir / "test.txt"
        test_file.write_text("test content")

        with patch.object(
            self.cleanup_manager, "cleanup_processed_files"
        ) as mock_cleanup:
            mock_cleanup.return_value = {"success": True, "files_deleted": 1}

            result = self.cleanup_manager.force_cleanup()

            mock_cleanup.assert_called_once()
            self.assertEqual(result["success"], True)
            self.assertEqual(result["files_deleted"], 1)

    @pytest.mark.unit
    def test_scheduler_loop_stops_on_signal(self):
        """Test that scheduler loop stops when stop event is set"""
        # Start scheduler
        self.assertTrue(self.cleanup_manager.start_cleanup_scheduler())

        # Wait a moment for thread to start
        time.sleep(0.1)

        # Stop scheduler
        self.assertTrue(self.cleanup_manager.stop_cleanup_scheduler())

        # Thread should have stopped
        self.assertFalse(self.cleanup_manager.running)


if __name__ == "__main__":
    unittest.main()
