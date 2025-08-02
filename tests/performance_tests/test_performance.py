"""Performance tests"""
import time

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
