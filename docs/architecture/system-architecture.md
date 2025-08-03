# System Architecture and Data Flow

This document provides a comprehensive overview of the Zeek-YARA Integration platform architecture, data flow, and component interactions.

## Architecture Overview

The platform integrates three primary security tools into a unified monitoring system:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ZEEK-YARA INTEGRATION PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │
│  │    ZEEK     │    │    YARA     │    │  SURICATA   │    │  CORRELATION    │   │
│  │  Network    │    │   File      │    │  Network    │    │    ENGINE       │   │
│  │  Analysis   │    │  Scanner    │    │   IDS/IPS   │    │                 │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────────┘   │
│          │                   │                   │                   │           │
│          └───────────────────┼───────────────────┼───────────────────┘           │
│                              │                   │                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          UNIFIED API SERVER                                │ │
│  │                     (FastAPI + REST Endpoints)                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         WEB INTERFACE & CLI                                │ │
│  │              (Tutorial System + zyi CLI + Dashboard)                       │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Core Components

#### 1. Zeek Network Analysis Engine
- **Purpose**: Network traffic monitoring and file extraction
- **Location**: `zeek/` directory, integrated via system binary
- **Key Functions**:
  - Deep packet inspection
  - Protocol analysis  
  - File extraction from network streams
  - Connection logging and metadata collection

#### 2. YARA File Scanner
- **Purpose**: Malware detection and behavioral analysis
- **Location**: `PLATFORM/core/scanner.py`
- **Key Functions**:
  - Multi-threaded file scanning
  - Rule-based pattern matching
  - File metadata extraction
  - Alert generation and database storage

#### 3. Suricata Network IDS/IPS
- **Purpose**: Network-based intrusion detection
- **Location**: `suricata/` directory, system integration
- **Key Functions**:
  - Real-time network monitoring
  - Signature-based detection
  - Protocol anomaly detection
  - Network event logging

#### 4. Correlation Engine
- **Purpose**: Cross-tool alert correlation and analysis
- **Location**: `suricata/alert_correlation/`
- **Key Functions**:
  - Time-proximity correlation
  - IP address correlation
  - File hash correlation
  - Threat intelligence integration

### Data Processing Architecture

```
Network Traffic                    Files on Disk
      │                                 │
      ▼                                 ▼
┌─────────────┐                ┌─────────────┐
│    ZEEK     │                │    YARA     │
│ Traffic     │◄──────────────►│ File        │
│ Analysis    │   Extracted    │ Scanner     │
│             │   Files        │             │
└─────────────┘                └─────────────┘
      │                                 │
      │ Network                         │ File
      │ Events                          │ Alerts
      ▼                                 ▼
┌─────────────────────────────────────────────┐
│           CORRELATION ENGINE                │
│  ┌─────────────┐ ┌─────────────────────────┐│
│  │ Time-based  │ │    IP/Hash Matching     ││
│  │ Correlation │ │    Alert Enhancement    ││
│  └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────┘
                      │
                      ▼
            ┌─────────────────┐
            │   SQLITE DB     │
            │ Alert Storage   │
            └─────────────────┘
                      │
                      ▼
            ┌─────────────────┐
            │   REST API      │
            │ Query Interface │
            └─────────────────┘
```

## Data Flow Diagram

### 1. Live Network Monitoring Flow

```
Internet/Network Traffic
         │
         ▼
┌────────────────┐     ┌──────────────────┐
│ Network        │────►│ Zeek File        │
│ Interface      │     │ Extraction       │
│ (eth0/en0)     │     │ Module           │
└────────────────┘     └──────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │ extracted_files/│
         │              │ Directory       │
         │              │ Monitoring      │
         │              └─────────────────┘
         │                       │
         ▼                       ▼
┌────────────────┐     ┌─────────────────┐
│ Suricata       │     │ YARA Scanner    │
│ Network IDS    │     │ (Multi-thread)  │
│                │     │                 │
└────────────────┘     └─────────────────┘
         │                       │
         │ Network Events         │ File Alerts
         │                       │
         └─────────┬─────────────┘
                   ▼
         ┌─────────────────┐
         │ Alert           │
         │ Correlation     │
         │ Engine          │
         └─────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ SQLite Database │
         │ Alert Storage   │
         └─────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ REST API        │
         │ Interface       │
         └─────────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │ Client Interfaces            │
    │ • Web Dashboard              │
    │ • CLI Tool (zyi)             │
    │ • Tutorial System            │
    │ • External Integrations      │
    └──────────────────────────────┘
```

