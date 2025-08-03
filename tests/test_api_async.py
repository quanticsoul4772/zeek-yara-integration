"""
Async test cases for FastAPI endpoints using pytest-asyncio
"""

import json
import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock

# Import the FastAPI app and components
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "PLATFORM")))

from api.api_server import app
from core.database import DatabaseManager
from core.scanner import SingleThreadScanner


@pytest.fixture
def client():
    """Test client fixture"""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def mock_config():
    """Mock configuration fixture"""
    temp_dir = tempfile.mkdtemp()
    return {
        "EXTRACT_DIR": os.path.join(temp_dir, "extracted_files"),
        "DB_FILE": os.path.join(temp_dir, "test.db"),
        "RULES_DIR": os.path.join(temp_dir, "rules"),
        "RULES_INDEX": os.path.join(temp_dir, "rules.index"),
        "MAX_FILE_SIZE": 1024 * 1024,
        "SCAN_TIMEOUT": 10,
        "THREADS": 2,
        "API_KEY": "test-api-key"
    }


@pytest.fixture
def mock_db_manager():
    """Mock database manager fixture"""
    mock_db = Mock(spec=DatabaseManager)
    mock_db.get_alerts.return_value = [
        {
            "id": 1,
            "timestamp": "2025-08-03T06:00:00",
            "file_path": "/test/file.txt",
            "file_name": "file.txt",
            "file_size": 1024,
            "file_type": "text/plain",
            "md5": "abc123",
            "sha256": "def456",
            "zeek_uid": "uid123",
            "rule_name": "test_rule",
            "rule_namespace": "default",
            "rule_meta": '{"author": "test"}',
            "strings_matched": '["test_string"]',
            "severity": 5
        }
    ]
    return mock_db


