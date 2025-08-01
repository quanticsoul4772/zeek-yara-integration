#!/usr/bin/env python3
"""
Suricata Integration Module for Zeek-YARA Integration
Created: April 25, 2025
Author: Security Team

This module provides integration with Suricata IDS for comprehensive network monitoring.
"""

import os
import json
import time
import logging
import subprocess
import threading
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

class SuricataConfig:
    """Suricata configuration management"""
    
    def __init__(self, config_file: str, rules_dir: str, log_dir: str):
        """
        Initialize Suricata configuration.
        
        Args:
            config_file (str): Path to Suricata configuration file
            rules_dir (str): Path to Suricata rules directory
            log_dir (str): Path to Suricata log directory
        """
        self.config_file = config_file
        self.rules_dir = rules_dir
        self.log_dir = log_dir
        self.logger = logging.getLogger('zeek_yara.suricata_config')
        
        # Create directories if they don't exist
        os.makedirs(rules_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize configuration
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Suricata configuration file if it doesn't exist"""
        if not os.path.exists(self.config_file):
            self.logger.info(f"Creating default Suricata configuration at {self.config_file}")
            try:
                default_config = self._create_default_config()
                with open(self.config_file, 'w') as f:
                    f.write(default_config)
                self.logger.info("Default Suricata configuration created successfully")
            except Exception as e:
                self.logger.error(f"Error creating default Suricata configuration: {e}")
    
    def _create_default_config(self) -> str:
        """
        Create default Suricata configuration.
        
        Returns:
            str: Default Suricata configuration as YAML string
        """
        # Normalize paths for YAML
        rules_dir = self.rules_dir.replace('\\', '/')
        log_dir = self.log_dir.replace('\\', '/')
        
        # Create basic default configuration
        return f"""# Suricata Configuration for Zeek-YARA Integration
%YAML 1.1
---
# Network Variables
vars:
  # Network Definitions
  HOME-NET: "[192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 127.0.0.0/8]"
  EXTERNAL-NET: "!$HOME-NET"
  
  # Server Definitions
  HTTP-SERVERS: "$HOME-NET"
  DNS-SERVERS: "$HOME-NET"
  SMTP-SERVERS: "$HOME-NET"
  SQL-SERVERS: "$HOME-NET"

# Logging directory
default-log-dir: {log_dir}

# Rule configuration
default-rule-path: {rules_dir}
rule-files:
  - "*.rules"

# Logging configuration
outputs:
  - fast:
      enabled: yes
      filename: fast.log
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert
        - http
        - dns
        - tls
        - files
        - ssh

# Performance settings
max-pending-packets: 1024

# Detect Engine Configuration
detect:
  profile: medium
  custom-detect-proto-layer: yes
"""
    
    def update_rules(self, download_emerging_threats: bool = True) -> bool:
        """
        Update Suricata rules.
        
        Args:
            download_emerging_threats (bool): Download and extract Emerging Threats rules
            
        Returns:
            bool: True if rules were updated successfully, False otherwise
        """
        success = True
        
        try:
            # Create rules directory if it doesn't exist
            os.makedirs(self.rules_dir, exist_ok=True)
            
            if download_emerging_threats:
                # Download Emerging Threats rules
                self.logger.info("Downloading Emerging Threats rules...")
                
                # URL for Emerging Threats Open rules
                et_url = "https://rules.emergingthreats.net/open/suricata-5.0/emerging.rules.tar.gz"
                
                # Download rules to temporary file
                temp_file = os.path.join(self.rules_dir, "emerging.rules.tar.gz")
                subprocess.run(["curl", "-o", temp_file, et_url], check=True)
                
                # Extract rules
                subprocess.run(["tar", "-xzf", temp_file, "-C", self.rules_dir], check=True)
                
                # Remove temporary file
                os.unlink(temp_file)
                
                self.logger.info("Emerging Threats rules downloaded and extracted successfully")
        
        except Exception as e:
            self.logger.error(f"Error updating Suricata rules: {e}")
            success = False
        
        return success

class SuricataRunner:
    """Suricata runner for analyzing network traffic"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Suricata runner.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.suricata_bin = config.get('SURICATA_BIN', 'suricata')
        self.suricata_config = config.get('SURICATA_CONFIG', 'config/suricata.yaml')
        self.output_dir = config.get('SURICATA_LOG_DIR', 'logs/suricata')
        self.rules_dir = config.get('SURICATA_RULES_DIR', 'rules/suricata')
        self.db_file = config.get('DB_FILE', 'logs/alerts.db')
        self.logger = logging.getLogger('zeek_yara.suricata_runner')
        
        # Create suricata configuration object
        self.suricata_config_obj = SuricataConfig(
            config_file=self.suricata_config,
            rules_dir=self.rules_dir,
            log_dir=self.output_dir
        )
        
        # Initialize database for Suricata alerts
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database for Suricata alerts"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            # Create Suricata alerts table
            c.execute('''
                CREATE TABLE IF NOT EXISTS suricata_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT,
                    src_ip TEXT,
                    src_port INTEGER,
                    dest_ip TEXT,
                    dest_port INTEGER,
                    proto TEXT,
                    action TEXT,
                    gid INTEGER,
                    sid INTEGER,
                    rev INTEGER,
                    signature TEXT,
                    category TEXT,
                    severity INTEGER,
                    payload TEXT,
                    packet_info TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for timestamp
            c.execute('CREATE INDEX IF NOT EXISTS idx_suricata_timestamp ON suricata_alerts(timestamp)')
            
            # Create index for signature
            c.execute('CREATE INDEX IF NOT EXISTS idx_suricata_signature ON suricata_alerts(signature)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Suricata alerts database initialized")
        
        except Exception as e:
            self.logger.error(f"Error initializing Suricata alerts database: {e}")
    
    def run_live(self, interface: str, duration: int = 0) -> bool:
        """
        Run Suricata on live traffic.
        
        Args:
            interface (str): Network interface to monitor
            duration (int): Duration in seconds (0 for continuous)
            
        Returns:
            bool: True if Suricata started successfully, False otherwise
        """
        try:
            # Build command
            cmd = [
                self.suricata_bin,
                "-c", self.suricata_config,
                "-i", interface,
                "-l", self.output_dir
            ]
            
            # Start Suricata process
            self.logger.info(f"Starting Suricata on interface {interface}")
            
            if duration > 0:
                # Run for a specified duration
                process = subprocess.Popen(cmd)
                time.sleep(duration)
                process.terminate()
                process.wait(timeout=10)
                self.logger.info(f"Suricata monitoring completed after {duration} seconds")
                
                # Process the results
                self._process_alerts()
                return True
            else:
                # Run in background
                subprocess.Popen(cmd)
                self.logger.info("Suricata started in background mode")
                return True
        
        except Exception as e:
            self.logger.error(f"Error running Suricata: {e}")
            return False
    
    def run_pcap(self, pcap_file: str) -> bool:
        """
        Run Suricata on a PCAP file.
        
        Args:
            pcap_file (str): Path to the PCAP file
            
        Returns:
            bool: True if analysis was successful, False otherwise
        """
        try:
            # Create output directory for this specific analysis
            pcap_name = os.path.basename(pcap_file)
            output_dir = os.path.join(self.output_dir, f"pcap_{pcap_name}_{int(time.time())}")
            os.makedirs(output_dir, exist_ok=True)
            
            # Build command
            cmd = [
                self.suricata_bin,
                "-c", self.suricata_config,
                "-r", pcap_file,
                "-l", output_dir
            ]
            
            # Run Suricata
            self.logger.info(f"Analyzing PCAP file: {pcap_file}")
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Check output
            if process.returncode == 0:
                self.logger.info(f"PCAP analysis completed successfully: {pcap_file}")
                
                # Process alerts
                self._process_alerts(output_dir)
                return True
            else:
                self.logger.error(f"Suricata exited with error code {process.returncode}")
                self.logger.error(f"Stderr: {process.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error analyzing PCAP file {pcap_file}: {e}")
            return False
    
    def _process_alerts(self, output_dir: Optional[str] = None) -> None:
        """
        Process Suricata alerts and store in database.
        
        Args:
            output_dir (str, optional): Custom output directory
        """
        # Use provided directory or default
        log_dir = output_dir or self.output_dir
        
        try:
            # Check if eve.json exists
            eve_json = os.path.join(log_dir, "eve.json")
            
            if not os.path.exists(eve_json):
                self.logger.warning(f"No eve.json file found in {log_dir}")
                return
            
            # Connect to database
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            # Process each line in eve.json (it's NDJSON format, one event per line)
            with open(eve_json, 'r') as f:
                for line in f:
                    try:
                        # Parse JSON
                        event = json.loads(line)
                        
                        # Only process alert events
                        if event.get('event_type') != 'alert':
                            continue
                        
                        # Extract alert information
                        alert = event.get('alert', {})
                        src_ip = event.get('src_ip', '')
                        src_port = event.get('src_port', 0)
                        dest_ip = event.get('dest_ip', '')
                        dest_port = event.get('dest_port', 0)
                        proto = event.get('proto', '')
                        timestamp = event.get('timestamp', datetime.now().isoformat())
                        
                        # Handle signature and metadata
                        signature = alert.get('signature', '')
                        action = alert.get('action', '')
                        gid = alert.get('gid', 0)
                        sid = alert.get('sid', 0)
                        rev = alert.get('rev', 0)
                        category = alert.get('category', '')
                        severity = alert.get('severity', 0)
                        
                        # Payload and packet info as JSON
                        payload = json.dumps(event.get('payload', {}))
                        packet_info = json.dumps(event.get('packet', {}))
                        
                        # Insert into database
                        c.execute('''
                            INSERT INTO suricata_alerts
                            (timestamp, event_type, src_ip, src_port, dest_ip, dest_port, proto,
                             action, gid, sid, rev, signature, category, severity, payload, packet_info)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            timestamp,
                            event.get('event_type', ''),
                            src_ip,
                            src_port,
                            dest_ip,
                            dest_port,
                            proto,
                            action,
                            gid,
                            sid,
                            rev,
                            signature,
                            category,
                            severity,
                            payload,
                            packet_info
                        ))
                    
                    except json.JSONDecodeError:
                        self.logger.warning(f"Invalid JSON in eve.json: {line}")
                        continue
                    except Exception as e:
                        self.logger.error(f"Error processing alert: {e}")
                        continue
            
            # Commit changes
            conn.commit()
            conn.close()
            
            self.logger.info("Suricata alerts processed and stored in database")
        
        except Exception as e:
            self.logger.error(f"Error processing Suricata alerts: {e}")
    
    def get_alerts(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve Suricata alerts from database.
        
        Args:
            filters (dict, optional): Dictionary of filter conditions
            limit (int, optional): Maximum number of results to return
            offset (int, optional): Number of results to skip
            
        Returns:
            list: List of alert dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Base query
            query = "SELECT * FROM suricata_alerts"
            
            # Build where clause from filter parameters
            where_clauses = []
            query_params = []
            
            if filters:
                for key, value in filters.items():
                    where_clauses.append(f"{key} LIKE ?")
                    query_params.append(f"%{value}%")
            
            # Add where clause if filters exist
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add order by
            query += " ORDER BY timestamp DESC"
            
            # Add pagination
            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                query_params.extend([limit, offset])
            
            # Execute query
            c.execute(query, query_params)
            
            # Fetch results
            results = []
            for row in c.fetchall():
                # Convert row to dictionary
                alert = dict(zip([column[0] for column in c.description], row))
                
                # Parse JSON fields
                try:
                    alert['payload'] = json.loads(alert['payload'])
                except:
                    alert['payload'] = {}
                
                try:
                    alert['packet_info'] = json.loads(alert['packet_info'])
                except:
                    alert['packet_info'] = {}
                
                results.append(alert)
            
            conn.close()
            return results
        
        except Exception as e:
            self.logger.error(f"Error retrieving Suricata alerts: {e}")
            return []
    
    def stop(self) -> bool:
        """
        Stop Suricata if running.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            # Find Suricata processes
            ps_output = subprocess.check_output(["ps", "aux"], text=True)
            
            # Get process IDs
            pids = []
            for line in ps_output.splitlines():
                if self.suricata_bin in line and "-c" in line and "-i" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pids.append(parts[1])
            
            # Kill processes
            for pid in pids:
                subprocess.run(["kill", pid], check=True)
                self.logger.info(f"Stopped Suricata process with PID {pid}")
            
            return len(pids) > 0
        
        except Exception as e:
            self.logger.error(f"Error stopping Suricata: {e}")
            return False
    
    def update_rules(self) -> bool:
        """
        Update Suricata rules.
        
        Returns:
            bool: True if rules were updated successfully, False otherwise
        """
        return self.suricata_config_obj.update_rules()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get Suricata status information.
        
        Returns:
            dict: Status information
        """
        status = {
            "running": False,
            "pid": None,
            "version": "Unknown",
            "alert_count": 0,
            "rules_count": 0
        }
        
        try:
            # Check if Suricata is running
            ps_output = subprocess.check_output(["ps", "aux"], text=True)
            
            # Get process ID
            for line in ps_output.splitlines():
                if self.suricata_bin in line and "-c" in line and "-i" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        status["running"] = True
                        status["pid"] = parts[1]
                        break
            
            # Get Suricata version
            try:
                version_output = subprocess.check_output([self.suricata_bin, "-V"], text=True)
                status["version"] = version_output.strip()
            except:
                pass
            
            # Count alerts
            try:
                conn = sqlite3.connect(self.db_file)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM suricata_alerts")
                status["alert_count"] = c.fetchone()[0]
                conn.close()
            except:
                pass
            
            # Count rules
            try:
                rule_count = 0
                for root, dirs, files in os.walk(self.rules_dir):
                    for file in files:
                        if file.endswith('.rules'):
                            with open(os.path.join(root, file), 'r') as f:
                                for line in f:
                                    if line.strip() and not line.strip().startswith('#'):
                                        rule_count += 1
                
                status["rules_count"] = rule_count
            except:
                pass
            
            return status
        
        except Exception as e:
            self.logger.error(f"Error getting Suricata status: {e}")
            return status
