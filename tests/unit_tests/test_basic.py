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
    if not any(
        isinstance(p, str) and p and Path(p).resolve() == src_path for p in sys.path
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
