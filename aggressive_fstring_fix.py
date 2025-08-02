#!/usr/bin/env python3
"""
Aggressively fix all f-string and formatting issues
"""

import os
import re
from pathlib import Path

def fix_all_fstrings_in_file(filepath):
    """Aggressively fix all f-string issues in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return False
    
    fixed = False
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for f-string patterns that might be broken
        if re.search(r'f["\'].*{$', line.rstrip()):
            # This line ends with an open brace in an f-string
            # Collect the full f-string
            indent = len(line) - len(line.lstrip())
            parts = [line.rstrip()]
            j = i + 1
            
            # Look for the closing of the f-string
            while j < len(lines) and j < i + 20:  # Max 20 lines
                next_line = lines[j].rstrip()
                parts.append(next_line.strip())
                
                # Check if this completes the f-string
                full_text = ' '.join(parts)
                if full_text.count('{') == full_text.count('}'):
                    # Found complete f-string, reconstruct it
                    # Clean up the formatting
                    full_text = re.sub(r'\s+', ' ', full_text)
                    full_text = re.sub(r'{\s+', '{', full_text)
                    full_text = re.sub(r'\s+}', '}', full_text)
                    
                    # Add proper line ending
                    if not full_text.endswith(('",', '",\n', '"\n', "',", "',\n", "'\n")):
                        if '")' in lines[j]:
                            full_text = full_text.rstrip() + ')'
                        elif '",' in lines[j]:
                            full_text = full_text.rstrip() + ','
                    
                    new_lines.append(' ' * indent + full_text + '\n')
                    i = j + 1
                    fixed = True
                    break
                j += 1
            else:
                # Couldn't fix, keep original
                new_lines.append(line)
                i += 1
        else:
            new_lines.append(line)
            i += 1
    
    if fixed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    
    return False

def main():
    print("🔍 Searching for and fixing f-string issues...")
    
    files_to_check = [
        "tutorial_system.py",
        "main.py",
        "setup_wizard.py",
        "bin/yara_scanner_cli.py",
        "tests/test_scanner.py",
        "tests/test_integration.py",
        "tests/test_deployment.py",
        "tests/test_security.py",
        "tests/test_setup_validation.py",
        "tests/test_setup_wizard.py",
        "zeek/scripts/generate_zeek_script.py",
        "EDUCATION/demo_runner.py",
        "EDUCATION/generate_exercises.py",
        "EDUCATION/setup_learning_env.py",
        "PLATFORM/notification_system.py",
        "PLATFORM/zeek_integration.py",
        "PLATFORM/data_processing.py"
    ]
    
    fixed_count = 0
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"Checking {file}...")
            if fix_all_fstrings_in_file(file):
                print(f"   ✅ Fixed {file}")
                fixed_count += 1
            else:
                # Try to compile to check for errors
                try:
                    with open(file, 'r') as f:
                        compile(f.read(), file, 'exec')
                except SyntaxError as e:
                    print(f"   ❌ Error in {file}:{e.lineno} - {e.msg}")
                    
                    # Try a more aggressive fix
                    with open(file, 'r') as f:
                        content = f.read()
                    
                    # Replace all multi-line f-strings with single line versions
                    content = re.sub(
                        r'f"{\s*([^}]+?)\s*}"',
                        lambda m: f'f"{{{m.group(1).replace(chr(10), " ").replace(chr(13), " ").strip()}}}"',
                        content,
                        flags=re.DOTALL
                    )
                    
                    with open(file, 'w') as f:
                        f.write(content)
                    print(f"   🔧 Applied aggressive fix to {file}")
                    fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")
    
    # Also run on all Python files in key directories
    for directory in ['PLATFORM', 'EDUCATION', 'TOOLS', 'scripts', 'bin']:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        if fix_all_fstrings_in_file(filepath):
                            print(f"   ✅ Fixed {filepath}")
                            fixed_count += 1
    
    print(f"\n✅ Total files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
