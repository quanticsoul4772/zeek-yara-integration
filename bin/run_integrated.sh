#!/bin/bash
# run_integrated.sh
# Purpose: Run the integrated Zeek-YARA-Suricata monitoring system
# Author: Security Team
# Date: April 25, 2025

# Configuration
PROJECT_DIR="/Users/russellsmith/zeek_yara_integration"
LOG_DIR="$PROJECT_DIR/logs"
SURICATA_LOG_DIR="$PROJECT_DIR/logs/suricata"
CONFIG_DIR="$PROJECT_DIR/config"
EXTRACT_DIR="$PROJECT_DIR/extracted_files"
SURICATA_CONFIG="$CONFIG_DIR/suricata.yaml"

# Default interface (can be overridden by command line)
DEFAULT_INTERFACE="en0"

# Default PCAP file (for reading mode)
DEFAULT_PCAP=""

# Set default mode
MODE="live"

# Default behavior flags
START_ZEEK=true
START_SURICATA=true
START_SCANNER=true
START_API=true

# Process command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    
    case $key in
        # Set to read mode with specified PCAP file
        --read|-r)
            MODE="read"
            DEFAULT_PCAP="$2"
            shift
            shift
            ;;
        # Set network interface
        --interface|-i)
            DEFAULT_INTERFACE="$2"
            shift
            shift
            ;;
        # Control which components to start
        --no-zeek)
            START_ZEEK=false
            shift
            ;;
        --no-suricata)
            START_SURICATA=false
            shift
            ;;
        --no-scanner)
            START_SCANNER=false
            shift
            ;;
        --no-api)
            START_API=false
            shift
            ;;
        # Help option
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --read, -r FILE        Read packets from PCAP file"
            echo "  --interface, -i IFACE  Use specified network interface"
            echo "  --no-zeek              Don't start Zeek"
            echo "  --no-suricata          Don't start Suricata"
            echo "  --no-scanner           Don't start YARA scanner"
            echo "  --no-api               Don't start API server"
            echo "  --help, -h             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $key"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Make sure required directories exist
mkdir -p "$LOG_DIR"
mkdir -p "$SURICATA_LOG_DIR"
mkdir -p "$EXTRACT_DIR"

# Function to check if a process is running
is_running() {
    ps -ef | grep -v grep | grep -q "$1"
    return $?
}

# Function to check component prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check for Zeek
    if $START_ZEEK; then
        if ! command -v zeek &> /dev/null; then
            echo "ERROR: Zeek not found. Please install Zeek and try again."
            exit 1
        fi
        echo "✓ Zeek is installed"
    fi
    
    # Check for Suricata
    if $START_SURICATA; then
        if ! command -v suricata &> /dev/null; then
            echo "ERROR: Suricata not found. Please install Suricata and try again."
            exit 1
        fi
        echo "✓ Suricata is installed"
    fi
    
    # Check for Python environment
    if $START_SCANNER || $START_API; then
        if [[ ! -d "$PROJECT_DIR/venv" ]]; then
            echo "ERROR: Python virtual environment not found. Please set up the environment first."
            exit 1
        fi
        echo "✓ Python environment exists"
    fi
    
    # Check for PCAP file in read mode
    if [[ "$MODE" == "read" ]]; then
        if [[ ! -f "$DEFAULT_PCAP" ]]; then
            echo "ERROR: PCAP file not found: $DEFAULT_PCAP"
            exit 1
        fi
        echo "✓ PCAP file is valid: $DEFAULT_PCAP"
    fi
    
    # Check for interface in live mode
    if [[ "$MODE" == "live" ]]; then
        if ! ifconfig "$DEFAULT_INTERFACE" &> /dev/null; then
            echo "ERROR: Interface not found: $DEFAULT_INTERFACE"
            exit 1
        fi
        echo "✓ Network interface is valid: $DEFAULT_INTERFACE"
    fi
    
    echo "Prerequisites check completed successfully"
}

# Function to start Zeek
start_zeek() {
    echo "Starting Zeek..."
    
    # Set Zeek options based on mode
    if [[ "$MODE" == "read" ]]; then
        # Read from PCAP file
        echo "Running Zeek in read mode with PCAP file: $DEFAULT_PCAP"
        cd "$PROJECT_DIR"
        zeek -r "$DEFAULT_PCAP" "$PROJECT_DIR/zeek/extract_files.zeek" &
        ZEEK_PID=$!
    else
        # Live traffic monitoring
        echo "Running Zeek in live mode on interface: $DEFAULT_INTERFACE"
        cd "$PROJECT_DIR"
        zeek -i "$DEFAULT_INTERFACE" "$PROJECT_DIR/zeek/extract_files.zeek" &
        ZEEK_PID=$!
    fi
    
    # Check if Zeek started successfully
    sleep 2
    if ps -p $ZEEK_PID > /dev/null; then
        echo "✓ Zeek started successfully (PID: $ZEEK_PID)"
    else
        echo "ERROR: Failed to start Zeek"
        exit 1
    fi
}

