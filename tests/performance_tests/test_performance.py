"""Performance benchmarks"""

import time


def test_basic_performance(benchmark):
    """Basic performance test"""

    def sample_function():
        time.sleep(0.001)
        return sum(range(100))

    result = benchmark(sample_function)
    assert result == 4950