### 2. PCAP Analysis Flow

```
PCAP File
    │
    ▼
┌─────────────────┐
│ Zeek Offline    │
│ Analysis        │
│ (zeek -r)       │
└─────────────────┘
    │
    ▼
┌─────────────────┐     ┌─────────────────┐
│ File Extraction │────►│ YARA Scanning   │
│ to temp dir     │     │ Batch Process   │
└─────────────────┘     └─────────────────┘
    │                           │
    ▼                           ▼
┌─────────────────┐     ┌─────────────────┐
│ Suricata PCAP   │     │ File Analysis   │
│ Analysis        │     │ Results         │
│ (suricata -r)   │     │                 │
└─────────────────┘     └─────────────────┘
    │                           │
    └─────────┬─────────────────┘
              ▼
    ┌─────────────────┐
    │ Results         │
    │ Aggregation     │
    │ & Correlation   │
    └─────────────────┘
```

## Database Schema

### YARA Alerts Table
```sql
CREATE TABLE yara_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    md5_hash TEXT,
    sha256_hash TEXT,
    rule_name TEXT NOT NULL,
    rule_namespace TEXT,
    rule_metadata TEXT,
    matched_strings TEXT,
    zeek_uid TEXT,  -- For correlation with Zeek logs
    threat_level TEXT DEFAULT 'medium',
    processed BOOLEAN DEFAULT 0,
    
    INDEX idx_timestamp (timestamp),
    INDEX idx_rule_name (rule_name),
    INDEX idx_file_hash (md5_hash, sha256_hash),
    INDEX idx_zeek_uid (zeek_uid)
);
```

### Suricata Alerts Integration
```sql
-- Correlation view combining YARA and Suricata alerts
CREATE VIEW correlated_alerts AS
SELECT 
    y.id as yara_id,
    y.timestamp as detection_time,
    y.file_name,
    y.rule_name as yara_rule,
    y.threat_level,
    s.alert_signature as suricata_rule,
    s.src_ip,
    s.dest_ip,
    s.proto,
    CASE 
        WHEN s.timestamp IS NOT NULL THEN 'CORRELATED'
        ELSE 'FILE_ONLY'
    END as correlation_status
FROM yara_alerts y
LEFT JOIN suricata_alerts s ON (
    y.zeek_uid = s.flow_id OR
    (ABS(strftime('%s', y.timestamp) - strftime('%s', s.timestamp)) < 300)
);
```

## API Architecture

### REST API Endpoints

#### Core Endpoints
- `GET /status` - System health and component status
- `GET /info` - Platform information and version details

#### YARA Scanner API
- `GET /alerts` - Paginated alert retrieval with filtering
- `POST /scanner/start` - Start file monitoring
- `POST /scanner/stop` - Stop file monitoring  
- `POST /scan` - On-demand file/directory scanning

#### Suricata Integration API
- `GET /suricata/status` - Suricata component status
- `GET /suricata/alerts` - Network alerts with filtering
- `POST /suricata/start` - Start network monitoring
- `POST /suricata/stop` - Stop network monitoring
- `POST /suricata/pcap` - PCAP file analysis

#### Correlation API
- `POST /suricata/correlate` - Trigger alert correlation
- `GET /suricata/correlation` - Retrieve correlated alerts

### API Response Format
```json
{
    "status": "success|error",
    "data": {
        "alerts": [...],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 150,
            "total_pages": 8
        }
    },
    "metadata": {
        "timestamp": "2025-01-15T10:30:00Z",
        "processing_time": 0.045,
        "version": "1.0.0"
    }
}
```

## Threading and Concurrency Model

### Scanner Threading Architecture
```
Main Thread
    │
    ├── File System Watcher (watchdog)
    │   └── Event Queue
    │
    ├── Worker Thread Pool
    │   ├── Worker 1 ──┐
    │   ├── Worker 2   │── File Processing
    │   ├── Worker 3   │   (YARA Analysis)
    │   └── Worker N ──┘
    │
    └── Database Thread Pool
        ├── Connection 1 ──┐
        ├── Connection 2   │── Alert Storage
        └── Connection N ──┘
```

