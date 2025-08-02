"""
Zeek-YARA Integration File Analyzer Tests
Created: April 24, 2025
Author: Russell Smith

This module contains tests for the file analyzer utility, including performance tests
for the optimizations implemented in Phase 2.
"""

import os
import sys

import pytest

from utils.file_utils import FileAnalyzer, FileTypeCategories

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Unit tests for FileAnalyzer
@pytest.mark.unit
class TestFileAnalyzer:
    """Unit tests for FileAnalyzer class"""

    def test_initialization(self, file_analyzer):
        """Test file analyzer initialization"""
        assert file_analyzer is not None
        assert file_analyzer.max_file_size == 1024 * 1024

    def test_file_size_check(self, file_analyzer, test_files):
        """Test file size checking"""
        # All test files should be within size limits
        for file_path in test_files["files"]:
            assert not file_analyzer.is_file_too_large(file_path)

        # Create a temporary large file
        large_file = os.path.join(test_files["dir"], "large.bin")
        with open(large_file, "wb") as f:
            f.write(b"\0" * (1024 * 1024 + 1))  # Just over max size

        # Test size check
        assert file_analyzer.is_file_too_large(large_file)

        # Clean up
        os.unlink(large_file)

    def test_mime_type_detection(self, file_analyzer, test_files):
        """Test MIME type detection"""
        # Test all files
        for file_path in test_files["files"]:
            mime_type = file_analyzer.get_mime_type(file_path)
            assert mime_type is not None
            assert isinstance(mime_type, str)
            assert len(mime_type) > 0

        # Specific checks
        assert file_analyzer.get_mime_type(test_files["paths"]["text.txt"]).startswith("text/")
        assert (
            file_analyzer.get_mime_type(test_files["paths"]["binary.bin"])
            == "application/octet-stream"
        )

    def test_file_type_detection(self, file_analyzer, test_files):
        """Test file type detection"""
        # Test all files
        for file_path in test_files["files"]:
            file_type = file_analyzer.get_file_type(file_path)
            assert file_type is not None
            assert isinstance(file_type, str)
            assert len(file_type) > 0

    def test_metadata_extraction(self, file_analyzer, test_files):
        """Test metadata extraction"""
        # Test text file
        metadata = file_analyzer.get_file_metadata(test_files["paths"]["text.txt"])
        assert metadata is not None
        assert isinstance(metadata, dict)

        # Check required fields
        assert "path" in metadata
        assert "name" in metadata
        assert "size" in metadata
        assert "mime_type" in metadata
        assert "file_type" in metadata
        assert "file_category" in metadata
        assert "md5" in metadata
        assert "sha256" in metadata

        # Check values
        assert metadata["name"] == "text.txt"
        assert metadata["size"] > 0
        assert metadata["mime_type"].startswith("text/")
        assert metadata["file_category"] in ["text", "document"]

    def test_file_categorization(self):
        """Test file type categorization"""
        # Test different MIME types
        test_cases = [
            ("application/pdf", "document"),
            ("application/msword", "document"),
            ("image/jpeg", "image"),
            ("image/png", "image"),
            ("application/x-executable", "executable"),
            ("application/zip", "archive"),
            ("text/x-python", "script"),
            ("text/plain", "text"),
            ("video/mp4", "video"),
            ("audio/mpeg", "audio"),
            ("application/octet-stream", "unknown"),
        ]

        for mime_type, expected_category in test_cases:
            category = FileTypeCategories.categorize_mime(mime_type)
            assert (
                category == expected_category
            ), f"Expected {expected_category} for {mime_type}, got {category}"


# Performance tests for FileAnalyzer
@pytest.mark.performance
class TestFileAnalyzerPerformance:
    """Performance tests for FileAnalyzer optimizations"""

    def test_lru_cache_performance(self, file_analyzer, test_files, timer):
        """Test performance benefit of LRU cache"""
        # Warm up - Make sure the cache is empty
        file_analyzer._get_mime_type.cache_clear()
        file_analyzer._get_file_type.cache_clear()

        # First run (uncached)
        timer.start()
        for _ in range(10):  # Multiple calls to same files
            for file_path in test_files["files"]:
                file_analyzer.get_mime_type(file_path)
                file_analyzer.get_file_type(file_path)
        uncached_time = timer.stop().duration

        # Second run (cached)
        timer.start()
        for _ in range(10):  # Same number of calls
            for file_path in test_files["files"]:
                file_analyzer.get_mime_type(file_path)
                file_analyzer.get_file_type(file_path)
        cached_time = timer.stop().duration

        # Assert that cached performance is better
        assert cached_time < uncached_time

        # Calculate improvement percentage
        improvement = (1 - (cached_time / uncached_time)) * 100
        print(
            f"LRU Cache Performance: Uncached: {
                uncached_time:.6f}s, Cached: {
                cached_time:.6f}s"
        )
        print(f"Performance improvement: {improvement:.2f}%")

        # Should see significant improvement (at least 50%)
        assert improvement > 50

    def test_metadata_extraction_performance(self, file_analyzer, test_files, timer):
        """Test performance of metadata extraction"""
        # Measure performance of extracting metadata from all files
        timer.start()
        for _ in range(5):  # Multiple iterations for reliable measurement
            for file_path in test_files["files"]:
                metadata = file_analyzer.get_file_metadata(file_path)
                assert metadata is not None
        duration = timer.stop().duration

        # Calculate per-file time
        per_file_time = duration / (5 * len(test_files["files"]))
        print(
            f"Metadata extraction: {
                duration:.6f}s total, {
                per_file_time:.6f}s per file"
        )

        # Should be reasonably fast (<50ms per file)
        assert per_file_time < 0.05

    def test_performance_tracking_decorator(self, test_files):
        """Test the performance tracking decorator"""
        # Create a logger that captures logs
        import io
        import logging

        log_stream = io.StringIO()
        test_logger = logging.getLogger("test_performance_tracking")
        test_logger.setLevel(logging.DEBUG)

        # Add a stream handler
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)

        # Create analyzer with the test logger
        analyzer = FileAnalyzer(max_file_size=1024 * 1024, logger=test_logger)

        # Run the decorated method
        for file_path in test_files["files"]:
            analyzer.get_file_metadata(file_path)

        # Check if performance logs were captured
        log_contents = log_stream.getvalue()
        assert "Method _get_mime_type executed in" in log_contents
        assert "Method _get_file_type executed in" in log_contents
