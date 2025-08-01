"""
ZYI Plugin System

Provides a flexible plugin architecture for extending the Zeek-YARA Integration
educational platform with custom functionality, educational content, and
integrations.
"""

from .base import BasePlugin, ScannerPlugin, IntegrationPlugin, EducationalPlugin
from .registry import plugin_registry, PluginRegistry

__all__ = [
    'BasePlugin',
    'ScannerPlugin', 
    'IntegrationPlugin',
    'EducationalPlugin',
    'plugin_registry',
    'PluginRegistry'
]

# Plugin system version
__version__ = "1.0.0"