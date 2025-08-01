#!/bin/bash
# Zeek-YARA Integration Setup Script
# Created: April 24, 2025

# Exit on error
set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Zeek-YARA Integration Setup${NC}"
echo "---------------------------------"

# Create directory structure
echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p "$PROJECT_DIR/extracted_files"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/rules/active/ransomware"
mkdir -p "$PROJECT_DIR/rules/active/document_malware"
mkdir -p "$PROJECT_DIR/rules/active/network_behavior"
mkdir -p "$PROJECT_DIR/rules/active/evasion_techniques"
mkdir -p "$PROJECT_DIR/rules/active/malware"
mkdir -p "$PROJECT_DIR/tests"

# Make scripts executable
echo -e "${YELLOW}Making scripts executable...${NC}"
chmod +x "$PROJECT_DIR/bin/run_scanner.sh"
chmod +x "$PROJECT_DIR/bin/run_zeek.sh"
chmod +x "$PROJECT_DIR/bin/yara_scanner_cli.py"
chmod +x "$PROJECT_DIR/bin/setup.sh"

# Create virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
    source "$PROJECT_DIR/venv/bin/activate"
    
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip install --upgrade pip
    pip install yara-python watchdog python-magic
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Copy rules from old installation if available
OLD_PROJECT_DIR="$HOME/zeek_yara_test"
if [ -d "$OLD_PROJECT_DIR" ]; then
    echo -e "${YELLOW}Found existing Zeek-YARA test installation.${NC}"
    
    # Copy rules
    if [ -d "$OLD_PROJECT_DIR/rules" ]; then
        echo -e "${YELLOW}Copying YARA rules from existing installation...${NC}"
        cp -r "$OLD_PROJECT_DIR/rules"/* "$PROJECT_DIR/rules/"
    fi
    
    # Copy test EICAR file if it exists
    if [ -f "$OLD_PROJECT_DIR/test_eicar.txt" ]; then
        echo -e "${YELLOW}Copying EICAR test file...${NC}"
        cp "$OLD_PROJECT_DIR/test_eicar.txt" "$PROJECT_DIR/tests/"
    fi
fi

# Create default rules index if it doesn't exist
if [ ! -f "$PROJECT_DIR/rules/index.yar" ]; then
    echo -e "${YELLOW}Creating default rules index...${NC}"
    cat > "$PROJECT_DIR/rules/index.yar" << EOF
/*
 * Zeek-YARA Integration Rule Index
 * Created: April 24, 2025
 * 
 * This file includes all YARA rules organized by category
 */

// Ransomware detection
include "./active/ransomware/ransomware_behaviors.yar"

// Malicious document detection 
include "./active/document_malware/maldoc_techniques.yar"

// Network behavior and C2 detection
include "./active/network_behavior/c2_behaviors.yar"

// Evasion techniques detection
include "./active/evasion_techniques/anti_analysis.yar"

// Basic test rules (EICAR)
include "./active/malware/test_rules.yar"
EOF
fi

# Create default test rule if it doesn't exist
EICAR_RULE_DIR="$PROJECT_DIR/rules/active/malware"
if [ ! -f "$EICAR_RULE_DIR/test_rules.yar" ]; then
    echo -e "${YELLOW}Creating test YARA rule...${NC}"
    mkdir -p "$EICAR_RULE_DIR"
    cat > "$EICAR_RULE_DIR/test_rules.yar" << EOF
/*
 * Test YARA Rules for Zeek-YARA Integration
 * Created: April 24, 2025
 */

rule EICAR_Test_File {
   meta:
      description = "This is a test rule to identify the EICAR test file"
      author = "Security Team"
      reference = "http://www.eicar.org/86-0-Intended-use.html"
      date = "2025-04-24"
      severity = 1
   strings:
      \$eicar_string = { 58 35 4F 21 50 25 40 41 50 5B 34 5C 50 5A 58 35 43 30 5F 5F 50 45 49 43 41 52 2D 53 54 41 4E 44 41 52 44 2D 41 4E 54 49 56 49 52 55 53 2D 54 45 53 54 2D 46 49 4C 45 21 24 48 2B 48 2A }
   condition:
      \$eicar_string
}
EOF
fi

# Create a test EICAR file if it doesn't exist
if [ ! -f "$PROJECT_DIR/tests/test_eicar.txt" ]; then
    echo -e "${YELLOW}Creating EICAR test file...${NC}"
    echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > "$PROJECT_DIR/tests/test_eicar.txt"
fi

