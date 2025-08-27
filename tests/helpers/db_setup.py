import json
import os
import sqlite3
import time


def initialize_test_db(db_file, seed_data=True, clear_existing=False):
    """
    Initialize a test database with schema and optional seed data.

    Args:
        db_file (str): Path to the SQLite database file
        seed_data (bool, optional): Whether to insert dummy data. Defaults to True.
        clear_existing (bool, optional): Whether to clear existing data. Defaults to False.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Create Suricata Alerts table
    c.execute(
        """
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
    """
    )

    # Create YARA Alerts table
    c.execute(
        """
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
    """
    )

    # Optional clearing of existing data
    if clear_existing:
        c.execute("DELETE FROM yara_alerts")
        c.execute("DELETE FROM suricata_alerts")

    # Seed data if requested
    if seed_data:
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000000", time.gmtime())

        # Only insert if no existing records
        c.execute("SELECT COUNT(*) FROM yara_alerts")
        yara_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM suricata_alerts")
        suricata_count = c.fetchone()[0]

        if yara_count == 0:
            # YARA Alert sample
            yara_alert = (
                timestamp,
                "/path/to/malicious.exe",
                "malicious.exe",
                1024,
                "application/x-dosexec",
                "abcdef1234567890",
                "1234567890abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmn",
                "CqTvvd2Y19NiSsNN2J",
                "MaliciousExe",
                "malware",
                json.dumps(
                    {"severity": 3, "description": "Detected malicious executable"}
                ),
                json.dumps(["string1", "string2"]),
                3,
            )
            c.execute(
                """
                INSERT INTO yara_alerts
                (timestamp, file_path, file_name, file_size, file_type, md5, sha256, zeek_uid,
                 rule_name, rule_namespace, rule_meta, strings_matched, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                yara_alert,
            )

        if suricata_count == 0:
            # Suricata Alert sample
            suricata_alert = (
                timestamp,
                "alert",
                "192.168.1.100",
                45678,
                "10.0.0.10",
                80,
                "TCP",
                "alert",
                1,
                1000001,
                1,
                "TEST-1 HTTP Traffic",
                "web",
                2,
                json.dumps({"method": "GET", "uri": "/test"}),
                json.dumps({"interface": "eth0", "vlan": None}),
            )
            c.execute(
                """
                INSERT INTO suricata_alerts
                (timestamp, event_type, src_ip, src_port, dest_ip, dest_port, proto,
                 action, gid, sid, rev, signature, category, severity, payload, packet_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                suricata_alert,
            )

    conn.commit()
    conn.close()
