# Configuration Reference

This document provides comprehensive reference information for all configuration options in the Zeek-YARA Integration platform.

## Configuration Files Overview

The platform uses a hierarchical configuration system with multiple sources:

| Configuration File | Purpose | Priority |
|--------------------|---------|----------|
| `config/default_config.json` | Main platform settings | High |
| `CONFIGURATION/defaults/config.py` | New modular config system | Medium |
| `config/suricata.yaml` | Suricata-specific settings | High |
| Environment Variables | Runtime overrides | Highest |

## Main Configuration (`config/default_config.json`)

### File Paths and Directories

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `EXTRACT_DIR` | string | `"extracted_files"` | Directory for Zeek-extracted files |
| `RULES_DIR` | string | `"rules/active"` | YARA rules directory |
| `LOG_FILE` | string | `"logs/yara_scan.log"` | YARA scanner log file |
| `DB_FILE` | string | `"logs/alerts.db"` | SQLite database file |
| `SURICATA_LOG_DIR` | string | `"logs/suricata"` | Suricata log directory |
| `TEMP_DIR` | string | `"/tmp"` | Temporary file directory |
| `BACKUP_DIR` | string | `"DATA/backups"` | Backup storage directory |

### Scanner Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `THREADS` | integer | `2` | Number of scanner worker threads |
| `MAX_FILE_SIZE` | integer | `104857600` | Maximum file size to scan (100MB) |
| `FILE_TIMEOUT` | integer | `30` | File scan timeout in seconds |
| `SCAN_INTERVAL` | integer | `1` | File system polling interval |
| `QUEUE_SIZE` | integer | `1000` | Maximum files in processing queue |
| `BATCH_SIZE` | integer | `100` | Database batch insert size |

### Database Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `DB_POOL_SIZE` | integer | `5` | Connection pool size |
| `DB_TIMEOUT` | integer | `30` | Database operation timeout |
| `DB_BACKUP_INTERVAL` | integer | `3600` | Backup interval in seconds |
| `DB_RETENTION_DAYS` | integer | `30` | Alert retention period |
| `DB_VACUUM_INTERVAL` | integer | `86400` | Database optimization interval |

### Logging Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `LOG_LEVEL` | string | `"INFO"` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | string | `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"` | Log message format |
| `LOG_MAX_SIZE` | integer | `10485760` | Maximum log file size (10MB) |
| `LOG_BACKUP_COUNT` | integer | `5` | Number of log file backups |
| `LOG_ROTATION` | string | `"daily"` | Log rotation frequency |

### Network Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `API_HOST` | string | `"0.0.0.0"` | API server bind address |
| `API_PORT` | integer | `8000` | API server port |
| `API_WORKERS` | integer | `1` | Number of API worker processes |
| `API_TIMEOUT` | integer | `60` | API request timeout |
| `CORS_ORIGINS` | array | `["*"]` | Allowed CORS origins |
| `API_KEY_REQUIRED` | boolean | `false` | Require API key authentication |

### Suricata Integration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SURICATA_ENABLED` | boolean | `true` | Enable Suricata integration |
| `SURICATA_INTERFACE` | string | `"eth0"` | Network interface for monitoring |
| `SURICATA_CONFIG` | string | `"config/suricata.yaml"` | Suricata configuration file |
| `SURICATA_BINARY` | string | `"suricata"` | Suricata executable path |
| `SURICATA_RULE_DIR` | string | `"rules/suricata"` | Suricata rules directory |
| `SURICATA_UPDATE_INTERVAL` | integer | `3600` | Rule update interval in seconds |

### Alert Correlation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `CORRELATION_ENABLED` | boolean | `true` | Enable alert correlation |
| `CORRELATION_WINDOW` | integer | `300` | Time window for correlation (seconds) |
| `TIME_PROXIMITY_WINDOW` | integer | `60` | Time proximity threshold |
| `MIN_ALERT_CONFIDENCE` | integer | `70` | Minimum confidence for correlation |
| `IP_CORRELATION_ENABLED` | boolean | `true` | Enable IP-based correlation |
| `HASH_CORRELATION_ENABLED` | boolean | `true` | Enable file hash correlation |

### Educational Platform

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `EDUCATION_MODE` | boolean | `true` | Enable educational features |
| `TUTORIAL_PORT` | integer | `8001` | Tutorial server port |
| `DEMO_MODE` | boolean | `false` | Enable demo mode restrictions |
| `SAFE_MODE` | boolean | `true` | Enable safe mode (limited functionality) |
| `SAMPLE_DATA_ENABLED` | boolean | `true` | Include sample data and demos |

## Environment Variable Overrides

All configuration parameters can be overridden using environment variables with the prefix `ZYI_`:

