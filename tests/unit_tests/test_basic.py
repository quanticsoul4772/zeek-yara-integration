"""Basic unit tests"""
from pathlib import Path

def test_imports():
    """Test basic imports work"""
    import main
    import setup_wizard
    import tutorial_system
    assert True

def test_placeholder():
    """Placeholder test"""
    assert 1 + 1 == 2

def test_no_py_typed_files():
    """Ensure no py.typed files exist in repository."""
    py_typed_files = list(Path('.').rglob('py.typed'))
    assert len(py_typed_files) == 0, f"Found py.typed files: {py_typed_files}"
