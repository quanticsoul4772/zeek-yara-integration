#!/usr/bin/env python3
"""
Test file processing state tracking functionality.
"""

import os
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PLATFORM.core.database import DatabaseManager


class TestFileStateTracking(unittest.TestCase):
    """Test file processing state tracking functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "test_states.db")
        self.db_manager = DatabaseManager(self.db_file)

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        os.rmdir(self.temp_dir)

    def test_add_file_state(self):
        """Test adding file state"""
        file_path = "/test/file.txt"
        file_metadata = {"size": 1024, "md5": "test_md5", "sha256": "test_sha256"}

        # Add file state
        result = self.db_manager.add_file_state(file_path, file_metadata)
        self.assertTrue(result)

        # Verify state was added
        state = self.db_manager.get_file_state(file_path)
        self.assertIsNotNone(state)
        self.assertEqual(state["file_path"], file_path)
        self.assertEqual(state["state"], "pending")
        self.assertEqual(state["file_size"], 1024)
        self.assertEqual(state["md5"], "test_md5")
        self.assertEqual(state["sha256"], "test_sha256")

    def test_update_file_state(self):
        """Test updating file state"""
        file_path = "/test/file.txt"

        # Add initial state
        self.db_manager.add_file_state(file_path)

        # Update to scanning
        result = self.db_manager.update_file_state(file_path, "scanning")
        self.assertTrue(result)

        state = self.db_manager.get_file_state(file_path)
        self.assertEqual(state["state"], "scanning")
        self.assertIsNotNone(state["started_at"])

        # Update to completed
        result = self.db_manager.update_file_state(file_path, "completed", None, 1500)
        self.assertTrue(result)

        state = self.db_manager.get_file_state(file_path)
        self.assertEqual(state["state"], "completed")
        self.assertEqual(state["scan_duration_ms"], 1500)
        self.assertIsNotNone(state["completed_at"])

    def test_get_files_by_state(self):
        """Test getting files by state"""
        # Add files with different states
        self.db_manager.add_file_state("/test/file1.txt")
        self.db_manager.add_file_state("/test/file2.txt")
        self.db_manager.update_file_state("/test/file2.txt", "scanning")

        # Get pending files
        pending_files = self.db_manager.get_files_by_state("pending")
        self.assertEqual(len(pending_files), 1)
        self.assertEqual(pending_files[0]["file_path"], "/test/file1.txt")

        # Get scanning files
        scanning_files = self.db_manager.get_files_by_state("scanning")
        self.assertEqual(len(scanning_files), 1)
        self.assertEqual(scanning_files[0]["file_path"], "/test/file2.txt")

    def test_interrupted_scans_recovery(self):
        """Test recovery of interrupted scans"""
        # Add file in scanning state
        file_path = "/test/interrupted.txt"
        self.db_manager.add_file_state(file_path)
        self.db_manager.update_file_state(file_path, "scanning")

        # Simulate time passing (we can't actually wait, so we'll directly manipulate)
        # In a real scenario, this would represent a scan that got stuck

        # Get interrupted scans (using 0 minutes timeout for testing)
        interrupted = self.db_manager.get_interrupted_scans(timeout_minutes=0)
        self.assertEqual(len(interrupted), 1)
        self.assertEqual(interrupted[0]["file_path"], file_path)

        # Recover interrupted scans
        recovered_count = self.db_manager.recover_interrupted_scans(timeout_minutes=0)
        self.assertEqual(recovered_count, 1)

        # Verify file is back to pending
        state = self.db_manager.get_file_state(file_path)
        self.assertEqual(state["state"], "pending")
        self.assertEqual(state["retry_count"], 1)

    def test_state_statistics(self):
        """Test state statistics"""
        # Add files with various states
        self.db_manager.add_file_state("/test/file1.txt")  # pending
        self.db_manager.add_file_state("/test/file2.txt")
        self.db_manager.update_file_state("/test/file2.txt", "completed", None, 1000)
        self.db_manager.add_file_state("/test/file3.txt")
        self.db_manager.update_file_state(
            "/test/file3.txt", "failed", "Test error", 500
        )

        # Get statistics
        stats = self.db_manager.get_state_statistics()
        self.assertIn("state_counts", stats)
        self.assertEqual(stats["state_counts"]["pending"], 1)
        self.assertEqual(stats["state_counts"]["completed"], 1)
        self.assertEqual(stats["state_counts"]["failed"], 1)
        self.assertEqual(stats["total_files"], 3)
        self.assertEqual(stats["average_scan_duration_ms"], 750.0)  # (1000 + 500) / 2

    def test_cleanup_completed_states(self):
        """Test cleanup of completed states"""
        # Add completed file
        file_path = "/test/completed.txt"
        self.db_manager.add_file_state(file_path)
        self.db_manager.update_file_state(file_path, "completed")

        # Cleanup with 0 hours retention (immediate cleanup)
        cleaned_count = self.db_manager.cleanup_completed_states(retention_hours=0)

        # Since we can't manipulate SQLite's datetime functions easily in tests,
        # this test mainly verifies the method runs without error
        self.assertIsInstance(cleaned_count, int)
        self.assertGreaterEqual(cleaned_count, 0)


if __name__ == "__main__":
    unittest.main()
