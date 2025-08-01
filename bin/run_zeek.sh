#!/bin/bash
# Run Zeek with File Extraction for YARA Scanner
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

echo -e "${BLUE}Zeek File Extraction for YARA Integration${NC}"
echo "-------------------------------------------"

# Ensure extracted_files directory exists
EXTRACT_DIR="$PROJECT_DIR/extracted_files"
if [ ! -d "$EXTRACT_DIR" ]; then
    echo -e "${YELLOW}Creating extracted_files directory...${NC}"
    mkdir -p "$EXTRACT_DIR"
fi

# Check if Zeek is installed
if ! command -v zeek &> /dev/null; then
    echo -e "${RED}Error: Zeek is not installed or not in PATH${NC}"
    echo "Please install Zeek before running this script."
    exit 1
fi

# Check if a network interface is specified
INTERFACE=""
PCAP_FILE=""
LIVE_MODE=true

# Process arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--interface)
            INTERFACE="$2"
            shift 2
            ;;
        -r|--read)
            PCAP_FILE="$2"
            LIVE_MODE=false
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--interface|-i INTERFACE] [--read|-r PCAP_FILE]"
            exit 1
            ;;
    esac
done

# If no interface specified in live mode, try to detect it
if [ "$LIVE_MODE" = true ] && [ -z "$INTERFACE" ]; then
    echo -e "${YELLOW}No interface specified, attempting to detect...${NC}"
    
    # For macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Try to get the active interface (usually en0 for WiFi, en1 for Ethernet)
        ACTIVE_IFACES=$(netstat -rn | grep default | awk '{print $NF}' | sort | uniq)
        for iface in $ACTIVE_IFACES; do
            INTERFACE="$iface"
            echo -e "${GREEN}Detected active interface: $INTERFACE${NC}"
            break
        done
    else
        # For Linux
        ACTIVE_IFACES=$(ip route | grep default | awk '{print $5}' | sort | uniq)
        for iface in $ACTIVE_IFACES; do
            INTERFACE="$iface"
            echo -e "${GREEN}Detected active interface: $INTERFACE${NC}"
            break
        done
    fi
    
    if [ -z "$INTERFACE" ]; then
        echo -e "${RED}Could not detect active network interface.${NC}"
        echo "Please specify using --interface option."
        exit 1
    fi
fi

# Run Zeek with appropriate options
if [ "$LIVE_MODE" = true ]; then
    echo -e "${GREEN}Starting Zeek file extraction on interface: $INTERFACE${NC}"
    echo "Press Ctrl+C to stop."
    
    # Run Zeek with file extraction in live mode
    zeek -i "$INTERFACE" "$PROJECT_DIR/zeek/extract_files.zeek"
else
    echo -e "${GREEN}Processing PCAP file: $PCAP_FILE${NC}"
    
    # Check if PCAP file exists
    if [ ! -f "$PCAP_FILE" ]; then
        echo -e "${RED}Error: PCAP file not found: $PCAP_FILE${NC}"
        exit 1
    fi
    
    # Run Zeek with file extraction on PCAP file
    zeek -r "$PCAP_FILE" "$PROJECT_DIR/zeek/extract_files.zeek"
    
    echo -e "${GREEN}PCAP processing complete. Extracted files saved to: $EXTRACT_DIR${NC}"
fi
