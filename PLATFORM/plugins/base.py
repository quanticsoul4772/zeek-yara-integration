"""
Base classes for the ZYI plugin system

Provides foundational plugin classes for extending platform functionality
while maintaining educational focus and community contribution standards.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for all ZYI plugins

    All plugins must inherit from this class and implement the required
    abstract methods. Provides common functionality for plugin management,
    configuration, and lifecycle management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the plugin with optional configuration

        Args:
            config: Plugin-specific configuration dictionary
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.version = getattr(self, "VERSION", "1.0.0")
        self.description = getattr(self, "DESCRIPTION", "")
        self.author = getattr(self, "AUTHOR", "Unknown")
        self.educational_value = getattr(self, "EDUCATIONAL_VALUE", "")
        self._initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin

        Called when the plugin is loaded. Should return True if
        initialization was successful, False otherwise.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources

        Called when the plugin is unloaded or the application shuts down.
        Should clean up any resources, connections, or temporary files.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information

        Returns:
            Dict containing plugin metadata and status
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "educational_value": self.educational_value,
            "config": self.config,
            "initialized": self._initialized,
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration

        Override this method to implement custom configuration validation.

        Args:
            config: Configuration dictionary to validate

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return True

    def get_educational_metadata(self) -> Dict[str, Any]:
        """Get educational metadata for this plugin

        Returns information about how this plugin contributes to learning
        objectives and educational outcomes.

        Returns:
            Dict containing educational metadata
        """
        return {
            "learning_objectives": getattr(self, "LEARNING_OBJECTIVES", []),
            "skill_level": getattr(self, "SKILL_LEVEL", "intermediate"),
            "topics_covered": getattr(self, "TOPICS_COVERED", []),
            "prerequisites": getattr(self, "PREREQUISITES", []),
            "estimated_time": getattr(self, "ESTIMATED_TIME", "unknown"),
        }


class ScannerPlugin(BasePlugin):
    """Base class for scanner plugins

    Scanner plugins extend the threat detection capabilities of the platform.
    They can implement custom scanning algorithms, new file type support,
    or specialized detection techniques.
    """

    @abstractmethod
    def scan_file(self, filepath: str) -> Dict[str, Any]:
        """Scan a file and return detection results

        Args:
            filepath: Path to the file to scan

        Returns:
            Dict containing scan results with the following structure:
            {
                'threats_detected': int,
                'detections': List[Dict],
                'scan_time_ms': float,
                'file_info': Dict,
                'metadata': Dict
            }
        """
        pass

    def scan_content(self, content: bytes) -> Dict[str, Any]:
        """Scan raw content and return detection results

        Default implementation creates a temporary file and calls scan_file.
        Override for more efficient in-memory scanning.

        Args:
            content: Raw file content as bytes

        Returns:
            Dict containing scan results
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file.flush()

            try:
                result = self.scan_file(tmp_file.name)
                return result
            finally:
                os.unlink(tmp_file.name)

    def get_supported_types(self) -> List[str]:
        """Get list of supported file types/extensions

        Returns:
            List of file extensions or MIME types supported by this scanner
        """
        return getattr(self, "SUPPORTED_TYPES", ["*"])


class IntegrationPlugin(BasePlugin):
    """Base class for tool integration plugins

    Integration plugins connect external security tools to the platform,
    enabling new data sources, processing capabilities, or output formats.
    """

    @abstractmethod
    def start_service(self) -> bool:
        """Start the integrated service

        Returns:
            bool: True if service started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop_service(self) -> bool:
        """Stop the integrated service

        Returns:
            bool: True if service stopped successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the integrated service

        Returns:
            Dict containing service status information
        """
        pass

    def restart_service(self) -> bool:
        """Restart the integrated service

        Default implementation stops then starts the service.
        Override for more sophisticated restart logic.

        Returns:
            bool: True if restart successful, False otherwise
        """
        if self.stop_service():
            return self.start_service()
        return False

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get JSON schema for configuration validation

        Returns:
            Dict containing JSON schema for validating configuration
        """
        return getattr(self, "CONFIG_SCHEMA", {})


class EducationalPlugin(BasePlugin):
    """Base class for educational content plugins

    Educational plugins provide new learning content, tutorials, assessments,
    or interactive educational experiences.
    """

    @abstractmethod
    def get_tutorials(self) -> List[Dict[str, Any]]:
        """Get available tutorials provided by this plugin

        Returns:
            List of tutorial dictionaries with metadata
        """
        pass

    @abstractmethod
    def run_tutorial(self, tutorial_id: str) -> Dict[str, Any]:
        """Run a specific tutorial

        Args:
            tutorial_id: Unique identifier for the tutorial to run

        Returns:
            Dict containing tutorial execution results
        """
        pass

    def get_assessments(self) -> List[Dict[str, Any]]:
        """Get available assessments provided by this plugin

        Returns:
            List of assessment dictionaries with metadata
        """
        return []

    def run_assessment(self, assessment_id: str) -> Dict[str, Any]:
        """Run a specific assessment

        Args:
            assessment_id: Unique identifier for the assessment to run

        Returns:
            Dict containing assessment results
        """
        raise NotImplementedError("Assessment functionality not implemented")

    def get_interactive_content(self) -> List[Dict[str, Any]]:
        """Get available interactive content

        Returns:
            List of interactive content items with metadata
        """
        return []

    def get_learning_path(self) -> Dict[str, Any]:
        """Get structured learning path provided by this plugin

        Returns:
            Dict describing the learning path structure and progression
        """
        return {
            "name": f"{self.name} Learning Path",
            "description": self.description,
            "modules": [],
            "estimated_duration": "variable",
            "difficulty": "intermediate",
        }


class AnalysisPlugin(BasePlugin):
    """Base class for analysis and correlation plugins

    Analysis plugins provide advanced data analysis, threat correlation,
    or intelligence enrichment capabilities.
    """

    @abstractmethod
    def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze provided data and return insights

        Args:
            data: Input data for analysis

        Returns:
            Dict containing analysis results and insights
        """
        pass

    def correlate_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Correlate multiple events to identify patterns

        Args:
            events: List of event dictionaries to correlate

        Returns:
            Dict containing correlation results
        """
        return {
            "correlations_found": 0,
            "patterns": [],
            "confidence_score": 0.0}

    def enrich_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich data with additional context or intelligence

        Args:
            data: Input data to enrich

        Returns:
            Dict containing enriched data
        """
        return data


class VisualizationPlugin(BasePlugin):
    """Base class for visualization and reporting plugins

    Visualization plugins provide custom dashboards, reports, or
    interactive visualizations for educational and analytical purposes.
    """

    @abstractmethod
    def generate_visualization(
            self, data: Dict[str, Any], viz_type: str) -> Dict[str, Any]:
        """Generate a visualization from provided data

        Args:
            data: Input data for visualization
            viz_type: Type of visualization to generate

        Returns:
            Dict containing visualization data and metadata
        """
        pass

    def get_available_visualizations(self) -> List[str]:
        """Get list of available visualization types

        Returns:
            List of visualization type identifiers
        """
        return []

    def generate_report(
            self, data: Dict[str, Any], report_format: str = "html") -> str:
        """Generate a formatted report from data

        Args:
            data: Input data for report generation
            report_format: Format for the report (html, pdf, etc.)

        Returns:
            Generated report content or file path
        """
        return f"Report generated by {self.name}"
