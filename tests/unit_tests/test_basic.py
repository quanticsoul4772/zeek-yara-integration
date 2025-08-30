"""Basic unit tests"""

from pathlib import Path


def test_imports():
    """Test basic imports work"""
    # Import from src directory to avoid circular import
    import sys
    from pathlib import Path

    # Add src to path (use absolute, normalized path to avoid duplicates)
    src_path = (Path(__file__).parent.parent.parent / "src").resolve()
    src_path_str = str(src_path)
    # More robust path comparison with error handling and better type safety
    src_path_resolved = str(src_path)
    
    def safe_path_resolve(path_entry):
        """Safely resolve a path entry, handling errors gracefully."""
        if not path_entry or not isinstance(path_entry, (str, Path)):
            return None
        try:
            return str(Path(path_entry).resolve())
        except (OSError, ValueError):
            # Handle malformed paths or filesystem errors
            return None
    
    if not any(
        safe_path_resolve(p) == src_path_resolved for p in sys.path
    ):
        sys.path.insert(0, src_path_str)

    import main as src_main
    import setup_wizard
    import tutorial_system

    assert True


def test_placeholder():
    """Placeholder test"""
    assert 1 + 1 == 2


def test_no_py_typed_files():
    """Ensure no py.typed files exist in repository (excluding venv)."""
    py_typed_files = [
        f
        for f in Path(".").rglob("py.typed")
        if "venv" not in str(f) and ".git" not in str(f)
    ]
    assert len(py_typed_files) == 0, f"Found py.typed files: {py_typed_files}"
