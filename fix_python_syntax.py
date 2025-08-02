#!/usr/bin/env python3
"""
Fix all Python syntax errors before Black formatting
"""

import os
import re
import subprocess
from pathlib import Path

def fix_multiline_fstrings(content):
    """Fix multi-line f-strings"""
    # Pattern to find f-strings that span multiple lines incorrectly
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has an f-string start but might be broken
        if 'f"{' in line or "f'{" in line:
            # Check if the f-string is not closed on the same line
            if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
                # Look ahead to find the closing quote
                j = i + 1
                combined = line
                while j < len(lines) and j < i + 10:  # Max 10 lines ahead
                    next_line = lines[j]
                    combined += ' ' + next_line.strip()
                    
                    # Check if we've closed the f-string
                    if ('"' in next_line and combined.count('"') % 2 == 0) or \
                       ("'" in next_line and combined.count("'") % 2 == 0):
                        # Found the end, now reconstruct
                        # Remove the broken f-string lines
                        indent = len(line) - len(line.lstrip())
                        fixed_line = ' ' * indent + combined.strip()
                        
                        # Clean up the f-string
                        fixed_line = re.sub(r'f"{\s*', 'f"{', fixed_line)
                        fixed_line = re.sub(r"f'{\s*", "f'{", fixed_line)
                        fixed_line = re.sub(r'\s*}"', '}"', fixed_line)
                        fixed_line = re.sub(r"\s*}'", "}'", fixed_line)
                        
                        fixed_lines.append(fixed_line)
                        i = j + 1
                        break
                    j += 1
                else:
                    # Couldn't fix, keep original
                    fixed_lines.append(line)
                    i += 1
            else:
                fixed_lines.append(line)
                i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_file(filepath):
    """Fix syntax errors in a Python file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix multi-line f-strings
        content = fix_multiline_fstrings(content)
        
        # Try to compile to check for errors
        try:
            compile(content, filepath, 'exec')
            if content != original_content:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"   ✅ Fixed {filepath}")
                return True
        except SyntaxError as e:
            print(f"   ⚠️  Still has errors: {filepath}:{e.lineno} - {e.msg}")
            
            # Try additional fixes
            if "EOL while scanning string literal" in str(e):
                # Find and fix unclosed strings
                lines = content.split('\n')
                if e.lineno and e.lineno <= len(lines):
                    line = lines[e.lineno - 1]
                    # Check for unclosed f-strings
                    if 'f"' in line or "f'" in line:
                        # Simple fix: close the string at the end of the line
                        if line.count('"') % 2 != 0:
                            lines[e.lineno - 1] = line + '"'
                        elif line.count("'") % 2 != 0:
                            lines[e.lineno - 1] = line + "'"
                        
                        content = '\n'.join(lines)
                        with open(filepath, 'w') as f:
                            f.write(content)
                        print(f"   ✅ Fixed EOL error in {filepath}")
                        return True
            
    except Exception as e:
        print(f"   ❌ Error processing {filepath}: {e}")
    
    return False

def main():
    print("🔧 Fixing Python syntax errors...")
    
    fixed_count = 0
    error_count = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments
        if 'venv' in root or '.venv' in root or '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_count += 1
                else:
                    # Try to get the specific error
                    try:
                        with open(filepath, 'r') as f:
                            compile(f.read(), filepath, 'exec')
                    except SyntaxError as e:
                        error_count += 1
                        print(f"   ❌ {filepath}:{e.lineno} - {e.msg}")
    
    print(f"\n✅ Fixed {fixed_count} files")
    print(f"❌ {error_count} files still have errors")
    
    # Run autopep8 to fix other issues
    print("\n🎨 Running autopep8...")
    result = subprocess.run(
        "autopep8 --in-place --recursive --aggressive --aggressive --max-line-length=100 .",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ autopep8 completed successfully")
    else:
        print(f"⚠️  autopep8 had issues: {result.stderr[:200]}")
    
    print("\n✨ Done! Try running Black again.")

if __name__ == "__main__":
    main()
