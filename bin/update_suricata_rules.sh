#!/bin/bash
# update_suricata_rules.sh
# Purpose: Update Suricata rules from online sources
# Author: Security Team
# Date: April 25, 2025

# Configuration
PROJECT_DIR="/Users/russellsmith/zeek_yara_integration"
RULES_DIR="$PROJECT_DIR/rules/suricata"
CONFIG_DIR="$PROJECT_DIR/config"
TEMP_DIR="$PROJECT_DIR/rules/temp"

# Create directories if they don't exist
mkdir -p "$RULES_DIR"
mkdir -p "$TEMP_DIR"

# Function to download and extract rules
download_rules() {
    local name=$1
    local url=$2
    local extract_path=$3
    
    echo "Downloading $name rules..."
    curl -s -L -o "$TEMP_DIR/$name.tar.gz" "$url"
    
    if [ $? -eq 0 ]; then
        echo "Extracting $name rules..."
        tar -xzf "$TEMP_DIR/$name.tar.gz" -C "$extract_path"
        
        if [ $? -eq 0 ]; then
            echo "Successfully updated $name rules"
            return 0
        else
            echo "Error extracting $name rules"
            return 1
        fi
    else
        echo "Error downloading $name rules"
        return 1
    fi
}

# Download Emerging Threats Open rules
download_emerging_threats() {
    local et_url="https://rules.emergingthreats.net/open/suricata-5.0/emerging.rules.tar.gz"
    local et_extract_path="$RULES_DIR/et_rules"
    
    mkdir -p "$et_extract_path"
    download_rules "et" "$et_url" "$et_extract_path"
    
    # Copy rules to main rules directory
    if [ $? -eq 0 ]; then
        echo "Copying ET rules to main rules directory..."
        cp "$et_extract_path"/*.rules "$RULES_DIR"
        return 0
    else
        return 1
    fi
}

# Download and extract OISF Suricata rules
download_oisf_rules() {
    local oisf_url="https://download.oisf.net/suricata/rules/suricata-latest.tar.gz"
    local oisf_extract_path="$RULES_DIR/oisf_rules"
    
    mkdir -p "$oisf_extract_path"
    download_rules "oisf" "$oisf_url" "$oisf_extract_path"
    
    # Copy rules to main rules directory
    if [ $? -eq 0 ]; then
        echo "Copying OISF rules to main rules directory..."
        cp "$oisf_extract_path"/rules/*.rules "$RULES_DIR" 2>/dev/null
        return 0
    else
        return 1
    fi
}

# Create basic rules if download fails
create_basic_rules() {
    echo "Creating basic rules..."
    
    # Create a simple test rule
    cat > "$RULES_DIR/local.rules" << EOF
# Local rules for testing
alert tcp any any -> any 80 (msg:"Test HTTP Traffic"; flow:established,to_server; content:"GET"; http_method; sid:1000001; rev:1;)
alert icmp any any -> any any (msg:"Test ICMP Traffic"; sid:1000002; rev:1;)
EOF
    
    echo "Basic rules created successfully"
}

# Main execution
echo "Starting Suricata rules update..."

# Try to download Emerging Threats rules
download_emerging_threats

# Try to download OISF rules (optional, may fail without subscription)
download_oisf_rules

# If no rules were downloaded, create basic rules
if [ $(ls -1 "$RULES_DIR"/*.rules 2>/dev/null | wc -l) -eq 0 ]; then
    echo "Warning: No rules downloaded, creating basic rules"
    create_basic_rules
fi

# Clean up temporary files
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# Count the number of rules
RULE_COUNT=$(grep -v "^#" "$RULES_DIR"/*.rules | wc -l)
echo "Update complete. Total rules: $RULE_COUNT"

exit 0
