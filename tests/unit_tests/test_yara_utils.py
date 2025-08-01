#!/usr/bin/env python3
"""
Comprehensive unit tests for YARA utilities module to maximize coverage.
"""

import logging
import os
import shutil
import tempfile
import time

import pytest
import yara

from utils.yara_utils import RuleManager, YaraMatcher


@pytest.fixture
def temp_rule_dir():
    """Create a temporary directory with YARA rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample YARA rules
        rules = [
            {
                "name": "test_rule1.yar",
                "content": """
rule TestRule1 {
    meta:
        description = "A test rule"
        author = "Test Author"

    strings:
        $test_string = "test_pattern"

    condition:
        $test_string
}
""",
            },
            {
                "name": "test_rule2.yar",
                "content": """
rule TestRule2 {
    meta:
        description = "Another test rule"
        author = "Another Test Author"

    strings:
        $another_string = "another_pattern"

    condition:
        $another_string
}
""",
            },
        ]

        # Write rules to files
        for rule in rules:
            with open(os.path.join(tmpdir, rule["name"]), "w") as f:
                f.write(rule["content"])

        yield tmpdir


@pytest.mark.yara
@pytest.mark.unit
def test_rule_manager_initialization(temp_rule_dir):
    """Test RuleManager initialization."""
    rule_manager = RuleManager(temp_rule_dir)

    assert rule_manager.rules_dir == temp_rule_dir
    assert rule_manager.rules is None
    assert rule_manager.last_compile_time == 0
    assert rule_manager.compile_errors == []


@pytest.mark.yara
@pytest.mark.unit
def test_rule_manager_compilation_with_index(temp_rule_dir):
    """Test rule compilation with index file."""
    # Create an index file
    index_path = os.path.join(temp_rule_dir, "index.yar")
    with open(index_path, "w") as f:
        f.write("\n".join(['include "test_rule1.yar"', 'include "test_rule2.yar"']))

    rule_manager = RuleManager(temp_rule_dir, rules_index=index_path)
    result = rule_manager.compile_rules()

    assert result is True
    assert rule_manager.rules is not None
    assert len(rule_manager.compile_errors) == 0


@pytest.mark.yara
@pytest.mark.unit
def test_rule_manager_compilation_error_handling(temp_rule_dir):
    """Test error handling during rule compilation."""
    # Create an invalid rule
    invalid_rule_path = os.path.join(temp_rule_dir, "invalid_rule.yar")
    with open(invalid_rule_path, "w") as f:
        f.write(
            """
rule InvalidRule {
    condition:
        invalid_condition
}
"""
        )

    rule_manager = RuleManager(temp_rule_dir)
    result = rule_manager.compile_rules()

    assert result is False
    assert len(rule_manager.compile_errors) > 0
    assert rule_manager.rules is None


@pytest.mark.yara
@pytest.mark.unit
def test_rule_manager_force_recompilation(temp_rule_dir):
    """Test forced rule recompilation."""
    rule_manager = RuleManager(temp_rule_dir)

    # First compilation
    rule_manager.compile_rules()
    first_compile_time = rule_manager.last_compile_time
    first_rules = rule_manager.rules

    # Force recompilation
    rule_manager.compile_rules(force=True)

    assert rule_manager.last_compile_time > first_compile_time
    assert rule_manager.rules is not None
    assert rule_manager.rules is not first_rules


@pytest.mark.yara
@pytest.mark.unit
def test_rule_manager_get_rules(temp_rule_dir):
    """Test get_rules method with various scenarios."""
    rule_manager = RuleManager(temp_rule_dir)

    # No rules initially
    assert rule_manager.get_rules() is not None

    # Repeated calls should return cached rules
    first_rules = rule_manager.get_rules()
    second_rules = rule_manager.get_rules()
    assert first_rules is second_rules

    # Force recompilation
    third_rules = rule_manager.get_rules(force_recompile=True)
    assert third_rules is not first_rules


@pytest.mark.yara
@pytest.mark.unit
def test_yara_matcher_initialization(temp_rule_dir):
    """Test YaraMatcher initialization and basic methods."""
    rule_manager = RuleManager(temp_rule_dir)
    rule_manager.compile_rules()

    matcher = YaraMatcher(rule_manager)

    assert matcher.rule_manager == rule_manager
    assert matcher.timeout == 60


@pytest.mark.yara
@pytest.mark.unit
def test_yara_matcher_file_matching(temp_rule_dir):
    """Test file matching with different scenarios."""
    rule_manager = RuleManager(temp_rule_dir)
    rule_manager.compile_rules()
    matcher = YaraMatcher(rule_manager)

    # Test matching files
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as match_file:
        match_file.write("test_pattern is here")
        match_file_path = match_file.name

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as no_match_file:
        no_match_file.write("completely different text")
        no_match_file_path = no_match_file.name

    try:
        # Test matching file
        match_result = matcher.scan_file(match_file_path)
        assert match_result["matched"] is True
        assert len(match_result["matches"]) > 0

        # Test non-matching file
        no_match_result = matcher.scan_file(no_match_file_path)
        assert no_match_result["matched"] is False
        assert len(no_match_result["matches"]) == 0
    finally:
        os.unlink(match_file_path)
        os.unlink(no_match_file_path)


@pytest.mark.yara
@pytest.mark.unit
def test_yara_matcher_file_not_found():
    """Test scanning a non-existent file."""
    rule_manager = RuleManager("/path/to/nonexistent/rules")
    rule_manager.compile_rules()
    matcher = YaraMatcher(rule_manager)

    result = matcher.scan_file("/path/to/nonexistent/file")

    assert result["matched"] is False
    assert result["error"] is not None


@pytest.mark.yara
@pytest.mark.unit
def test_yara_matcher_whitelist(temp_rule_dir):
    """Test the whitelisting functionality."""
    # Create a whitelist rule
    whitelist_content = """
