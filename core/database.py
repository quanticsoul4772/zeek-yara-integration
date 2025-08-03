#!/usr/bin/env python3
"""
Zeek-YARA Integration Database Module
Created: April 24, 2025
Author: Security Team

This module manages the database operations for YARA alerts with enhanced performance.
"""

import datetime
import json
import logging
import os
import queue
import sqlite3
import threading
import time
from contextlib import contextmanager
from functools import wraps
from threading import Lock, local


def performance_track(logger=None, level=logging.DEBUG):
    """
    Performance tracking decorator for database methods.

    Args:
        logger (logging.Logger, optional): Logger for tracking
        level (int, optional): Logging level
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()

                if logger:
                    logger.log(
                        level,
                        f"Method {func.__name__} executed in {(end_time - start_time) * 1000:.2f} ms",
                    )

                return result
            except Exception as e:
                if logger:
                    logger.exception(f"Error in {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


class ConnectionPool:
    """
    Efficient database connection pool management with thread safety
    """

    def __init__(self, database_file, max_connections=5, timeout=30):
        """
        Initialize connection pool

        Args:
            database_file (str): Path to SQLite database
            max_connections (int): Maximum number of connections
            timeout (int): Connection timeout in seconds
        """
        self._pools = {}
        self._local = local()
        self._database_file = database_file
        self._max_connections = max_connections
        self._timeout = timeout
        self._logger = logging.getLogger("zeek_yara.connection_pool")

    @contextmanager
    def connection(self):
        """
        Thread-safe context manager for database connections

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = self._get_connection()
            yield conn
        except Exception as e:
            self._logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                self._release_connection(conn)

    def _get_connection(self):
        """
        Get a thread-specific database connection

        Returns:
            sqlite3.Connection: Database connection
        """
        thread_id = threading.get_ident()

        # Create a new pool for this thread if it doesn't exist
        if thread_id not in self._pools:
            self._pools[thread_id] = queue.Queue(maxsize=self._max_connections)

        # Try to get a connection from the pool
        try:
            conn = self._pools[thread_id].get(block=False)
            return conn
        except queue.Empty:
            # If pool is empty, create a new connection
            conn = sqlite3.connect(self._database_file)
            return conn

    def _release_connection(self, connection):
        """
        Release a database connection back to the thread-specific pool

        Args:
            connection (sqlite3.Connection): Connection to release
        """
        thread_id = threading.get_ident()

        try:
            if thread_id in self._pools and not self._pools[thread_id].full():
                self._pools[thread_id].put(connection, block=False)
            else:
                connection.close()
        except Exception as e:
            self._logger.error(f"Error releasing connection: {e}")
            connection.close()


