#!/bin/bash
# cleanup_extracted.sh
# Purpose: Clean up extracted files after test runs while preserving test samples
# Author: Russell Smith
# Date: April 24, 2025

# Configuration - modify these variables as needed
MAIN_EXTRACT_DIR="/Users/russellsmith/zeek_yara_integration/extracted_files"
TEST_EXTRACT_DIR="/Users/russellsmith/zeek_yara_test/extracted_files"
LOG_FILE="/Users/russellsmith/zeek_yara_integration/logs/cleanup_log.txt"
# Files to preserve (comma-separated list of patterns)
PRESERVE_PATTERNS="test_eicar"
# Age of files to delete (in minutes)
AGE_THRESHOLD=60

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
  echo "$1"
}

log "Starting cleanup process..."

# Convert preserve patterns to find arguments
if [ -n "$PRESERVE_PATTERNS" ]; then
  PRESERVE_ARGS=()
  IFS=',' read -ra PATTERNS <<< "$PRESERVE_PATTERNS"
  for pattern in "${PATTERNS[@]}"; do
    PRESERVE_ARGS+=("-not" "-name" "*${pattern}*")
  done
fi

# Remove files from main extract directory
if [ -d "$MAIN_EXTRACT_DIR" ]; then
  log "Cleaning $MAIN_EXTRACT_DIR"
  file_count=$(find "$MAIN_EXTRACT_DIR" -type f -mmin +$AGE_THRESHOLD "${PRESERVE_ARGS[@]}" | wc -l)
  log "Found $file_count files older than $AGE_THRESHOLD minutes to delete"
  
  # Delete files
  find "$MAIN_EXTRACT_DIR" -type f -mmin +$AGE_THRESHOLD "${PRESERVE_ARGS[@]}" -delete
  log "Deleted files from $MAIN_EXTRACT_DIR"
else
  log "Warning: $MAIN_EXTRACT_DIR does not exist"
fi

# Remove files from test extract directory
if [ -d "$TEST_EXTRACT_DIR" ]; then
  log "Cleaning $TEST_EXTRACT_DIR"
  file_count=$(find "$TEST_EXTRACT_DIR" -type f -mmin +$AGE_THRESHOLD "${PRESERVE_ARGS[@]}" | wc -l)
  log "Found $file_count files older than $AGE_THRESHOLD minutes to delete"
  
  # Delete files
  find "$TEST_EXTRACT_DIR" -type f -mmin +$AGE_THRESHOLD "${PRESERVE_ARGS[@]}" -delete
  log "Deleted files from $TEST_EXTRACT_DIR"
else
  log "Warning: $TEST_EXTRACT_DIR does not exist"
fi

log "Cleanup process completed"
exit 0
