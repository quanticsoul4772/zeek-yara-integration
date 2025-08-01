#!/usr/bin/env python3
"""
Enhanced setup.py for Zeek-YARA Educational Platform package distribution
Supports pip, conda, and other package managers
"""

from version import VERSION_INFO
import os
import sys
from pathlib import Path

from setuptools import find_packages, setup

# Add project root to path for version import
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT / "packaging"))


# Read requirements
def read_requirements(filename):
    """Read requirements from requirements file."""
    req_path = PROJECT_ROOT / filename
    if req_path.exists():
        with open(req_path, "r") as f:
            return [line.strip() for line in f if line.strip()
                    and not line.startswith("#")]
    return []


def read_readme():
    """Read README file for long description."""
    readme_path = PROJECT_ROOT / "README.md"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return VERSION_INFO["description"]


# Package data and entry points
def get_package_data():
    """Get package data files."""
    data_files = []

    # Educational content
    education_dir = PROJECT_ROOT / "EDUCATION"
    if education_dir.exists():
        for root, dirs, files in os.walk(education_dir):
            for file in files:
                if file.endswith((".md", ".json", ".yaml", ".yml")):
                    rel_path = Path(root).relative_to(PROJECT_ROOT)
                    data_files.append(str(rel_path / file))

    # Configuration files
    config_dir = PROJECT_ROOT / "CONFIGURATION"
    if config_dir.exists():
        for root, dirs, files in os.walk(config_dir):
            for file in files:
                if file.endswith((".json", ".yaml", ".yml")):
                    rel_path = Path(root).relative_to(PROJECT_ROOT)
                    data_files.append(str(rel_path / file))

    # Documentation
    docs_dir = PROJECT_ROOT / "docs"
    if docs_dir.exists():
        for root, dirs, files in os.walk(docs_dir):
            for file in files:
                if file.endswith((".md", ".rst", ".html")):
                    rel_path = Path(root).relative_to(PROJECT_ROOT)
                    data_files.append(str(rel_path / file))

    # Rules and templates
    rules_dir = PROJECT_ROOT / "rules"
    if rules_dir.exists():
        for root, dirs, files in os.walk(rules_dir):
            for file in files:
                if file.endswith((".yar", ".rules", ".conf")):
                    rel_path = Path(root).relative_to(PROJECT_ROOT)
                    data_files.append(str(rel_path / file))

    return data_files


