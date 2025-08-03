# Zeek-YARA Integration: Educational Security Platform

## Network Security Education Platform

An educational platform that teaches network security monitoring, threat detection, and security tool integration. This project integrates **Zeek's network analysis**, **YARA's malware detection**, and **Suricata's intrusion detection** into a unified monitoring system.

### How the Components Work Together

- **Zeek** monitors network traffic and extracts files for analysis
- **YARA** scans extracted files for malware signatures and behavioral patterns  
- **Suricata** provides network-based intrusion detection and prevention
- **Alert Correlation Engine** combines detections from all three tools for comprehensive threat visibility

**Target Audience**: Students, educators, security professionals, and researchers.

## Quick Start

**Prerequisites: Requires Python 3.12.5 or higher**

### 🚀 Fastest Path to Success

1. **5-Minute Demo**: Run the EICAR detection demo to see the platform in action
   ```bash
   ./TOOLS/cli/zyi demo run --tutorial basic-detection
   ```

2. **Educational Setup**: Start the tutorial server for guided learning
   ```bash
   cd EDUCATION && python start_tutorial_server.py
   # Access at http://localhost:8001
   ```

3. **Production Setup**: Follow the complete installation guide below

**Starting points**:
1. [EICAR Demo](docs/examples/quick-demos/eicar-detection.md) - Threat detection demonstration
2. [Getting Started Tutorial](docs/tutorials/getting-started.md) - Setup and first steps
3. [Network Security Concepts](docs/explanations/network-security-basics.md) - Technical fundamentals

**Additional resources**:
- [Documentation](docs/) - Technical guides and references
- [Community Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions) - Support and collaboration

## Learning Objectives

### Core Topics
- **Network Security Monitoring**: Detecting threats in network traffic
- **Tool Integration**: Combining security tools in operational environments
- **Threat Detection**: Malware analysis and intrusion detection techniques
- **Incident Response**: Investigating and responding to security events

### Technologies Covered
- **Zeek**: Network analysis and file extraction
- **YARA**: Malware detection and rule creation
- **Suricata**: Network intrusion detection and prevention
- **Alert Correlation**: Combining data from multiple sources
- **API Integration**: Automating security workflows

### Learning Paths
- **Beginner**: Basic concepts and initial setup
- **Intermediate**: Building monitoring capabilities
- **Advanced**: Platform customization and extension
- **Educator**: Using the platform in teaching environments

## Features

- **Documentation**: Step-by-step tutorials and technical guides
- **Labs**: Practical exercises with real-world scenarios
- **Self-Assessment**: Tests and verification tools
- **Community Support**: Discussion forums and issue tracking
- **Learning Tracks**: Structured progression paths
- **Research Platform**: Extensible architecture for experimentation

## Requirements

**Important: Python Version Requirement**
- **Python 3.12.5 or higher** (Required for consistent test execution and compatibility)

**System Requirements**:
- Zeek (latest stable release)
- YARA 4.2.0+
- Suricata 6.0.0+
- SQLite 3.30.0+

**Python Dependencies**:
```
yara-python>=4.2.0
watchdog>=2.1.0
python-magic>=0.4.24
fastapi>=0.89.0
uvicorn>=0.20.0
pydantic>=1.10.0
typing-extensions>=4.4.0
sqlalchemy>=2.0.0
requests>=2.28.0
```

## Installation

### Method 1: Automated Installation (Recommended)

```bash
# Verify Python version (must be 3.12.5 or higher)
python3 --version  # Should output: Python 3.12.5 or higher

# Clone the repository
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration

# Run the automated installer (creates virtual environment, installs dependencies, configures platform)
python install_platform.py

# OR use the pip-installable command after installation
# pip install -e .
# zeek-yara-install

# Run setup wizard for configuration
python setup_wizard.py

# Verify installation with CLI tool
./TOOLS/cli/zyi --version
./TOOLS/cli/zyi status
```

### Method 2: Manual Setup

```bash
# Verify Python version requirement
python3 --version  # Must be Python 3.12.5 or higher

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (production + development)
pip install -r requirements.txt
pip install -r test-requirements.txt

# Install platform in development mode (for CI/CD and development)
pip install -e .

# Run initial setup
bin/setup.sh

# Verify installation
./TOOLS/cli/zyi --version
./TOOLS/cli/zyi status
```

