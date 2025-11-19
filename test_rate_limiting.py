#!/usr/bin/env python3
"""
Test rate limiting functionality of LLM7Client
"""

import time
from llm7_client import LLM7Client

def test_rate_limit_validation():
    """Test that rate limits are properly enforced"""
    print("=" * 70)
    print("TESTING RATE LIMITING")
    print("=" * 70)
    print()
    
    client = LLM7Client('test_token')
    
    # Test 1: Validate request size limit (128k chars)
    print("Test 1: Request size validation (128k chars/req)")
    large_prompt = "x" * 130000  # Exceeds limit
    result = client._validate_request_size(large_prompt)
    assert result == False, "Should reject requests larger than 128k chars"
    print("✅ Large request rejected")
    
    small_prompt = "x" * 1000  # Within limit
    result = client._validate_request_size(small_prompt)
    assert result == True, "Should accept requests smaller than 128k chars"
    print("✅ Normal request accepted")
    print()
    
    # Test 2: Check rate limit constants
    print("Test 2: Rate limit constants")
    assert client.MAX_CHARS_PER_REQUEST == 128000, "Max chars should be 128k"
    print(f"✅ Max chars/req: {client.MAX_CHARS_PER_REQUEST}")
    
    assert client.MAX_REQUESTS_PER_HOUR == 1500, "Max hourly should be 1500"
    print(f"✅ Max req/hour: {client.MAX_REQUESTS_PER_HOUR}")
    
    assert client.MAX_REQUESTS_PER_MINUTE == 60, "Max per minute should be 60"
    print(f"✅ Max req/min: {client.MAX_REQUESTS_PER_MINUTE}")
    
    assert client.MAX_REQUESTS_PER_SECOND == 5, "Max per second should be 5"
    print(f"✅ Max req/sec: {client.MAX_REQUESTS_PER_SECOND}")
    print()
    
    # Test 3: Test rate limit tracking
    print("Test 3: Rate limit tracking")
    
    # Simulate 3 requests
    for i in range(3):
        client._record_request()
        time.sleep(0.1)
    
    # Check that requests were recorded
    assert len(client._request_times_second) > 0, "Should track requests"
    assert len(client._request_times_minute) > 0, "Should track requests"
    assert len(client._request_times_hour) > 0, "Should track requests"
    print("✅ Request tracking working")
    print()
    
    # Test 4: Test cleanup of old requests
    print("Test 4: Cleanup of old requests")
    client2 = LLM7Client('test_token')
    
    # Add some old requests
    old_time = time.time() - 3700  # More than 1 hour ago
    client2._request_times_hour.append(old_time)
    client2._request_times_minute.append(old_time)
    client2._request_times_second.append(old_time)
    
    # Cleanup
    client2._cleanup_old_requests()
    
    # Old requests should be removed
    assert len(client2._request_times_hour) == 0, "Old hour requests should be cleaned"
    assert len(client2._request_times_minute) == 0, "Old minute requests should be cleaned"
    assert len(client2._request_times_second) == 0, "Old second requests should be cleaned"
    print("✅ Old requests cleaned up correctly")
    print()
    
    # Test 5: Test per-second rate limiting
    print("Test 5: Per-second rate limiting (5 req/s)")
    client3 = LLM7Client('test_token')
    
    # Fill up to the limit
    current_time = time.time()
    for i in range(5):
        client3._request_times_second.append(current_time)
    
    # Next request should trigger wait
    start = time.time()
    client3._wait_for_rate_limit()
    elapsed = time.time() - start
    
    # Should have waited close to 1 second
    assert elapsed >= 0.9, f"Should wait ~1s, waited {elapsed:.2f}s"
    print(f"✅ Rate limiter waited {elapsed:.2f}s (expected ~1s)")
    print()
    
    print("=" * 70)
    print("✅ ALL RATE LIMITING TESTS PASSED")
    print("=" * 70)
    print()
    print("Rate limits enforced:")
    print("  • 128k chars/req   ✓")
    print("  • 1,500 req/h      ✓")
    print("  • 60 req/min       ✓")
    print("  • 5 req/s          ✓")

if __name__ == '__main__':
    try:
        test_rate_limit_validation()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
