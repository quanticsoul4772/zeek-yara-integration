# Zeek-YARA Integration Test Workflow

## Prerequisite Verification

### 1. Check System Requirements

Verify installed dependencies:
```bash
which python3
python3 --version
which zeek
zeek --version
which sqlite3
sqlite3 --version
```

### 2. Project Structure Validation

Expected Directory Structure:
```
zeek_yara_integration/
├── bin/
│   ├── run_zeek.sh
│   ├── run_scanner.sh
│   └── yara_scanner_cli.py
├── config/
│   └── default_config.json
├── extracted_files/
├── logs/
│   ├── yara_scan.log
│   └── yara_alerts.db
├── rules/
│   └── active/
│       └── malware/
│           └── test_rules.yar
└── tests/
    └── test_eicar.txt
```

### 3. Configuration Verification

1. Check default configuration:
```bash
cat config/default_config.json
```

2. Verify YARA test rules:
```bash
cat rules/active/malware/test_rules.yar
```

## Test Workflow

### Preparation

1. Activate Virtual Environment:
```bash
source venv/bin/activate
```

2. Clean Previous Test Artifacts:
```bash
# Remove previous log files
rm -f logs/yara_scan.log
rm -f logs/yara_alerts.db

# Clear extracted files directory
rm -rf extracted_files/*
```

### Test Scenarios

#### Scenario 1: EICAR Test File Detection

1. Copy EICAR test file:
```bash
cp tests/test_eicar.txt extracted_files/test_eicar.txt
```

2. Start Zeek (Terminal 1):
```bash
bin/run_zeek.sh
```

3. Start YARA Scanner (Terminal 2):
```bash
bin/run_scanner.sh
```

4. Verification Steps:

a. Check Log File:
```bash
tail -n 50 logs/yara_scan.log
```

b. Check SQLite Database:
```bash
sqlite3 logs/yara_alerts.db "SELECT * FROM yara_alerts;"
```

#### Scenario 2: Suspicious Executable Detection

1. Prepare Test Executable:
```bash
# Create a sample executable with suspicious strings
echo -e '#include <stdio.h>\nint main() {\n    system("cmd.exe");\n    return 0;\n}' > test_suspicious.c
gcc test_suspicious.c -o extracted_files/test_suspicious
```

2. Repeat scanning process from Scenario 1

#### Scenario 3: Large File Handling

1. Create Large Test File:
```bash
# Create a file larger than MAX_FILE_SIZE (20MB)
dd if=/dev/zero of=extracted_files/large_file.bin bs=1M count=30
```

2. Repeat scanning process from Scenario 1

### Log and Database Analysis

1. Comprehensive Log Review:
```bash
# Full log contents
cat logs/yara_scan.log

# Errors and warnings
grep -E "ERROR|WARNING" logs/yara_scan.log

# Matched files
grep "YARA match" logs/yara_scan.log
```

2. Database Comprehensive Query:
```bash
# Detailed database information
sqlite3 logs/yara_alerts.db <<EOF
.headers on
.mode column
SELECT * FROM yara_alerts;
EOF
```

## Troubleshooting Guide

### Common Issues

1. No files being detected
   - Verify YARA rules in rules/active/malware/test_rules.yar
   - Check log levels in config/default_config.json
   - Ensure files are in extracted_files/

2. Scanner not starting
   - Verify virtual environment is activated
   - Check Python and dependency versions
   - Inspect logs/yara_scan.log for startup errors

3. No database entries
   - Confirm SQLite is installed
   - Check file permissions on logs directory
   - Verify scanner has write access

## Cleanup

After testing:
```bash
# Deactivate virtual environment
deactivate

# Optional: clean test artifacts
rm extracted_files/test_*
rm logs/yara_scan.log
rm logs/yara_alerts.db
```

## Notes

- Always run in the project root directory
- Test files are deliberately simple to demonstrate detection mechanism
- Actual malware detection requires comprehensive, updated YARA rules
