#!/bin/bash
# Run the Zeek-YARA Integration API Server
# Created: April 24, 2025
# Author: Russell Smith

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT" || { echo "Error: Could not change to project root directory"; exit 1; }

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Default values
HOST="127.0.0.1"
PORT=8000
AUTO_START=false
MULTI_THREADED=false
THREADS=4

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --host)
        HOST="$2"
        shift
        shift
        ;;
        --port)
        PORT="$2"
        shift
        shift
        ;;
        --auto-start)
        AUTO_START=true
        shift
        ;;
        --multi-threaded)
        MULTI_THREADED=true
        shift
        ;;
        --threads)
        THREADS="$2"
        shift
        shift
        ;;
        --help)
        echo "Usage: run_api.sh [OPTIONS]"
        echo "Options:"
        echo "  --host HOST               Host to listen on (default: 127.0.0.1)"
        echo "  --port PORT               Port to listen on (default: 8000)"
        echo "  --auto-start              Auto-start scanner when API starts"
        echo "  --multi-threaded          Use multi-threaded scanner"
        echo "  --threads N               Number of threads for scanner (default: 4)"
        echo "  --help                    Show this help message"
        exit 0
        ;;
        *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
    esac
done

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables for API configuration
export API_HOST="$HOST"
export API_PORT="$PORT"
export AUTO_START_SCANNER="$AUTO_START"
export MULTI_THREADED="$MULTI_THREADED"
export THREADS="$THREADS"

# Run the API server
echo "Starting Zeek-YARA Integration API Server on $HOST:$PORT"
if [ "$AUTO_START" = true ]; then
    echo "Auto-starting scanner (Multi-threaded: $MULTI_THREADED, Threads: $THREADS)"
fi

python -m api.api_server

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate 2>/dev/null || true
fi
