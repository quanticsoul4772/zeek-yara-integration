"""
Enhanced Database Manager with Connection Pooling and Better Error Handling
Created: 2025
"""

import contextlib
import json
import logging
import sqlite3
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import aiosqlite


@dataclass
class ConnectionPoolConfig:
    """Configuration for database connection pool"""
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 30
    idle_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 0.1


class DatabaseError(Exception):
    """Custom database exception"""
    pass


class ConnectionPool:
    """Thread-safe SQLite connection pool"""
    
    def __init__(self, db_path: str, config: ConnectionPoolConfig):
        self.db_path = db_path
        self.config = config
        self._connections = deque()
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(config.max_connections)
        self._created_connections = 0
        self.logger = logging.getLogger(__name__)
        
        # Pre-create minimum connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections"""
        for _ in range(self.config.min_connections):
            conn = self._create_connection()
            if conn:
                self._connections.append(conn)
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection with optimizations"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.connection_timeout,
                check_same_thread=False,
                isolation_level=None  # Auto-commit mode
            )
            
            # Enable performance optimizations
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Balanced durability
            conn.execute("PRAGMA cache_size=10000")  # 10MB cache
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
            
            conn.row_factory = sqlite3.Row  # Enable column access by name
            self._created_connections += 1
            return conn
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to create connection: {e}")
            return None
    
    @contextlib.contextmanager
    def get_connection(self):
        """Get a connection from the pool with context manager support"""
        self._semaphore.acquire()
        conn = None
        
        try:
            with self._lock:
                # Try to get an existing connection
                if self._connections:
                    conn = self._connections.popleft()
                else:
                    # Create new connection if under limit
                    if self._created_connections < self.config.max_connections:
                        conn = self._create_connection()
                    
            if not conn:
                raise DatabaseError("Failed to obtain database connection")
            
            # Test connection is alive
            try:
                conn.execute("SELECT 1")
            except sqlite3.Error:
                # Connection is dead, create a new one
                conn = self._create_connection()
                if not conn:
                    raise DatabaseError("Failed to create new connection")
            
            yield conn
            
        finally:
            # Return connection to pool
            if conn:
                with self._lock:
                    self._connections.append(conn)
            self._semaphore.release()
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            while self._connections:
                conn = self._connections.popleft()
                try:
                    conn.close()
                except Exception:
                    pass
            self._created_connections = 0


