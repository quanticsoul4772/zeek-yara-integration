# Zeek-YARA Integration: Educational Security Platform

## 🎓 Learn Network Security Through Hands-On Practice

An open-source educational platform designed to teach network security monitoring, threat detection, and security tool integration. This project combines Zeek's network analysis, YARA's malware detection, and Suricata's intrusion detection in a comprehensive learning environment that bridges theory and practice.

**Perfect for**: Students, educators, security professionals, researchers, and anyone interested in learning practical cybersecurity skills.

## 🚀 Quick Start

**New to network security?** Start here:
1. [5-Minute EICAR Demo](docs/examples/quick-demos/eicar-detection.md) - See threat detection in action
2. [Getting Started Tutorial](docs/tutorials/getting-started.md) - Complete beginner's guide
3. [Understanding Network Security](docs/explanations/network-security-basics.md) - Learn the fundamentals

**Ready to dive deeper?** 
- [Complete Documentation](docs/) - Comprehensive learning resources
- [Community Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions) - Get help and share knowledge

## 🎯 What You'll Learn

### Core Skills
- **Network Security Monitoring**: Understand how to detect threats in network traffic
- **Tool Integration**: Learn how security tools work together in real environments
- **Threat Detection**: Develop skills in malware analysis and intrusion detection
- **Incident Response**: Practice investigating and responding to security events

### Hands-On Experience With
- **🔍 Zeek**: Network analysis and file extraction from traffic
- **🛡️ YARA**: Malware detection and custom rule creation
- **🚨 Suricata**: Network intrusion detection and prevention
- **📊 Alert Correlation**: Combining insights from multiple security tools
- **🔌 API Integration**: Automating security workflows

### Learning Paths
- **Beginner Path**: Start with basic concepts and simple setups
- **Intermediate Path**: Build comprehensive monitoring capabilities
- **Advanced Path**: Customize and extend the platform for research
- **Educator Path**: Use the platform for teaching cybersecurity courses

## ✨ Educational Features

- **📚 Comprehensive Documentation**: Step-by-step tutorials and conceptual guides
- **🎮 Interactive Labs**: Hands-on exercises with real scenarios
- **📝 Self-Assessment**: Quizzes and verification tools to test your knowledge
- **👥 Community Support**: Active community for questions and collaboration
- **🏆 Certification Paths**: Structured learning with achievement tracking
- **🔬 Research Ready**: Extensible platform for academic and industry research

## Prerequisites

- **System Requirements**:
  - Python 3.8+
  - Zeek (latest stable release)
  - YARA 4.2.0+
  - Suricata 6.0.0+
  - SQLite 3.30.0+

- **Python Dependencies**:
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

# Run initial setup (if available)
# bin/setup.sh

# Verify installation
./TOOLS/cli/zyi --version
./TOOLS/cli/zyi status
```

### Installation Verification

After completing the installation, verify everything is working correctly:

```bash
# 1. Check that the CLI tool is working
./TOOLS/cli/zyi info

# 2. Verify platform status
./TOOLS/cli/zyi status

# 3. Run a quick demo to test functionality
./TOOLS/cli/zyi demo run --tutorial basic-detection

# 4. Test educational tutorial server
cd EDUCATION
python start_tutorial_server.py
# Open http://localhost:8001 in your browser

# 5. Run basic tests (if available)
./TOOLS/cli/zyi dev test
```

**Expected Output:**
- CLI commands should run without errors
- Platform status should show "Ready for education!"
- Demo should successfully detect EICAR test file
- Tutorial server should be accessible at http://localhost:8001
- Basic tests should pass

**Troubleshooting Installation Issues:**
- If CLI tool fails: Check Python path and virtual environment activation
- If platform status shows missing components: Ensure all directories exist
- If demo fails: Check that temporary directories can be created
- If tutorial server fails: Verify port 8001 is available and dependencies installed
- If tests fail: Check that TESTING/ directory exists and pytest is installed

## Configuration

Configuration is managed through `config/default_config.json`. Key options include:

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

The easiest way to use the system is with the integrated script that starts all components together:

```bash
# Run the integrated system (Zeek, YARA scanner, Suricata, and API server)
bin/run_integrated.sh --interface en0

