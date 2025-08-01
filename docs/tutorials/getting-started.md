# Getting Started with Zeek-YARA Integration

Welcome to your first hands-on experience with network security monitoring! This tutorial will guide you through setting up and running a basic threat detection system using Zeek, YARA, and Suricata.

## What You'll Learn

By the end of this tutorial, you will be able to:
- Set up a complete network security monitoring environment
- Extract files from network traffic using Zeek
- Scan extracted files for threats using YARA
- Understand how different security tools work together
- Analyze your first security alerts

## Prerequisites

**Knowledge Requirements:**
- Basic understanding of command line operations
- Familiarity with basic networking concepts (IP addresses, ports)
- No prior experience with security tools required

**System Requirements:**
- Ubuntu 20.04+ or macOS 10.15+ (Windows with WSL2 also supported)
- At least 4GB RAM and 10GB free disk space
- Python 3.8 or higher
- Administrative/sudo access

**Estimated Time:** 45-60 minutes

## Learning Objectives Breakdown

This tutorial is structured to build your understanding progressively:

1. **Environment Setup** (15 minutes) - Get all tools installed and configured
2. **Basic Detection** (15 minutes) - Run your first threat detection
3. **Understanding Results** (15 minutes) - Learn to interpret alerts and logs
4. **Experimentation** (15 minutes) - Try different scenarios and customizations

## Step 1: Environment Setup

### 1.1 Clone the Project

```bash
# Navigate to your preferred directory
cd ~/Downloads

# Clone the repository
git clone https://github.com/your-repo/zeek_yara_integration.git
cd zeek_yara_integration

# Verify the project structure
ls -la
```

**Expected Output:**
You should see directories like `api/`, `config/`, `core/`, `docs/`, etc.

### 1.2 Install Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import yara; print('YARA installed successfully')"
```

### 1.3 Run Setup Script

```bash
# Run the automated setup
bin/setup.sh

# Verify setup completed successfully
echo "Setup complete! Testing basic functionality..."
python -c "from core.scanner import BaseScanner; print('Scanner ready!')"
```

### What's Happening Here?

The setup script performs several important tasks:
- **Creates necessary directories** for logs and extracted files
- **Downloads sample YARA rules** for basic threat detection
- **Configures the system** with appropriate default settings
- **Verifies all components** are working correctly

If you encounter errors, check our [Troubleshooting Guide](../reference/troubleshooting.md).

## Step 2: Your First Threat Detection

### 2.1 Create a Test File

Let's start with the EICAR test file - a harmless file specifically designed for testing antivirus and security tools:

```bash
# Navigate to the extracted files directory
cd extracted_files

# Create the EICAR test file
echo 'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > eicar_test.txt

# Verify the file was created
ls -la eicar_test.txt
cat eicar_test.txt
```

### 2.2 Start the Scanner

Open a new terminal window (keeping the first one open) and start the YARA scanner:

```bash
# In the new terminal, navigate to the project directory
cd ~/Downloads/zeek_yara_integration
source venv/bin/activate

# Start the file scanner
bin/run_scanner.sh
```

**Expected Output:**
```
[INFO] Starting YARA scanner...
[INFO] Watching directory: extracted_files/
[INFO] Scanner ready and monitoring for new files
```

### 2.3 Watch the Detection

In your first terminal, check the scanner logs:

```bash
# Monitor the scan logs in real-time
tail -f logs/yara_scan.log
```

You should see output similar to:
```
[INFO] File detected: extracted_files/eicar_test.txt
[INFO] YARA match found: EICAR-Test-File
[INFO] Alert stored in database
```

### What's Happening Here?

1. **File Monitoring**: The scanner watches the `extracted_files/` directory for new files
2. **YARA Scanning**: When a file appears, it's scanned against all YARA rules
3. **Alert Generation**: Matches are logged and stored in the database
4. **Real-time Processing**: Everything happens automatically as files are detected

## Step 3: Understanding Your Results

### 3.1 Check the Database

```bash
# View all alerts in the database
sqlite3 logs/yara_alerts.db "SELECT * FROM yara_alerts;"
```

**Expected Output:**
You'll see a detailed record including:
- File path and metadata (size, type, hashes)
- YARA rule that matched (rule name, namespace)
- Timestamps and severity information

### 3.2 Analyze the Alert

Let's break down what each field means:

```bash
# Get a nicely formatted view of the latest alert
sqlite3 logs/yara_alerts.db <<EOF
.headers on
.mode column
SELECT 
    file_path,
    rule_name,
    severity,
    created_at
FROM yara_alerts 
ORDER BY created_at DESC 
LIMIT 1;
EOF
```

### 3.3 Explore the Logs

```bash
# View the complete scan log
cat logs/yara_scan.log

