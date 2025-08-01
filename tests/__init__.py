"""
Zeek-YARA Integration Test Package
Created: August 1, 2025

This package contains all tests for the Zeek-YARA integration platform.
"""

import os
import sys

# Ensure project root is in path for all test modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)