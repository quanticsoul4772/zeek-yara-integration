#!/usr/bin/env python3
"""
Zeek-YARA Integration Platform - setuptools configuration
Educational platform for network security monitoring and malware detection
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements from requirements.txt
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, "r") as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

# Read test requirements from test-requirements.txt
test_requirements = []
test_requirements_file = this_directory / "test-requirements.txt"
if test_requirements_file.exists():
    with open(test_requirements_file, "r") as f:
        test_requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="zeek-yara-integration",
    version="1.0.0",
    author="quanticsoul4772",
    author_email="quanticsoul4772@users.noreply.github.com",
    description="Educational platform for network security monitoring integrating Zeek, YARA, and Suricata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quanticsoul4772/zeek-yara-integration",
    
    # Package discovery
    packages=find_packages(include=[
        "PLATFORM*",
        "api*", 
        "core*",
        "config*",
        "utils*",
        "suricata*",
        "zeek*"
    ]),
    
    # Include additional files
    include_package_data=True,
    package_data={
        "": [
            "*.yaml", 
            "*.json", 
            "*.yar", 
            "*.rules",
            "*.zeek",
            "*.md",
            "*.txt"
        ],
    },
    
    # Requirements
    install_requires=requirements,
    extras_require={
        "test": test_requirements,
        "dev": test_requirements + [
            "pre-commit>=2.20.0",
            "tox>=3.25.0",
        ]
    },
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Entry points for CLI tools
    entry_points={
        "console_scripts": [
            "zyi=main:main",
            "zeek-yara-install=install_platform:main",
            "setup-wizard=setup_wizard:main",
            "tutorial-system=tutorial_system:main",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
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
    ],
    
    # Keywords
    keywords="zeek yara suricata network security monitoring education malware detection",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/quanticsoul4772/zeek-yara-integration/issues",
        "Source": "https://github.com/quanticsoul4772/zeek-yara-integration",
        "Documentation": "https://github.com/quanticsoul4772/zeek-yara-integration/blob/main/README.md",
    },
    
    # Zip safe
    zip_safe=False,
)