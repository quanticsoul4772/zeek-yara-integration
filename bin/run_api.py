#!/usr/bin/env python3
"""
API Server Runner Script
Created: April 25, 2025
Author: Security Team

This script starts the REST API server for the Zeek-YARA-Suricata integration.
"""

import argparse
import logging
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.expanduser("~/zeek_yara_integration/logs/api.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("api_server")


def main():
    parser = argparse.ArgumentParser(
        description="API Server for Zeek-YARA-Suricata Integration"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--config", default=None, help="Path to configuration file")
    args = parser.parse_args()

    # Try to import required modules
    try:
        # Import application components
        import uvicorn

        from config.config import Config

        # Load configuration
        if args.config:
            config = Config.load_config(args.config)
        else:
            config = Config.load_config()

        # Import API server after config is loaded
        from api.api_server import app

        # Start server
        logger.info(f"Starting API server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)

    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
        logger.error("Please install missing dependencies with bin/install_deps.sh")
        return 1
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
