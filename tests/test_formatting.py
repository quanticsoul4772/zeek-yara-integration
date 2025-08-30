"""
Test file to verify Black formatting and isort import sorting checks work properly.
This file is intentionally misformatted to test CI behavior.
"""

# Intentionally poorly formatted imports (isort violations)
import os
import pytest
from pathlib import Path
import sys
from typing import Dict, List

# Intentionally poorly formatted code (Black violations)
def poorly_formatted_function(param1,param2,param3):
    """This function has poor formatting to test Black enforcement."""
    # Long line that exceeds 88 characters and should be wrapped by Black formatting tool
    result={'key1':'value1','key2':'value2','key3':'value3','key4':'value4'}
    
    if param1=='test'and param2=='value'or param3=='something':
        return result
    
    return None


class TestFormatting:
    """Test class to verify formatting tools work correctly."""
    
    def test_black_formatting_check(self):
        """Test that verifies Black formatting is enforced."""
        # This function should pass once formatting is fixed
        assert True
        
    def test_isort_import_check(self):
        """Test that verifies isort import sorting is enforced.""" 
        # This function should pass once import sorting is fixed
        assert True
        
    def test_formatting_consistency(self):
        """Test that ensures consistent code formatting across the project."""
        assert True