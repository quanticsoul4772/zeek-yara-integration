#!/usr/bin/env python3
import os
import sys

# Same path resolution as used in test_cleanup_manager.py
test_file_path = "/Users/russellsmith/Projects/zeek_yara_integration/tests/unit_tests/test_cleanup_manager.py"
project_root = os.path.abspath(os.path.join(os.path.dirname(test_file_path), "../.."))
sys.path.insert(0, project_root)

print(f"Test file path: {test_file_path}")
print(f"Project root: {project_root}")
print(f"PLATFORM exists: {os.path.exists(os.path.join(project_root, 'PLATFORM'))}")
print(f"cleanup_manager.py exists: {os.path.exists(os.path.join(project_root, 'PLATFORM/core/cleanup_manager.py'))}")

# Try the import
try:
    from PLATFORM.core.cleanup_manager import FileCleanupManager
    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")
    print(f"Python path: {sys.path[:3]}")
