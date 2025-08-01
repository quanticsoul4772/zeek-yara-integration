#!/usr/bin/env python3
"""
Base classes and interfaces for alert correlation
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import sqlite3
import json
from datetime import datetime, timedelta


class AlertRetriever(ABC):
    """Abstract base class for alert retrieval"""
    
    @abstractmethod
    def get_alerts(self, conn: sqlite3.Connection, start_time: str) -> List[Dict[str, Any]]:
        """
        Retrieve alerts from a specific source
        
        Args:
            conn (sqlite3.Connection): Database connection
            start_time (str): Start time for retrieving alerts
        
        Returns:
            List of alerts
        """
        pass


class CorrelationStrategy(ABC):
    """Abstract base class for correlation strategies"""
    
    @abstractmethod
    def correlate(self, 
                  yara_alerts: List[Dict[str, Any]], 
                  suricata_alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform correlation between YARA and Suricata alerts
        
        Args:
            yara_alerts (List[Dict]): List of YARA alerts
            suricata_alerts (List[Dict]): List of Suricata alerts
        
        Returns:
            List of correlated alert groups
        """
        pass


class AlertDatabaseManager:
    """
    Manages database operations for alerts and correlations
    """
    
    def __init__(self, db_file: str):
        """
        Initialize database manager
        
        Args:
            db_file (str): Path to SQLite database file
        """
        self.db_file = db_file
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection
        
        Returns:
            sqlite3.Connection: Database connection
        """
        return sqlite3.connect(self.db_file)
    
    def initialize_database(self):
        """
        Initialize database tables and indexes
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                
                # Create correlated alerts table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS correlated_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        correlation_id TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        alert_id TEXT NOT NULL,
                        correlation_confidence INTEGER NOT NULL,
                        correlation_rationale TEXT,
                        correlated_alerts TEXT,
                        threat_intel TEXT,
                        summary TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create YARA alerts table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS yara_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        file_path TEXT,
                        file_name TEXT,
                        file_size INTEGER,
                        file_type TEXT,
                        md5 TEXT,
                        sha256 TEXT,
                        zeek_uid TEXT,
                        rule_name TEXT,
                        rule_namespace TEXT,
                        rule_meta TEXT,
                        strings_matched TEXT,
                        severity INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                c.execute('CREATE INDEX IF NOT EXISTS idx_correlation_id ON correlated_alerts(correlation_id)')
                c.execute('CREATE INDEX IF NOT EXISTS idx_alert_type ON correlated_alerts(alert_type)')
                c.execute('CREATE INDEX IF NOT EXISTS idx_yara_timestamp ON yara_alerts(timestamp)')
                c.execute('CREATE INDEX IF NOT EXISTS idx_yara_rule_name ON yara_alerts(rule_name)')
                
                conn.commit()
        
        except Exception as e:
            raise RuntimeError(f"Error initializing database: {e}")
    
    def store_correlated_alerts(self, correlated_groups: List[Dict[str, Any]]):
        """
        Store correlated alerts in the database
        
        Args:
            correlated_groups (List[Dict]): List of correlated alert groups
        """
        if not correlated_groups:
            return
        
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                
                for group in correlated_groups:
                    # Get primary alert information
                    primary_alert = group.get('primary_alert', {})
                    primary_id = f"{primary_alert.get('source', 'unknown')}_{primary_alert.get('id', 0)}"
                    
                    # Get related alerts
                    related_alerts = group.get('related_alerts', [])
                    related_alerts_json = json.dumps([
                        {
                            'id': alert.get('id', 0),
                            'source': alert.get('source', 'unknown'),
                            'timestamp': alert.get('timestamp', ''),
                            'summary': self._get_alert_summary(alert)
                        }
                        for alert in related_alerts
                    ])
                    
                    # Insert correlation record
                    c.execute('''
                        INSERT INTO correlated_alerts
                        (timestamp, correlation_id, alert_type, alert_id, correlation_confidence,
                         correlation_rationale, correlated_alerts, summary)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        group.get('timestamp', datetime.now().isoformat()),
                        group.get('correlation_id', f"corr_{int(datetime.now().timestamp())}"),
                        primary_alert.get('source', 'unknown'),
                        primary_id,
                        group.get('confidence', 0),
                        group.get('rationale', ''),
                        related_alerts_json,
                        group.get('summary', '')
                    ))
                
                conn.commit()
        
        except Exception as e:
            raise RuntimeError(f"Error storing correlated alerts: {e}")
    
    def _get_alert_summary(self, alert: Dict[str, Any]) -> str:
        """
        Generate a summary for an alert
        
        Args:
            alert (Dict): Alert dictionary
        
        Returns:
            str: Alert summary
        """
        if alert.get('source') == 'yara':
            return f"YARA match: {alert.get('rule_name', 'Unknown rule')} on file {alert.get('file_name', 'Unknown file')}"
        elif alert.get('source') == 'suricata':
            return f"Suricata alert: {alert.get('signature', 'Unknown signature')} from {alert.get('src_ip', 'Unknown')} to {alert.get('dest_ip', 'Unknown')}"
        else:
            return f"Unknown alert type: {alert.get('source', 'unknown')}"
    
    def get_correlated_alerts(self, 
                               filters: Optional[Dict[str, Any]] = None, 
                               limit: Optional[int] = None, 
                               offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve correlated alerts from database
        
        Args:
            filters (Dict, optional): Filtering conditions
            limit (int, optional): Maximum number of results
            offset (int, optional): Number of results to skip
        
        Returns:
            List of correlated alert dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                
                # Base query
                query = "SELECT * FROM correlated_alerts"
                
                # Build where clause
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
                        alert['correlated_alerts'] = json.loads(alert['correlated_alerts'])
                    except:
                        alert['correlated_alerts'] = []
                    
                    try:
                        alert['threat_intel'] = json.loads(alert['threat_intel']) if alert['threat_intel'] else {}
                    except:
                        alert['threat_intel'] = {}
                    
                    results.append(alert)
                
                return results
        
        except Exception as e:
            raise RuntimeError(f"Error retrieving correlated alerts: {e}")
