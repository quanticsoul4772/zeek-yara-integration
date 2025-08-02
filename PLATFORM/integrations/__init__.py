"""Mock integrations"""
class ZeekIntegration:
    def __init__(self):
        pass
    
    def process_file(self, filepath):
        return {"status": "processed"}

class YaraIntegration:
    def __init__(self):
        pass
    
    def scan(self, filepath):
        return {"matches": []}
