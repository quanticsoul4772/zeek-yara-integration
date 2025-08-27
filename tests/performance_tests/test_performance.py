"""Performance tests"""

import time

import pytest


def test_basic_performance(benchmark):
    """Basic performance test"""

    def sample_function():
        time.sleep(0.001)
        return sum(range(100))

    result = benchmark(sample_function)
    assert result == 4950


def test_suricata_performance_placeholder(benchmark):
    """Placeholder for suricata performance"""

    def mock_operation():
        return {"status": "success"}

    result = benchmark(mock_operation)
    assert result["status"] == "success"


@pytest.mark.performance
def test_import_performance():
    """Verify import performance meets targets."""
    start = time.time()
    import PLATFORM.core.scanner

    duration = time.time() - start
    assert duration < 0.5, f"Import took {duration}s, exceeds 500ms target"
