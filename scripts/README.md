# Zeek-YARA Cleanup Tools

This directory contains scripts for managing disk space by cleaning up extracted files after Zeek-YARA integration tests.

## Scripts Overview

- `cleanup_extracted.sh`: Standalone bash script that removes extracted files older than a configurable time threshold
- `post_test_cleanup.py`: Python wrapper that verifies the database before cleanup and provides more options
- `install_cleanup_cron.sh`: Helper script to install an hourly cron job for regular cleanup
- `run_with_cleanup.sh`: Wrapper script in the main directory that runs tests followed by cleanup

## Usage Options

### 1. Run tests with automatic cleanup

```
cd /Users/russellsmith/zeek_yara_integration
./run_with_cleanup.sh [any test arguments]
```

This will run your main test script and automatically clean up extracted files afterward.

### 2. Manual cleanup after tests

```
cd /Users/russellsmith/zeek_yara_integration
./scripts/cleanup_extracted.sh
```

This will remove extracted files older than 60 minutes (configurable in the script).

### 3. Automated regular cleanup

```
cd /Users/russellsmith/zeek_yara_integration
./scripts/install_cleanup_cron.sh
```

This will install a cron job that runs every hour to clean up old extracted files.

### 4. Advanced cleanup with database verification

```
cd /Users/russellsmith/zeek_yara_integration
python3 ./scripts/post_test_cleanup.py --verify-db
```

Options:
- `--verify-db`: Check the database integrity before cleanup
- `--db-path PATH`: Specify a custom database path
- `--force`: Force cleanup even if verification fails
- `--delay SEC`: Wait specified seconds before cleaning up

## Configuration

You can modify the following settings in the scripts:

- In `cleanup_extracted.sh`:
  - `MAIN_EXTRACT_DIR`: Path to the main extraction directory
  - `TEST_EXTRACT_DIR`: Path to the test extraction directory
  - `PRESERVE_PATTERNS`: Files to preserve (comma-separated patterns)
  - `AGE_THRESHOLD`: Age in minutes of files to delete (default: 60)

- In `post_test_cleanup.py`:
  - Database path via the `--db-path` argument

## Log Files

All scripts generate logs to help with troubleshooting:

- Main cleanup log: `/Users/russellsmith/zeek_yara_integration/logs/cleanup_log.txt`
- Python wrapper log: `/Users/russellsmith/zeek_yara_integration/logs/post_test_cleanup.log`
- Run with cleanup log: `/Users/russellsmith/zeek_yara_integration/logs/run_*.log`
