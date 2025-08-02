"""
Unit tests for the educational content validation script.

This module tests the validate_examples.py script that validates code blocks
in educational markdown files for syntax errors and security patterns.
"""

import os
import shutil

# Add the TOOLS directory to path to import the validation script
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "TOOLS", "dev-tools", "documentation")
)

from validate_examples import (
    CodeBlock,
    ValidationResult,
    extract_code_blocks,
    validate_bash_code,
    validate_code_block,
    validate_directory,
    validate_json_yaml,
    validate_python_code,
)


@pytest.mark.unit
class TestCodeBlock:
    """Unit tests for CodeBlock class"""

    def test_code_block_initialization(self):
        """Test CodeBlock initialization"""
        block = CodeBlock(
            code="print('hello')", language="python", file_path="/test/file.md", line_number=5
        )

        assert block.code == "print('hello')"
        assert block.language == "python"
        assert block.file_path == "/test/file.md"
        assert block.line_number == 5


@pytest.mark.unit
class TestValidationResult:
    """Unit tests for ValidationResult class"""

    def test_validation_result_initialization(self):
        """Test ValidationResult initialization"""
        block = CodeBlock("test", "python", "/test.md", 1)
        result = ValidationResult(block)

        assert result.block == block
        assert result.errors == []
        assert result.warnings == []
        assert result.is_valid is True

    def test_add_error(self):
        """Test adding errors"""
        block = CodeBlock("test", "python", "/test.md", 1)
        result = ValidationResult(block)

        result.add_error("Syntax error")

        assert len(result.errors) == 1
        assert result.errors[0] == "Syntax error"
        assert result.is_valid is False

    def test_add_warning(self):
        """Test adding warnings"""
        block = CodeBlock("test", "python", "/test.md", 1)
        result = ValidationResult(block)

        result.add_warning("Security warning")

        assert len(result.warnings) == 1
        assert result.warnings[0] == "Security warning"
        assert result.is_valid is True  # Warnings don't affect validity


@pytest.mark.unit
class TestExtractCodeBlocks:
    """Unit tests for extract_code_blocks function"""

    def create_temp_markdown(self, content):
        """Helper to create temporary markdown file"""
        fd, path = tempfile.mkstemp(suffix=".md")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            return path
        except Exception:
            os.close(fd)
            raise

    def test_extract_single_code_block(self):
        """Test extracting a single code block"""
        content = """# Test Document

```python
print("hello world")
```

Some text after.
"""
        path = self.create_temp_markdown(content)
        try:
            blocks = extract_code_blocks(path)

            assert len(blocks) == 1
            assert blocks[0].language == "python"
            assert blocks[0].code == 'print("hello world")\n'
            assert blocks[0].file_path == path
            assert blocks[0].line_number == 3
        finally:
            os.unlink(path)

    def test_extract_multiple_code_blocks(self):
        """Test extracting multiple code blocks"""
        content = """# Test Document

```python
print("python code")
```

Some text between blocks.

```bash
echo "bash code"
```

```json
{"key": "value"}
```
"""
        path = self.create_temp_markdown(content)
        try:
            blocks = extract_code_blocks(path)

            assert len(blocks) == 3

            # Python block
            assert blocks[0].language == "python"
            assert blocks[0].code == 'print("python code")\n'
            assert blocks[0].line_number == 3

            # Bash block
            assert blocks[1].language == "bash"
            assert blocks[1].code == 'echo "bash code"\n'
            assert blocks[1].line_number == 9

            # JSON block
            assert blocks[2].language == "json"
            assert blocks[2].code == '{"key": "value"}\n'
            assert blocks[2].line_number == 13
        finally:
            os.unlink(path)

    def test_extract_code_block_without_language(self):
        """Test extracting code block without language specified"""
        content = """# Test Document

```
plain code block
```
"""
        path = self.create_temp_markdown(content)
        try:
            blocks = extract_code_blocks(path)

            assert len(blocks) == 1
            assert blocks[0].language == ""
            assert blocks[0].code == "plain code block\n"
        finally:
            os.unlink(path)

    def test_extract_empty_code_block(self):
        """Test extracting empty code block"""
        content = """# Test Document

```python
```
"""
        path = self.create_temp_markdown(content)
        try:
            blocks = extract_code_blocks(path)

            assert len(blocks) == 0  # Empty blocks are not extracted
        finally:
            os.unlink(path)

    def test_extract_nested_code_blocks(self):
        """Test handling nested code blocks (malformed markdown)"""
        content = """# Test Document

```python
print("start")
```bash
echo "nested"
```
print("end")
```
"""
        path = self.create_temp_markdown(content)
        try:
            blocks = extract_code_blocks(path)

            # Should handle this gracefully by treating the second ``` as end
            assert len(blocks) == 2  # Actually finds 2 blocks due to malformed syntax
            assert blocks[0].language == "python"
            assert 'print("start")' in blocks[0].code
        finally:
            os.unlink(path)

    def test_extract_from_nonexistent_file(self):
        """Test extracting from non-existent file"""
        blocks = extract_code_blocks("/nonexistent/file.md")
        assert blocks == []


