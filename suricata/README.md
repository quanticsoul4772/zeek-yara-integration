# Suricata Integration for Zeek-YARA

This module integrates Suricata with the Zeek-YARA system for comprehensive network security monitoring.

## Overview

The Suricata integration adds network-based intrusion detection to the existing file-based scanning capabilities, providing:

- Real-time traffic monitoring and alert generation
- PCAP file analysis capabilities
- Advanced rule management
- Alert correlation with YARA detections
- API endpoints for system control and monitoring

## Components

- **SuricataRunner**: Core class for managing Suricata instances
- **AlertCorrelator**: Correlates alerts between Suricata and YARA
- **API Integration**: RESTful endpoints for Suricata management

## Configuration

Suricata configuration is managed through:

- `config/suricata.yaml`: Main Suricata configuration file
- `config/default_config.json`: Integration settings

Key configuration options:

```json
{
  "SURICATA_BIN": "suricata",
  "SURICATA_CONFIG": "/path/to/suricata.yaml",
  "SURICATA_RULES_DIR": "/path/to/rules",
  "SURICATA_LOG_DIR": "/path/to/logs",
  "SURICATA_AUTO_START": false,
  "SURICATA_INTERFACE": "eth0",
  "CORRELATION_ENABLED": true,
  "CORRELATION_WINDOW": 300,
  "TIME_PROXIMITY_WINDOW": 60
}
```

## Usage

### Starting the Integrated System

Use the `run_integrated.sh` script to start the complete system:

```bash
bin/run_integrated.sh --interface eth0
```

Options:
- `--read, -r FILE`: Read from PCAP file
- `--interface, -i IFACE`: Specify network interface
- `--no-zeek`: Don't start Zeek
- `--no-suricata`: Don't start Suricata
- `--no-scanner`: Don't start YARA scanner
- `--no-api`: Don't start API server

### API Endpoints

Suricata-specific API endpoints:

- `GET /suricata/status`: Get Suricata status
- `POST /suricata/start`: Start Suricata on interface
- `POST /suricata/stop`: Stop Suricata
- `POST /suricata/pcap`: Analyze PCAP file
- `GET /suricata/alerts`: Get Suricata alerts
- `POST /suricata/rules/update`: Update Suricata rules
- `POST /suricata/correlate`: Correlate alerts
- `GET /suricata/correlation`: Get correlated alerts

## Alert Correlation

The system correlates alerts between Suricata and YARA based on:

1. IP-based correlation: Matching file detections with network traffic from related IPs
2. Hash-based correlation: Matching file hashes detected by YARA with references in Suricata alerts
3. Time-proximity correlation: Associating alerts that occur within a close timeframe

Correlation confidence is calculated for each group and stored for later retrieval.

## Prerequisites

- Suricata 6.0.0+
- Zeek (latest stable)
- Python 3.8+
- YARA 4.2.0+

## Troubleshooting

- Ensure Suricata is correctly installed and in the system PATH
- Check that network interfaces are correctly specified
- Verify that Suricata has sufficient permissions to capture traffic
- Review logs in the specified log directory
