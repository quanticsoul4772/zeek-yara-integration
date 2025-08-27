"""Mock YARA scanner"""


class YaraScanner:
    def __init__(self, rules_path=None):
        self.rules_path = rules_path

    def scan_file(self, filepath):
        """Mock scan"""
        return []

    def scan_buffer(self, data):
        """Mock scan"""
        return []