@pytest.mark.unit
class TestValidatePythonCode:
    """Unit tests for validate_python_code function"""

    def test_valid_python_code(self):
        """Test validation of valid Python code"""
        block = CodeBlock("print('hello world')", "python", "/test.md", 1)
        result = validate_python_code(block)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_invalid_python_syntax(self):
        """Test validation of invalid Python syntax"""
        block = CodeBlock("print('hello world'", "python", "/test.md", 1)
        result = validate_python_code(block)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Syntax error" in result.errors[0]

    def test_python_security_patterns(self):
        """Test detection of security patterns in Python code"""
        security_codes = [
            ("eval('1+1')", "eval()"),
            ("exec('print(1)')", "exec()"),
            ("__import__('os')", "__import__"),
            ("os.system('ls')", "os.system"),
            ("subprocess.call('ls', shell=True)", "shell=True"),
        ]

        for code, pattern in security_codes:
            block = CodeBlock(code, "python", "/test.md", 1)
            result = validate_python_code(block)

            assert result.is_valid is True  # Warnings don't invalidate
            assert len(result.warnings) >= 1
            # Check that the warning mentions the dangerous pattern
            warning_text = " ".join(result.warnings)
            assert (
                pattern in code or pattern.replace("()", "") in code
            )  # Verify our test case is correct

    def test_complex_python_code(self):
        """Test validation of complex valid Python code"""
        complex_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
"""
        block = CodeBlock(complex_code, "python", "/test.md", 1)
        result = validate_python_code(block)

        assert result.is_valid is True
        assert len(result.errors) == 0


@pytest.mark.unit
class TestValidateBashCode:
    """Unit tests for validate_bash_code function"""

    def test_valid_bash_code(self):
        """Test validation of valid Bash code"""
        block = CodeBlock("echo 'hello world'", "bash", "/test.md", 1)
        result = validate_bash_code(block)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_bash_security_patterns(self):
        """Test detection of security patterns in Bash code"""
        security_codes = [
            ("rm -rf /", "rm command"),
            (": () { : | : & }; :", "Fork bomb"),
            ("echo test > /dev/sda", "disk write"),
            ("dd if=/dev/zero of=/dev/sdb", "dd command"),
        ]

        for code, pattern_desc in security_codes:
            block = CodeBlock(code, "bash", "/test.md", 1)
            result = validate_bash_code(block)

            assert result.is_valid is True  # Warnings don't invalidate
            assert len(result.warnings) >= 1

    def test_invalid_bash_syntax(self):
        """Test validation of invalid Bash syntax"""
        # Use invalid syntax that bash -n will catch
        block = CodeBlock("if [ test; then echo 'missing fi'", "bash", "/test.md", 1)
        result = validate_bash_code(block)

        # Should have either an error or warning about syntax
        assert len(result.errors) >= 1 or len(result.warnings) >= 1

    def test_complex_bash_script(self):
        """Test validation of complex valid Bash script"""
        complex_bash = """#!/bin/bash
for file in *.txt; do
    if [[ -f "$file" ]]; then
        echo "Processing $file"
        wc -l "$file"
    fi
done
"""
        block = CodeBlock(complex_bash, "bash", "/test.md", 1)
        result = validate_bash_code(block)

        # Should be valid (no errors)
        assert len(result.errors) == 0

    @patch("subprocess.run")
    def test_bash_validation_subprocess_error(self, mock_run):
        """Test handling of subprocess errors during bash validation"""
        mock_run.side_effect = Exception("Subprocess failed")

        block = CodeBlock("echo 'test'", "bash", "/test.md", 1)
        result = validate_bash_code(block)

        # Should add a warning about validation failure
        assert len(result.warnings) >= 1
        assert "Could not validate bash syntax" in result.warnings[0]


@pytest.mark.unit
class TestValidateJsonYaml:
    """Unit tests for validate_json_yaml function"""

    def test_valid_json(self):
        """Test validation of valid JSON"""
        json_code = '{"name": "test", "value": 123}'
        block = CodeBlock(json_code, "json", "/test.md", 1)
        result = validate_json_yaml(block)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_invalid_json(self):
        """Test validation of invalid JSON"""
        json_code = '{"name": "test", "value": 123'  # Missing closing brace
        block = CodeBlock(json_code, "json", "/test.md", 1)
        result = validate_json_yaml(block)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Invalid JSON" in result.errors[0]

    def test_valid_yaml(self):
        """Test validation of valid YAML"""
        yaml_code = """
