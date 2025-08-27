# Zeek-YARA Integration Platform - API Reference

## Overview

The Zeek-YARA Integration Platform provides a RESTful API for controlling and monitoring network security operations. The API runs on port 8000 by default and integrates YARA file scanning, Suricata IDS/IPS, and alert correlation.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication for local development. Production deployments should implement appropriate authentication mechanisms.

## Rate Limiting

API endpoints are protected by rate limiting (implemented via slowapi):
- Default: 100 requests per minute per IP
- Configurable in `config/default_config.json`

## Endpoints

### YARA Scanner

#### GET /alerts
Retrieve YARA scan alerts from the database.

**Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "timestamp": "2025-08-27T10:00:00",
      "file_path": "/extracted_files/file1.exe",
      "rule_name": "Malware_Generic",
      "tags": ["malware", "executable"],
      "meta": {"author": "security-team"},
      "strings_matched": ["$suspicious_string"]
    }
  ],
  "total": 1
}
```

#### POST /scanner/start
Start the YARA scanner service.

**Request Body:**
```json
{
  "directory": "/extracted_files",
  "threads": 4,
  "recursive": true
}
```

**Response:**
```json
{
  "status": "started",
  "pid": 12345,
  "monitoring_directory": "/extracted_files"
}
```

#### POST /scanner/stop
Stop the YARA scanner service.

**Response:**
```json
{
  "status": "stopped",
  "alerts_processed": 150
}
```

#### POST /scan
Scan a specific file or directory.

**Request Body:**
```json
{
  "target": "/path/to/file_or_directory",
  "rules_dir": "/rules/active",
  "recursive": true,
  "max_file_size": 104857600
}
```

**Response:**
```json
{
  "scanned_files": 10,
  "matches": 2,
  "errors": 0,
  "results": [
    {
      "file": "/path/to/malicious.exe",
      "rules_matched": ["Ransomware_Behavior", "Encryption_Routine"]
    }
  ]
}
```

### Suricata Integration

#### GET /suricata/status
Get current Suricata service status.

**Response:**
```json
{
  "running": true,
  "pid": 54321,
  "interface": "eth0",
  "uptime_seconds": 3600,
  "packets_processed": 1000000,
  "alerts_generated": 250
}
```

#### GET /suricata/alerts
Retrieve Suricata alerts with filtering options.

**Query Parameters:**
- `limit` (integer): Maximum alerts to return (default: 100)
- `offset` (integer): Pagination offset (default: 0)
- `severity` (integer): Filter by severity (1-3)
- `category` (string): Filter by alert category
- `start_time` (ISO 8601): Start time for date range
- `end_time` (ISO 8601): End time for date range

**Response:**
```json
{
  "alerts": [
    {
      "timestamp": "2025-08-27T10:30:00",
      "event_type": "alert",
      "src_ip": "192.168.1.100",
      "dest_ip": "10.0.0.1",
      "proto": "TCP",
      "alert": {
        "action": "allowed",
        "gid": 1,
        "signature_id": 2001219,
        "signature": "ET SCAN Suspicious User-Agent",
        "category": "Web Application Attack",
        "severity": 2
      }
    }
  ],
  "total": 250,
  "page": 1
}
```

#### POST /suricata/start
Start Suricata on specified interface.

**Request Body:**
```json
{
  "interface": "eth0",
  "config_file": "/config/suricata.yaml",
  "log_dir": "/logs/suricata"
}
```

**Response:**
```json
{
  "status": "started",
  "pid": 54321,
  "monitoring_interface": "eth0"
}
```

#### POST /suricata/stop
Stop Suricata service.

**Response:**
```json
{
  "status": "stopped",
  "runtime_seconds": 3600,
  "total_alerts": 250
}
```

#### POST /suricata/pcap
Analyze PCAP file with Suricata.

**Request Body:**
```json
{
  "pcap_file": "/path/to/capture.pcap",
  "rules_file": "/rules/suricata/local.rules",
  "output_dir": "/analysis/results"
}
```

**Response:**
```json
{
  "analysis_complete": true,
  "alerts_generated": 15,
  "eve_json_path": "/analysis/results/eve.json"
}
```

#### POST /suricata/rules/update
Update Suricata rules from configured sources.

**Response:**
```json
{
  "status": "updated",
  "rules_downloaded": 50000,
  "rules_enabled": 45000,
  "sources": ["emerging-threats", "snort-community"]
}
```

### Alert Correlation

#### POST /suricata/correlate
Correlate alerts from multiple sources.

**Request Body:**
```json
{
  "time_window": 300,
  "correlation_types": ["ip_based", "hash_based", "time_proximity"],
  "min_confidence": 70
}
```

**Response:**
```json
{
  "correlated_incidents": [
    {
      "incident_id": "INC-2025-001",
      "confidence": 85,
      "related_alerts": [
        {
          "source": "yara",
          "alert_id": 123,
          "rule": "Ransomware_Behavior"
        },
        {
          "source": "suricata", 
          "alert_id": 456,
          "signature": "ET MALWARE C2 Communication"
        }
      ],
      "common_indicators": {
        "ip_addresses": ["192.168.1.100"],
        "file_hashes": ["abc123..."]
      }
    }
  ],
  "total_correlated": 5
}
```

#### GET /suricata/correlation
Retrieve previously correlated alerts.

**Query Parameters:**
- `incident_id` (string): Specific incident ID
- `min_confidence` (integer): Minimum confidence score
- `limit` (integer): Maximum results

**Response:**
```json
{
  "correlations": [
    {
      "incident_id": "INC-2025-001",
      "created_at": "2025-08-27T11:00:00",
      "confidence": 85,
      "status": "active",
      "severity": "high"
    }
  ]
}
```

### System Management

#### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "yara_scanner": "running",
    "suricata": "running",
    "database": "connected",
    "api": "operational"
  },
  "uptime_seconds": 86400
}
```

