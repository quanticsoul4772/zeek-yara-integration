# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running Tests
```bash
# Cross-platform test runner (recommended - works on Windows, macOS, Linux)
python run_tests.py --all                    # Run all tests
python run_tests.py --unit                   # Unit tests only
python run_tests.py --integration            # Integration tests only
python run_tests.py --performance            # Performance tests only
python run_tests.py --suricata               # Suricata-specific tests
python run_tests.py --all --verbose          # Run with verbose output
python run_tests.py --all --output-dir results  # Custom output directory

# Legacy bash script (Unix/Linux/macOS only)
bin/run_tests.sh --all
bin/run_tests.sh --unit          # Unit tests only
bin/run_tests.sh --integration   # Integration tests only
bin/run_tests.sh --performance   # Performance tests only
bin/run_tests.sh --suricata      # Suricata-specific tests

# Direct pytest usage (from project root)
python -m pytest tests/ -v
python -m pytest tests/ -m "unit" -v
python -m pytest tests/ --cov=core --cov=utils --cov=suricata
```

### Development Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (production + development)
pip install -r requirements.txt
pip install -r test-requirements.txt

# Run platform setup wizard (creates configs, directories)
python setup.py install
python setup_wizard.py

# Initialize with simplified educational config
python setup.py  # Creates educational platform setup
```

### Starting the System

#### Unified CLI Tool (Recommended)
```bash
# Educational demonstrations
./TOOLS/cli/zyi demo run --tutorial basic-detection   # EICAR detection demo
./TOOLS/cli/zyi demo run --list                       # List available tutorials

# Development server and API
./TOOLS/cli/zyi api start --dev --port 8000           # Start API server
./TOOLS/cli/zyi dev start --reload                    # Start with auto-reload
./TOOLS/cli/zyi dev test                              # Run test suite

# File scanning operations
./TOOLS/cli/zyi scan file /path/to/file               # Scan single file
./TOOLS/cli/zyi scan file /path/to/file --output results.json

# System status and management
./TOOLS/cli/zyi status                                # Check platform status
./TOOLS/cli/zyi info                                  # Show platform information
./TOOLS/cli/zyi config init --environment education  # Initialize config
```

#### Legacy Individual Components
```bash
# For development and testing individual components
bin/run_integrated.sh --interface en0                # All components
bin/run_api.sh --host 0.0.0.0 --port 8000          # API server only
bin/run_scanner.sh                                   # YARA scanner only
bin/run_zeek.sh --interface en0                     # Zeek file extraction
```

### Educational Platform Usage
```bash
# Start tutorial web server (port 8001)
cd EDUCATION
python start_tutorial_server.py

# Access educational content
python tutorial_web_server.py  # Interactive tutorials
python tutorial_system.py      # Tutorial management
```

### Testing With Sample Files
```bash
# Test YARA detection with EICAR test file
cp tests/test_eicar.txt extracted_files/test_eicar.txt

# Monitor scan results in real-time
tail -f logs/yara_scan.log

# Query alert database directly
sqlite3 logs/yara_alerts.db "SELECT * FROM yara_alerts ORDER BY timestamp DESC LIMIT 10;"
sqlite3 logs/yara_alerts.db "SELECT rule_name, COUNT(*) FROM yara_alerts GROUP BY rule_name;"

