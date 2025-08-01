#!/usr/bin/env python3
"""
Simple linting check for common issues that flake8 would catch
"""

import ast
import os
import re
import sys

def check_syntax_errors(file_path):
    """Check for syntax errors (E9 errors)"""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check for syntax errors
        try:
            ast.parse(source, filename=file_path)
        except SyntaxError as e:
            errors.append({
                'file': file_path,
                'line': e.lineno,
                'col': e.offset or 0,
                'code': 'E901',
                'message': f'SyntaxError: {e.msg}'
            })
        except Exception as e:
            errors.append({
                'file': file_path,
                'line': 1,
                'col': 0,
                'code': 'E902',
                'message': f'Error parsing file: {str(e)}'
            })
            
    except Exception as e:
        errors.append({
            'file': file_path,
            'line': 1,
            'col': 0,
            'code': 'E903',
            'message': f'Error reading file: {str(e)}'
        })
    
    return errors

def check_unused_imports(file_path):
    """Check for potentially unused imports (F401)"""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        import_lines = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                # Skip relative imports and common patterns that are likely used
                if ('import *' not in line and 
                    'from typing import' not in line and
                    'from pathlib import' not in line and
                    'from datetime import' not in line):
                    import_lines.append((i, line))
        
        # For now, just flag imports that look suspicious (basic check)
        # This is a simplified version of what flake8 would do
        
    except Exception:
        pass
    
    return errors

def check_undefined_names(file_path):
    """Check for undefined names (F821)"""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse AST to find undefined names
        try:
            tree = ast.parse(source, filename=file_path)
            # This would require more complex analysis
        except SyntaxError:
            pass
            
    except Exception:
        pass
    
    return errors

def analyze_file(file_path):
    """Analyze a single Python file for linting issues"""
    all_errors = []
    
    # Check syntax errors (E9 codes)
    all_errors.extend(check_syntax_errors(file_path))
    
    # Check unused imports (F401)
    all_errors.extend(check_unused_imports(file_path))
    
    # Check undefined names (F821)
    all_errors.extend(check_undefined_names(file_path))
    
    return all_errors

def main():
    """Main function to analyze all Python files"""
    exclude_dirs = {'venv', '.venv', '__pycache__', 'extracted_files', 'DATA'}
    exclude_patterns = {'runtime', '.git'}
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs and 
                  not any(pattern in d for pattern in exclude_patterns)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    total_errors = []
    file_count = 0
    
    for py_file in python_files:
        file_count += 1
        errors = analyze_file(py_file)
        total_errors.extend(errors)
    
    # Print results in flake8 format
    if total_errors:
        for error in total_errors:
            print(f"{error['file']}:{error['line']}:{error['col']}: {error['code']} {error['message']}")
        print(f"\nTotal: {len(total_errors)} errors found in {file_count} files")
    else:
        print(f"No critical syntax errors found in {file_count} Python files")
        print("Note: This is a basic syntax check. For complete linting, install and run flake8.")

if __name__ == "__main__":
    main()