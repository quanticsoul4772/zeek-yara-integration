# Zeek-YARA Integration Platform - Configuration Guide

## Overview

The platform uses a hierarchical configuration system with JSON files for different environments. Configuration can be set through files, environment variables, or command-line arguments.

## Configuration Files

### Primary Configuration Locations

```
config/
├── default_config.json      # Default settings
├── production_config.json   # Production environment
├── distributed_config.json  # Distributed deployment
├── education_config.json    # Educational environment
├── pytest.ini              # Test configuration
└── suricata.yaml          # Suricata-specific config
```

## Core Configuration Parameters

### Scanner Settings

```json
{
  "SCANNER": {
    "THREADS": 4,
    "MAX_FILE_SIZE": 104857600,
    "SCAN_TIMEOUT": 60,
    "BATCH_SIZE": 100,
    "RECURSIVE": true,
    "FOLLOW_SYMLINKS": false,
    "CACHE_RULES": true,
    "MEMORY_LIMIT": 536870912
  }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `THREADS` | integer | 4 | Number of scanner worker threads |
| `MAX_FILE_SIZE` | integer | 100MB | Maximum file size to scan (bytes) |
| `SCAN_TIMEOUT` | integer | 60 | Timeout per file scan (seconds) |
| `BATCH_SIZE` | integer | 100 | Files to process per batch |
| `RECURSIVE` | boolean | true | Scan directories recursively |
| `FOLLOW_SYMLINKS` | boolean | false | Follow symbolic links |
| `CACHE_RULES` | boolean | true | Cache compiled YARA rules |
| `MEMORY_LIMIT` | integer | 512MB | Scanner memory limit (bytes) |

### Database Configuration

```json
{
  "DATABASE": {
    "PATH": "/logs/alerts.db",
    "CONNECTION_POOL_SIZE": 10,
    "MAX_CONNECTIONS": 20,
    "TIMEOUT": 30,
    "WAL_MODE": true,
    "AUTO_VACUUM": true,
    "CACHE_SIZE": 10000
  }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `PATH` | string | /logs/alerts.db | Database file path |
| `CONNECTION_POOL_SIZE` | integer | 10 | Connection pool size |
| `MAX_CONNECTIONS` | integer | 20 | Maximum concurrent connections |
| `TIMEOUT` | integer | 30 | Connection timeout (seconds) |
| `WAL_MODE` | boolean | true | Enable Write-Ahead Logging |
| `AUTO_VACUUM` | boolean | true | Automatic database vacuuming |
| `CACHE_SIZE` | integer | 10000 | SQLite cache size (pages) |

### API Server Configuration

```json
{
  "API": {
    "HOST": "0.0.0.0",
    "PORT": 8000,
    "WORKERS": 4,
    "RELOAD": false,
    "DEBUG": false,
    "RATE_LIMIT": "100/minute",
    "CORS_ORIGINS": ["*"],
    "MAX_REQUEST_SIZE": 10485760
  }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `HOST` | string | 0.0.0.0 | API server host |
| `PORT` | integer | 8000 | API server port |
| `WORKERS` | integer | 4 | Number of worker processes |
| `RELOAD` | boolean | false | Auto-reload on code changes |
| `DEBUG` | boolean | false | Enable debug mode |
| `RATE_LIMIT` | string | 100/minute | Rate limiting configuration |
| `CORS_ORIGINS` | array | ["*"] | Allowed CORS origins |
| `MAX_REQUEST_SIZE` | integer | 10MB | Maximum request body size |

### Suricata Integration

```json
{
  "SURICATA": {
    "INTERFACE": "eth0",
    "CONFIG_FILE": "/config/suricata.yaml",
    "RULES_DIR": "/rules/suricata",
    "LOG_DIR": "/logs/suricata",
    "EVE_JSON": true,
    "STATS_ENABLED": true,
    "STATS_INTERVAL": 60,
    "AF_PACKET_BUFFER_SIZE": 33554432
  }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `INTERFACE` | string | eth0 | Network interface to monitor |
| `CONFIG_FILE` | string | /config/suricata.yaml | Suricata config path |
| `RULES_DIR` | string | /rules/suricata | Rules directory |
| `LOG_DIR` | string | /logs/suricata | Log output directory |
| `EVE_JSON` | boolean | true | Enable EVE JSON output |
| `STATS_ENABLED` | boolean | true | Enable statistics |
| `STATS_INTERVAL` | integer | 60 | Stats update interval (seconds) |
| `AF_PACKET_BUFFER_SIZE` | integer | 32MB | Packet buffer size |

### Alert Correlation

```json
{
  "CORRELATION": {
    "ENABLED": true,
    "TIME_WINDOW": 300,
    "TIME_PROXIMITY_WINDOW": 60,
    "MIN_CONFIDENCE": 70,
    "MAX_DISTANCE": 5,
    "CORRELATION_TYPES": [
      "ip_based",
      "hash_based",
      "time_proximity",
      "behavioral"
    ]
  }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ENABLED` | boolean | true | Enable alert correlation |
| `TIME_WINDOW` | integer | 300 | Correlation window (seconds) |
| `TIME_PROXIMITY_WINDOW` | integer | 60 | Time proximity threshold |
| `MIN_CONFIDENCE` | integer | 70 | Minimum confidence score |
| `MAX_DISTANCE` | integer | 5 | Maximum correlation distance |
| `CORRELATION_TYPES` | array | [...] | Enabled correlation methods |

### Logging Configuration

```json
{
  "LOGGING": {
    "LEVEL": "INFO",
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "FILE": "/logs/platform.log",
    "MAX_SIZE": 10485760,
    "BACKUP_COUNT": 5,
    "CONSOLE": true,
    "SYSLOG": false
  }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `LEVEL` | string | INFO | Log level (DEBUG/INFO/WARNING/ERROR) |
| `FORMAT` | string | ... | Log message format |
| `FILE` | string | /logs/platform.log | Log file path |
| `MAX_SIZE` | integer | 10MB | Maximum log file size |
| `BACKUP_COUNT` | integer | 5 | Number of backup files |
| `CONSOLE` | boolean | true | Log to console |
| `SYSLOG` | boolean | false | Send to syslog |

## Environment-Specific Configurations

### Production Configuration

```json
{
  "ENVIRONMENT": "production",
  "SCANNER": {
    "THREADS": 8,
    "MAX_FILE_SIZE": 209715200
  },
  "API": {
    "DEBUG": false,
    "RATE_LIMIT": "1000/minute"
  },
  "LOGGING": {
    "LEVEL": "WARNING",
    "SYSLOG": true
  }
}
```

### Educational Configuration

```json
{
  "ENVIRONMENT": "education",
  "SCANNER": {
    "THREADS": 2,
    "MAX_FILE_SIZE": 10485760
  },
  "API": {
    "DEBUG": true,
    "RATE_LIMIT": "10/minute"
  },
  "TUTORIALS": {
    "ENABLED": true,
    "PORT": 8001
  }
}
```

### Distributed Configuration

```json
{
  "ENVIRONMENT": "distributed",
  "DISTRIBUTED": {
    "ENABLED": true,
    "MASTER_NODE": "192.168.1.100",
    "WORKER_NODES": [
      "192.168.1.101",
      "192.168.1.102"
    ],
    "QUEUE_TYPE": "redis",
    "QUEUE_HOST": "192.168.1.100",
    "QUEUE_PORT": 6379
  }
}
```

## Platform-Specific Network Interfaces

### Linux
```json
{
  "SURICATA": {
    "INTERFACE": "eth0"  // or "enp0s3", "wlan0"
  }
}
```

### macOS
```json
{
  "SURICATA": {
    "INTERFACE": "en0"  // Wi-Fi, or "en1" for Ethernet
  }
}
```

### Windows
```json
{
  "SURICATA": {
    "INTERFACE": "Ethernet"  // or "Wi-Fi"
  }
}
```

## Environment Variables

Override configuration with environment variables:

```bash
# Scanner configuration
export ZYI_SCANNER_THREADS=8
export ZYI_SCANNER_MAX_FILE_SIZE=209715200

# API configuration
export ZYI_API_HOST=0.0.0.0
export ZYI_API_PORT=8080

# Database configuration
export ZYI_DATABASE_PATH=/data/alerts.db

# Suricata configuration
export ZYI_SURICATA_INTERFACE=eth1
```

## Command-Line Configuration

Override settings via CLI:

```bash
# Scanner with custom settings
./TOOLS/cli/zyi scan --threads 8 --max-size 200MB

# API server with custom port
./TOOLS/cli/zyi api start --port 8080 --workers 6

# Suricata with specific interface
./TOOLS/cli/zyi suricata start --interface en1
```

## Configuration Precedence

Configuration sources are applied in order (highest to lowest priority):

1. Command-line arguments
2. Environment variables
3. Environment-specific config files
4. Default configuration

## YARA Rules Configuration

### Rules Directory Structure
```
rules/
├── active/               # Active rules for scanning
│   ├── malware/         # Malware detection rules
│   ├── ransomware/      # Ransomware-specific rules
│   ├── document_malware/# Document-based threats
│   ├── network_behavior/# Network indicators
│   └── evasion_techniques/
├── templates/           # Rule templates
└── validation/          # Test rules
```

### Rules Loading Configuration
```json
{
  "YARA": {
    "RULES_DIR": "/rules/active",
    "RECURSIVE_LOAD": true,
    "VALIDATE_ON_LOAD": true,
    "INCLUDE_PATTERNS": ["*.yar", "*.yara"],
    "EXCLUDE_PATTERNS": ["test_*", "*.disabled"]
  }
}
```

## Performance Tuning

### High-Performance Configuration
```json
{
  "PERFORMANCE": {
    "SCANNER": {
      "THREADS": 16,
      "BATCH_SIZE": 500,
      "CACHE_RULES": true,
      "MEMORY_LIMIT": 2147483648
    },
    "DATABASE": {
      "CONNECTION_POOL_SIZE": 20,
      "CACHE_SIZE": 50000,
      "SYNCHRONOUS": "NORMAL"
    },
    "API": {
      "WORKERS": 8,
      "WORKER_CLASS": "uvicorn.workers.UvicornWorker"
    }
  }
}
```

### Low-Resource Configuration
```json
{
  "PERFORMANCE": {
    "SCANNER": {
      "THREADS": 2,
      "BATCH_SIZE": 50,
      "MEMORY_LIMIT": 268435456
    },
    "DATABASE": {
      "CONNECTION_POOL_SIZE": 5,
      "CACHE_SIZE": 2000
    },
    "API": {
      "WORKERS": 2
    }
  }
}
```

## Security Configuration

### Hardened Security Settings
```json
{
  "SECURITY": {
    "API": {
      "ENABLE_AUTH": true,
      "AUTH_TYPE": "bearer",
      "TOKEN_EXPIRY": 3600,
      "ENABLE_HTTPS": true,
      "SSL_CERT": "/certs/server.crt",
      "SSL_KEY": "/certs/server.key"
    },
    "SCANNER": {
      "SANDBOX_ENABLED": true,
      "CHROOT_DIR": "/sandbox",
      "DROP_PRIVILEGES": true,
      "RUN_AS_USER": "scanner"
    },
    "AUDIT": {
      "ENABLED": true,
      "LOG_ALL_REQUESTS": true,
      "LOG_FILE_ACCESS": true
    }
  }
}
```

## Monitoring Configuration

### Metrics and Monitoring
```json
{
  "MONITORING": {
    "PROMETHEUS": {
      "ENABLED": true,
      "PORT": 9090,
      "METRICS_PATH": "/metrics"
    },
    "HEALTH_CHECK": {
      "ENABLED": true,
      "INTERVAL": 30,
      "TIMEOUT": 10
    },
    "ALERTING": {
      "ENABLED": true,
      "WEBHOOK_URL": "https://hooks.slack.com/..."
    }
  }
}
```

## Validation and Testing

### Validate Configuration
```bash
# Check configuration validity
./TOOLS/cli/zyi config validate

# Test configuration
./TOOLS/cli/zyi config test --file config/production_config.json

# Show effective configuration
./TOOLS/cli/zyi config show --merged
```

### Configuration Schema
```python
from pydantic import BaseModel, Field

class ScannerConfig(BaseModel):
    threads: int = Field(ge=1, le=32)
    max_file_size: int = Field(ge=1024, le=1073741824)
    scan_timeout: int = Field(ge=1, le=3600)
    
class APIConfig(BaseModel):
    host: str = Field(regex=r'^[\d\.]+$|^localhost$')
    port: int = Field(ge=1024, le=65535)
    workers: int = Field(ge=1, le=16)
```

## Troubleshooting Configuration

### Common Issues

1. **Port Already in Use**
   ```json
   {
     "API": {"PORT": 8001}  // Change to available port
   }
   ```

2. **Insufficient Threads**
   ```json
   {
     "SCANNER": {"THREADS": 8}  // Increase for better performance
   }
   ```

3. **Database Lock Issues**
   ```json
   {
     "DATABASE": {
       "WAL_MODE": true,  // Enable for concurrent access
       "TIMEOUT": 60      // Increase timeout
     }
   }
   ```

### Configuration Debugging
```bash
# Enable debug logging
export ZYI_LOGGING_LEVEL=DEBUG

# Show configuration load order
./TOOLS/cli/zyi config debug --trace

# Test specific component
./TOOLS/cli/zyi config test --component scanner
```

## Best Practices

1. **Use environment-specific files** for different deployments
2. **Keep secrets in environment variables**, not config files
3. **Version control configuration** (except secrets)
4. **Document custom configurations** in team wiki
5. **Test configuration changes** in staging first
6. **Monitor configuration drift** between environments
7. **Use configuration validation** before deployment
8. **Implement configuration backups** for recovery