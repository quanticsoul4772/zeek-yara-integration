# Zeek-YARA Integration: Educational Security Platform

## Network Security Education Platform

An educational platform that teaches network security monitoring, threat detection, and security tool integration. This project integrates Zeek's network analysis, YARA's malware detection, and Suricata's intrusion detection.

**Target Audience**: Students, educators, security professionals, and researchers.

## Quick Start

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

## Prerequisites

**System Requirements**:
- Python 3.8+
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

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

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

### Integrated System

Run all components together:

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

```
zeek_yara_integration/
├── api/                 # RESTful API server implementation
├── bin/                 # Command-line tools and scripts
├── config/              # Configuration files
│   ├── default_config.json
│   └── suricata.yaml
├── core/                # Core scanning and database functionality
├── extracted_files/     # Files extracted by Zeek for scanning
├── logs/                # Log directory
│   └── suricata/        # Suricata-specific logs
├── rules/               # Rules directory
│   ├── active/          # YARA rules
│   └── suricata/        # Suricata rules
├── suricata/            # Suricata integration
│   ├── alert_correlation.py
│   └── suricata_integration.py
├── tests/               # Testing framework
├── utils/               # Utility modules
└── zeek/                # Zeek scripts for file extraction
```

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

### Common Issues

**Missing dependencies**:
```bash
pip install -r requirements.txt
```

**API server startup failure**:
```bash
pip install uvicorn fastapi
```

**Scanner startup failure**:
```bash
# Create test rule
mkdir -p rules/active/malware
echo 'rule test {strings: $a = "test" condition: $a}' > rules/active/malware/test.yar
```

**No file extraction**:
```bash
# Test Zeek configuration
zeek -i en0 -C zeek/extract_files.zeek
```

### Log Locations

- YARA Scanner: `logs/yara_scan.log`
- Suricata: `logs/suricata/`
- API Server: `logs/api.log`
- Zeek: Log files in project root (`*.log`)

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
