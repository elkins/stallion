"""
Tests for PyPI API rate limiting functionality.
"""
import pytest
import time
from stallion.main import RateLimiter


class TestRateLimiter:
    """Tests for the RateLimiter class."""
    
    def test_rate_limiter_basic(self):
        """Test basic rate limiter functionality."""
        limiter = RateLimiter(max_calls=5, period=1.0)
        
        # Should allow 5 calls immediately
        start_time = time.time()
        for _ in range(5):
            limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        # Should complete quickly (under 0.1s)
        assert elapsed < 0.1
    
    def test_rate_limiter_blocks(self):
        """Test that rate limiter blocks when limit exceeded."""
        limiter = RateLimiter(max_calls=3, period=1.0)
        
        # Make 3 calls quickly
        for _ in range(3):
            limiter.wait_if_needed()
        
        # The 4th call should block
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        # Should have slept for close to 1 second
        assert elapsed >= 0.9  # Account for timing variance
        assert elapsed < 1.2   # But not too much longer
    
    def test_rate_limiter_allows_after_period(self):
        """Test that rate limiter allows calls after the period expires."""
        limiter = RateLimiter(max_calls=2, period=0.5)
        
        # Make 2 calls
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        
        # Wait for period to expire
        time.sleep(0.6)
        
        # Should allow 2 more calls immediately
        start_time = time.time()
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        # Should complete quickly
        assert elapsed < 0.1
    
    def test_rate_limiter_sliding_window(self):
        """Test that rate limiter uses sliding window correctly."""
        limiter = RateLimiter(max_calls=3, period=1.0)
        
        # Make 3 calls
        limiter.wait_if_needed()
        time.sleep(0.4)
        limiter.wait_if_needed()
        time.sleep(0.4)
        limiter.wait_if_needed()
        
        # Now we've spread calls over 0.8s
        # The 4th call should only need to wait ~0.2s (until first call expires at 1.0s)
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        # Should wait around 0.2s (until 1.0s from first call)
        assert elapsed >= 0.15
        assert elapsed < 0.4
    
    def test_rate_limiter_concurrent_safety(self):
        """Test that rate limiter is thread-safe."""
        import threading
        
        limiter = RateLimiter(max_calls=10, period=1.0)
        call_times = []
        
        def make_call():
            limiter.wait_if_needed()
            call_times.append(time.time())
        
        # Start 20 threads trying to make calls
        threads = []
        start_time = time.time()
        for _ in range(20):
            t = threading.Thread(target=make_call)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        total_time = time.time() - start_time
        
        # With 20 calls and max 10 per second, should take at least 1 second
        assert total_time >= 0.9
        assert len(call_times) == 20
    
    def test_rate_limiter_zero_calls(self):
        """Test rate limiter initialization with various values."""
        limiter = RateLimiter(max_calls=1, period=0.1)
        
        # First call should be immediate
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        assert elapsed < 0.05
    
    def test_rate_limiter_preserves_order(self):
        """Test that rate limiter preserves call order."""
        limiter = RateLimiter(max_calls=2, period=0.5)
        
        call_order = []
        
        for i in range(4):
            limiter.wait_if_needed()
            call_order.append(i)
        
        # Should process in order: 0, 1, 2, 3
        assert call_order == [0, 1, 2, 3]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
