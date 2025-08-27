"""Basic integration tests"""

import os
import tempfile


def test_temp_directory():
    """Test temp directory creation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        assert os.path.exists(tmpdir)
    assert True
