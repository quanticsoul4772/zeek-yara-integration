# Zeek-YARA Integration Platform - Developer Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [Development Workflow](#development-workflow)
5. [Testing Strategy](#testing-strategy)
6. [Contributing Guidelines](#contributing-guidelines)
7. [Performance Optimization](#performance-optimization)
8. [Security Considerations](#security-considerations)

## Getting Started

### Prerequisites

- Python 3.12.5 or higher (required for consistent test execution)
- Git for version control
- Virtual environment management (venv or pyenv)
- System dependencies: Zeek, YARA, Suricata

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration

# Set Python version (using pyenv)
pyenv install 3.12.5
pyenv local 3.12.5

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r config/test-requirements.txt

# Install in development mode
pip install -e .

# Verify installation
./TOOLS/cli/zyi status
```

## Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                           │
│                    (FastAPI - Port 8000)                     │
└─────────────┬───────────────────┬───────────────┬──────────┘
              │                   │               │
    ┌─────────▼─────────┐ ┌──────▼──────┐ ┌─────▼─────┐
    │   YARA Scanner    │ │   Suricata   │ │    Zeek    │
    │  (Multi-threaded) │ │   (IDS/IPS)  │ │ (Network)  │
    └─────────┬─────────┘ └──────┬──────┘ └─────┬─────┘
              │                   │               │
    ┌─────────▼───────────────────▼───────────────▼─────────┐
    │              Alert Correlation Engine                  │
    │         (IP, Hash, Time-based correlation)            │
    └─────────────────────────┬─────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   SQLite Database  │
                    │  (Connection Pool)  │
                    └────────────────────┘
```

### Directory Structure

```
zeek-yara-integration/
├── PLATFORM/           # Core platform modules
│   ├── core/          # Scanner, database, monitoring
│   ├── api/           # REST API implementation
│   └── integrations/  # Tool integrations
├── TOOLS/             # CLI and utility tools
│   ├── cli/          # zyi command-line interface
│   └── scripts/      # Automation scripts
├── EDUCATION/         # Tutorial and learning system
├── TESTING/           # Test suites
├── rules/            # YARA and Suricata rules
└── config/           # Configuration files
```

## Core Components

### 1. YARA Scanner (`PLATFORM/core/scanner.py`)

The multi-threaded file scanning engine with watchdog integration.

```python
from PLATFORM.core.scanner import Scanner

# Initialize scanner
scanner = Scanner(
    rules_dir="/rules/active",
    db_path="/logs/alerts.db",
    threads=4
)

# Start monitoring directory
scanner.start_monitoring("/extracted_files")

# Scan specific file
results = scanner.scan_file("/path/to/file")
```

**Key Features:**
- Multi-threaded scanning for performance
- File type detection with python-magic
- Configurable file size limits
- Real-time directory monitoring
- Database persistence of alerts

### 2. Database Manager (`PLATFORM/core/database.py`)

SQLite database with connection pooling for concurrent access.

```python
from PLATFORM.core.database import DatabaseManager

# Initialize database
db = DatabaseManager("/logs/alerts.db")

# Store alert
db.store_yara_alert(
    file_path="/extracted_files/malware.exe",
    rule_name="Ransomware_Behavior",
    tags=["ransomware", "encryption"],
    meta={"severity": "high"}
)

# Query alerts
alerts = db.get_alerts(limit=100, offset=0)
```

**Schema:**
```sql
CREATE TABLE yara_alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    tags TEXT,
    meta TEXT,
    strings_matched TEXT
);

CREATE TABLE suricata_alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    event_type TEXT,
    src_ip TEXT,
    dest_ip TEXT,
    proto TEXT,
    alert_data TEXT
);
```

### 3. API Server (`PLATFORM/api/api_server.py`)

FastAPI-based REST API with rate limiting and async support.

```python
from fastapi import FastAPI, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

app = FastAPI(title="Zeek-YARA Integration API")
limiter = Limiter(key_func=get_remote_address)

@app.get("/alerts")
@limiter.limit("100/minute")
async def get_alerts(limit: int = 100):
    """Retrieve YARA alerts with pagination"""
    return await fetch_alerts(limit)
```

### 4. Alert Correlation (`suricata/alert_correlation/`)

Sophisticated correlation engine combining multiple detection sources.

```python
from suricata.alert_correlation import AlertCorrelator

correlator = AlertCorrelator()

# Correlate alerts within time window
incidents = correlator.correlate_alerts(
    time_window=300,  # 5 minutes
    correlation_types=["ip_based", "hash_based"]
)
```

**Correlation Methods:**
- **IP-based**: Links file detections to network traffic
- **Hash-based**: Matches file hashes across systems
- **Time-proximity**: Associates alerts within time windows
- **Behavioral**: Pattern-based correlation

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-detection-method

# Make changes and test
./TOOLS/cli/zyi dev test

# Run specific tests
python -m pytest tests/unit_tests/test_scanner.py -v

# Check code quality
black PLATFORM/ --check
flake8 PLATFORM/
mypy PLATFORM/ --config-file config/mypy.ini

# Commit changes
git add .
git commit -m "feat: Add new detection method for encrypted payloads"
```

### 2. Adding YARA Rules

```bash
# Create new rule category
mkdir -p rules/active/new_category

# Add rule file
cat > rules/active/new_category/detection.yar << EOF
rule NewThreat_Detection {
    meta:
        author = "Security Team"
        description = "Detects new threat pattern"
        severity = "high"
    
    strings:
        \$pattern1 = {48 8B 45 ?? 48 89 45}
        \$pattern2 = "suspicious_string"
    
    condition:
        any of them
}
EOF

# Test rule compilation
yara-python -c rules/active/new_category/detection.yar
```

### 3. API Endpoint Addition

```python
# In PLATFORM/api/api_server.py

@app.post("/scan/advanced")
async def advanced_scan(request: ScanRequest):
    """Advanced scanning with custom options"""
    try:
        results = await scanner.advanced_scan(
            target=request.target,
            options=request.options
        )
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing Strategy

### Test Categories

1. **Unit Tests** (`tests/unit_tests/`)
   - Component isolation
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`tests/integration_tests/`)
   - Component interaction
   - Database operations
   - API endpoint testing

3. **Performance Tests** (`tests/performance_tests/`)
   - Scanning throughput
   - Database performance
   - API response times

### Running Tests

```bash
# All tests
bin/run_tests.sh --all

# Specific category
python -m pytest tests/unit_tests/ -v
python -m pytest tests/integration_tests/ -v
python -m pytest tests/performance_tests/ -v

# With coverage
python -m pytest --cov=PLATFORM --cov-report=html

# Specific test file
python -m pytest tests/unit_tests/test_scanner.py::TestScanner::test_scan_file
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from PLATFORM.core.scanner import Scanner

class TestScanner:
    @pytest.fixture
    def scanner(self):
        """Create scanner instance for testing"""
        return Scanner(rules_dir="test_rules", threads=2)
    
    def test_scan_file_detects_threat(self, scanner, tmp_path):
        """Test that scanner detects known threat"""
        # Create test file
        test_file = tmp_path / "malware.exe"
        test_file.write_bytes(b"EICAR-STANDARD-ANTIVIRUS-TEST")
        
        # Scan file
        results = scanner.scan_file(str(test_file))
        
        # Verify detection
        assert len(results) > 0
        assert "EICAR" in results[0].rule_name
```

## Contributing Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use black for formatting: `black PLATFORM/ --line-length=88`
- Type hints for function signatures
- Docstrings for public methods

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Test additions
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

### Pull Request Process

1. Fork the repository
2. Create feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Update documentation
6. Submit PR with description

## Performance Optimization

### Scanner Optimization

```python
# Configure for high-throughput scanning
config = {
    "THREADS": 8,  # Increase worker threads
    "MAX_FILE_SIZE": 100 * 1024 * 1024,  # 100MB limit
    "BATCH_SIZE": 100,  # Process files in batches
    "CACHE_COMPILED_RULES": True  # Cache YARA rules
}
```

### Database Optimization

```python
# Enable WAL mode for concurrent access
db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA synchronous=NORMAL")

# Create indexes for common queries
db.execute("""
    CREATE INDEX idx_alerts_timestamp 
    ON yara_alerts(timestamp DESC)
""")
```

### API Performance

```python
# Use async database operations
async def get_alerts_async():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM alerts") as cursor:
            return await cursor.fetchall()

# Implement caching
from functools import lru_cache

@lru_cache(maxsize=128)
def get_rules_cached(rules_dir: str):
    return compile_rules(rules_dir)
```

## Security Considerations

### Input Validation

```python
from pydantic import BaseModel, validator

class ScanRequest(BaseModel):
    target: str
    max_size: int = 100_000_000
    
    @validator('target')
    def validate_path(cls, v):
        # Prevent path traversal
        if '..' in v or v.startswith('/etc'):
            raise ValueError('Invalid path')
        return v
```

### File Handling

```python
import hashlib
import tempfile

def secure_file_scan(file_content: bytes):
    """Scan file content securely"""
    # Create temporary file with restricted permissions
    with tempfile.NamedTemporaryFile(mode='wb', delete=True) as tmp:
        # Write content
        tmp.write(file_content)
        tmp.flush()
        
        # Verify file integrity
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Scan with size limits
        if len(file_content) > MAX_SIZE:
            raise ValueError("File too large")
        
        return scanner.scan_file(tmp.name)
```

### API Security

```python
# Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

# Input sanitization
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/secure-endpoint")
async def secure_endpoint(credentials: HTTPBearer = Security(security)):
    # Verify token
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=403, detail="Invalid token")
```

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

### Database Inspection

```bash
# Inspect database
sqlite3 logs/alerts.db

# Common queries
.tables
.schema yara_alerts
SELECT COUNT(*) FROM yara_alerts;
SELECT * FROM yara_alerts ORDER BY timestamp DESC LIMIT 10;
```

### API Testing

```bash
# Use httpie for testing
pip install httpie

# Test endpoints
http GET localhost:8000/health
http POST localhost:8000/scan target=/path/to/file
http GET localhost:8000/alerts limit==10
```

## Resources

- [Project Repository](https://github.com/quanticsoul4772/zeek-yara-integration)
- [API Documentation](./API_REFERENCE.md)
- [Configuration Guide](./reference/configuration-reference.md)
- [YARA Documentation](https://yara.readthedocs.io/)
- [Suricata Documentation](https://suricata.io/documentation/)
- [Zeek Documentation](https://docs.zeek.org/)