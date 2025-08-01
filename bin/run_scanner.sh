#!/bin/bash
# Run the YARA scanner with virtual environment
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

echo -e "${BLUE}Zeek-YARA Integration Scanner${NC}"
echo "----------------------------------------"

# Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"
    
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip install --upgrade pip
    pip install yara-python watchdog python-magic
else
    echo -e "${GREEN}Activating existing virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"
fi

# Check if required directories exist
for dir in "extracted_files" "logs" "rules"; do
    if [ ! -d "$PROJECT_DIR/$dir" ]; then
        echo -e "${YELLOW}Creating $dir directory...${NC}"
        mkdir -p "$PROJECT_DIR/$dir"
    fi
done

# Copy rules from old location if needed and the old location exists
OLD_RULES_DIR="$HOME/zeek_yara_test/rules"
if [ -d "$OLD_RULES_DIR" ] && [ ! -f "$PROJECT_DIR/rules/index.yar" ]; then
    echo -e "${YELLOW}Copying rules from old location...${NC}"
    cp -r "$OLD_RULES_DIR"/* "$PROJECT_DIR/rules/"
fi

# Make CLI script executable
chmod +x "$SCRIPT_DIR/yara_scanner_cli.py"

# Determine whether to use multi-threaded scanner
MULTI_THREADED=""
THREADS="2"
for arg in "$@"; do
    if [[ "$arg" == "--multi-threaded" || "$arg" == "-mt" ]]; then
        MULTI_THREADED="--multi-threaded"
    fi
    if [[ "$arg" == "--threads="* || "$arg" == "-t="* ]]; then
        THREADS="${arg#*=}"
    fi
done

# If no specific mode was specified, default to multi-threaded
if [[ "$@" != *"--scan-file"* && "$@" != *"-f"* && "$@" != *"--scan-dir"* && "$@" != *"-s"* && "$MULTI_THREADED" == "" ]]; then
    MULTI_THREADED="--multi-threaded"
    echo -e "${GREEN}Using default multi-threaded scanner with $THREADS threads${NC}"
fi

# Run the scanner with all provided arguments
echo -e "${GREEN}Starting YARA scanner...${NC}"
"$SCRIPT_DIR/yara_scanner_cli.py" $MULTI_THREADED --threads "$THREADS" "$@"
