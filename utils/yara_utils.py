#!/usr/bin/env python3
"""
Zeek-YARA Integration YARA Utilities Module
Created: April 24, 2025
Author: Security Team

This module contains utilities for YARA rule management and scanning.
"""

import json
import logging
import os
import time

import yara


class RuleManager:
    """Class for managing YARA rules compilation and access"""

    def __init__(self, rules_dir, rules_index=None):
        """
        Initialize the rule manager.

        Args:
            rules_dir (str): Directory containing YARA rules
            rules_index (str, optional): Path to index file that includes all rules.
        """
        self.rules_dir = rules_dir
        self.rules_index = rules_index
        self.rules = None
        self.last_compile_time = 0
        self.compile_errors = []
        self.logger = logging.getLogger("zeek_yara.rule_manager")

    def compile_rules(self, force=False):
        """
        Compile YARA rules from directory or index file.

        Args:
            force (bool): Force recompilation even if rules haven't changed

        Returns:
            bool: True if compilation was successful, False otherwise
        """
        self.compile_errors = []

        try:
            # Check if recompilation is needed based on file modification times
            if not force and self.rules:
                # Check index file if provided
                if self.rules_index and os.path.exists(self.rules_index):
                    index_mtime = os.path.getmtime(self.rules_index)
                    if index_mtime <= self.last_compile_time:
                        return True

                # Check individual rule files if no index or index has changed
                recompile_needed = False
                for root, dirs, files in os.walk(self.rules_dir):
                    for file in files:
                        if file.endswith(".yar") or file.endswith(".yara"):
                            file_path = os.path.join(root, file)
                            file_mtime = os.path.getmtime(file_path)
                            if file_mtime > self.last_compile_time:
                                recompile_needed = True
                                break
                    if recompile_needed:
                        break

                if not recompile_needed:
                    return True

            # Compilation is needed, proceed
            start_time = time.time()
            self.logger.info("Compiling YARA rules...")

            if self.rules_index and os.path.exists(self.rules_index):
                # Compile from index file
                self.logger.info(f"Using index file: {self.rules_index}")
                self.rules = yara.compile(self.rules_index)
            else:
                # Compile from individual files
                rule_files = []
                for root, dirs, files in os.walk(self.rules_dir):
                    for file in files:
                        if file.endswith(".yar") or file.endswith(".yara"):
                            rule_files.append(os.path.join(root, file))

                if not rule_files:
                    self.logger.warning("No YARA rule files found!")
                    self.compile_errors.append("No YARA rule files found in directory")
                    self.rules = None
                    return False

                self.rules = yara.compile(filepaths={f: f for f in rule_files})
                self.logger.info(f"Compiled {len(rule_files)} YARA rule files")

            # Update last compile time
            self.last_compile_time = time.time()
            self.logger.info(
                f"Rule compilation completed in {time.time() - start_time:.2f} seconds"
            )
            return True

        except Exception as e:
            self.compile_errors.append(str(e))
            self.logger.error(f"Error compiling rules: {str(e)}")
            return False

    def get_rules(self, force_recompile=False):
        """
        Get compiled YARA rules, recompiling if necessary.

        Args:
            force_recompile (bool): Force rules recompilation

        Returns:
            yara.Rules: Compiled YARA rules, or None if compilation failed
        """
        if not self.rules or force_recompile:
            self.compile_rules(force=force_recompile)
        return self.rules

    def get_compile_errors(self):
        """
        Get any errors from the last rule compilation attempt.

        Returns:
            list: List of error messages
        """
        return self.compile_errors


class YaraMatcher:
    """Class for scanning files with YARA rules"""

    def __init__(self, rule_manager, timeout=60):
        """
        Initialize YARA matcher.

        Args:
            rule_manager (RuleManager): Manager for YARA rules
            timeout (int): Timeout in seconds for each scan
        """
        self.rule_manager = rule_manager
        self.timeout = timeout
        self.logger = logging.getLogger("zeek_yara.matcher")

    def scan_file(self, file_path, callback=None):
        """
        Scan a file with YARA rules.

        Args:
            file_path (str): Path to file to scan
            callback (function, optional): Optional callback function for YARA

        Returns:
            dict: Dictionary with scan results
        """
        result = {
            "file_path": file_path,
            "matched": False,
            "matches": [],
            "error": None,
            "scan_time": 0,
        }

        # Make sure rules are available
        rules = self.rule_manager.get_rules()
        if not rules:
            result["error"] = "No YARA rules available"
            return result

        try:
            start_time = time.time()

            # Default callback to continue scanning
            if not callback:
                callback = lambda data: yara.CALLBACK_CONTINUE

            # Scan the file
            matches = rules.match(file_path, timeout=self.timeout, callback=callback)

            # Update result
            result["scan_time"] = time.time() - start_time

            if matches:
                result["matched"] = True

                # Process matches
                for match in matches:
                    match_info = {
                        "rule": getattr(match, "rule", "unknown"),
                        "namespace": getattr(match, "namespace", "unknown"),
                        "meta": {},
                        "strings": [],
                    }

                    # Extract metadata if available
                    if hasattr(match, "meta") and match.meta:
                        match_info["meta"] = match.meta

                    # Extract matched strings if available
                    if hasattr(match, "strings"):
                        try:
                            for string_id, offset, string_data in match.strings:
                                match_info["strings"].append(
                                    {
                                        "id": string_id,
                                        "offset": offset,
                                        "data": (
                                            string_data.hex()
                                            if isinstance(string_data, bytes)
                                            else str(string_data)
                                        ),
                                    }
                                )
                        except Exception as e:
                            self.logger.warning(f"Error extracting matched strings: {str(e)}")

                    result["matches"].append(match_info)

            return result

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Error scanning file {file_path}: {str(e)}")
            return result

    def is_file_whitelisted(self, file_path, whitelist_rules):
        """
        Check if a file is whitelisted and should be skipped.

        Args:
            file_path (str): Path to file to check
            whitelist_rules (yara.Rules): YARA rules for whitelist

        Returns:
            bool: True if file is whitelisted, False otherwise
        """
        if not whitelist_rules:
            return False

        try:
            matches = whitelist_rules.match(file_path)
            return len(matches) > 0
        except:
            return False
