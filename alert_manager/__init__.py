"""Mock alert manager"""
class AlertManager:
    def __init__(self):
        self.alerts = []
    
    def add_alert(self, alert):
        self.alerts.append(alert)
    
    def get_alerts(self):
        return self.alerts
