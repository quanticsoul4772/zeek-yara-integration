# Quick Demo: EICAR Test File Detection

This 5-minute demonstration shows how the Zeek-YARA Integration platform detects malicious files using the standard EICAR test file.

## What This Demo Shows

- Real-time file monitoring and scanning
- YARA rule-based threat detection
- Alert generation and storage
- Basic log analysis

## Prerequisites

- Project installed and set up (see [Getting Started](../../tutorials/getting-started.md))
- 5 minutes of time
- Basic command line familiarity

## Demo Steps

### 1. Start the Scanner (1 minute)

```bash
# Navigate to project directory
cd zeek_yara_integration
source venv/bin/activate

# Start the YARA scanner in background
bin/run_scanner.sh &

# Verify it's running
tail -n 5 logs/yara_scan.log
```

### 2. Create EICAR Test File (1 minute)

```bash
# Create the EICAR test file
echo 'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > extracted_files/eicar_demo.txt

# Verify file creation
ls -la extracted_files/eicar_demo.txt
```

### 3. Watch Detection Happen (1 minute)

```bash
# Monitor logs in real-time
tail -f logs/yara_scan.log

# You should see:
# [INFO] File detected: extracted_files/eicar_demo.txt
# [INFO] YARA match found: EICAR-Test-File
# [INFO] Alert stored in database
```

### 4. Check Results (2 minutes)

```bash
# View the alert in the database
sqlite3 logs/yara_alerts.db "SELECT file_path, rule_name, severity, created_at FROM yara_alerts WHERE file_path LIKE '%eicar_demo%';"

# Check file metadata
sqlite3 logs/yara_alerts.db "SELECT file_size, file_type, md5_hash FROM yara_alerts WHERE file_path LIKE '%eicar_demo%';"
```

## What You Just Learned

**Technical Concepts:**
- File system monitoring detects new files automatically
- YARA rules scan files for known threat signatures
- Alerts are stored with comprehensive metadata
- Real-time processing enables immediate threat response

**Security Principles:**
- Signature-based detection identifies known threats
- File analysis provides forensic information
- Automated monitoring scales beyond human capability
- Alert correlation enables pattern analysis

## Next Steps

- [Full Getting Started Tutorial](../../tutorials/getting-started.md)
- [Understanding YARA Rules](../../tutorials/yara-basics.md)
- [Network Traffic Analysis](../../tutorials/zeek-basics.md)

## Cleanup

```bash
# Stop the scanner
pkill -f "python.*scanner"

# Remove demo file
rm extracted_files/eicar_demo.txt

# Optional: Clear alerts
sqlite3 logs/yara_alerts.db "DELETE FROM yara_alerts WHERE file_path LIKE '%eicar_demo%';"
```

---

**Demo Complete!** You've seen how automated threat detection works in practice. This same process scales to handle thousands of files and network connections in real-world environments.