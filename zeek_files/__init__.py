"""Mock zeek files module"""
class FileExtractor:
    def __init__(self, extract_dir):
        self.extract_dir = extract_dir
    
    def extract(self, filepath):
        """Mock extract"""
        return []
