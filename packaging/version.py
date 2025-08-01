#!/usr/bin/env python3
"""
Version management for Zeek-YARA Educational Platform
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# Application version
VERSION = "1.0.0"
BUILD_DATE = datetime.now().isoformat()
COMMIT_HASH = os.environ.get('GITHUB_SHA', 'development')[:8]

# Version info for packaging
VERSION_INFO = {
    "version": VERSION,
    "major": int(VERSION.split('.')[0]),
    "minor": int(VERSION.split('.')[1]),
    "patch": int(VERSION.split('.')[2]),
    "build_date": BUILD_DATE,
    "commit": COMMIT_HASH,
    "name": "Zeek-YARA Educational Platform",
    "description": "Educational network security monitoring platform",
    "author": "Zeek-YARA Educational Team",
    "license": "MIT",
    "url": "https://github.com/your-org/zeek_yara_integration",
    "download_url": "https://github.com/your-org/zeek_yara_integration/releases",
    "documentation_url": "https://your-org.github.io/zeek_yara_integration",
    "support_url": "https://github.com/your-org/zeek_yara_integration/issues"
}

def get_version():
    """Get current version string."""
    return VERSION

def get_version_info():
    """Get complete version information."""
    return VERSION_INFO.copy()

def get_build_string():
    """Get build string for display."""
    return f"{VERSION} (build {COMMIT_HASH}, {BUILD_DATE[:10]})"

def save_version_file(output_path: Path):
    """Save version info to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(VERSION_INFO, f, indent=2)

if __name__ == "__main__":
    print(f"Version: {get_version()}")
    print(f"Build: {get_build_string()}")