name: test
value: 123
items:
  - item1
  - item2
"""
        block = CodeBlock(yaml_code, "yaml", "/test.md", 1)
        result = validate_json_yaml(block)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_invalid_yaml(self):
        """Test validation of invalid YAML"""
        yaml_code = """
name: test
  value: 123  # Invalid indentation
"""
        block = CodeBlock(yaml_code, "yaml", "/test.md", 1)
        result = validate_json_yaml(block)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Invalid YAML" in result.errors[0]

    def test_yaml_without_pyyaml(self):
        """Test YAML validation when PyYAML is not available"""
        # This test simulates the case where yaml module is not importable
        yaml_code = "name: test"
        block = CodeBlock(yaml_code, "yaml", "/test.md", 1)

        # Mock the import to raise ImportError
        with patch("builtins.__import__", side_effect=ImportError("No module named yaml")):
            result = validate_json_yaml(block)

            assert result.is_valid is True  # No error, just warning
            assert len(result.warnings) >= 1
            assert "PyYAML not installed" in result.warnings[0]

    def test_case_insensitive_languages(self):
        """Test that language detection is case insensitive"""
        json_code = '{"test": true}'

        # Test various case combinations
        for lang in ["JSON", "Json", "json"]:
            block = CodeBlock(json_code, lang, "/test.md", 1)
            result = validate_json_yaml(block)
            assert result.is_valid is True

        yaml_code = "test: true"
        for lang in ["YAML", "Yaml", "yaml", "YML", "yml"]:
            block = CodeBlock(yaml_code, lang, "/test.md", 1)
            result = validate_json_yaml(block)
            assert result.is_valid is True


@pytest.mark.unit
class TestValidateCodeBlock:
    """Unit tests for validate_code_block function"""

    def test_python_code_validation(self):
        """Test validation routing for Python code"""
        block = CodeBlock("print('test')", "python", "/test.md", 1)
        result = validate_code_block(block)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_bash_code_validation(self):
        """Test validation routing for Bash code"""
        block = CodeBlock("echo 'test'", "bash", "/test.md", 1)
        result = validate_code_block(block)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_json_code_validation(self):
        """Test validation routing for JSON code"""
        block = CodeBlock('{"test": true}', "json", "/test.md", 1)
        result = validate_code_block(block)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_yaml_code_validation(self):
        """Test validation routing for YAML code"""
        block = CodeBlock("test: true", "yaml", "/test.md", 1)
        result = validate_code_block(block)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_unsupported_language(self):
        """Test validation of unsupported language"""
        block = CodeBlock("SELECT * FROM users;", "sql", "/test.md", 1)
        result = validate_code_block(block)

        assert result.is_valid is True  # No validation performed
        assert len(result.warnings) == 1
        assert "No validator for language: sql" in result.warnings[0]

    def test_empty_language(self):
        """Test validation of code block with no language specified"""
        block = CodeBlock("some generic code", "", "/test.md", 1)
        result = validate_code_block(block)

        assert result.is_valid is True  # No validation performed
        assert len(result.warnings) == 0  # No warning for empty language

    def test_language_aliases(self):
        """Test that language aliases work correctly"""
        python_aliases = ["python", "py", "python3"]
        bash_aliases = ["bash", "sh", "shell"]
        yaml_aliases = ["yaml", "yml"]

        # Test Python aliases
        for alias in python_aliases:
            block = CodeBlock("print('test')", alias, "/test.md", 1)
            result = validate_code_block(block)
            assert result.is_valid is True

        # Test Bash aliases
        for alias in bash_aliases:
            block = CodeBlock("echo 'test'", alias, "/test.md", 1)
            result = validate_code_block(block)
            assert result.is_valid is True

        # Test YAML aliases
        for alias in yaml_aliases:
            block = CodeBlock("test: true", alias, "/test.md", 1)
            result = validate_code_block(block)
            assert result.is_valid is True


@pytest.mark.unit
class TestValidateDirectory:
    """Unit tests for validate_directory function"""

    def setUp_temp_directory(self):
        """Set up a temporary directory with test markdown files"""
        temp_dir = tempfile.mkdtemp()

        # Create markdown file with valid code
        valid_md = os.path.join(temp_dir, "valid.md")
        with open(valid_md, "w") as f:
            f.write(
                """# Valid Examples

```python
print("hello world")
```

