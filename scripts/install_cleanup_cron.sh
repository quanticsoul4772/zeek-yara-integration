#!/bin/bash
# install_cleanup_cron.sh
# Purpose: Install a cron job to regularly clean up extracted files
# Author: Russell Smith
# Date: April 24, 2025

PROJECT_DIR="/Users/russellsmith/zeek_yara_integration"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
CLEANUP_SCRIPT="$SCRIPTS_DIR/cleanup_extracted.sh"
TEMP_CRON_FILE="/tmp/zeek_yara_cron"

# Ensure the cleanup script exists and is executable
if [ ! -f "$CLEANUP_SCRIPT" ]; then
  echo "ERROR: Cleanup script not found at $CLEANUP_SCRIPT"
  exit 1
fi

chmod +x "$CLEANUP_SCRIPT"

# Define the cron job - runs every hour
CRON_JOB="0 * * * * $CLEANUP_SCRIPT > /dev/null 2>&1"

# Check if the cron job already exists
(crontab -l 2>/dev/null | grep -v "$CLEANUP_SCRIPT") > "$TEMP_CRON_FILE"
echo "$CRON_JOB" >> "$TEMP_CRON_FILE"

# Install the cron job
if crontab "$TEMP_CRON_FILE"; then
  echo "Cron job installed successfully. Extracted files will be cleaned up hourly."
  echo "To view installed cron jobs, run: crontab -l"
else
  echo "Failed to install cron job."
  exit 1
fi

# Clean up the temporary file
rm -f "$TEMP_CRON_FILE"
exit 0
