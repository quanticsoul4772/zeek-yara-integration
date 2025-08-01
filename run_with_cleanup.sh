#!/bin/bash
# run_with_cleanup.sh
# Purpose: Run Zeek-YARA integration test with automatic cleanup
# Author: Russell Smith
# Date: April 24, 2025

# Configuration
PROJECT_DIR="/Users/russellsmith/zeek_yara_integration"
LOG_DIR="$PROJECT_DIR/logs"
SCRIPTS_DIR="$PROJECT_DIR/scripts"

# Create necessary directories
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"

# Log function
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if main script exists
MAIN_SCRIPT="$PROJECT_DIR/run_test.sh"
if [ ! -f "$MAIN_SCRIPT" ]; then
  log "ERROR: Main test script not found at $MAIN_SCRIPT"
  log "Please specify the correct path to your main test script"
  exit 1
fi

# Run the main test
log "Starting Zeek-YARA integration test..."
bash "$MAIN_SCRIPT" "$@" 2>&1 | tee -a "$LOG_FILE"
TEST_EXIT_CODE=${PIPESTATUS[0]}

if [ $TEST_EXIT_CODE -eq 0 ]; then
  log "Test completed successfully"
else
  log "Test failed with exit code $TEST_EXIT_CODE"
fi

# Run cleanup
log "Running post-test cleanup..."
python3 "$SCRIPTS_DIR/post_test_cleanup.py" --verify-db --delay 5 2>&1 | tee -a "$LOG_FILE"
CLEANUP_EXIT_CODE=${PIPESTATUS[0]}

if [ $CLEANUP_EXIT_CODE -eq 0 ]; then
  log "Cleanup completed successfully"
else
  log "Cleanup failed with exit code $CLEANUP_EXIT_CODE"
fi

log "All operations completed"

# Return the test exit code, not the cleanup code
# This ensures that build systems/CI tools will correctly detect test failures
exit $TEST_EXIT_CODE