class DatabaseManager:
    """
    Enhanced database manager with performance optimizations
    """

    def __init__(self, db_file):
        """
        Initialize database manager with connection pooling

        Args:
            db_file (str): Path to SQLite database file
        """
        self.db_file = db_file
        self.logger = logging.getLogger("zeek_yara.database")
        self.db_lock = Lock()
        self.connection_pool = ConnectionPool(db_file)

        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        # Initialize the database
        self._init_db()

    def _init_db(self):
        """
        Initialize the SQLite database schema for YARA alerts.

        Creates the necessary table if it doesn't exist, with columns
        to support comprehensive alert tracking.
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()

                # Create YARA alerts table with comprehensive schema
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS yara_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_name TEXT,
                        file_size INTEGER,
                        file_type TEXT,
                        md5 TEXT,
                        sha256 TEXT,
                        zeek_uid TEXT,
                        rule_name TEXT NOT NULL,
                        rule_namespace TEXT,
                        rule_meta TEXT,
                        strings_matched TEXT,
                        severity INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create index for performance
                c.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON yara_alerts(timestamp)
                """
                )
                c.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_rule_name ON yara_alerts(rule_name)
                """
                )

                # Create file processing states table
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS file_processing_states (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL UNIQUE,
                        file_name TEXT,
                        file_size INTEGER,
                        md5 TEXT,
                        sha256 TEXT,
                        state TEXT NOT NULL CHECK (state IN ('pending', 'scanning', 'completed', 'failed', 'quarantined')),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        started_at DATETIME,
                        completed_at DATETIME,
                        error_message TEXT,
                        scan_duration_ms INTEGER,
                        retry_count INTEGER DEFAULT 0
                    )
                """
                )

                # Create indexes for file processing states
                c.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_file_state ON file_processing_states(state)
                """
                )
                c.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_file_path ON file_processing_states(file_path)
                """
                )
                c.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_file_updated ON file_processing_states(updated_at)
                """
                )

                conn.commit()
                self.logger.info("Database initialized successfully")

        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise

    @performance_track()
    def add_alert(self, file_data, match_data):
        """
        Add a single alert to the database

        Args:
            file_data (dict): Information about the file
            match_data (dict): YARA matching information

        Returns:
            bool: True if alert was added successfully
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()

                # Prepare alert data
                # Get file path from the correct field in file_data
                file_path = file_data.get("path", file_data.get("file_path", ""))

                # Get file name, either from metadata or from path
                file_name = file_data.get("name", file_data.get("file_name", ""))
                if not file_name and file_path:
                    file_name = os.path.basename(file_path)

                # Ensure absolute path is used for consistent querying
                if file_path and not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)

                alert_record = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "file_path": file_path,
                    "file_name": file_name,
                    "file_size": file_data.get("size", file_data.get("file_size", 0)),
                    "file_type": file_data.get("file_type", ""),
                    "md5": file_data.get("md5", ""),
                    "sha256": file_data.get("sha256", ""),
                    "zeek_uid": file_data.get("zeek_uid", "unknown_uid"),
                    "rule_name": "unknown",
                    "rule_namespace": "unknown",
                    "rule_meta": "{}",
                    "strings_matched": "[]",
                    "severity": 0,
                }
                self.logger.debug(
                    f"Alert record: file_path={alert_record['file_path']}, file_name={alert_record['file_name']}, metadata={file_data}"
                )

                # Process match data if present
                if match_data and match_data.get("matched", False):
                    matches = match_data.get("matches", [])
                    if matches:
                        first_match = matches[0]
                        alert_record.update(
                            {
                                "rule_name": first_match.get("rule", "unknown"),
                                "rule_namespace": first_match.get("namespace", "unknown"),
                                "rule_meta": json.dumps(first_match.get("meta", {})),
                                "strings_matched": json.dumps(first_match.get("strings", [])),
                                "severity": first_match.get("meta", {}).get("severity", 0),
                            }
                        )

                # Prepare insert query
                insert_query = """
                    INSERT INTO yara_alerts
                    (timestamp, file_path, file_name, file_size, file_type,
                    md5, sha256, zeek_uid, rule_name, rule_namespace,
                    rule_meta, strings_matched, severity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                # Execute insert
                c.execute(
                    insert_query,
                    (
                        alert_record["timestamp"],
                        alert_record["file_path"],
                        alert_record["file_name"],
                        alert_record["file_size"],
                        alert_record["file_type"],
                        alert_record["md5"],
                        alert_record["sha256"],
                        alert_record["zeek_uid"],
                        alert_record["rule_name"],
                        alert_record["rule_namespace"],
                        alert_record["rule_meta"],
                        alert_record["strings_matched"],
                        alert_record["severity"],
                    ),
                )

                # Commit
                conn.commit()
                return True

        except Exception as e:
            self.logger.error(f"Error adding alert: {e}")
            return False

    @performance_track()
    def bulk_insert_alerts(self, alerts_data):
        """
        Bulk insert multiple alerts efficiently

        Args:
            alerts_data (list): List of alert dictionaries

        Returns:
            int: Number of alerts inserted
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()

                # Prepare bulk insert
                insert_query = """
                    INSERT INTO yara_alerts
                    (timestamp, file_path, file_name, file_size, file_type,
                    md5, sha256, zeek_uid, rule_name, rule_namespace,
                    rule_meta, strings_matched, severity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                # Batch insert with error handling
                successful_inserts = 0
                for alert in alerts_data:
                    try:
                        c.execute(
                            insert_query,
                            (
                                alert.get("timestamp", datetime.datetime.now().isoformat()),
                                alert.get("file_path", ""),
                                alert.get("file_name", ""),
                                alert.get("file_size", 0),
                                alert.get("file_type", ""),
                                alert.get("md5", ""),
                                alert.get("sha256", ""),
                                alert.get("zeek_uid", "unknown_uid"),
                                alert.get("rule_name", "unknown"),
                                alert.get("rule_namespace", "unknown"),
                                json.dumps(alert.get("rule_meta", {})),
                                json.dumps(alert.get("strings_matched", [])),
                                alert.get("severity", 0),
                            ),
                        )
                        successful_inserts += 1
                    except Exception as e:
                        self.logger.error(f"Error inserting alert: {e}")

                conn.commit()
                return successful_inserts

        except Exception as e:
            self.logger.error(f"Bulk insert failed: {e}")
            return 0

    @performance_track()
    def get_alerts(self, filters=None, limit=None, offset=0):
        """
        Retrieve alerts with optional filtering and pagination

        Args:
            filters (dict, optional): Dictionary of filter conditions
            limit (int, optional): Maximum number of results to return
            offset (int, optional): Number of results to skip

        Returns:
            list: List of alert dictionaries
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()

                # Base query
                query = "SELECT * FROM yara_alerts"

                # Build where clause from filter parameters
                where_clauses = []
                query_params = []

                if filters:
                    for key, value in filters.items():
                        where_clauses.append(f"{key} = ?")
                        query_params.append(value)

                # Add where clause if filters exist
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

                # Add pagination
                if limit is not None:
                    query += " LIMIT ? OFFSET ?"
                    query_params.extend([limit, offset])
                else:
                    # When no limit is specified, use a very large number
                    query += " LIMIT ? OFFSET ?"
                    query_params.extend([1000000, offset])

                # Execute query
                c.execute(query, query_params)

                # Fetch results
                columns = [column[0] for column in c.description]
                results = [dict(zip(columns, row)) for row in c.fetchall()]

                return results

        except Exception as e:
            self.logger.error(f"Error retrieving alerts: {e}")
            return []

    @performance_track()
    def delete_alerts(self, filter_params=None):
        """
        Delete alerts based on optional filter parameters

        Args:
            filter_params (dict, optional): Dictionary of filter conditions

        Returns:
            int: Number of alerts deleted
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()

                # Base delete query
                query = "DELETE FROM yara_alerts"

                # Build where clause from filter parameters
                where_clauses = []
                query_params = []

                if filter_params:
                    for key, value in filter_params.items():
                        where_clauses.append(f"{key} = ?")
                        query_params.append(value)

                # Add where clause if filters exist
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

                # Execute delete
                c.execute(query, query_params)
                conn.commit()

                return c.rowcount

        except Exception as e:
            self.logger.error(f"Error deleting alerts: {e}")
            return 0

    # File Processing State Tracking Methods

    @performance_track()
    def add_file_state(self, file_path, file_metadata=None):
        """
        Add a new file to processing state tracking with 'pending' state
        
        Args:
            file_path (str): Path to the file
            file_metadata (dict, optional): File metadata including size, hashes, etc.
            
        Returns:
            bool: True if state was added successfully
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()
                
                # Ensure absolute path
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                
                # Extract metadata
                file_name = os.path.basename(file_path)
                file_size = None
                md5 = None
                sha256 = None
                
                if file_metadata:
                    file_size = file_metadata.get("size", file_metadata.get("file_size"))
                    md5 = file_metadata.get("md5", "")
                    sha256 = file_metadata.get("sha256", "")
                
                # Insert with pending state
                c.execute(
                    """
                    INSERT OR REPLACE INTO file_processing_states 
                    (file_path, file_name, file_size, md5, sha256, state, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (file_path, file_name, file_size, md5, sha256)
                )
                
                conn.commit()
                self.logger.debug(f"Added file state for: {file_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error adding file state for {file_path}: {e}")
            return False

    @performance_track()
    def update_file_state(self, file_path, new_state, error_message=None, scan_duration_ms=None):
        """
        Update the processing state of a file
        
        Args:
            file_path (str): Path to the file
            new_state (str): New state (pending, scanning, completed, failed, quarantined)
            error_message (str, optional): Error message if state is 'failed'
            scan_duration_ms (int, optional): Scan duration in milliseconds
            
        Returns:
            bool: True if state was updated successfully
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()
                
                # Ensure absolute path
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                
                # Build update query based on new state
                if new_state == 'scanning':
                    c.execute(
                        """
                        UPDATE file_processing_states 
                        SET state = ?, started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                        WHERE file_path = ?
                        """,
                        (new_state, file_path)
                    )
                elif new_state in ['completed', 'failed', 'quarantined']:
                    c.execute(
                        """
                        UPDATE file_processing_states 
                        SET state = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP,
                            error_message = ?, scan_duration_ms = ?
                        WHERE file_path = ?
                        """,
                        (new_state, error_message, scan_duration_ms, file_path)
                    )
                else:
                    c.execute(
                        """
                        UPDATE file_processing_states 
                        SET state = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE file_path = ?
                        """,
                        (new_state, file_path)
                    )
                
                conn.commit()
                
                if c.rowcount > 0:
                    self.logger.debug(f"Updated file state to '{new_state}' for: {file_path}")
                    return True
                else:
                    self.logger.warning(f"No file state record found for: {file_path}")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error updating file state for {file_path}: {e}")
            return False

    @performance_track()
    def get_file_state(self, file_path):
        """
        Get the current processing state of a file
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            dict: File state record or None if not found
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()
                
                # Ensure absolute path
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                
                c.execute(
                    "SELECT * FROM file_processing_states WHERE file_path = ?",
                    (file_path,)
                )
                
                row = c.fetchone()
                if row:
                    columns = [column[0] for column in c.description]
                    return dict(zip(columns, row))
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting file state for {file_path}: {e}")
            return None

    @performance_track()
    def get_files_by_state(self, state, limit=None):
        """
        Get all files in a specific processing state
        
        Args:
            state (str): State to filter by
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of file state records
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()
                
                query = "SELECT * FROM file_processing_states WHERE state = ? ORDER BY updated_at DESC"
                params = [state]
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                c.execute(query, params)
                
                columns = [column[0] for column in c.description]
                return [dict(zip(columns, row)) for row in c.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error getting files by state '{state}': {e}")
            return []

    @performance_track()
    def get_interrupted_scans(self, timeout_minutes=30):
        """
        Find files that may have been interrupted during scanning
        
        Args:
            timeout_minutes (int): Minutes after which a scanning state is considered interrupted
            
        Returns:
            list: List of potentially interrupted file records
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()
                
                # Find files in 'scanning' state that haven't been updated recently
                c.execute(
                    """
                    SELECT * FROM file_processing_states 
                    WHERE state = 'scanning' 
                    AND datetime(updated_at) < datetime('now', '-' || ? || ' minutes')
                    ORDER BY updated_at ASC
                    """,
                    (timeout_minutes,)
                )
                
                columns = [column[0] for column in c.description]
                return [dict(zip(columns, row)) for row in c.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error finding interrupted scans: {e}")
            return []

    @performance_track()
    def recover_interrupted_scans(self, timeout_minutes=30):
        """
        Reset interrupted scans back to 'pending' state for retry
        
        Args:
            timeout_minutes (int): Minutes after which a scanning state is considered interrupted
            
        Returns:
            int: Number of files recovered
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()
                
                # Update interrupted scans back to pending and increment retry count
                c.execute(
                    """
                    UPDATE file_processing_states 
                    SET state = 'pending', 
                        updated_at = CURRENT_TIMESTAMP,
                        retry_count = retry_count + 1,
                        error_message = 'Recovered from interrupted scan'
                    WHERE state = 'scanning' 
                    AND datetime(updated_at) < datetime('now', '-' || ? || ' minutes')
                    """,
                    (timeout_minutes,)
                )
                
                recovered_count = c.rowcount
                conn.commit()
                
                if recovered_count > 0:
                    self.logger.info(f"Recovered {recovered_count} interrupted scans")
                
                return recovered_count
                
        except Exception as e:
            self.logger.error(f"Error recovering interrupted scans: {e}")
            return 0

    @performance_track()
    def cleanup_completed_states(self, retention_hours=24):
        """
        Clean up old completed file state records
        
        Args:
            retention_hours (int): Hours to retain completed records
            
        Returns:
            int: Number of records cleaned up
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()
                
                c.execute(
                    """
                    DELETE FROM file_processing_states 
                    WHERE state = 'completed' 
                    AND datetime(completed_at) < datetime('now', '-' || ? || ' hours')
                    """,
                    (retention_hours,)
                )
                
                deleted_count = c.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} completed file state records")
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Error cleaning up completed states: {e}")
            return 0

    @performance_track()
    def get_state_statistics(self):
        """
        Get statistics about file processing states
        
        Returns:
            dict: Statistics about current file processing states
        """
        try:
            with self.connection_pool.connection() as conn:
                c = conn.cursor()
                
                # Get counts by state
                c.execute(
                    """
                    SELECT state, COUNT(*) as count 
                    FROM file_processing_states 
                    GROUP BY state
                    """
                )
                
                state_counts = {row[0]: row[1] for row in c.fetchall()}
                
                # Get oldest pending file
                c.execute(
                    """
                    SELECT MIN(datetime(created_at)) as oldest_pending
                    FROM file_processing_states 
                    WHERE state = 'pending'
                    """
                )
                oldest_pending = c.fetchone()[0]
                
                # Get average scan duration
                c.execute(
                    """
                    SELECT AVG(scan_duration_ms) as avg_duration_ms
                    FROM file_processing_states 
                    WHERE scan_duration_ms IS NOT NULL
                    """
                )
                avg_duration = c.fetchone()[0]
                
                return {
                    "state_counts": state_counts,
                    "oldest_pending": oldest_pending,
                    "average_scan_duration_ms": avg_duration,
                    "total_files": sum(state_counts.values())
                }
                
        except Exception as e:
            self.logger.error(f"Error getting state statistics: {e}")
            return {}