### Installation Verification

Verify the installation:

```bash
# 1. Check CLI tool
./TOOLS/cli/zyi info

# 2. Verify platform status
./TOOLS/cli/zyi status

# 3. Run demo
./TOOLS/cli/zyi demo run --tutorial basic-detection

# 4. Test tutorial server
cd EDUCATION
python start_tutorial_server.py
# Access at http://localhost:8001

# 5. Run tests
./TOOLS/cli/zyi dev test
```

**Expected Results**:
- CLI commands execute without errors
- Platform status shows "Ready for education!"
- Demo detects EICAR test file
- Tutorial server accessible at http://localhost:8001
- Tests pass

**Troubleshooting**:
- **Wrong Python version**: Install Python 3.12.5 using pyenv:
  ```bash
  # Install pyenv (see: https://github.com/pyenv/pyenv#installation)
  pyenv install 3.12.5
  pyenv local 3.12.5
  python3 --version  # Verify version
  ```
- CLI tool fails: Check Python path and virtual environment activation
- Platform status shows missing components: Verify all directories exist
- Demo fails: Check temporary directory permissions
- Tutorial server fails: Verify port 8001 availability and dependencies
- Tests fail: Check TESTING/ directory exists and pytest installed

## Configuration

Configuration via `config/default_config.json`:

- `EXTRACT_DIR`: Directory for extracted files
- `RULES_DIR`: Path to YARA rule directory
- `DB_FILE`: SQLite database path
- `LOG_FILE`: Logging file path
- `MAX_FILE_SIZE`: Maximum file size to scan
- `THREADS`: Number of scanner threads
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `SURICATA_CONFIG`: Path to Suricata configuration
- `SURICATA_INTERFACE`: Default network interface
- `CORRELATION_WINDOW`: Time window for alert correlation

## Usage

### Primary CLI Tool: `zyi` (Zeek-YARA Integration)

The `zyi` CLI tool is the unified interface for all platform operations:

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

### Integrated System (Legacy)

Run all components together using legacy scripts:

```bash
# Run integrated system (Zeek, YARA scanner, Suricata, and API server)
bin/run_integrated.sh --interface en0

# Run on PCAP file
bin/run_integrated.sh --read /path/to/capture.pcap

# Custom component selection
bin/run_integrated.sh --no-suricata  # Without Suricata
bin/run_integrated.sh --no-api       # Without API server
bin/run_integrated.sh --no-scanner   # Without YARA scanner
```

Integration script features:
- System prerequisite detection
- Log directory creation
- Process monitoring and restart
- Component shutdown handling

### Individual Components

Run components separately:

#### Zeek File Extraction

```bash
# Live network interface
bin/run_zeek.sh --interface en0

# PCAP file
bin/run_zeek.sh --read /path/to/capture.pcap
```

#### YARA Scanner CLI

```bash
# Single file scan
bin/yara_scanner_cli.py --scan-file /path/to/file

# Directory scan
bin/yara_scanner_cli.py --scan-dir /path/to/directory

# Multi-threaded scan
bin/yara_scanner_cli.py --scan-dir /path/to/directory --multi-threaded --threads 4

# Custom configuration
bin/yara_scanner_cli.py \
    --scan-dir /path/to/directory \
    --rules-dir /custom/rules \
    --log-file /custom/log.txt \
    --debug
```

#### Suricata Controls

```bash
# Run on interface
bin/suricata_cli.py --interface en0

# Run for duration (seconds)
bin/suricata_cli.py --interface en0 --duration 300

# Analyze PCAP
bin/suricata_cli.py --pcap /path/to/capture.pcap

# Check status
bin/suricata_cli.py --status

# Update rules
bin/suricata_cli.py --update-rules

# Stop Suricata
bin/suricata_cli.py --stop

# Alert correlation
bin/suricata_cli.py --correlate --correlation-window 600
```

#### API Server

```bash
# Start API server
bin/run_api.py --host 0.0.0.0 --port 8000
```

## Rule Management

### YARA Rules