# Run on a specific PCAP file
bin/run_integrated.sh --read /path/to/capture.pcap

# Run with custom component selection
bin/run_integrated.sh --no-suricata  # Run without Suricata
bin/run_integrated.sh --no-api       # Run without API server
bin/run_integrated.sh --no-scanner   # Run without YARA scanner
```

The integration script includes:
- Auto-detection of system prerequisites
- Automatic log directory creation
- Process monitoring and auto-restart
- Clean shutdown of all components

### Individual Components

You can also run each component separately:

#### Zeek File Extraction

```bash
# Scan live network interface
bin/run_zeek.sh --interface en0

# Scan a specific PCAP file
bin/run_zeek.sh --read /path/to/capture.pcap
```

#### YARA Scanner CLI

```bash
# Scan a single file
bin/yara_scanner_cli.py --scan-file /path/to/file

# Scan entire directory
bin/yara_scanner_cli.py --scan-dir /path/to/directory

# Multi-threaded scanning
bin/yara_scanner_cli.py --scan-dir /path/to/directory --multi-threaded --threads 4

# Advanced scanning with configuration
bin/yara_scanner_cli.py \
    --scan-dir /path/to/directory \
    --rules-dir /custom/rules \
    --log-file /custom/log.txt \
    --debug
```

#### Suricata Controls

```bash
# Run Suricata standalone on an interface
bin/suricata_cli.py --interface en0

# Run Suricata for a specific duration (in seconds)
bin/suricata_cli.py --interface en0 --duration 300

# Analyze PCAP with Suricata
bin/suricata_cli.py --pcap /path/to/capture.pcap

# Check Suricata status
bin/suricata_cli.py --status

# Update Suricata rules
bin/suricata_cli.py --update-rules

# Manually stop running Suricata
bin/suricata_cli.py --stop

# Run alert correlation
bin/suricata_cli.py --correlate --correlation-window 600
```

#### API Server

```bash
# Start the API server
bin/run_api.py --host 0.0.0.0 --port 8000
```

## Rule Management

### YARA Rules

YARA rules are stored in `rules/active/` with subdirectories for different rule categories:

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

Suricata rules are stored in `rules/suricata/` and can be automatically updated from online sources:

```bash
# Update Suricata rules
bin/update_suricata_rules.sh
```

## API Endpoints

The system provides a comprehensive RESTful API for remote control and monitoring:

### YARA Scanner Endpoints
- `GET /alerts`: Get YARA scan alerts
- `POST /scanner/start`: Start the YARA scanner
- `POST /scanner/stop`: Stop the YARA scanner
- `POST /scan`: Scan a specific file or directory

### Suricata Endpoints
- `GET /suricata/status`: Get Suricata status
- `GET /suricata/alerts`: Get Suricata alerts with filtering
- `POST /suricata/start`: Start Suricata on an interface
- `POST /suricata/stop`: Stop Suricata
- `POST /suricata/pcap`: Analyze PCAP with Suricata
- `POST /suricata/rules/update`: Update Suricata rules

### Alert Correlation Endpoints
- `POST /suricata/correlate`: Correlate alerts
- `GET /suricata/correlation`: Get correlated alerts

## Alert Correlation

The system correlates alerts from different sources (YARA, Suricata, Zeek) to provide comprehensive threat detection:

- **IP-based correlation**: Match file detections with network traffic
- **Hash-based correlation**: Match file hashes with network alerts
- **Time-proximity correlation**: Associate alerts occurring within a close timeframe

Correlation settings can be configured in `config/default_config.json`:

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

# Run specific test categories
bin/run_tests.sh --unit
bin/run_tests.sh --integration
bin/run_tests.sh --performance

# Generate coverage report
bin/run_tests.sh --all --coverage
```

## Troubleshooting

### Common Issues

- **Missing dependencies**: Make sure all Python dependencies are installed
  ```bash
  pip install -r requirements.txt
  ```

- **API server won't start**: Ensure `uvicorn` and `fastapi` are installed
  ```bash
  pip install uvicorn fastapi
  ```

