"""Alert correlation module"""
try:
    from .base import AlertDatabaseManager, AlertRetriever, CorrelationStrategy
except ImportError:
    # Mock implementations for testing
    class AlertDatabaseManager:
        pass
    class AlertRetriever:
        pass
    class CorrelationStrategy:
        pass

from .correlator import AlertCorrelator