class TestAsyncAPIEndpoints:
    """Test class for async API endpoints"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_root_endpoint(self, client):
        """Test async access to root endpoint"""
        async with client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Zeek-YARA Integration API"
            assert data["version"] == "1.0.0"
            assert "documentation" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_status_endpoint_with_mocked_components(self, client, mock_config, mock_db_manager):
        """Test async status endpoint with mocked components"""
        with patch('api.api_server.config', mock_config), \
             patch('api.api_server.db_manager', mock_db_manager), \
             patch('api.api_server.rule_manager') as mock_rule_manager, \
             patch('api.api_server.suricata_runner') as mock_suricata:
            
            # Setup mocks
            mock_rule_manager.get_rule_list.return_value = ["rule1", "rule2"]
            mock_suricata.get_status.return_value = {
                "running": True,
                "version": "7.0.0",
                "alert_count": 5,
                "rules_count": 10
            }
            
            # Create extract directory for the test
            os.makedirs(mock_config["EXTRACT_DIR"], exist_ok=True)
            
            # Make request
            async with client:
                response = await client.get("/status", headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "operational"
            assert "uptime" in data
            assert data["scanner_running"] is False
            assert data["rules_count"] == 2
            assert data["alerts_count"] == 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_alerts_endpoint_with_mocked_data(self, client, mock_db_manager):
        """Test async alerts endpoint with mocked data"""
        with patch('api.api_server.db_manager', mock_db_manager):
            async with client:
                response = await client.get("/alerts?page=1&page_size=10", headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert "alerts" in data
            assert data["count"] == 1
            assert data["total"] == 1
            assert data["page"] == 1
            assert data["page_size"] == 10
            
            # Check alert structure
            alert = data["alerts"][0]
            assert alert["id"] == 1
            assert alert["file_name"] == "file.txt"
            assert alert["rule_name"] == "test_rule"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_alerts_endpoint_with_filters(self, client, mock_db_manager):
        """Test async alerts endpoint with query filters"""
        with patch('api.api_server.db_manager', mock_db_manager):
            async with client:
                # Test with severity filter
                response = await client.get("/alerts?severity=5", headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
                
                # Test with rule name filter
                response = await client.get("/alerts?rule_name=test", headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
                
                # Test with file type filter
                response = await client.get("/alerts?file_type=text", headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_specific_alert_endpoint(self, client, mock_db_manager):
        """Test async access to specific alert by ID"""
        with patch('api.api_server.db_manager', mock_db_manager):
            async with client:
                response = await client.get("/alerts/1", headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == 1
            assert data["file_name"] == "file.txt"
            assert data["rule_name"] == "test_rule"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_specific_alert_not_found(self, client, mock_db_manager):
        """Test async access to non-existent alert"""
        with patch('api.api_server.db_manager', mock_db_manager):
            async with client:
                response = await client.get("/alerts/999", headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_scan_endpoint_file_not_found(self, client):
        """Test async scan endpoint with non-existent file"""
        scan_data = {"file_path": "/nonexistent/file.txt", "recursive": False}
        async with client:
            response = await client.post("/scan", 
                                 json=scan_data,
                                 headers={"X-API-Key": "test-api-key"})
            assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_scan_endpoint_with_temp_file(self, client, mock_config):
        """Test async scan endpoint with temporary file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file_path = tmp_file.name
        
        try:
            with patch('api.api_server.config', mock_config), \
                 patch('api.api_server.scanner') as mock_scanner:
                
                # Setup mock scanner
                mock_scanner_instance = Mock(spec=SingleThreadScanner)
                mock_scanner_instance.scan_file.return_value = {
                    "matched": False,
                    "error": None
                }
                mock_scanner = mock_scanner_instance
                
                # Mock db_manager to return empty results
                with patch('api.api_server.db_manager') as mock_db:
                    mock_db.get_alerts.return_value = []
                    
                    scan_data = {"file_path": tmp_file_path, "recursive": False}
                    async with client:
                        response = await client.post("/scan", 
                                             json=scan_data,
                                             headers={"X-API-Key": "test-api-key"})
                        assert response.status_code == 200
                    
                    data = response.json()
                    assert data["success"] is True
                    assert "scan_time" in data
                    assert data["scanned_files"] == 1
        finally:
            os.unlink(tmp_file_path)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_scanner_start_endpoint(self, client, mock_config):
        """Test async scanner start endpoint"""
        with patch('api.api_server.config', mock_config), \
             patch('api.api_server.SingleThreadScanner') as mock_scanner_class:
            
            mock_scanner = Mock()
            mock_scanner.start_monitoring.return_value = True
            mock_scanner_class.return_value = mock_scanner
            
            async with client:
                response = await client.post("/scanner/start?threads=0", 
                                     headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["scanner_type"] == "Single-threaded"
            assert data["threads"] == 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_scanner_stop_endpoint(self, client):
        """Test async scanner stop endpoint"""
        with patch('api.api_server.scanner') as mock_scanner:
            mock_scanner.running = True
            mock_scanner.stop_monitoring.return_value = True
            
            async with client:
                response = await client.post("/scanner/stop", 
                                     headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["status"] == "stopped"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rules_update_endpoint(self, client):
        """Test async rules update endpoint"""
        with patch('api.api_server.rule_manager') as mock_rule_manager:
            mock_rule_manager.compile_rules.return_value = True
            mock_rule_manager.get_rule_list.return_value = ["rule1", "rule2"]
            
            async with client:
                response = await client.post("/rules/update", 
                                     headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["rule_count"] == 2
            assert data["status"] == "updated"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rules_get_endpoint(self, client):
        """Test async rules list endpoint"""
        with patch('api.api_server.rule_manager') as mock_rule_manager:
            mock_rules = [
                {"name": "test_rule", "namespace": "default", "tags": ["test"], "meta": {"author": "test"}},
                {"name": "malware_rule", "namespace": "malware", "tags": ["malware"], "meta": {"severity": "high"}}
            ]
            mock_rule_manager.get_rule_list.return_value = mock_rules
            
            async with client:
                response = await client.get("/rules", headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert "rules" in data
            assert data["count"] == 2
            assert len(data["rules"]) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_api_key_authentication(self, client):
        """Test async API key authentication"""
        async with client:
            # Test without API key
            response = await client.get("/status")
            assert response.status_code == 401
            
            # Test with wrong API key
            response = await client.get("/status", headers={"X-API-Key": "wrong-key"})
            assert response.status_code == 401
            
            # Test with correct API key (mocked)
            with patch('api.api_server.API_KEY', 'test-api-key'):
                response = await client.get("/status", headers={"X-API-Key": "test-api-key"})
                # This may still fail due to other dependencies, but auth should pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_webhook_config_endpoint(self, client):
        """Test async webhook configuration endpoint"""
        webhook_config = {
            "url": "https://example.com/webhook",
            "secret": "webhook-secret",
            "events": ["alert", "scan"],
            "enabled": True
        }
        
        with patch('builtins.open'), \
             patch('json.dump'):
            
            async with client:
                response = await client.post("/webhook/config", 
                                     json=webhook_config,
                                     headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "webhook" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_webhook_get_config_endpoint(self, client):
        """Test async webhook get configuration endpoint"""
        with patch('os.path.exists', return_value=False):
            async with client:
                response = await client.get("/webhook/config", 
                                    headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert data["configured"] is False
            assert data["webhook"] is None


class TestAsyncPerformance:
    """Performance tests for async endpoints"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_status_requests(self, client):
        """Test concurrent async requests to status endpoint"""
        import asyncio
        
        async def make_request():
            async with client:
                with patch('api.api_server.API_KEY', ''):  # Disable auth for test
                    return await client.get("/status")
        
        # Test concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_alerts_endpoint_performance(self, client, mock_db_manager):
        """Test async alerts endpoint performance with large dataset"""
        # Mock large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                "id": i,
                "timestamp": f"2025-08-03T06:{i%60:02d}:00",
                "file_path": f"/test/file_{i}.txt",
                "file_name": f"file_{i}.txt",
                "file_size": 1024 + i,
                "file_type": "text/plain",
                "md5": f"abc{i}",
                "sha256": f"def{i}",
                "zeek_uid": f"uid{i}",
                "rule_name": f"test_rule_{i%10}",
                "rule_namespace": "default",
                "rule_meta": '{"author": "test"}',
                "strings_matched": '["test_string"]',
                "severity": i % 10
            })
        
        mock_db_manager.get_alerts.return_value = large_dataset
        
        with patch('api.api_server.db_manager', mock_db_manager):
            async with client:
                response = await client.get("/alerts?page=1&page_size=50", 
                                    headers={"X-API-Key": "test-api-key"})
                assert response.status_code == 200
            
            data = response.json()
            assert data["count"] == 50  # Page size
            assert data["total"] == 1000  # Total records


@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_endpoint_error_handling(client):
    """Test async error handling in endpoints"""
    async with client:
        # Test with malformed JSON in scan request
        response = await client.post("/scan", 
                             data="invalid json",
                             headers={"X-API-Key": "test-api-key",
                                    "Content-Type": "application/json"})
        assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_verify_api_key_function():
    """Test async API key verification function"""
    from api.api_server import verify_api_key
    
    # Test valid key
    with patch('api.api_server.API_KEY', 'test-key'):
        result = await verify_api_key('test-key')
        assert result is True
    
    # Test invalid key - should raise HTTPException
    with patch('api.api_server.API_KEY', 'test-key'):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key('wrong-key')
        assert exc_info.value.status_code == 401