# Setup configuration
setup_config = {
    # Basic package info
    "name": "zeek-yara-educational",
    "version": VERSION_INFO["version"],
    "description": VERSION_INFO["description"],
    "long_description": read_readme(),
    "long_description_content_type": "text/markdown",
    # Author and contact info
    "author": VERSION_INFO["author"],
    "author_email": "support@zeek-yara-educational.org",
    "maintainer": VERSION_INFO["author"],
    "maintainer_email": "support@zeek-yara-educational.org",
    # URLs
    "url": VERSION_INFO["url"],
    "download_url": VERSION_INFO["download_url"],
    "project_urls": {
        "Documentation": VERSION_INFO["documentation_url"],
        "Source": VERSION_INFO["url"],
        "Tracker": VERSION_INFO["support_url"],
        "Funding": "https://github.com/sponsors/zeek-yara-educational",
        "Wiki": VERSION_INFO["url"] + "/wiki",
        "Discussions": VERSION_INFO["url"] + "/discussions",
    },
    # Package discovery
    "packages": find_packages(
        where=str(PROJECT_ROOT), exclude=["tests", "tests.*", "packaging", "packaging.*"]
    ),
    "package_dir": {"": str(PROJECT_ROOT)},
    "package_data": {
        "": get_package_data(),
    },
    "include_package_data": True,
    # Requirements
    "python_requires": ">=3.8",
    "install_requires": read_requirements("requirements.txt"),
    "extras_require": {
        "dev": read_requirements("test-requirements.txt")
        + [
            "black>=22.0.0",
            "flake8>=4.0.0",
            "isort>=5.10.0",
            "mypy>=0.991",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "packaging": [
            "pyinstaller>=5.0.0",
            "cx-freeze>=6.0.0",
            "setuptools-scm>=6.0.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.17.0",
        ],
        "performance": [
            "pytest-benchmark>=3.4.0",
            "memory-profiler>=0.60.0",
        ],
    },
    # Entry points
    "entry_points": {
        "console_scripts": [
            "zeek-yara-educational=main:main",
            "zye=main:main",  # Short alias
            "zeek-yara-setup=setup_wizard:main",
            "zye-setup=setup_wizard:main",
        ],
        "gui_scripts": [
            "zeek-yara-educational-gui=main:main",
        ],
    },
    # Data files for system-wide installation
    "data_files": [
        # Desktop integration
        ("share/applications",
         ["packaging/assets/zeek-yara-educational.desktop"]),
        ("share/pixmaps", ["packaging/assets/icon.png"]),
        ("share/icons/hicolor/48x48/apps", ["packaging/assets/icon-48.png"]),
        ("share/icons/hicolor/64x64/apps", ["packaging/assets/icon-64.png"]),
        ("share/icons/hicolor/128x128/apps",
         ["packaging/assets/icon-128.png"]),
        # Documentation
        (
            "share/doc/zeek-yara-educational",
            [
                "README.md",
                "LICENSE",
                "CONTRIBUTING.md",
            ],
        ),
        # Configuration examples
        (
            "share/zeek-yara-educational/config",
            [
                "config/default_config.json",
            ],
        ),
        # Educational content
        (
            "share/zeek-yara-educational/education",
            (
                [
                    file
                    for file in (PROJECT_ROOT / "EDUCATION").rglob("*")
                    if file.is_file() and file.suffix in [".md", ".json", ".yaml"]
                ]
                if (PROJECT_ROOT / "EDUCATION").exists()
                else []
            ),
        ),
    ],
    # Classification
    "classifiers": [
        # Development Status
        "Development Status :: 4 - Beta",
        # Intended Audience
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        # Topic
        "Topic :: Education",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Software Development :: Libraries :: Python Modules",
        # License
        "License :: OSI Approved :: MIT License",
        # Programming Language
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        # Operating System
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        # Environment
        "Environment :: Console",
        "Environment :: Web Environment",
        "Environment :: X11 Applications",
        # Natural Language
        "Natural Language :: English",
    ],
    # Keywords for search
    "keywords": [
        "security",
        "networking",
        "education",
        "zeek",
        "yara",
        "suricata",
        "network-monitoring",
        "intrusion-detection",
        "malware-analysis",
        "cybersecurity",
        "tutorial",
        "learning-platform",
        "ids",
        "nids",
    ],
    # License
    "license": VERSION_INFO["license"],
    # Compatibility
    "zip_safe": False,
    # Build requirements
    "setup_requires": [
        "setuptools>=45",
        "wheel",
        "setuptools-scm>=6.0",
    ],
    # Test suite
    "test_suite": "tests",
    "tests_require": read_requirements("test-requirements.txt"),
    # Command classes for custom commands
    "cmdclass": {},
}


# Custom commands
class DevelopCommand:
    """Custom develop command with additional setup."""

    def run(self):
        """Run development setup."""
        import subprocess

        # Install in development mode
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e", "."])

        # Install development dependencies
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"])

        # Setup pre-commit hooks if available
        try:
            subprocess.check_call(["pre-commit", "install"])
            print("✅ Pre-commit hooks installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ Pre-commit not available, skipping hooks")

        print("✅ Development environment setup complete!")


class TestCommand:
    """Custom test command."""

    def run(self):
        """Run test suite."""
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pytest", "tests/", "-v"])


class CleanCommand:
    """Custom clean command."""

    def run(self):
        """Clean build artifacts."""
        import shutil

        patterns = [
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".coverage",
            "htmlcov",
            ".pytest_cache",
            ".mypy_cache",
        ]

        for pattern in patterns:
            for path in Path(".").rglob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")
                elif path.is_file():
                    path.unlink()
                    print(f"Removed file: {path}")


# Add custom commands
try:
    from setuptools import Command

    class DevelopCommandClass(Command):
        description = "Set up development environment"
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            DevelopCommand().run()

    class TestCommandClass(Command):
        description = "Run test suite"
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            TestCommand().run()

    class CleanCommandClass(Command):
        description = "Clean build artifacts"
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            CleanCommand().run()

    setup_config["cmdclass"] = {
        "develop": DevelopCommandClass,
        "test": TestCommandClass,
        "clean": CleanCommandClass,
    }

except ImportError:
    # Fallback for older setuptools versions
    pass

if __name__ == "__main__":
    setup(**setup_config)