- **Scanner fails to start**: Check that the scanner can find the YARA rules
  ```bash
  # Create a basic rule for testing
  mkdir -p rules/active/malware
  echo 'rule test {strings: $a = "test" condition: $a}' > rules/active/malware/test.yar
  ```

- **No files being extracted**: Verify your Zeek installation and configuration
  ```bash
  # Test Zeek configuration
  zeek -i en0 -C zeek/extract_files.zeek
  ```

### Log Locations

- YARA Scanner: `logs/yara_scan.log`
- Suricata: `logs/suricata/`
- API Server: `logs/api.log`
- Zeek: Log files in the project root (`*.log`)

## 🤝 Community and Contributing

### Get Involved

We welcome contributions from security professionals, students, educators, and enthusiasts of all skill levels!

**Ways to Contribute:**
- 📖 **Documentation**: Improve tutorials, fix typos, add translations
- 🐛 **Bug Reports**: Help us find and fix issues
- 💡 **Feature Requests**: Suggest new educational content or platform improvements
- 🎓 **Educational Content**: Create tutorials, case studies, or assessment materials
- 🔧 **Code Contributions**: Enhance the platform or add new features

**Getting Started:**
1. Read our [Contributing Guidelines](CONTRIBUTING.md)
2. Check out [Good First Issues](https://github.com/quanticsoul4772/zeek-yara-integration/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
3. Join our [Community Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions)

### Community Resources

- **📋 [Project Roadmap](PROJECT_PLAN.md)**: See what we're working on and planning
- **💬 [Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions)**: Ask questions, share ideas, get help
- **🐛 [Issue Tracker](https://github.com/quanticsoul4772/zeek-yara-integration/issues)**: Report bugs or request features
- **📚 [Documentation Standards](DOCUMENTATION_STANDARDS.md)**: Guidelines for contributors
- **🎯 [Educational Goals](docs/explanations/educational-goals.md)**: Our mission and vision

### For Educators

**Teaching with This Platform:**
- 🏫 **Classroom Setup Guide**: Deploy for educational environments
- 📋 **Curriculum Integration**: Align with cybersecurity education standards
- 📊 **Assessment Tools**: Built-in quizzes and practical evaluations
- 👨‍🏫 **Instructor Resources**: Teaching guides and presentation materials

**Academic Partnerships:**
- Research collaboration opportunities
- Guest lecture and workshop support
- Curriculum development assistance
- Student project mentorship

### Recognition

**Contributors:**
All contributors are recognized in our [Contributors List](CONTRIBUTORS.md) and project documentation.

**Special Thanks:**
- 🌟 **Core Contributors**: Long-term project maintainers and major feature developers
- 🎓 **Educational Partners**: Universities and institutions using the platform
- 🔒 **Security Community**: Researchers and professionals who've shared their expertise

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

This open-source license ensures the platform remains free and accessible for educational use while allowing commercial applications and derivative works.

## 🙏 Acknowledgments

This project builds upon the incredible work of the open-source security community:

- **[Zeek Project](https://zeek.org/)** - Network analysis framework
- **[YARA](https://virustotal.github.io/yara/)** - Malware identification and classification
- **[Suricata](https://suricata.io/)** - Network threat detection engine
- **Open Source Security Tools** - The broader ecosystem that makes this integration possible
- **Educational Community** - Educators and students who inspire continuous improvement
- **Contributors** - Everyone who has helped improve this platform

## 🚀 Getting Started

Ready to begin your network security journey? 

1. **📖 Start with the Basics**: [Understanding Network Security](docs/explanations/network-security-basics.md)
2. **⚡ Quick Demo**: [5-Minute EICAR Detection](docs/examples/quick-demos/eicar-detection.md)
3. **🎯 Full Tutorial**: [Complete Getting Started Guide](docs/tutorials/getting-started.md)
4. **💬 Join the Community**: [GitHub Discussions](https://github.com/quanticsoul4772/zeek-yara-integration/discussions)

**Questions?** Don't hesitate to ask in our community discussions or create an issue. We're here to help you learn and succeed!

---

*Happy Learning! The future of cybersecurity depends on well-trained professionals. Let's build that future together.* 🛡️
