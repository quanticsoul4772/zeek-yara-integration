#!/usr/bin/env python3
"""
Zeek-YARA Integration Platform - Package Setup
Network security monitoring toolkit integrating Zeek, YARA, and Suricata.
"""

from setuptools import setup, find_packages
from pathlib import Path
import os

# Read version from version file or use default
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from packaging.version import VERSION
    version = VERSION
except ImportError:
    version = "1.0.0"

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

# Read requirements files
def read_requirements(filename):
    """Read requirements from file, handling missing files gracefully."""
    req_file = this_directory / filename
    if req_file.exists():
        return req_file.read_text().strip().split('\n')
    return []

# Core requirements
install_requires = read_requirements("requirements.txt")

# Development and testing requirements
test_requires = read_requirements("test-requirements.txt")

# Educational requirements
education_requires = read_requirements("EDUCATION/requirements.txt")

setup(
    name="zeek-yara-integration",
    version=version,
    author="Security Education Platform Team",
    author_email="security@example.com",
    description="Network security monitoring toolkit integrating Zeek, YARA, and Suricata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quanticsoul4772/zeek-yara-integration",
    project_urls={
        "Bug Tracker": "https://github.com/quanticsoul4772/zeek-yara-integration/issues",
        "Documentation": "https://github.com/quanticsoul4772/zeek-yara-integration/tree/main/docs",
        "Source Code": "https://github.com/quanticsoul4772/zeek-yara-integration",
    },
    
    # Package discovery
    packages=find_packages(exclude=["tests*", "test*", "extracted_files*", "logs*"]),
    
    # Include additional files
    package_data={
        "": [
            "*.md", "*.txt", "*.yaml", "*.yml", "*.json", "*.yar",
            "config/*.json", "config/*.yaml",
            "rules/**/*.yar",
            "CONFIGURATION/defaults/*.json", "CONFIGURATION/defaults/*.yaml",
            "zeek/*.zeek",
            "EDUCATION/templates/*.html", "EDUCATION/static/**/*",
        ],
    },
    include_package_data=True,
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=install_requires,
    
    # Optional dependencies
    extras_require={
        "test": test_requires,
        "education": education_requires,
        "dev": test_requires + education_requires + [
            "setuptools>=45.0.0",
            "wheel>=0.37.0",
            "twine>=3.0.0",
        ],
        "all": test_requires + education_requires,
    },
    
    # Console scripts / entry points
    entry_points={
        "console_scripts": [
            # Main CLI tool
            "zyi=TOOLS.cli.zyi:cli",
            
            # Platform installer (preserved functionality)
            "zeek-yara-install=install_platform:main",
            
            # Core platform scripts
            "setup-wizard=setup_wizard:main", 
            "tutorial-system=tutorial_system:main",
            
            # Educational tools
            "zeek-yara-tutorial=EDUCATION.tutorial_web_server:main",
            "tutorial-server=EDUCATION.start_tutorial_server:main",
            
            # API and development
            "zeek-yara-api=PLATFORM.api.api_server:main",
            "zeek-yara-scanner=PLATFORM.core.scanner:main",
        ]
    },
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: Education",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: Web Environment",
    ],
    
    # Keywords for discovery
    keywords=[
        "security", "network-monitoring", "intrusion-detection", 
        "malware-analysis", "zeek", "yara", "suricata",
        "cybersecurity", "education", "threat-detection"
    ],
    
    # License
    license="MIT",
    
    # Zip safety
    zip_safe=False,
)