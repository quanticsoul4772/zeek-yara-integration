"""
ZYI Plugin System

Provides a flexible plugin architecture for extending the Zeek-YARA Integration
educational platform with custom functionality, educational content, and
integrations.
"""

from .base import BasePlugin, EducationalPlugin, IntegrationPlugin, ScannerPlugin

__all__ = [
    "BasePlugin",
    "ScannerPlugin",
    "IntegrationPlugin",
    "EducationalPlugin",
]

# Plugin system version
__version__ = "1.0.0"
