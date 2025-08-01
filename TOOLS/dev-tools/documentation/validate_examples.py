#!/usr/bin/env python3
"""
Validate code examples in educational documentation.

This script extracts and validates code blocks from markdown files,
checking for syntax errors, security issues, and best practices.
"""

import argparse
import ast
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class CodeBlock:
    """Represents a code block extracted from markdown."""

    def __init__(self, code: str, language: str, file_path: str, line_number: int):
        self.code = code
        self.language = language
        self.file_path = file_path
        self.line_number = line_number


class ValidationResult:
    """Result of validating a code block."""

    def __init__(self, block: CodeBlock):
        self.block = block
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.is_valid = True

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)


def extract_code_blocks(file_path: str) -> List[CodeBlock]:
    """Extract code blocks from a markdown file."""
    blocks = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return blocks

    in_code_block = False
    current_block = []
    current_language = ""
    block_start_line = 0

    for i, line in enumerate(content, 1):
        # Check for code block markers
        if line.strip().startswith("```"):
            if not in_code_block:
                # Starting a code block
                in_code_block = True
                block_start_line = i
                # Extract language if specified
                lang_match = re.match(r"```(\w+)", line.strip())
                current_language = lang_match.group(1) if lang_match else ""
            else:
                # Ending a code block
                if current_block:
                    code = "".join(current_block)
                    blocks.append(
                        CodeBlock(
                            code=code,
                            language=current_language,
                            file_path=file_path,
                            line_number=block_start_line,
                        )
                    )
                in_code_block = False
                current_block = []
                current_language = ""
        elif in_code_block:
            current_block.append(line)

    return blocks


def validate_python_code(block: CodeBlock) -> ValidationResult:
    """Validate Python code for syntax and basic security issues."""
    result = ValidationResult(block)

    try:
        # Parse the code to check syntax
        ast.parse(block.code)
    except SyntaxError as e:
        result.add_error(f"Syntax error: {e.msg} at line {e.lineno}")
        return result

    # Check for common security issues in educational context
    dangerous_patterns = [
        ("eval(", "Use of eval() is dangerous"),
        ("exec(", "Use of exec() is dangerous"),
        ("__import__", "Dynamic imports can be dangerous"),
        ("os.system", "Direct system calls should be avoided"),
        ("subprocess.call(shell=True", "Shell injection risk"),
    ]

    for pattern, message in dangerous_patterns:
        if pattern in block.code:
            # In educational content, these might be intentional examples
            result.add_warning(f"Security pattern detected: {message}")

    return result


def validate_bash_code(block: CodeBlock) -> ValidationResult:
    """Validate Bash/Shell code for dangerous patterns."""
    result = ValidationResult(block)

    # Check for dangerous patterns
    dangerous_patterns = [
        (r"rm\s+-rf\s+/", "Dangerous rm command detected"),
        (r":\s*\(\s*\)\s*\{.*\}\s*;?\s*:", "Fork bomb pattern detected"),
        (r">\s*/dev/sda", "Direct disk write detected"),
        (r"dd\s+.*of=/dev/", "Dangerous dd command detected"),
    ]

    for pattern, message in dangerous_patterns:
        if re.search(pattern, block.code):
            result.add_warning(f"Security risk: {message}")

    # Basic syntax check using bash -n
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(block.code)
            temp_path = f.name

        result_check = subprocess.run(["bash", "-n", temp_path], capture_output=True, text=True)

        if result_check.returncode != 0:
            result.add_error(f"Bash syntax error: {result_check.stderr}")

        os.unlink(temp_path)
    except Exception as e:
        result.add_warning(f"Could not validate bash syntax: {e}")

    return result


def validate_json_yaml(block: CodeBlock) -> ValidationResult:
    """Validate JSON/YAML configuration examples."""
    result = ValidationResult(block)

    if block.language in ["json", "JSON"]:
        try:
            json.loads(block.code)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")

    elif block.language in ["yaml", "yml", "YAML", "YML"]:
        try:
            import yaml

            yaml.safe_load(block.code)
        except ImportError:
            result.add_warning("PyYAML not installed, skipping YAML validation")
        except Exception as e:
            result.add_error(f"Invalid YAML: {e}")

    return result


def validate_code_block(block: CodeBlock) -> ValidationResult:
    """Validate a single code block based on its language."""
    language_validators = {
        "python": validate_python_code,
        "py": validate_python_code,
        "python3": validate_python_code,
        "bash": validate_bash_code,
        "sh": validate_bash_code,
        "shell": validate_bash_code,
        "json": validate_json_yaml,
        "yaml": validate_json_yaml,
        "yml": validate_json_yaml,
    }

    validator = language_validators.get(block.language.lower())
    if validator:
        return validator(block)
    else:
        # No specific validator for this language
        result = ValidationResult(block)
        if block.language:
            result.add_warning(f"No validator for language: {block.language}")
        return result


def validate_directory(directory: str, verbose: bool = False) -> Tuple[int, int]:
    """Validate all markdown files in a directory recursively."""
    total_errors = 0
    total_warnings = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                blocks = extract_code_blocks(file_path)

                if verbose and blocks:
                    logger.info(f"Validating {len(blocks)} code blocks in {file_path}")

                for block in blocks:
                    result = validate_code_block(block)

                    if result.errors:
                        total_errors += len(result.errors)
                        for error in result.errors:
                            logger.error(
                                f"{block.file_path}:{block.line_number} "
                                f"[{block.language}] {error}"
                            )

                    if result.warnings:
                        total_warnings += len(result.warnings)
                        if verbose:
                            for warning in result.warnings:
                                logger.warning(
                                    f"{block.file_path}:{block.line_number} "
                                    f"[{block.language}] {warning}"
                                )

    return total_errors, total_warnings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate code examples in educational documentation"
    )
    parser.add_argument(
        "--directory", default="EDUCATION", help="Directory to validate (default: EDUCATION)"
    )
    parser.add_argument("--verbose", action="store_true", help="Show warnings and detailed output")

    args = parser.parse_args()

    if not os.path.exists(args.directory):
        logger.error(f"Directory not found: {args.directory}")
        sys.exit(1)

    logger.info(f"Validating code examples in {args.directory}...")
    errors, warnings = validate_directory(args.directory, args.verbose)

    # Summary
    logger.info(f"\nValidation complete:")
    logger.info(f"  Errors: {errors}")
    if args.verbose:
        logger.info(f"  Warnings: {warnings}")

    # Exit with error code if there were errors
    sys.exit(1 if errors > 0 else 0)


if __name__ == "__main__":
    main()