# Test API endpoints
curl -X GET "http://localhost:8000/status"
curl -X GET "http://localhost:8000/alerts?page=1&page_size=5"
```

## Architecture Overview

This is a **network security monitoring toolkit** that integrates three main components:

### Core Components
- **Zeek**: Network traffic analysis and file extraction
- **YARA**: File scanning and malware detection
- **Suricata**: Network intrusion detection

### Key Python Modules

#### Scanner Architecture (`PLATFORM/core/scanner.py`)
- `BaseScanner`: Common functionality for file scanning
- `SingleThreadScanner`: Simple file monitoring implementation  
- `MultiThreadScanner`: High-performance multi-threaded scanning
- File system watching using `watchdog` library
- Queue-based processing for thread safety

#### Database Layer (`PLATFORM/core/database.py`)
- `DatabaseManager`: SQLite-based alert storage with connection pooling
- Performance tracking decorators
- Thread-safe operations with connection pools
- Bulk insert capabilities for high-volume alerts

#### API Server (`PLATFORM/api/api_server.py`)
- FastAPI-based REST API
- CORS middleware for web integration
- Authentication via API keys
- Endpoints for alerts, scanner control, and Suricata integration

#### Configuration System (`CONFIGURATION/` and legacy `config/`)
- JSON-based configuration in `config/default_config.json` (legacy) and `CONFIGURATION/defaults/`
- Centralized settings for all components
- Paths, logging, threading, and correlation parameters

### Data Flow
1. **Network Traffic** → Zeek extracts files → `extracted_files/` directory
2. **File Monitoring** → Scanner detects new files → YARA analysis
3. **YARA Matches** → Database storage → API exposure
4. **Suricata** → Network-based detection → Alert correlation
5. **Correlation Engine** → Cross-reference file and network alerts

### Threading Model
- Scanner supports both single and multi-threaded modes
- Configuration via `THREADS` parameter in config
- Queue-based work distribution for multi-threading
- Thread-safe database operations with connection pooling

### Integration Points
- **Zeek Scripts**: Custom scripts in `zeek/` for file extraction
- **YARA Rules**: Organized in `rules/active/` by category
- **Suricata Rules**: Managed in `rules/suricata/`
- **Alert Correlation**: Time and IP-based correlation between systems

## Important Development Notes

### Project Structure and Key Files
- `PLATFORM/core/scanner.py` - Main scanning engine with both single and multi-threaded implementations
- `PLATFORM/core/database.py` - SQLite database manager with connection pooling and performance optimization
- `PLATFORM/api/api_server.py` - FastAPI-based REST API server with comprehensive endpoints
- `TOOLS/cli/zyi` - Primary CLI tool for all platform operations
- `setup.py` - Cross-platform installer with educational platform setup
- `config/default_config.json` - Legacy configuration (still used)
- `CONFIGURATION/defaults/` - New modular configuration system

### Database Schema and Operations
The `yara_alerts` table includes comprehensive metadata:
- File information: path, name, size, type, MD5/SHA256 hashes
- YARA match details: rule name, namespace, metadata, matched strings
- Zeek correlation data: UID tracking for network context
- Performance: indexed timestamps and rule names for fast queries
- Thread safety: Connection pooling with per-thread isolation

Key database methods in `PLATFORM/core/database.py`:
- `add_alert(file_data, match_data)` - Insert single alert
- `bulk_insert_alerts(alerts_data)` - Efficient batch operations
- `get_alerts(filters, limit, offset)` - Paginated retrieval with filtering

### Configuration Management
Configuration follows a hybrid approach:
- Legacy: `config/default_config.json` - still actively used by scanner and API
- New: `CONFIGURATION/defaults/` - modular system for future expansion
- Key settings: file paths, thread counts, API settings, Suricata integration
- Environment-specific configs: educational, development, production modes

When developing:
- Absolute paths preferred for file locations
- Use environment variables for deployment flexibility
- All log/data directories must exist before component startup
- Thread count affects scanner performance significantly

### Scanner Architecture Details
`PLATFORM/core/scanner.py` implements a sophisticated scanning system:

**BaseScanner** - Common functionality:
- File metadata extraction and validation
- YARA rule compilation and matching
- Database persistence with error handling
- MIME type and extension filtering
- Configurable file size limits

**SingleThreadScanner** - Simple monitoring:
- File system watching via `watchdog` library
- Direct file processing in main thread
- Suitable for low-volume environments

**MultiThreadScanner** - High-performance scanning:
- Queue-based work distribution
- Configurable thread pool (default: 2 threads)
- Thread-safe database operations
- Graceful shutdown with timeout handling

### API Server Architecture
`PLATFORM/api/api_server.py` provides comprehensive REST API:

**Core Endpoints:**
- `/status` - System health and statistics
- `/alerts` - Paginated alert retrieval with filtering
- `/scan` - On-demand file/directory scanning
- `/scanner/start|stop` - Scanner lifecycle management
- `/rules` - YARA rule management

**Integration Features:**
- CORS middleware for web integration
- Optional API key authentication
- Structured error responses with proper HTTP status codes
- Background tasks for long-running operations
- Auto-start scanner and Suricata integration

**Performance Optimizations:**
- Connection pooling for database access
- Async/await for non-blocking operations
- Pagination to handle large result sets
- JSON parsing for metadata fields

### Testing Framework
`pytest.ini` defines test markers and structure:
- **unit** - Fast, isolated component tests
- **integration** - Cross-component functionality tests  
- **performance** - Load and timing tests
- **suricata** - Network integration tests

Test execution via `bin/run_tests.sh`:
- Automatic virtual environment activation
- Coverage reporting with HTML and XML output
- Test result summary with success rates
- Parallel execution support

### CLI Tool Design
`TOOLS/cli/zyi` uses Click framework for command structure:
- **demo** - Educational tutorials and demonstrations
- **scan** - File and directory scanning operations
- **dev** - Development tools and server management
- **api** - API server lifecycle management
- **config** - Configuration initialization and management

Each command group provides focused functionality with consistent parameter patterns.

### Error Handling and Logging Patterns
- **Comprehensive logging**: DEBUG, INFO, WARNING, ERROR levels with structured messages
- **Database operations**: Wrapped in try/catch with proper connection cleanup
- **Scanner threads**: Designed to handle individual file failures without stopping monitoring
- **API endpoints**: Return structured JSON error responses with appropriate HTTP status codes
- **Performance tracking**: Decorators for method execution timing in database operations

### Performance Considerations
- **Database connection pooling**: Thread-safe connection management with queue-based pooling
- **Configurable limits**: File size limits prevent memory exhaustion
- **Multi-threading**: Queue-based work distribution for high-volume scanning
- **Bulk operations**: Batch database inserts for efficiency
- **Index optimization**: Database indexes on timestamp and rule_name for fast queries

### Security Focus and Defensive Design
This is a **defensive security tool** designed for:
- Network traffic analysis and monitoring
- Malware detection and behavioral analysis
- Intrusion detection and prevention
- Security event correlation across multiple tools
- Educational cybersecurity training

**Important Security Note**: This platform is designed for defensive security purposes only. Do not use for creating malicious tools, bypassing security measures, or any offensive security activities.