| Environment Variable | Configuration Parameter | Example |
|---------------------|------------------------|---------|
| `ZYI_THREADS` | `THREADS` | `export ZYI_THREADS=4` |
| `ZYI_API_PORT` | `API_PORT` | `export ZYI_API_PORT=9000` |
| `ZYI_LOG_LEVEL` | `LOG_LEVEL` | `export ZYI_LOG_LEVEL=DEBUG` |
| `ZYI_SURICATA_INTERFACE` | `SURICATA_INTERFACE` | `export ZYI_SURICATA_INTERFACE=en0` |
| `ZYI_EDUCATION_MODE` | `EDUCATION_MODE` | `export ZYI_EDUCATION_MODE=false` |

## Platform-Specific Configurations

### Windows Configuration

```json
{
    "EXTRACT_DIR": "extracted_files",
    "LOG_FILE": "logs\\yara_scan.log",
    "DB_FILE": "logs\\alerts.db",
    "SURICATA_INTERFACE": "Ethernet",
    "TEMP_DIR": "C:\\temp",
    "SURICATA_BINARY": "C:\\Program Files\\Suricata\\bin\\suricata.exe",
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}
```

### macOS Configuration

```json
{
    "EXTRACT_DIR": "extracted_files",
    "LOG_FILE": "logs/yara_scan.log", 
    "DB_FILE": "logs/alerts.db",
    "SURICATA_INTERFACE": "en0",
    "TEMP_DIR": "/tmp",
    "SURICATA_BINARY": "/usr/local/bin/suricata",
    "ZEEK_BINARY": "/usr/local/bin/zeek"
}
```

### Linux Configuration

```json
{
    "EXTRACT_DIR": "extracted_files",
    "LOG_FILE": "logs/yara_scan.log",
    "DB_FILE": "logs/alerts.db", 
    "SURICATA_INTERFACE": "eth0",
    "TEMP_DIR": "/tmp",
    "SURICATA_BINARY": "/usr/bin/suricata",
    "ZEEK_BINARY": "/usr/bin/zeek"
}
```

## Docker Configuration

### Environment Variables for Containers

```bash
# Basic container configuration
ZYI_ENV=education|development|production
ZYI_CONFIG=/app/config.json
ZYI_SAFE_MODE=true
ZYI_DEMO_MODE=true

# Network configuration
ZYI_API_HOST=0.0.0.0
ZYI_API_PORT=8000
ZYI_TUTORIAL_PORT=8001

# Database configuration
ZYI_DB_FILE=/app/DATA/alerts.db
ZYI_LOG_FILE=/app/logs/yara_scan.log

# Performance tuning
ZYI_THREADS=2
ZYI_API_WORKERS=1
ZYI_DB_POOL_SIZE=5
```

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  zyi-education:
    environment:
      - ZYI_ENV=education
      - ZYI_SAFE_MODE=true
      - ZYI_THREADS=2
      - ZYI_API_PORT=8000
      - ZYI_LOG_LEVEL=INFO
    volumes:
      - educational_data:/app/DATA
      - ./config/education.json:/app/config.json:ro
```

## Suricata Configuration (`config/suricata.yaml`)

### Basic Settings

```yaml
# Suricata configuration for Zeek-YARA Integration

# Global settings
vars:
  address-groups:
    HOME_NET: "[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12]"
    EXTERNAL_NET: "!$HOME_NET"
  port-groups:
    HTTP_PORTS: "80"
    SHELLCODE_PORTS: "!80"

# Rule files
default-rule-path: rules/suricata
rule-files:
  - local.rules
  - emerging-threats/emerging.rules

# Logging configuration
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: logs/suricata/eve.json
      types:
        - alert
        - http
        - dns
        - tls
        - files
        - smtp

  - fast:
      enabled: yes
      filename: logs/suricata/fast.log
      append: yes

# Performance settings
threading:
  cpu-affinity:
    - management-cpu-set:
        cpu: [ 0 ]
    - receive-cpu-set:
        cpu: [ 0 ]
    - worker-cpu-set:
        cpu: [ 0-1 ]

# Network interface configuration
af-packet:
  - interface: eth0
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
    
pcap:
  - interface: eth0
    buffer-size: 32768
```

### Educational Mode Settings

```yaml
# Educational-specific settings
vars:
  address-groups:
    HOME_NET: "any"
    EXTERNAL_NET: "any"

# Reduced rule set for education
rule-files:
  - educational/basic-detection.rules
  - educational/malware-samples.rules

# Enhanced logging for learning
outputs:
  - eve-log:
      enabled: yes
      filename: logs/suricata/educational.json
      types:
        - alert
        - http
        - files
        - flow
      
