"""Mock Suricata integration"""
class SuricataIntegration:
    def __init__(self, config=None):
        self.config = config or {}
    
    def process_alerts(self, alerts):
        """Process alerts"""
        return alerts
    
    def start(self):
        """Start integration"""
        pass
    
    def stop(self):
        """Stop integration"""
        pass