class ImprovedDatabaseManager:
    """Enhanced database manager with better performance and error handling"""
    
    def __init__(self, db_path: str, config: Optional[ConnectionPoolConfig] = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.config = config or ConnectionPoolConfig()
        self.pool = ConnectionPool(str(self.db_path), self.config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database schema
        self._init_database()
    
    def _init_database(self):
        """Initialize database with optimized schema"""
        with self.pool.get_connection() as conn:
            # Create tables with proper indexes
            conn.executescript("""
                -- YARA alerts table
                CREATE TABLE IF NOT EXISTS yara_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    rule_name TEXT NOT NULL,
                    tags TEXT,
                    meta TEXT,
                    strings_matched TEXT,
                    severity TEXT,
                    confidence INTEGER
                );
                
                -- Indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_yara_timestamp 
                    ON yara_alerts(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_yara_file_path 
                    ON yara_alerts(file_path);
                CREATE INDEX IF NOT EXISTS idx_yara_rule_name 
                    ON yara_alerts(rule_name);
                CREATE INDEX IF NOT EXISTS idx_yara_severity 
                    ON yara_alerts(severity);
                
                -- File processing state table
                CREATE TABLE IF NOT EXISTS file_states (
                    file_path TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_hash TEXT,
                    scan_time REAL,
                    error_message TEXT
                );
                
                -- Suricata alerts table
                CREATE TABLE IF NOT EXISTS suricata_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    src_ip TEXT,
                    dest_ip TEXT,
                    src_port INTEGER,
                    dest_port INTEGER,
                    proto TEXT,
                    alert_data TEXT,
                    severity INTEGER
                );
                
                -- Indexes for Suricata alerts
                CREATE INDEX IF NOT EXISTS idx_suricata_timestamp 
                    ON suricata_alerts(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_suricata_ips 
                    ON suricata_alerts(src_ip, dest_ip);
                
                -- Correlated incidents table
                CREATE TABLE IF NOT EXISTS correlated_incidents (
                    incident_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence INTEGER,
                    severity TEXT,
                    status TEXT DEFAULT 'active',
                    related_alerts TEXT,
                    common_indicators TEXT
                );
                
                -- Performance statistics table
                CREATE TABLE IF NOT EXISTS performance_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    component TEXT,
                    metric TEXT,
                    value REAL,
                    metadata TEXT
                );
            """)
    
    def store_yara_alert(
        self, 
        file_path: str, 
        rule_name: str,
        tags: List[str] = None,
        meta: Dict[str, Any] = None,
        strings_matched: List[str] = None,
        file_hash: str = None,
        severity: str = None,
        confidence: int = None
    ) -> int:
        """Store a YARA alert with enhanced metadata"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO yara_alerts 
                    (file_path, file_hash, rule_name, tags, meta, 
                     strings_matched, severity, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_path,
                    file_hash,
                    rule_name,
                    json.dumps(tags) if tags else None,
                    json.dumps(meta) if meta else None,
                    json.dumps(strings_matched) if strings_matched else None,
                    severity,
                    confidence
                ))
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to store YARA alert: {e}")
            raise DatabaseError(f"Failed to store alert: {e}")
    
    def get_alerts(
        self,
        limit: int = 100,
        offset: int = 0,
        severity: str = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Retrieve alerts with filtering and pagination"""
        try:
            with self.pool.get_connection() as conn:
                query = "SELECT * FROM yara_alerts WHERE 1=1"
                params = []
                
                if severity:
                    query += " AND severity = ?"
                    params.append(severity)
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve alerts: {e}")
            return []
    
    def update_file_state(
        self,
        file_path: str,
        state: str,
        error_message: str = None,
        file_hash: str = None,
        scan_time: float = None
    ):
        """Update file processing state with UPSERT"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    INSERT INTO file_states (file_path, state, error_message, file_hash, scan_time)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(file_path) DO UPDATE SET
                        state = excluded.state,
                        timestamp = CURRENT_TIMESTAMP,
                        error_message = excluded.error_message,
                        file_hash = COALESCE(excluded.file_hash, file_hash),
                        scan_time = COALESCE(excluded.scan_time, scan_time)
                """, (file_path, state, error_message, file_hash, scan_time))
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to update file state: {e}")
            raise DatabaseError(f"Failed to update state: {e}")
    
    def get_file_state(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file processing state"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM file_states WHERE file_path = ?",
                    (file_path,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get file state: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics and metrics"""
        try:
            with self.pool.get_connection() as conn:
                stats = {}
                
                # Alert counts
                cursor = conn.execute(
                    "SELECT COUNT(*) as total, COUNT(DISTINCT rule_name) as unique_rules "
                    "FROM yara_alerts"
                )
                stats['yara_alerts'] = dict(cursor.fetchone())
                
                # File processing stats
                cursor = conn.execute(
                    "SELECT state, COUNT(*) as count FROM file_states GROUP BY state"
                )
                stats['file_states'] = {row['state']: row['count'] for row in cursor}
                
                # Recent activity
                cursor = conn.execute("""
                    SELECT 
                        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                        COUNT(*) as alerts
                    FROM yara_alerts
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY hour
                    ORDER BY hour DESC
                """)
                stats['recent_activity'] = [dict(row) for row in cursor.fetchall()]
                
                return stats
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove old data to maintain database size"""
        try:
            with self.pool.get_connection() as conn:
                cutoff_date = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                
                # Delete old alerts
                conn.execute(
                    "DELETE FROM yara_alerts WHERE timestamp < datetime('now', ?)",
                    (f'-{days_to_keep} days',)
                )
                
                # Delete old file states
                conn.execute(
                    "DELETE FROM file_states WHERE timestamp < datetime('now', ?)",
                    (f'-{days_to_keep} days',)
                )
                
                # Vacuum to reclaim space
                conn.execute("VACUUM")
                
                self.logger.info(f"Cleaned up data older than {days_to_keep} days")
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def close(self):
        """Close all database connections"""
        self.pool.close_all()


# Async version for high-performance scenarios
class AsyncDatabaseManager:
    """Async database manager for high-concurrency scenarios"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    async def init_database(self):
        """Initialize database asynchronously"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.executescript("""
                -- Same schema as sync version
                CREATE TABLE IF NOT EXISTS yara_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    tags TEXT,
                    meta TEXT
                );
            """)
            await db.commit()
    
    async def store_alert_async(self, file_path: str, rule_name: str, **kwargs):
        """Store alert asynchronously"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "INSERT INTO yara_alerts (file_path, rule_name, tags, meta) VALUES (?, ?, ?, ?)",
                (file_path, rule_name, 
                 json.dumps(kwargs.get('tags')),
                 json.dumps(kwargs.get('meta')))
            )
            await db.commit()