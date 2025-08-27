"""Mock database module"""

import sqlite3
from typing import Any, Dict, List


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(":memory:")

    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()

    def execute(self, query: str, params: tuple = None):
        """Execute query"""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def create_tables(self):
        """Create tables"""
        pass
