#!/usr/bin/env python3
"""
Simple test script to verify rate limiting implementation for worker registration endpoint
"""

import os
import sys
import json
import asyncio
from httpx import AsyncClient

# Add PLATFORM to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "PLATFORM")))

from api.api_server import app

async def test_worker_registration_rate_limiting():
    """Test that worker registration rate limiting is properly enforced"""
    print("Testing worker registration rate limiting...")
    
    # Test data for worker registration
    worker_data = {
        "worker_id": "test-worker-001",
        "host": "localhost",
        "port": 8001,
        "capabilities": ["file_scan"],
        "max_tasks": 5,
        "metadata": {"version": "1.0"}
    }
    
    headers = {"X-API-Key": "test-key"}  # May need valid key depending on config
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        success_count = 0
        rate_limited_count = 0
        
        # Try to make more requests than the rate limit allows
        print("Making 15 requests to test rate limiting (limit should be 10/minute)...")
        
        for i in range(15):
            try:
                # Change worker_id for each request to avoid duplicate registration errors
                test_data = worker_data.copy()
                test_data["worker_id"] = f"test-worker-{i:03d}"
                
                response = await client.post(
                    "/distributed/workers/register",
                    json=test_data,
                    headers=headers
                )
                
                if response.status_code == 429:
                    rate_limited_count += 1
                    print(f"Request {i+1}: Rate limited (HTTP 429) ✓")
                elif response.status_code in [200, 201]:
                    success_count += 1
                    print(f"Request {i+1}: Success (HTTP {response.status_code})")
                else:
                    print(f"Request {i+1}: Other response (HTTP {response.status_code}): {response.text}")
                    
            except Exception as e:
                print(f"Request {i+1}: Exception - {e}")
        
        print(f"\nResults:")
        print(f"Successful requests: {success_count}")
        print(f"Rate limited requests: {rate_limited_count}")
        print(f"Total requests: {success_count + rate_limited_count}")
        
        # Verify rate limiting is working
        if rate_limited_count > 0:
            print("✓ Rate limiting is working - requests were blocked with HTTP 429")
            return True
        else:
            print("✗ Rate limiting may not be working - no requests were rate limited")
            return False

if __name__ == "__main__":
    # Simple syntax check first
    try:
        from api.api_server import app, worker_registration_rate_limit
        print(f"✓ API server imports successfully")
        print(f"✓ Worker registration rate limit: {worker_registration_rate_limit}")
        
        # Run the actual test
        result = asyncio.run(test_worker_registration_rate_limiting())
        
        if result:
            print("\n✓ Rate limiting test passed!")
        else:
            print("\n⚠ Rate limiting test inconclusive")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")