### Configuration Parameters
- `THREADS`: Number of scanner worker threads (default: 2)
- `DB_POOL_SIZE`: Database connection pool size (default: 5)
- `MAX_QUEUE_SIZE`: File processing queue limit (default: 1000)
- `BATCH_SIZE`: Database batch insert size (default: 100)

## File System Layout

### Core Directory Structure
```
zeek-yara-integration/
├── extracted_files/          # Zeek extracted files (monitored)
│   ├── extract-*-HTTP-*      # HTTP extracted files
│   ├── extract-*-SMTP-*      # Email attachments
│   └── extract-*-FTP-*       # FTP transfers
│
├── logs/                     # All system logs
│   ├── yara_scan.log        # YARA scanner operations
│   ├── api.log              # API server logs
│   ├── alerts.db            # SQLite alert database
│   └── suricata/            # Suricata-specific logs
│       ├── eve.json         # JSON event log
│       ├── fast.log         # Fast alert format
│       └── suricata.log     # Suricata engine log
│
├── rules/                    # Detection rules
│   ├── active/              # Active YARA rules
│   │   ├── malware/         # Malware detection
│   │   ├── ransomware/      # Ransomware patterns
│   │   └── document_malware/ # Office/PDF malware
│   └── suricata/            # Suricata rules
│       ├── local.rules      # Custom rules
│       └── emerging-threats/ # Community rules
│
└── config/                   # Configuration files
    ├── default_config.json  # Main platform config
    └── suricata.yaml        # Suricata configuration
```

### Data Flow Through File System
1. **Network Traffic** → Zeek → `extracted_files/`
2. **File Detection** → Watchdog → Scanner Queue
3. **YARA Analysis** → Results → `logs/alerts.db`
4. **Log Aggregation** → `logs/` directory
5. **Rule Updates** → `rules/active/` and `rules/suricata/`

## Performance Characteristics

### Processing Throughput
- **File Scanning**: 100-500 files/second (depending on file size and rules)
- **Network Monitoring**: Line-rate processing up to 1Gbps
- **Database Operations**: 1000+ inserts/second with connection pooling
- **API Response Time**: <100ms for typical queries

### Resource Usage
- **Memory**: 256MB base + 50MB per scanner thread
- **CPU**: Scales with thread count and rule complexity
- **Disk I/O**: Dependent on file extraction rate and log rotation
- **Network**: Minimal overhead for live monitoring

### Scalability Limits
- **Files**: Limited by disk space and database size
- **Concurrent Connections**: 100+ API clients supported
- **Rule Count**: 1000+ YARA rules without significant impact
- **Alert Retention**: Configurable database cleanup policies

## Security Considerations

### Network Security
- **Privilege Separation**: Components run with minimal required privileges
- **Network Isolation**: Optional containerized deployment
- **Encrypted Communication**: HTTPS/TLS for API endpoints
- **Access Control**: API key authentication and rate limiting

### File System Security
- **Sandboxed Analysis**: Extracted files processed in isolation
- **Permission Controls**: Strict file system permissions
- **Quarantine Capabilities**: Automatic isolation of detected threats
- **Audit Logging**: Complete activity tracking

### Data Protection
- **Log Rotation**: Automatic cleanup of sensitive logs
- **Database Encryption**: Optional SQLite encryption
- **Memory Protection**: Secure memory handling for sensitive data
- **Export Controls**: Sanitized data export capabilities

## Integration Points

### External Tool Integration
- **Threat Intelligence**: API endpoints for IOC feeds
- **SIEM Integration**: JSON log format for easy ingestion
- **Orchestration**: REST API for automated workflows
- **Notification Systems**: Webhook support for alerts

### Development Integration
- **Plugin Architecture**: Extensible component system
- **Custom Rules**: Easy rule development and testing
- **API Extensions**: RESTful API for custom integrations
- **Educational Platform**: Built-in tutorial and learning system

This architecture supports both educational use cases and production deployment scenarios, with clear separation of concerns and extensible design patterns.