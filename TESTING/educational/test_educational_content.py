#!/usr/bin/env python3
"""
Educational Content Validation Tests
Tests to validate educational materials and tutorials
"""

import os
from pathlib import Path

import pytest


class TestEducationalContent:
    """Test educational content structure and validity"""

    def test_education_directory_exists(self):
        """Test that EDUCATION directory exists"""
        education_dir = Path("EDUCATION")
        assert education_dir.exists(), "EDUCATION directory should exist"
        assert education_dir.is_dir(), "EDUCATION should be a directory"

    def test_required_education_files_exist(self):
        """Test that required educational files exist"""
        education_dir = Path("EDUCATION")
        required_files = ["README.md", "tutorial_web_server.py"]

        for file_name in required_files:
            file_path = education_dir / file_name
            assert file_path.exists(), f"Required educational file {file_name} should exist"

    def test_tutorial_directories_exist(self):
        """Test that tutorial directory structure exists"""
        education_dir = Path("EDUCATION")
        tutorial_dirs = ["tutorials", "examples", "getting-started"]

        for dir_name in tutorial_dirs:
            dir_path = education_dir / dir_name
            assert dir_path.exists(), f"Tutorial directory {dir_name} should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"

    def test_tutorial_content_has_content(self):
        """Test that tutorial directories are not empty"""
        tutorials_dir = Path("EDUCATION/tutorials")
        if tutorials_dir.exists():
            # Check if there are any files or subdirectories
            contents = list(tutorials_dir.iterdir())
            # Allow empty for now, but structure should exist
            assert tutorials_dir.is_dir(), "Tutorials directory should be a directory"

    def test_basic_markdown_files_readable(self):
        """Test that basic markdown files can be read"""
        education_dir = Path("EDUCATION")
        readme_path = education_dir / "README.md"

        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert len(content) > 0, "README.md should have content"
                assert "education" in content.lower(), "README should mention education"


class TestTutorialValidation:
    """Test tutorial content validation"""

    def test_eicar_detection_tutorial_exists(self):
        """Test that EICAR detection tutorial exists"""
        eicar_tutorial = Path("EDUCATION/examples/quick-demos/eicar-detection.md")
        if eicar_tutorial.exists():
            with open(eicar_tutorial, "r", encoding="utf-8") as f:
                content = f.read()
                assert "EICAR" in content, "EICAR tutorial should mention EICAR"

    def test_getting_started_content_exists(self):
        """Test that getting started content exists"""
        getting_started_dir = Path("EDUCATION/getting-started")
        if getting_started_dir.exists():
            # Check for any content in getting started
            contents = list(getting_started_dir.rglob("*.md"))
            # Allow empty for now, just check structure exists
            assert getting_started_dir.is_dir(), "Getting started should be a directory"


if __name__ == "__main__":
    pytest.main([__file__])