#### GET /metrics
System metrics and statistics.

**Response:**
```json
{
  "system": {
    "cpu_usage": 25.5,
    "memory_usage": 45.2,
    "disk_usage": 60.0
  },
  "scanner": {
    "files_scanned": 10000,
    "threats_detected": 50,
    "scan_rate": 100
  },
  "suricata": {
    "packets_processed": 1000000,
    "alerts_generated": 250,
    "drop_rate": 0.01
  }
}
```

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format.

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "Additional context"
    }
  }
}
```

### Common Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## WebSocket Support

Real-time alert streaming is available via WebSocket connection.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts');

ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log('New alert:', alert);
};
```

### Message Format

```json
{
  "type": "alert",
  "source": "yara|suricata",
  "timestamp": "2025-08-27T12:00:00",
  "data": {
    // Alert-specific data
  }
}
```

## Examples

### Python Client Example

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Start YARA scanner
response = requests.post(f"{BASE_URL}/scanner/start", 
    json={"directory": "/extracted_files", "threads": 4})
print("Scanner started:", response.json())

# Get alerts
response = requests.get(f"{BASE_URL}/alerts")
alerts = response.json()
print(f"Found {alerts['total']} alerts")

# Scan specific file
response = requests.post(f"{BASE_URL}/scan",
    json={"target": "/suspicious/file.exe"})
results = response.json()
print(f"Scan results: {results}")
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Start YARA scanner
curl -X POST http://localhost:8000/scanner/start \
  -H "Content-Type: application/json" \
  -d '{"directory": "/extracted_files"}'

# Get Suricata alerts
curl "http://localhost:8000/suricata/alerts?limit=10&severity=2"

# Correlate alerts
curl -X POST http://localhost:8000/suricata/correlate \
  -H "Content-Type: application/json" \
  -d '{"time_window": 300}'
```

## Versioning

The API follows semantic versioning. The current version is v1.0.0.

Future versions will maintain backward compatibility where possible, with deprecation notices for breaking changes.

## Support

For issues, feature requests, or questions:
- GitHub Issues: https://github.com/quanticsoul4772/zeek-yara-integration/issues
- Documentation: https://github.com/quanticsoul4772/zeek-yara-integration/docs