# Look for specific events
grep "YARA match" logs/yara_scan.log
grep "ERROR" logs/yara_scan.log
```

### What This Tells Us

The EICAR detection demonstrates several key concepts:
- **Signature-based detection**: YARA rules contain signatures that match known threats
- **File analysis**: Every file is analyzed for suspicious patterns
- **Alert correlation**: Information is stored for later analysis and correlation
- **Automated response**: The system can automatically process threats as they're detected

## Step 4: Experimentation and Exploration

### 4.1 Try Different File Types

Create different types of files to see how the scanner responds:

```bash
# Create a normal text file
echo "This is a normal document" > extracted_files/normal_file.txt

# Create a file with suspicious content
echo "This file contains the word virus in it" > extracted_files/suspicious_file.txt

# Create a binary file
dd if=/dev/random of=extracted_files/random_binary.bin bs=1024 count=1
```

Watch the logs to see which files trigger detections and which don't.

### 4.2 Explore YARA Rules

```bash
# Look at the YARA rules being used
ls rules/active/malware/
cat rules/active/malware/eicar.yar
```

### 4.3 Try the API

Start the API server to explore programmatic access:

```bash
# In a new terminal
bin/run_api.py

# In another terminal, test the API
curl http://localhost:8000/alerts
curl http://localhost:8000/scanner/status
```

### What You're Learning

Through experimentation, you're discovering:
- **Different file types** trigger different analysis methods
- **YARA rules** define what constitutes suspicious content
- **APIs** allow programmatic access to the system
- **Real-time monitoring** enables immediate threat response

## Troubleshooting Common Issues

### Scanner Won't Start
**Symptoms**: Error messages when running `bin/run_scanner.sh`

**Solution**:
```bash
# Check Python dependencies
pip install -r requirements.txt

# Verify configuration
cat config/default_config.json

# Check file permissions
ls -la bin/run_scanner.sh
chmod +x bin/run_scanner.sh
```

### No Detections Appearing
**Symptoms**: Files created but no alerts generated

**Solution**:
```bash
# Verify YARA rules exist
ls rules/active/malware/

# Check scanner logs for errors
cat logs/yara_scan.log | grep ERROR

# Manually test YARA
yara rules/active/malware/eicar.yar extracted_files/eicar_test.txt
```

### Database Issues
**Symptoms**: SQLite errors or missing alerts

**Solution**:
```bash
# Check database exists and is readable
ls -la logs/yara_alerts.db

# Verify database schema
sqlite3 logs/yara_alerts.db ".schema"

# Reset database if needed
rm logs/yara_alerts.db
python -c "from core.database import DatabaseManager; db = DatabaseManager(); db.create_tables()"
```

## Summary and Next Steps

Congratulations! You've successfully:
- ✅ Set up a complete network security monitoring environment
- ✅ Detected your first threat using YARA rules
- ✅ Understood how file monitoring and scanning work
- ✅ Explored the alert database and logging system
- ✅ Experimented with different file types and scenarios

### What You've Learned

**Technical Skills:**
- How to install and configure security tools
- Basic threat detection using signature-based methods
- Log analysis and database querying
- API interaction and automation concepts

**Security Concepts:**
- File-based threat detection
- Automated security monitoring
- Alert generation and correlation
- Real-time security analysis

### Next Steps

Now that you have the basics working, you can:

1. **Learn About Network Traffic Analysis**
   - [Tutorial: Zeek Network Monitoring](zeek-basics.md)
   - Capture and analyze real network traffic
   - Extract files from network streams

2. **Create Custom YARA Rules**
   - [Tutorial: Writing YARA Rules](yara-basics.md)
   - Detect specific threats relevant to your environment
   - Understand rule syntax and testing

3. **Add Network-Based Detection**
   - [Tutorial: Suricata Integration](suricata-basics.md)
   - Monitor network traffic for suspicious activity
   - Correlate file and network alerts

4. **Explore Advanced Features**
   - [Guide: Performance Optimization](../guides/performance-optimization.md)
   - [Guide: Custom Integration](../guides/advanced-integration.md)
   - [Reference: API Documentation](../reference/api-reference.md)

### Self-Assessment Questions

Test your understanding:

1. **What happens when a file is placed in the `extracted_files/` directory?**
2. **Where are YARA detection alerts stored?**
3. **How would you add a new YARA rule to the system?**
4. **What's the difference between the log files and the database?**
5. **How could you automate responses to specific types of threats?**

### Get Help and Stay Connected

- **Questions?** Ask in our [Community Discussions](https://github.com/your-repo/discussions)
- **Found a bug?** [Report it](https://github.com/your-repo/issues)
- **Want to contribute?** See our [Contributing Guide](../../CONTRIBUTING.md)

### Additional Resources

- [Network Security Monitoring Basics](../explanations/network-security-basics.md)
- [Understanding YARA Rules](../explanations/yara-concepts.md)
- [Security Tool Integration Patterns](../explanations/integration-patterns.md)
- [Recommended Reading List](../reference/reading-list.md)

---

**Well done!** You've taken your first steps into network security monitoring. The skills you've learned here form the foundation for more advanced security analysis and threat detection techniques.

*Next: [Understanding Zeek Network Analysis](zeek-basics.md)*