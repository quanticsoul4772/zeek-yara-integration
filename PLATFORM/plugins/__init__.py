"""
ZYI Plugin System

Provides a flexible plugin architecture for extending the Zeek-YARA Integration
educational platform with custom functionality, educational content, and
integrations.
"""

from .base import BasePlugin, EducationalPlugin, IntegrationPlugin, ScannerPlugin
from .registry import PluginRegistry, plugin_registry

__all__ = [
    "BasePlugin",
    "ScannerPlugin",
    "IntegrationPlugin",
    "EducationalPlugin",
    "plugin_registry",
    "PluginRegistry",
]

# Plugin system version
__version__ = "1.0.0"
