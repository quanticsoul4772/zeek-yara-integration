#!/usr/bin/env python3
"""
Distributed Worker Node for Zeek-YARA Integration
Created: August 2025
Author: Security Team

This module implements a standalone worker node that connects to the
distributed scanning master node to process file scanning tasks.
"""

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
import uuid
from typing import Any, Dict, Optional

import requests
import urllib3
import uvicorn
from fastapi import FastAPI, HTTPException

# Disable SSL warnings for development (still enforces SSL verification)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.config import Config
from core.scanner import BaseScanner
from PLATFORM.core.schemas import SchemaValidator
from utils.file_utils import FileAnalyzer
from utils.yara_utils import RuleManager, YaraMatcher


class DistributedWorker:
    """Distributed worker node implementation"""

    def __init__(
        self,
        config: Dict[str, Any],
        worker_id: str,
        master_host: str,
        master_port: int,
        worker_port: int,
        max_tasks: int = 5,
        threads: int = 2,
        api_key: Optional[str] = None,
    ):
        self.config = config
        self.worker_id = worker_id
        self.master_host = master_host
        self.master_port = master_port
        self.worker_port = worker_port
        self.max_tasks = max_tasks
        self.threads = threads
        self.api_key = api_key or config.get("API_KEY", "")

        self.logger = logging.getLogger(f"zeek_yara.worker.{worker_id}")

        # Initialize schema validator
        self.schema_validator = SchemaValidator()

        # Initialize scanner components
        self.file_analyzer = FileAnalyzer(max_file_size=config.get("MAX_FILE_SIZE"))
        self.rule_manager = RuleManager(
            rules_dir=config.get("RULES_DIR"), rules_index=config.get("RULES_INDEX")
        )
        self.yara_matcher = YaraMatcher(
            rule_manager=self.rule_manager, timeout=config.get("SCAN_TIMEOUT", 60)
        )

        # Worker state
        self.running = False
        self.current_tasks = 0
        self.total_processed = 0
        self.error_count = 0
        self.start_time = time.time()
        self.processing_times = []

        # Threading
        self.heartbeat_thread = None
        self.stop_event = threading.Event()
        self.task_lock = threading.Lock()

        # API server for task reception
        self.app = FastAPI(title=f"Worker {worker_id}", version="1.0.0")
        self.setup_routes()

        # Capabilities
        self.capabilities = ["file_scan", "yara_analysis"]

        # Prepare YARA rules
        self.rule_manager.compile_rules()

        # Determine if we should use HTTPS
        self.use_https = self._should_use_https()
        if self.use_https:
            self.logger.info("Using HTTPS for secure communication")
        else:
            self.logger.warning("Using HTTP - not recommended for production")

    def setup_routes(self):
        """Setup FastAPI routes for task handling"""

        @self.app.post("/task")
        async def receive_task(task_data: Dict[str, Any]):
            """Receive and process a task from the master"""
            try:
                with self.task_lock:
                    if self.current_tasks >= self.max_tasks:
                        raise HTTPException(
                            status_code=503, detail="Worker at capacity"
                        )
                    self.current_tasks += 1

                # Process task in background
                threading.Thread(
                    target=self._process_task, args=(task_data,), daemon=True
                ).start()

                return {
                    "success": True,
                    "message": "Task accepted",
                    "worker_id": self.worker_id,
                }

            except Exception as e:
                self.logger.error(f"Error receiving task: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/status")
        async def get_status():
            """Get worker status"""
            return {
                "worker_id": self.worker_id,
                "running": self.running,
                "current_tasks": self.current_tasks,
                "max_tasks": self.max_tasks,
                "total_processed": self.total_processed,
                "error_count": self.error_count,
                "uptime": time.time() - self.start_time,
                "average_processing_time": (
                    sum(self.processing_times) / len(self.processing_times)
                    if self.processing_times
                    else 0
                ),
                "capabilities": self.capabilities,
            }

        @self.app.post("/shutdown")
        async def shutdown():
            """Shutdown worker gracefully"""
            threading.Thread(target=self._shutdown, daemon=True).start()
            return {"success": True, "message": "Shutdown initiated"}

    def _process_task(self, task_data: Dict[str, Any]):
        """Process a scanning task"""
        task_start_time = time.time()

        try:
            task_id = task_data.get("task_id", "unknown")
            file_path = task_data.get("file_path")

            if not file_path:
                self.logger.error(f"Task {task_id}: No file path provided")
                return

            self.logger.info(f"Processing task {task_id}: {file_path}")

            # Perform file scan
            scan_result = self._scan_file(file_path)

            # Record processing time
            processing_time = time.time() - task_start_time
            self.processing_times.append(processing_time)
            if len(self.processing_times) > 100:  # Keep last 100 times
                self.processing_times = self.processing_times[-100:]

            self.total_processed += 1

            # Send result back to master (simplified - would use proper API in production)
            self.logger.info(f"Completed task {task_id} in {processing_time:.2f}s")

        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            self.error_count += 1
        finally:
            with self.task_lock:
                self.current_tasks -= 1

    def _scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a file with YARA (simplified version of BaseScanner.scan_file)"""
        scan_start_time = time.perf_counter()

        # Check if file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return {"matched": False, "error": "File not found"}

        # Check file size
        if self.file_analyzer.is_file_too_large(file_path):
            self.logger.warning(f"File too large to scan: {file_path}")
            return {"matched": False, "error": "File too large"}

        # Get file metadata
        try:
            file_metadata = self.file_analyzer.get_file_metadata(file_path)
        except Exception as e:
            self.logger.error(f"Error getting file metadata: {e}")
            file_metadata = {
                "file_path": file_path,
                "name": os.path.basename(file_path),
            }

        self.logger.info(
            f"Scanning: {file_path} ({file_metadata.get('size', 0)} bytes)"
        )

        try:
            # Scan file with YARA
            scan_result = self.yara_matcher.scan_file(file_path)

            # Calculate scan duration
            scan_duration_ms = int((time.perf_counter() - scan_start_time) * 1000)
            scan_result["scan_duration_ms"] = scan_duration_ms

            if scan_result.get("matched", False):
                self.logger.info(f"YARA match found in {file_metadata.get('name', '')}")
                for match in scan_result.get("matches", []):
                    rule_name = match.get("rule", "unknown")
                    rule_namespace = match.get("namespace", "unknown")
                    self.logger.info(f"  Rule Match: {rule_namespace}.{rule_name}")
            else:
                self.logger.info(f"No matches for file: {file_path}")

            return scan_result

        except Exception as e:
            error_msg = f"Error scanning file: {str(e)}"
            self.logger.error(error_msg)
            return {"matched": False, "error": error_msg}

    def _should_use_https(self) -> bool:
        """Determine if HTTPS should be used based on environment"""
        environment = self.config.get("ENVIRONMENT", "development").lower()

        # Force HTTPS in production
        if environment == "production":
            return True

        # Allow HTTP in development and testing
        if environment in ["development", "testing", "education"]:
            # Check if HTTPS is explicitly configured
            return self.config.get("FORCE_HTTPS", False)

        # Default to HTTPS for unknown environments
        return True

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        return headers

    def _get_base_url(self) -> str:
        """Get base URL for master node communication"""
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.master_host}:{self.master_port}"

    def _validate_registration_data(self, data: Dict[str, Any]) -> None:
        """Validate worker registration data against schema"""
        try:
            self.schema_validator.validate("worker_registration", data)
        except Exception as e:
            raise ValueError(f"Invalid registration data: {e}")

    def register_with_master(self) -> bool:
        """Register this worker with the master node"""
        try:
            # Check API key requirement
            if not self.api_key:
                self.logger.error("API key is required for worker registration")
                return False

            registration_data = {
                "worker_id": self.worker_id,
                "host": "localhost",  # Could be made configurable
                "port": self.worker_port,
                "max_tasks": self.max_tasks,
                "capabilities": self.capabilities,
                "metadata": {
                    "threads": self.threads,
                    "start_time": self.start_time,
                    "version": "1.0.0",
                    "platform": sys.platform,
                },
            }

            # Validate registration data against schema
            try:
                self._validate_registration_data(registration_data)
            except ValueError as e:
                self.logger.error(f"Registration data validation failed: {e}")
                return False

            # Prepare request
            url = f"{self._get_base_url()}/distributed/workers/register"
            headers = self._get_auth_headers()

            # Configure SSL verification
            verify_ssl = self.use_https and self.config.get("VERIFY_SSL", True)

            response = requests.post(
                url,
                json=registration_data,
                headers=headers,
                timeout=10,
                verify=verify_ssl,
            )

            if response.status_code == 200:
                self.logger.info(
                    f"Successfully registered with master at {self._get_base_url()}"
                )
                return True
            elif response.status_code == 401:
                self.logger.error("Authentication failed - invalid API key")
                return False
            elif response.status_code == 400:
                self.logger.error(
                    f"Registration failed - invalid data: {response.text}"
                )
                return False
            else:
                self.logger.error(
                    f"Failed to register with master: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.SSLError as e:
            self.logger.error(f"SSL/TLS error during registration: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error during registration: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error registering with master: {e}")
            return False

    def unregister_from_master(self) -> bool:
        """Unregister this worker from the master node"""
        try:
            url = f"{self._get_base_url()}/distributed/workers/{self.worker_id}"
            headers = self._get_auth_headers()
            verify_ssl = self.use_https and self.config.get("VERIFY_SSL", True)

            response = requests.delete(
                url, headers=headers, timeout=10, verify=verify_ssl
            )

            if response.status_code == 200:
                self.logger.info("Successfully unregistered from master")
                return True
            else:
                self.logger.warning(
                    f"Failed to unregister from master: {response.status_code}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error unregistering from master: {e}")
            return False

    def send_heartbeat(self):
        """Send heartbeat to master node"""
        try:
            heartbeat_data = {
                "current_tasks": self.current_tasks,
                "total_processed": self.total_processed,
                "error_count": self.error_count,
                "average_processing_time": (
                    sum(self.processing_times) / len(self.processing_times)
                    if self.processing_times
                    else 0
                ),
            }

            # Validate heartbeat data
            try:
                self.schema_validator.validate("worker_heartbeat", heartbeat_data)
            except Exception as e:
                self.logger.error(f"Heartbeat data validation failed: {e}")
                return

            url = (
                f"{self._get_base_url()}/distributed/workers/{self.worker_id}/heartbeat"
            )
            headers = self._get_auth_headers()
            verify_ssl = self.use_https and self.config.get("VERIFY_SSL", True)

            response = requests.put(
                url, json=heartbeat_data, headers=headers, timeout=5, verify=verify_ssl
            )

            if response.status_code != 200:
                self.logger.warning(f"Heartbeat failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")

    def _heartbeat_loop(self):
        """Heartbeat loop thread"""
        heartbeat_interval = self.config.get("WORKER_HEARTBEAT_INTERVAL", 30)

        while not self.stop_event.is_set():
            try:
                self.send_heartbeat()

                # Sleep with responsive shutdown checking
                sleep_remaining = heartbeat_interval
                while sleep_remaining > 0 and not self.stop_event.is_set():
                    sleep_time = min(1.0, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time

            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(5.0)

    def start(self) -> bool:
        """Start the worker node"""
        try:
            # Register with master
            if not self.register_with_master():
                self.logger.error("Failed to register with master, aborting startup")
                return False

            # Start heartbeat thread
            self.stop_event.clear()
            self.heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop, daemon=True
            )
            self.heartbeat_thread.start()

            self.running = True
            self.logger.info(
                f"Worker {self.worker_id} started on port {self.worker_port}"
            )

            # Start API server (blocking)
            uvicorn.run(
                self.app, host="0.0.0.0", port=self.worker_port, log_level="warning"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error starting worker: {e}")
            return False

    def stop(self):
        """Stop the worker node gracefully"""
        self.logger.info(f"Stopping worker {self.worker_id}")
        self.running = False

        # Stop heartbeat thread
        self.stop_event.set()
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5.0)

        # Unregister from master
        self.unregister_from_master()

        self.logger.info(f"Worker {self.worker_id} stopped")

    def _shutdown(self):
        """Shutdown worker (called from API endpoint)"""
        time.sleep(1)  # Brief delay to allow response to be sent
        os._exit(0)


def main():
    """Main entry point for the distributed worker"""
    parser = argparse.ArgumentParser(description="Zeek-YARA Distributed Worker Node")

    parser.add_argument(
        "--worker-id",
        default=f"worker-{uuid.uuid4().hex[:8]}",
        help="Unique worker identifier",
    )
    parser.add_argument(
        "--master-host", default="localhost", help="Master node host address"
    )
    parser.add_argument(
        "--master-port", type=int, default=8000, help="Master node port"
    )
    parser.add_argument(
        "--worker-port", type=int, default=8001, help="Worker node port"
    )
    parser.add_argument(
        "--max-tasks", type=int, default=5, help="Maximum concurrent tasks"
    )
    parser.add_argument(
        "--threads", type=int, default=2, help="Number of processing threads"
    )
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--api-key", help="API key for authentication with master node")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/worker_{args.worker_id}.log"),
        ],
    )

    logger = logging.getLogger("zeek_yara.worker.main")

    try:
        # Load configuration
        if args.config:
            config = Config.load_config(args.config)
        else:
            config = Config.load_config()

        # Create worker instance
        worker = DistributedWorker(
            config=config,
            worker_id=args.worker_id,
            master_host=args.master_host,
            master_port=args.master_port,
            worker_port=args.worker_port,
            max_tasks=args.max_tasks,
            threads=args.threads,
            api_key=args.api_key,
        )

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            worker.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info(f"Starting distributed worker {args.worker_id}")
        logger.info(f"Master: {args.master_host}:{args.master_port}")
        logger.info(f"Worker port: {args.worker_port}")
        logger.info(f"Max tasks: {args.max_tasks}")

        # Start worker (blocking)
        success = worker.start()

        if not success:
            logger.error("Failed to start worker")
            return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")
        return 0
    except Exception as e:
        logger.error(f"Error running worker: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