# Create placeholder rule files if they don't exist
for rule_type in "ransomware/ransomware_behaviors.yar" "document_malware/maldoc_techniques.yar" "network_behavior/c2_behaviors.yar" "evasion_techniques/anti_analysis.yar"; do
    rule_file="$PROJECT_DIR/rules/active/$rule_type"
    rule_dir=$(dirname "$rule_file")
    
    if [ ! -f "$rule_file" ]; then
        echo -e "${YELLOW}Creating placeholder rule file: $rule_type${NC}"
        mkdir -p "$rule_dir"
        rule_name=$(basename "$rule_type" .yar | tr '_' ' ' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1' | tr -d ' ')
        
        cat > "$rule_file" << EOF
/*
 * $rule_name Rules for Zeek-YARA Integration
 * Created: April 24, 2025
 * 
 * This is a placeholder file. Add your rules here or replace with actual rules.
 */

rule Example_${rule_name}_Detection {
   meta:
      description = "Example rule for ${rule_name} detection"
      author = "Security Team"
      date = "2025-04-24"
      severity = 2
   strings:
      \$example_string = "This is a placeholder rule"
   condition:
      false // Placeholder rule, will never match
}
EOF
    fi
done

# Create default configuration file
CONFIG_FILE="$PROJECT_DIR/config/default_config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Creating default configuration file...${NC}"
    cat > "$CONFIG_FILE" << EOF
{
    "EXTRACT_DIR": "${PROJECT_DIR}/extracted_files",
    "RULES_DIR": "${PROJECT_DIR}/rules",
    "RULES_INDEX": "${PROJECT_DIR}/rules/index.yar",
    "LOG_DIR": "${PROJECT_DIR}/logs",
    "LOG_FILE": "${PROJECT_DIR}/logs/yara_scan.log",
    "DB_FILE": "${PROJECT_DIR}/logs/yara_alerts.db",
    "MAX_FILE_SIZE": 20971520,
    "SCAN_INTERVAL": 10,
    "THREADS": 2,
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "%(asctime)s - %(levelname)s - %(message)s",
    "SCAN_MIME_TYPES": [],
    "SCAN_EXTENSIONS": []
}
EOF
fi

# Create a basic README.md file
README_FILE="$PROJECT_DIR/README.md"
if [ ! -f "$README_FILE" ]; then
    echo -e "${YELLOW}Creating README file...${NC}"
    cat > "$README_FILE" << EOF
# Zeek-YARA Integration

A comprehensive integration between Zeek (network monitoring) and YARA (file analysis) for enhanced malware detection.

## Overview

This project provides a modular, configurable platform that extracts files from network traffic using Zeek and scans them with YARA rules to detect malicious content. This integration enhances network security by combining behavioral analysis with signature-based file detection.

## Directory Structure

\`\`\`
zeek_yara_integration/
├── bin/               # Executable scripts
├── config/            # Configuration files
├── core/              # Core functionality
├── extracted_files/   # Files extracted by Zeek
├── logs/              # Logs and database
├── rules/             # YARA rule files
├── tests/             # Test files and utilities
├── utils/             # Utility modules
└── zeek/              # Zeek scripts
\`\`\`

## Usage

### Basic Workflow

1. Run Zeek with file extraction:
   \`\`\`bash
   bin/run_zeek.sh --interface en0
   \`\`\`

2. In a separate terminal, run the YARA scanner:
   \`\`\`bash
   bin/run_scanner.sh
   \`\`\`

### Options

- **Scanner Modes**:
  - Single-threaded: \`bin/run_scanner.sh\`
  - Multi-threaded: \`bin/run_scanner.sh --multi-threaded --threads 4\`
  - Scan a single file: \`bin/run_scanner.sh --scan-file path/to/file\`
  - Scan a directory once: \`bin/run_scanner.sh --scan-dir path/to/directory\`

- **Zeek Options**:
  - Live capture: \`bin/run_zeek.sh --interface <interface_name>\`
  - PCAP analysis: \`bin/run_zeek.sh --read path/to/capture.pcap\`

## Testing

To test the system with a known detection:

\`\`\`bash
cp tests/test_eicar.txt extracted_files/
\`\`\`

This will trigger a detection using the EICAR test file.

## Configuration

Edit \`config/default_config.json\` to customize settings, or use command-line options with \`run_scanner.sh\`.

## Components

- **Scanner**: Provides both single-threaded and multi-threaded file scanning
- **Database**: SQLite database for storing and querying alerts
- **Rules Management**: Supports categorized rules with automatic recompilation
- **Logging**: Comprehensive logging with various output formats
- **File Analysis**: File type detection and metadata extraction

## License

This project is licensed under the MIT License - see the LICENSE file for details.
EOF
fi

# Create a basic LICENSE file
LICENSE_FILE="$PROJECT_DIR/LICENSE"
if [ ! -f "$LICENSE_FILE" ]; then
    echo -e "${YELLOW}Creating LICENSE file...${NC}"
    cat > "$LICENSE_FILE" << EOF
MIT License

Copyright (c) 2025 Security Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
fi

echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "You can now run the following commands:"
echo -e "${BLUE}  bin/run_zeek.sh${NC} - Run Zeek with file extraction"
echo -e "${BLUE}  bin/run_scanner.sh${NC} - Run the YARA scanner"
echo ""
echo "Example full workflow:"
echo "  1. In one terminal: bin/run_zeek.sh --interface en0"
echo "  2. In another terminal: bin/run_scanner.sh --multi-threaded"
echo "  3. To test detection, copy tests/test_eicar.txt to extracted_files/"
echo ""
echo "For more information, see the README.md file."