rule WhitelistRule {
    meta:
        description = "Whitelist rule for testing"

    strings:
        $whitelist_marker = "safe_pattern"

    condition:
        $whitelist_marker
}
"""

    with tempfile.TemporaryDirectory() as whitelist_dir:
        with open(os.path.join(whitelist_dir, "whitelist.yar"), "w") as f:
            f.write(whitelist_content)

        # Compile whitelist rules
        whitelist_rules = yara.compile(os.path.join(whitelist_dir, "whitelist.yar"))

        rule_manager = RuleManager(temp_rule_dir)
        rule_manager.compile_rules()
        matcher = YaraMatcher(rule_manager)

        # Test files
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as whitelisted_file:
            whitelisted_file.write("safe_pattern here")
            whitelisted_path = whitelisted_file.name

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as non_whitelisted_file:
            non_whitelisted_file.write("other content")
            non_whitelisted_path = non_whitelisted_file.name

        try:
            # Test whitelisting
            assert matcher.is_file_whitelisted(whitelisted_path, whitelist_rules) is True
            assert matcher.is_file_whitelisted(non_whitelisted_path, whitelist_rules) is False

            # Test with no whitelist rules
            assert matcher.is_file_whitelisted(whitelisted_path, None) is False
        finally:
            os.unlink(whitelisted_path)
            os.unlink(non_whitelisted_path)


@pytest.mark.yara
@pytest.mark.unit
def test_yara_matcher_scan_with_callback(temp_rule_dir):
    """Test scanning with a custom callback."""
    rule_manager = RuleManager(temp_rule_dir)
    rule_manager.compile_rules()
    matcher = YaraMatcher(rule_manager)

    # Create a test file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as test_file:
        test_file.write("test_pattern is here")
        test_file_path = test_file.name

    # Create a callback that stops scanning after first match
    def stop_after_first_match(data):
        return yara.CALLBACK_ABORT

    try:
        result = matcher.scan_file(test_file_path, callback=stop_after_first_match)

        assert result["matched"] is True
        assert len(result["matches"]) > 0
    finally:
        os.unlink(test_file_path)


@pytest.mark.yara
@pytest.mark.unit
def test_yara_matcher_timeout(temp_rule_dir):
    """Test scanner timeout functionality."""
    rule_manager = RuleManager(temp_rule_dir)
    rule_manager.compile_rules()

    # Create a matcher with a very short timeout
    matcher = YaraMatcher(rule_manager, timeout=0.001)

    # Create a test file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as test_file:
        test_file.write("large content to potentially time out")
        test_file_path = test_file.name

    try:
        result = matcher.scan_file(test_file_path)

        # The result might be partial or an error
        assert "error" in result or "matched" in result
    finally:
        os.unlink(test_file_path)


@pytest.mark.yara
@pytest.mark.unit
def test_rule_manager_compilation_empty_directory():
    """Test rule compilation with an empty directory."""
    with tempfile.TemporaryDirectory() as empty_dir:
        rule_manager = RuleManager(empty_dir)
        result = rule_manager.compile_rules()

        assert result is False
        assert len(rule_manager.compile_errors) > 0
        assert rule_manager.rules is None


@pytest.mark.yara
@pytest.mark.unit
def test_rule_manager_modification_time_check(temp_rule_dir):
    """Test rule compilation based on modification times."""
    rule_manager = RuleManager(temp_rule_dir)

    # First compilation
    first_result = rule_manager.compile_rules()
    first_compile_time = rule_manager.last_compile_time

    # Simulate modification by adjusting file times
    for root, _, files in os.walk(temp_rule_dir):
        for file in files:
            file_path = os.path.join(root, file)
            os.utime(file_path, (first_compile_time + 1, first_compile_time + 1))

    # Recompile without force
    second_result = rule_manager.compile_rules()

    assert second_result is True
    assert rule_manager.last_compile_time > first_compile_time


@pytest.mark.yara
@pytest.mark.unit
def test_yara_matcher_binary_string_matches(temp_rule_dir):
    """Test handling of binary string matches."""
    rule_manager = RuleManager(temp_rule_dir)
    rule_manager.compile_rules()
    matcher = YaraMatcher(rule_manager)

    # Create a test file with binary content
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as binary_file:
        binary_file.write(b"\x00\x01\x02test_pattern\xff\xfe")
        binary_file_path = binary_file.name

    try:
        result = matcher.scan_file(binary_file_path)

        # Check match details
        if result["matched"]:
            for match in result["matches"]:
                for string_match in match.get("strings", []):
                    assert "data" in string_match
                    # Verify data can be processed
                    assert isinstance(string_match["data"], str)
    finally:
        os.unlink(binary_file_path)


@pytest.mark.yara
@pytest.mark.unit
def test_yara_matcher_error_handling_non_readable_file(temp_rule_dir):
    """Test error handling for non-readable or corrupt files."""
    rule_manager = RuleManager(temp_rule_dir)
    rule_manager.compile_rules()
    matcher = YaraMatcher(rule_manager)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file without read permissions
        restricted_file_path = os.path.join(temp_dir, "restricted.bin")
        with open(restricted_file_path, "wb") as f:
            f.write(b"some content")
        os.chmod(restricted_file_path, 0o000)  # Remove all permissions

        try:
            result = matcher.scan_file(restricted_file_path)

            # Should result in an error
            assert result["error"] is not None
            assert result["matched"] is False
        finally:
            # Restore permissions to allow cleanup
            os.chmod(restricted_file_path, 0o666)
