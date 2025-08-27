"""
Simple async test examples demonstrating pytest-asyncio usage
This file shows the basic pattern requested in the GitHub issue
"""

import asyncio
import os

# Import the FastAPI app
import sys
from unittest.mock import patch

import pytest
from httpx import AsyncClient

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "PLATFORM"))
)

from api.api_server import app


@pytest.mark.asyncio
async def test_api_endpoint():
    """Test async FastAPI endpoints - basic example as requested"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test the root endpoint
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data


@pytest.mark.asyncio
async def test_status_endpoint():
    """Test async status endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Disable API key auth for this test
        with patch("api.api_server.API_KEY", ""):
            response = await client.get("/status")
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert "uptime" in data


@pytest.mark.asyncio
async def test_concurrent_api_calls():
    """Test multiple concurrent async API calls"""
    async with AsyncClient(app=app, base_url="http://test") as client:

        async def make_api_call():
            """Helper function to make an API call"""
            return await client.get("/")

        # Make multiple concurrent requests
        tasks = [make_api_call() for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # Verify all responses
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Zeek-YARA Integration API"


@pytest.mark.asyncio
async def test_alerts_endpoint_basic():
    """Test async alerts endpoint - basic usage"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Mock the database to avoid dependencies
        with patch("api.api_server.db_manager") as mock_db:
            mock_db.get_alerts.return_value = []

            # Disable API key for test
            with patch("api.api_server.API_KEY", ""):
                response = await client.get("/alerts")
                assert response.status_code == 200

                data = response.json()
                assert "alerts" in data
                assert isinstance(data["alerts"], list)


@pytest.mark.asyncio
async def test_async_exception_handling():
    """Test async exception handling in API calls"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test accessing non-existent endpoint
        response = await client.get("/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ["/", "/docs", "/openapi.json"])
async def test_multiple_endpoints_async(endpoint):
    """Test multiple endpoints using async and parametrize"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(endpoint)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_async_with_timeout():
    """Test async API calls with timeout"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Use asyncio.wait_for to test with timeout
        try:
            response = await asyncio.wait_for(client.get("/"), timeout=5.0)
            assert response.status_code == 200
        except asyncio.TimeoutError:
            pytest.fail("API call timed out")


@pytest.mark.asyncio
async def test_async_setup_and_teardown():
    """Test async setup and teardown patterns"""
    # Async setup
    setup_data = await asyncio.sleep(0.1, result="setup_complete")
    assert setup_data == "setup_complete"

    try:
        # Test the actual functionality
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200
    finally:
        # Async teardown
        teardown_data = await asyncio.sleep(0.1, result="teardown_complete")
        assert teardown_data == "teardown_complete"
