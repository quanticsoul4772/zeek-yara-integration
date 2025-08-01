#!/usr/bin/env python3
"""
Zeek-YARA Integration File Utilities Module
Created: April 24, 2025
Author: Security Team

This module contains utilities for file handling and analysis.
"""

import hashlib
import logging
import os
import time
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, Optional

import magic


def performance_track(logger=None, level=logging.DEBUG):
    """
    Performance tracking decorator for method timing and logging.

    Args:
        logger (logging.Logger, optional): Logger to use for performance tracking
        level (int, optional): Logging level for performance metrics
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()

                # Log performance if logger is provided
                if logger:
                    logger.log(
                        level,
                        f"Method {func.__name__} executed in {(end_time - start_time) * 1000:.2f} ms",
                    )

                return result
            except Exception as e:
                # Optionally log exceptions
                if logger:
                    logger.exception(f"Error in {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


class FileTypeCategories:
    """
    Comprehensive file type categorization system
    """

    CATEGORIES = {
        "document": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ],
        "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
        "executable": ["application/x-executable", "application/x-msdownload"],
        "archive": [
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
        ],
        "script": ["text/x-python", "text/x-shellscript", "application/x-perl"],
    }

    @classmethod
    def categorize_mime(cls, mime_type: str) -> str:
        """
        Categorize a MIME type into a high-level category.

        Args:
            mime_type (str): MIME type to categorize

        Returns:
            str: Categorized file type or 'unknown'
        """
        for category, mime_types in cls.CATEGORIES.items():
            if mime_type in mime_types or any(
                mime_type.startswith(prefix) for prefix in mime_types
            ):
                return category

        # Additional category detection for generic MIME types
        if mime_type.startswith("text/"):
            return "text"
        if mime_type.startswith("video/"):
            return "video"
        if mime_type.startswith("audio/"):
            return "audio"

        return "unknown"


class FileAnalyzer:
    """
    Enhanced file analysis class with performance optimization
    """

    def __init__(
        self, max_file_size: Optional[int] = None, logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the file analyzer.

        Args:
            max_file_size (int, optional): Maximum file size to process in bytes.
            logger (logging.Logger, optional): Logger for performance tracking
        """
        self.max_file_size = max_file_size
        self.logger = logger or logging.getLogger("zeek_yara.file_utils")

        # Configure performance tracking
        self.get_mime_type = performance_track(logger=self.logger)(self._get_mime_type)
        self.get_file_type = performance_track(logger=self.logger)(self._get_file_type)

    def is_file_too_large(self, file_path: str) -> bool:
        """
        Check if a file exceeds the maximum size limit.

        Args:
            file_path (str): Path to the file to check

        Returns:
            bool: True if file is too large, False otherwise
        """
        # If no max size is set, no file is too large
        if self.max_file_size is None:
            return False

        try:
            file_size = os.path.getsize(file_path)
            return file_size > self.max_file_size
        except Exception as e:
            # Log error and assume file is not too large
            self.logger.error(f"Error checking file size for {file_path}: {e}")
            return False

    @lru_cache(maxsize=1024)
    def _get_mime_type(self, file_path: str) -> str:
        """
        Cached MIME type detection with fallback

        Args:
            file_path (str): Path to the file

        Returns:
            str: MIME type of the file
        """
        try:
            return magic.from_file(file_path, mime=True)
        except Exception:
            return "application/octet-stream"

    @lru_cache(maxsize=1024)
    def _get_file_type(self, file_path: str) -> str:
        """
        Cached file type detection

        Args:
            file_path (str): Path to the file

        Returns:
            str: Detailed file type description
        """
        try:
            return magic.from_file(file_path)
        except Exception:
            return "Unknown"

    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Enhanced file metadata extraction with performance tracking

        Args:
            file_path (str): Path to the file

        Returns:
            dict: Comprehensive file metadata
        """
        # Validate file exists and size
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.is_file_too_large(file_path):
            self.logger.warning(f"File {file_path} exceeds maximum size limit")
            return {}

        # Extract file metadata
        metadata = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "directory": os.path.dirname(file_path),
            "extension": os.path.splitext(file_path)[1].lower(),
        }

        try:
            # Get file stats
            stat = os.stat(file_path)
            metadata.update(
                {
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "accessed": stat.st_atime,
                }
            )

            # Detect MIME type and categorize
            mime_type = self.get_mime_type(file_path)
            metadata.update(
                {
                    "mime_type": mime_type,
                    "file_category": FileTypeCategories.categorize_mime(mime_type),
                    "file_type": self.get_file_type(file_path),
                }
            )

            # Calculate hashes
            metadata.update(self.calculate_hashes(file_path))

            # Extract Zeek UID
            metadata["zeek_uid"] = self.extract_zeek_uid(metadata["name"])

        except Exception as e:
            self.logger.error(f"Error processing file metadata for {file_path}: {e}")

        return metadata

    def calculate_hashes(self, file_path: str) -> Dict[str, str]:
        """
        Calculate MD5 and SHA256 hashes for a file.

        Args:
            file_path (str): Path to the file

        Returns:
            dict: Dictionary with MD5 and SHA256 hashes
        """
        # Initialize hash objects
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()

        try:
            # Read file in chunks to avoid memory issues with large files
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5.update(chunk)
                    sha256.update(chunk)

            return {"md5": md5.hexdigest(), "sha256": sha256.hexdigest()}
        except Exception as e:
            self.logger.error(f"Error calculating hashes for {file_path}: {e}")
            return {"md5": "", "sha256": ""}

    def extract_zeek_uid(self, filename: str) -> str:
        """
        Extract Zeek UID from filename.

        Args:
            filename (str): Filename to extract UID from

        Returns:
            str: Extracted UID or 'unknown_uid'
        """
        # Zeek UIDs are typically alphanumeric strings
        # This is a simple heuristic and may need to be adjusted
        if (
            len(filename) >= 10
            and any(c.isalpha() for c in filename)
            and any(c.isdigit() for c in filename)
        ):
            return filename

        return "unknown_uid"

    def filter_file_by_mime(self, file_path: str, allowed_mime_types: list) -> bool:
        """
        Filter file by MIME type.

        Args:
            file_path (str): Path to the file
            allowed_mime_types (list): List of allowed MIME types or prefixes

        Returns:
            bool: True if file should be processed, False otherwise
        """
        if not allowed_mime_types:
            return True  # No filter, process all files

        mime_type = self.get_mime_type(file_path)

        # Check exact matches and prefixes
        for allowed in allowed_mime_types:
            if mime_type == allowed or mime_type.startswith(allowed):
                return True

        return False

    def filter_file_by_extension(self, file_path: str, allowed_extensions: list) -> bool:
        """
        Filter file by extension.

        Args:
            file_path (str): Path to the file
            allowed_extensions (list): List of allowed file extensions

        Returns:
            bool: True if file should be processed, False otherwise
        """
        if not allowed_extensions:
            return True  # No filter, process all files

        # Get file extension (lowercase, with dot)
        extension = os.path.splitext(file_path)[1].lower()

        # Handle extensions with or without leading dot
        return extension in allowed_extensions or extension[1:] in allowed_extensions