Rules stored in `rules/active/` with category subdirectories:

```
rules/
└── active/
    ├── document_malware/
    ├── evasion_techniques/
    ├── malware/
    ├── network_behavior/
    └── ransomware/
```

### Suricata Rules

Rules stored in `rules/suricata/` with automatic updates:

```bash
# Update Suricata rules
bin/update_suricata_rules.sh
```

## API Endpoints

RESTful API for control and monitoring:

### YARA Scanner Endpoints
- `GET /alerts`: Retrieve YARA scan alerts
- `POST /scanner/start`: Start YARA scanner
- `POST /scanner/stop`: Stop YARA scanner
- `POST /scan`: Scan file or directory

### Suricata Endpoints
- `GET /suricata/status`: Retrieve Suricata status
- `GET /suricata/alerts`: Retrieve Suricata alerts with filtering
- `POST /suricata/start`: Start Suricata on interface
- `POST /suricata/stop`: Stop Suricata
- `POST /suricata/pcap`: Analyze PCAP with Suricata
- `POST /suricata/rules/update`: Update Suricata rules

### Alert Correlation Endpoints
- `POST /suricata/correlate`: Correlate alerts
- `GET /suricata/correlation`: Retrieve correlated alerts

## Alert Correlation

System correlates alerts from YARA, Suricata, and Zeek:

- **IP-based correlation**: Match file detections with network traffic
- **Hash-based correlation**: Match file hashes with network alerts
- **Time-proximity correlation**: Associate alerts within time windows

Configuration in `config/default_config.json`:

```json
{
  "CORRELATION_ENABLED": true,
  "CORRELATION_WINDOW": 300,
  "TIME_PROXIMITY_WINDOW": 60,
  "MIN_ALERT_CONFIDENCE": 70
}
```

## Directory Structure

### Core Platform Structure

```
zeek-yara-integration/
├── PLATFORM/            # Main platform code
│   ├── core/            # Core scanning and database functionality
│   │   ├── scanner.py   # Multi-threaded file scanning engine
│   │   └── database.py  # SQLite database manager with connection pooling
│   ├── api/             # FastAPI-based REST API server
│   │   ├── api_server.py
│   │   └── suricata_api.py
│   └── integrations/    # Tool integrations (Zeek, YARA, Suricata)
├── TOOLS/               # Command-line tools and utilities
│   ├── cli/             # Primary CLI tool (`zyi`)
│   ├── gui/             # Graphical interfaces (dashboard, rule editor)
│   └── scripts/         # Automation and maintenance scripts
├── EDUCATION/           # Educational platform and tutorials
│   ├── tutorials/       # Step-by-step learning modules
│   ├── examples/        # Practical demonstrations
│   └── static/          # Web assets for tutorial server
├── CONFIGURATION/       # Modern configuration system
│   └── defaults/        # Default configuration templates
└── TESTING/             # Comprehensive testing framework
    ├── unit/            # Unit tests
    ├── integration/     # Integration tests
    └── performance/     # Performance benchmarks
```

### Legacy Structure (Still Active)

```
├── api/                 # Legacy API server (still used)
├── bin/                 # Legacy command-line tools and scripts
├── config/              # Legacy configuration files
│   ├── default_config.json  # Main configuration file
│   └── suricata.yaml    # Suricata configuration
├── core/                # Legacy core modules (still used)
├── extracted_files/     # Files extracted by Zeek for scanning
├── logs/                # Log directory
│   ├── yara_scan.log    # YARA scanner logs
│   ├── api.log          # API server logs
│   └── suricata/        # Suricata-specific logs
├── rules/               # Rules directory
│   ├── active/          # YARA rules organized by category
│   │   ├── malware/
│   │   ├── ransomware/
│   │   └── document_malware/
│   └── suricata/        # Suricata rules
├── suricata/            # Suricata integration modules
├── utils/               # Utility modules
└── zeek/                # Zeek scripts for file extraction
```

### Key Directories Explained