# Function to start Suricata
start_suricata() {
    echo "Starting Suricata..."
    
    # Set Suricata options based on mode
    if [[ "$MODE" == "read" ]]; then
        # Read from PCAP file
        echo "Running Suricata in read mode with PCAP file: $DEFAULT_PCAP"
        suricata -c "$SURICATA_CONFIG" -r "$DEFAULT_PCAP" -l "$SURICATA_LOG_DIR" &
        SURICATA_PID=$!
    else
        # Live traffic monitoring
        echo "Running Suricata in live mode on interface: $DEFAULT_INTERFACE"
        suricata -c "$SURICATA_CONFIG" -i "$DEFAULT_INTERFACE" -l "$SURICATA_LOG_DIR" &
        SURICATA_PID=$!
    fi
    
    # Check if Suricata started successfully
    sleep 2
    if ps -p $SURICATA_PID > /dev/null; then
        echo "✓ Suricata started successfully (PID: $SURICATA_PID)"
    else
        echo "ERROR: Failed to start Suricata"
        exit 1
    fi
}

# Function to start YARA scanner
start_scanner() {
    echo "Starting YARA scanner..."
    
    # Activate virtual environment
    source "$PROJECT_DIR/venv/bin/activate"
    
    # Start scanner in background
    cd "$PROJECT_DIR"
    python bin/run_scanner.py --multi-threaded &
    SCANNER_PID=$!
    
    # Check if scanner started successfully
    sleep 2
    if ps -p $SCANNER_PID > /dev/null; then
        echo "✓ YARA scanner started successfully (PID: $SCANNER_PID)"
    else
        echo "ERROR: Failed to start YARA scanner"
        exit 1
    fi
}

# Function to start API server
start_api() {
    echo "Starting API server..."
    
    # Activate virtual environment
    source "$PROJECT_DIR/venv/bin/activate"
    
    # Start API server in background
    cd "$PROJECT_DIR"
    python bin/run_api.py &
    API_PID=$!
    
    # Check if API server started successfully
    sleep 3
    if ps -p $API_PID > /dev/null; then
        echo "✓ API server started successfully (PID: $API_PID)"
        echo "API server is running at http://127.0.0.1:8000"
    else
        echo "ERROR: Failed to start API server"
        exit 1
    fi
}

# Function to handle cleanup when script exits
cleanup() {
    echo "Shutting down..."
    
    # Kill processes if they exist
    if [[ -n "$ZEEK_PID" ]] && ps -p $ZEEK_PID > /dev/null; then
        echo "Stopping Zeek (PID: $ZEEK_PID)..."
        kill $ZEEK_PID
    fi
    
    if [[ -n "$SURICATA_PID" ]] && ps -p $SURICATA_PID > /dev/null; then
        echo "Stopping Suricata (PID: $SURICATA_PID)..."
        kill $SURICATA_PID
    fi
    
    if [[ -n "$SCANNER_PID" ]] && ps -p $SCANNER_PID > /dev/null; then
        echo "Stopping YARA scanner (PID: $SCANNER_PID)..."
        kill $SCANNER_PID
    fi
    
    if [[ -n "$API_PID" ]] && ps -p $API_PID > /dev/null; then
        echo "Stopping API server (PID: $API_PID)..."
        kill $API_PID
    fi
    
    echo "Cleanup complete"
}

# Register cleanup function to run on exit
trap cleanup EXIT

# Main execution
echo "Starting Zeek-YARA-Suricata Integration System"
echo "Mode: $MODE"
echo "Interface: $DEFAULT_INTERFACE"
if [[ "$MODE" == "read" ]]; then
    echo "PCAP file: $DEFAULT_PCAP"
fi

# Check prerequisites
check_prerequisites

# Start components based on user preferences
if $START_ZEEK; then
    start_zeek
fi

if $START_SURICATA; then
    start_suricata
fi

if $START_SCANNER; then
    start_scanner
fi

if $START_API; then
    start_api
fi

echo "All components started successfully"
echo "Press Ctrl+C to stop"

# Keep script running until user interrupts
while true; do
    sleep 10
    
    # Check if processes are still running
    if $START_ZEEK && [[ -n "$ZEEK_PID" ]] && ! ps -p $ZEEK_PID > /dev/null; then
        echo "WARNING: Zeek process has died. Restarting..."
        start_zeek
    fi
    
    if $START_SURICATA && [[ -n "$SURICATA_PID" ]] && ! ps -p $SURICATA_PID > /dev/null; then
        echo "WARNING: Suricata process has died. Restarting..."
        start_suricata
    fi
    
    if $START_SCANNER && [[ -n "$SCANNER_PID" ]] && ! ps -p $SCANNER_PID > /dev/null; then
        echo "WARNING: YARA scanner process has died. Restarting..."
        start_scanner
    fi
    
    if $START_API && [[ -n "$API_PID" ]] && ! ps -p $API_PID > /dev/null; then
        echo "WARNING: API server process has died. Restarting..."
        start_api
    fi
done