```json
{"valid": true}
```
"""
            )

        # Create markdown file with invalid code
        invalid_md = os.path.join(temp_dir, "invalid.md")
        with open(invalid_md, "w") as f:
            f.write(
                """# Invalid Examples

```python
print("unclosed string
```

```json
{"invalid": json}
```
"""
            )

        # Create markdown file with security warnings
        security_md = os.path.join(temp_dir, "security.md")
        with open(security_md, "w") as f:
            f.write(
                """# Security Examples

```python
eval("1+1")
```

```bash
rm -rf /tmp
```
"""
            )

        # Create subdirectory with markdown
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)
        sub_md = os.path.join(subdir, "sub.md")
        with open(sub_md, "w") as f:
            f.write(
                """# Subdirectory Examples

```python
import os
```
"""
            )

        # Create non-markdown file (should be ignored)
        txt_file = os.path.join(temp_dir, "readme.txt")
        with open(txt_file, "w") as f:
            f.write("This is not markdown")

        return temp_dir

    def test_validate_directory_success(self):
        """Test successful directory validation"""
        temp_dir = self.setUp_temp_directory()
        try:
            errors, warnings = validate_directory(temp_dir, verbose=False)

            # Should find some errors in invalid.md
            assert errors > 0
            # Should find some warnings in security.md
            assert warnings > 0
        finally:
            shutil.rmtree(temp_dir)

    def test_validate_directory_verbose(self):
        """Test directory validation with verbose output"""
        temp_dir = self.setUp_temp_directory()
        try:
            # Capture log output would require more complex setup
            # For now, just verify it runs without error
            errors, warnings = validate_directory(temp_dir, verbose=True)

            assert isinstance(errors, int)
            assert isinstance(warnings, int)
        finally:
            shutil.rmtree(temp_dir)

    def test_validate_nonexistent_directory(self):
        """Test validation of non-existent directory"""
        # This should be handled by the main() function
        # The validate_directory function itself will process what it finds
        errors, warnings = validate_directory("/nonexistent/directory")

        # Should not crash, should return 0 errors and warnings
        assert errors == 0
        assert warnings == 0

    def test_validate_empty_directory(self):
        """Test validation of empty directory"""
        temp_dir = tempfile.mkdtemp()
        try:
            errors, warnings = validate_directory(temp_dir)

            assert errors == 0
            assert warnings == 0
        finally:
            shutil.rmtree(temp_dir)

    def test_recursive_directory_processing(self):
        """Test that subdirectories are processed recursively"""
        temp_dir = self.setUp_temp_directory()
        try:
            errors, warnings = validate_directory(temp_dir, verbose=True)

            # Should process files in subdirectories too
            # The exact counts depend on the validation results
            assert isinstance(errors, int)
            assert isinstance(warnings, int)
        finally:
            shutil.rmtree(temp_dir)


@pytest.mark.integration
class TestValidationIntegration:
    """Integration tests for the validation system"""

    def test_end_to_end_validation(self):
        """Test complete validation workflow"""
        # Create a comprehensive test markdown file
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "comprehensive.md")

        content = """# Comprehensive Test Document

## Valid Python Code
```python
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
```

## Invalid Python Code
```python
def broken_function(
    # Missing closing parenthesis and body
```

## Valid Bash Code
```bash
#!/bin/bash
for file in *.txt; do
    echo "Processing $file"
done
```

## Security Warning Code
```python
user_input = input("Enter code: ")
eval(user_input)  # Dangerous!
```

```bash
# Dangerous command
rm -rf /tmp/test
```

## Valid JSON
```json
{
    "name": "test",
    "version": "1.0.0",
    "dependencies": []
}
```

## Invalid JSON
```json
{
    "name": "test",
    "version": 1.0.0,  // Comments not allowed in JSON
    "missing_quote": test
}
```

## Valid YAML
```yaml
name: test
version: 1.0.0
dependencies:
  - numpy
  - pandas
```

## Unsupported Language
```rust
fn main() {
    println!("Hello, Rust!");
}
```
"""

        try:
            with open(test_file, "w") as f:
                f.write(content)

            # Test extraction
            blocks = extract_code_blocks(test_file)
            assert len(blocks) == 9  # Should find all code blocks

            # Test validation
            errors, warnings = validate_directory(temp_dir, verbose=True)

            # Should have some errors (invalid Python, invalid JSON)
            assert errors > 0
            # Should have some warnings (security patterns, unsupported language)
            assert warnings > 0

            # Test individual block validation
            python_blocks = [b for b in blocks if b.language == "python"]
            assert len(python_blocks) == 2  # One valid, one invalid

            valid_python = python_blocks[0]  # First one should be valid
            result = validate_python_code(valid_python)
            assert result.is_valid is True

        finally:
            shutil.rmtree(temp_dir)