- **PLATFORM/**: Modern platform architecture with improved organization
- **TOOLS/cli/**: Unified CLI tool (`zyi`) for all platform operations
- **EDUCATION/**: Complete educational system with tutorials and web interface
- **extracted_files/**: Temporary storage for files extracted by Zeek from network traffic
- **rules/active/**: YARA rules organized by threat category (malware, ransomware, etc.)
- **logs/**: All system logs including scanner, API, and Suricata outputs
- **config/**: System configuration files (paths, threading, correlation settings)
- **TESTING/**: Comprehensive test suite with unit, integration, and performance tests

## Testing

```bash
# Run all tests
bin/run_tests.sh --all

# Run test categories
bin/run_tests.sh --unit
bin/run_tests.sh --integration
bin/run_tests.sh --performance

# Generate coverage report
bin/run_tests.sh --all --coverage
```

## Troubleshooting

### Common Issues and Solutions

#### Installation Issues

**Wrong Python version**:
```bash
# Install Python 3.12.5 using pyenv (recommended)
curl https://pyenv.run | bash
pyenv install 3.12.5
pyenv local 3.12.5
python3 --version  # Verify version
```

**Missing dependencies**:
```bash
# Reinstall all dependencies
pip install -r requirements.txt
pip install -r test-requirements.txt

# For API server issues specifically
pip install uvicorn fastapi
```

**Virtual environment issues**:
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Runtime Issues

**CLI tool fails**:
```bash
# Check Python path and virtual environment activation
which python3
echo $VIRTUAL_ENV
source venv/bin/activate

# Make CLI tool executable
chmod +x ./TOOLS/cli/zyi
```

**Platform status shows missing components**:
```bash
# Create required directories
mkdir -p extracted_files logs logs/suricata rules/active rules/suricata

# Check permissions
ls -la extracted_files logs
sudo chown -R $USER:$USER extracted_files logs
```

**Scanner startup failure**:
```bash
# Create test rule to verify YARA functionality
mkdir -p rules/active/malware
echo 'rule test {strings: $a = "test" condition: $a}' > rules/active/malware/test.yar

# Test YARA compilation
yara-python -c rules/active/malware/test.yar
```

**No file extraction from Zeek**:
```bash
# Test Zeek configuration
zeek -i en0 -C zeek/extract_files.zeek

# Check interface name
ip link show  # Linux
ifconfig      # macOS

# Test with PCAP file instead
zeek -r test.pcap zeek/extract_files.zeek
```

**Demo fails**:
```bash
# Check temporary directory permissions
ls -la /tmp
mkdir -p /tmp/zeek-yara-demo
chmod 777 /tmp/zeek-yara-demo

# Verify EICAR test file creation
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > test_eicar.txt
```

**Tutorial server fails**:
```bash
# Check port availability
netstat -an | grep 8001
lsof -i :8001

# Install tutorial dependencies
cd EDUCATION
pip install -r requirements.txt

# Use different port if needed
python start_tutorial_server.py --port 8002
```

**Tests fail**:
```bash
# Ensure TESTING directory exists
mkdir -p TESTING

# Install test dependencies
pip install pytest pytest-cov

# Run specific test categories
bin/run_tests.sh --unit
bin/run_tests.sh --integration

# Check test configuration
cat pytest.ini
```

#### Performance Issues

**Slow scanning**:
```bash
# Increase thread count in config
vim config/default_config.json
# Set "THREADS": 4 or higher

# Check system resources
top
htop
```

**Database performance**:
```bash
# Check database file
ls -la logs/alerts.db
sqlite3 logs/alerts.db "VACUUM;"

# Check database indexes
sqlite3 logs/alerts.db ".schema"
```

### Diagnostic Commands

```bash
# Platform health check
./TOOLS/cli/zyi status
./TOOLS/cli/zyi info

# Check component logs
tail -f logs/yara_scan.log
tail -f logs/api.log
tail -f logs/suricata/eve.json

# Database inspection
sqlite3 logs/alerts.db "SELECT COUNT(*) FROM yara_alerts;"
sqlite3 logs/alerts.db "SELECT rule_name, COUNT(*) FROM yara_alerts GROUP BY rule_name;"

# Test network connectivity (for Suricata)
ping 8.8.8.8
netstat -rn
```

### Log Locations

- **YARA Scanner**: `logs/yara_scan.log`
- **API Server**: `logs/api.log`
- **Suricata**: `logs/suricata/eve.json`, `logs/suricata/suricata.log`
- **Zeek**: Log files in project root (`*.log`)
- **Database**: `logs/alerts.db` (SQLite)
- **Tutorial Server**: Console output and browser developer tools

### Sample Data and Testing Files

The platform includes test data for immediate experimentation:

**EICAR Test File** (Safe Malware Test):
```bash
# Create EICAR test file for immediate testing
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > tests/test_eicar.txt

# Test with YARA scanner
./TOOLS/cli/zyi scan file tests/test_eicar.txt

# Expected result: Detection by malware rules
```

**Sample Network Traffic** (Educational):
```bash
# The platform includes sample PCAP files in DATA/samples/pcaps/
ls DATA/samples/pcaps/

# Run analysis on sample PCAP
bin/run_integrated.sh --read DATA/samples/pcaps/sample.pcap

# Expected: File extraction, YARA scanning, and Suricata alerts
```

**Working Configuration Examples**:
```bash
# Educational configuration (recommended for learning)
cp CONFIGURATION/defaults/config.py config/educational_config.py

# Production configuration (for real deployment)
cp config/default_config.json config/production_config.json
```

### Expected Outputs and Results

When the platform is working correctly, you should see:

1. **File Extraction**: Files appear in `extracted_files/` directory
2. **YARA Alerts**: Logged to `logs/yara_scan.log` and `logs/alerts.db`
3. **Suricata Alerts**: Logged to `logs/suricata/eve.json`
4. **API Responses**: Available at `http://localhost:8000/alerts`
5. **Dashboard Access**: Tutorial server at `http://localhost:8001`

### Getting Help

1. **Check Issues**: [GitHub Issues](https://github.com/quanticsoul4772/zeek-yara-integration/issues)
2. **Community Discussion**: [GitHub Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions)
3. **Documentation**: Review [CLAUDE.md](CLAUDE.md) for detailed developer guidance
4. **Educational Support**: Use tutorial server at `http://localhost:8001` for guided troubleshooting

## Community and Contributing

### Contributing

Contributions welcome from all skill levels.

**Contribution Areas**:
- **Documentation**: Tutorials, fixes, translations
- **Bug Reports**: Issue identification and fixes
- **Feature Requests**: Platform improvements
- **Educational Content**: Tutorials, case studies, assessments
- **Code**: Platform enhancements and features

**Getting Started**:
1. Read [Contributing Guidelines](CONTRIBUTING.md)
2. Review [Good First Issues](https://github.com/quanticsoul4772/zeek-yara-integration/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
3. Join [Community Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions)

### Community Resources

- [Project Roadmap](PROJECT_PLAN.md): Development plans
- [Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions): Questions and collaboration
- [Issue Tracker](https://github.com/quanticsoul4772/zeek-yara-integration/issues): Bug reports and features
- [Documentation Standards](DOCUMENTATION_STANDARDS.md): Contributor guidelines
- [Educational Goals](docs/explanations/educational-goals.md): Project mission

### For Educators

**Platform Usage**:
- Classroom deployment guides
- Curriculum alignment resources
- Assessment tools and quizzes
- Teaching materials

**Academic Support**:
- Research collaboration
- Guest lectures and workshops
- Curriculum development
- Student project guidance

### Recognition

**Contributors**: Listed in [Contributors List](CONTRIBUTORS.md)

**Acknowledgments**:
- Core maintainers and developers
- Educational institutions using the platform
- Security researchers and professionals

## License

MIT License - See [LICENSE](LICENSE) file.

## Acknowledgments

This project builds on:

- [Zeek Project](https://zeek.org/) - Network analysis framework
- [YARA](https://virustotal.github.io/yara/) - Malware identification and classification
- [Suricata](https://suricata.io/) - Network threat detection engine
- Open source security tools community
- Educational community
- All contributors

## Getting Started

1. [Network Security Concepts](docs/explanations/network-security-basics.md)
2. [EICAR Detection Demo](docs/examples/quick-demos/eicar-detection.md)
3. [Getting Started Guide](docs/tutorials/getting-started.md)
4. [GitHub Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions)

For questions, use community discussions or create an issue.