# Performance settings for limited resources  
threading:
  management-threads: 1
  receive-threads: 1
  worker-threads: 1
```

## Performance Tuning Guidelines

### CPU-Intensive Workloads

```json
{
    "THREADS": 4,
    "API_WORKERS": 2,
    "DB_POOL_SIZE": 8,
    "BATCH_SIZE": 200,
    "QUEUE_SIZE": 2000
}
```

### Memory-Constrained Environments  

```json
{
    "THREADS": 1,
    "MAX_FILE_SIZE": 10485760,
    "QUEUE_SIZE": 100,
    "DB_POOL_SIZE": 2,
    "LOG_MAX_SIZE": 1048576
}
```

### High-Volume File Processing

```json
{
    "THREADS": 8,
    "BATCH_SIZE": 500,
    "QUEUE_SIZE": 5000,
    "SCAN_INTERVAL": 0.5,
    "FILE_TIMEOUT": 10
}
```

## Configuration Validation

### Required Parameters

The following parameters are required for basic operation:

- `EXTRACT_DIR`: Must exist and be writable
- `RULES_DIR`: Must contain valid YARA rules
- `LOG_FILE`: Directory must exist and be writable
- `DB_FILE`: Directory must exist and be writable

### Parameter Validation Rules

| Parameter | Validation Rule | Error Message |
|-----------|----------------|---------------|
| `THREADS` | 1 ≤ value ≤ 16 | "Thread count must be between 1 and 16" |
| `MAX_FILE_SIZE` | value > 0 | "Maximum file size must be positive" |
| `API_PORT` | 1024 ≤ value ≤ 65535 | "Port must be between 1024 and 65535" |
| `LOG_LEVEL` | value ∈ {DEBUG, INFO, WARNING, ERROR} | "Invalid log level" |
| `CORRELATION_WINDOW` | 1 ≤ value ≤ 3600 | "Correlation window must be 1-3600 seconds" |

### Configuration Testing

Use the platform's built-in configuration validator:

```bash
# Validate current configuration
./TOOLS/cli/zyi config validate

# Test specific configuration file
./TOOLS/cli/zyi config validate --file custom_config.json

# Check configuration compatibility
./TOOLS/cli/zyi config check --platform windows|macos|linux
```

## Configuration Examples

### Educational Deployment

```json
{
    "EDUCATION_MODE": true,
    "DEMO_MODE": true,
    "SAFE_MODE": true,
    "THREADS": 2,
    "MAX_FILE_SIZE": 10485760,
    "LOG_LEVEL": "INFO",
    "API_PORT": 8000,
    "TUTORIAL_PORT": 8001,
    "SURICATA_ENABLED": false,
    "CORRELATION_ENABLED": true,
    "SAMPLE_DATA_ENABLED": true
}
```

### Production Deployment  

```json
{
    "EDUCATION_MODE": false,
    "DEMO_MODE": false,
    "SAFE_MODE": false,
    "THREADS": 8,
    "MAX_FILE_SIZE": 1073741824,
    "LOG_LEVEL": "WARNING",
    "API_PORT": 80,
    "API_KEY_REQUIRED": true,
    "SURICATA_ENABLED": true,
    "CORRELATION_ENABLED": true,
    "DB_RETENTION_DAYS": 90,
    "LOG_ROTATION": "daily"
}
```

### Development Environment

```json
{
    "EDUCATION_MODE": true,
    "DEMO_MODE": false,
    "SAFE_MODE": false,
    "THREADS": 4,
    "LOG_LEVEL": "DEBUG",
    "API_PORT": 8000,
    "SURICATA_ENABLED": true,
    "CORRELATION_ENABLED": true,
    "DB_BACKUP_INTERVAL": 7200,
    "LOG_MAX_SIZE": 52428800
}
```

## Migration and Upgrade Notes

### Version 1.0 to 2.0 Migration

- `SCANNER_THREADS` → `THREADS`
- `API_BIND_ADDRESS` → `API_HOST` 
- `SURICATA_IFACE` → `SURICATA_INTERFACE`
- New required: `CORRELATION_ENABLED`

### Legacy Configuration Support

The platform maintains backward compatibility with older configuration formats:

```json
// Legacy format (still supported)
{
    "scanner_threads": 2,
    "api_bind_address": "0.0.0.0",
    "suricata_iface": "eth0"
}

// Automatically converted to:
{
    "THREADS": 2,
    "API_HOST": "0.0.0.0", 
    "SURICATA_INTERFACE": "eth0"
}
```

Use the migration tool to update configurations:

```bash
./TOOLS/cli/zyi config migrate --from-version 1.0 --to-version 2.0
```