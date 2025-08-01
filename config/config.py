#!/usr/bin/env python3
"""
Zeek-YARA Integration Configuration Module
Created: April 24, 2025
Author: Security Team

This module centralizes all configuration parameters for the Zeek-YARA integration.
"""

import os
import json
import logging
from pathlib import Path

# Base directory for the project
BASE_DIR = os.path.expanduser("~/zeek_yara_integration")

# Default configuration
DEFAULT_CONFIG = {
    # File paths
    "EXTRACT_DIR": os.path.join(BASE_DIR, "extracted_files"),
    "RULES_DIR": os.path.join(BASE_DIR, "rules"),
    "RULES_INDEX": os.path.join(BASE_DIR, "rules", "index.yar"),
    "LOG_DIR": os.path.join(BASE_DIR, "logs"),
    "LOG_FILE": os.path.join(BASE_DIR, "logs", "yara_scan.log"),
    "DB_FILE": os.path.join(BASE_DIR, "logs", "yara_alerts.db"),
    
    # Scanning parameters
    "MAX_FILE_SIZE": 20 * 1024 * 1024,  # 20MB default size limit
    "SCAN_INTERVAL": 10,  # Seconds between rule recompilation
    "THREADS": 2,  # Number of scanner threads
    
    # Logging settings
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "%(asctime)s - %(levelname)s - %(message)s",
    
    # File types to scan (empty list means all files)
    "SCAN_MIME_TYPES": [],
    
    # File extensions to scan (empty list means all files)
    "SCAN_EXTENSIONS": [],
    
    # YARA matching settings
    "SCAN_TIMEOUT": 60,  # Seconds before timeout for scanning a single file
}

def get_config(config_file=None):
    """
    Load configuration from file, with fallback to default config.
    
    Args:
        config_file (str, optional): Path to config file. Defaults to None.
        
    Returns:
        dict: Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # If config file is provided, load and merge with defaults
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
                logging.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logging.error(f"Error loading config file: {str(e)}")
    
    # Ensure all directory paths exist
    for key in ['EXTRACT_DIR', 'LOG_DIR', 'RULES_DIR']:
        os.makedirs(config[key], exist_ok=True)
    
    return config

def save_config(config, config_file):
    """
    Save configuration to file.
    
    Args:
        config (dict): Configuration dictionary
        config_file (str): Path to save config file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving config file: {str(e)}")
        return False

# Add a Config class wrapper for compatibility with test framework
class Config:
    """Configuration wrapper class for compatibility"""
    
    @staticmethod
    def load_config(config_file=None):
        """
        Wrapper for get_config to maintain compatibility with test framework.
        
        Args:
            config_file (str, optional): Path to config file. Defaults to None.
            
        Returns:
            dict: Configuration dictionary
        """
        return get_config(config_file)
