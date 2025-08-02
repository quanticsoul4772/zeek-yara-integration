"""Performance tests"""

import time


def test_performance(benchmark):
    """Basic performance test"""

    def sample_function():
        time.sleep(0.001)
        return True

    result = benchmark(sample_function)
    assert result is True
