#!/usr/bin/env python3
"""
Interactive Help System for Educational Security Platform
Provides context-aware guidance and assistance
"""

import json
import os
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class HelpTopic:
    """Represents a help topic with content and metadata."""

    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    difficulty: str
    related_topics: List[str]
    quick_actions: List[Dict[str, str]]


class ContextualHelpSystem:
    """Provides context-aware help and guidance for users."""

    def __init__(self, config: Dict, console: Optional[Console] = None):
        self.config = config
        self.console = console or (Console() if RICH_AVAILABLE else None)
        self.project_root = Path(config.get("PROJECT_ROOT", "."))
        self.help_topics = self.load_help_topics()
        self.user_context = self.detect_user_context()

    def detect_user_context(self) -> Dict[str, any]:
        """Detect current user context for contextual help."""
        context = {
            "experience_level": self.config.get(
                "EXPERIENCE_LEVEL",
                "beginner"),
            "platform_mode": self.config.get(
                "PLATFORM_MODE",
                "educational"),
            "tools_available": self.config.get(
                "TOOLS_ENABLED",
                {}),
            "tutorial_mode": self.config.get(
                "TUTORIAL_MODE",
                True),
            "current_task": "general_use",
            "last_action": None,
            "common_issues": self.detect_common_issues(),
        }
        return context

    def detect_common_issues(self) -> List[str]:
        """Detect common issues the user might be experiencing."""
        issues = []

        # Check if tools are properly configured
        tools_enabled = self.config.get("TOOLS_ENABLED", {})
        if not any(tools_enabled.values()):
            issues.append("no_tools_configured")

        # Check if first-time user
        if self.config.get("SETUP_COMPLETED", False) == False:
            issues.append("first_time_user")

        # Check for common directory issues
        extract_dir = Path(self.config.get("EXTRACT_DIR", ""))
        if not extract_dir.exists():
            issues.append("missing_directories")

        return issues

    def load_help_topics(self) -> Dict[str, HelpTopic]:
        """Load help topics and documentation."""
        topics = {
            "getting_started": HelpTopic(
                id="getting_started",
                title="Getting Started Guide",
                content="""
# Getting Started with the Security Platform

Welcome to your network security learning journey! This guide will help you get up and running quickly.

## First Steps
1. **Run Setup**: If you haven't already, run the setup wizard to configure your tools
2. **Learn the Basics**: Start with the "Network Security Fundamentals" tutorial
3. **Try a Detection**: Create your first malware detection with the EICAR test
4. **Explore the Dashboard**: Open the web interface to see real-time monitoring

## Quick Tips for Beginners
- Start with tutorial mode enabled for guided learning
- Use the web dashboard for an overview of all activity
- Don't worry about advanced features initially
- Focus on understanding concepts before diving into configuration

## Need More Help?
- Type 'help tutorials' to see available learning materials
- Type 'help troubleshooting' for common issues
- Use 'help search <topic>' to find specific information
                """,
                category="basics",
                tags=["beginner", "setup", "overview"],
                difficulty="beginner",
                related_topics=["tutorials", "setup", "dashboard"],
                quick_actions=[
                    {"action": "run_setup", "label": "Run Setup Wizard"},
                    {"action": "start_tutorial", "label": "Start First Tutorial"},
                    {"action": "open_dashboard", "label": "Open Web Dashboard"},
                ],
            ),
            "tutorials": HelpTopic(
                id="tutorials",
                title="Available Tutorials",
                content="""
# Interactive Tutorials

Our platform includes step-by-step tutorials designed for hands-on learning.

## Beginner Tutorials
- **Network Security Fundamentals**: Learn the basics of network security monitoring
- **Your First Threat Detection**: Detect malware using YARA and EICAR test file
- **Network Monitoring with Zeek**: Monitor traffic and extract files
- **Intrusion Detection with Suricata**: Detect network attacks

## Intermediate Tutorials
- **Writing Custom YARA Rules**: Create your own malware detection rules
- **Alert Correlation**: Combine alerts from multiple security tools
- **Advanced Network Analysis**: Deep dive into traffic analysis techniques

## Tutorial Features
- **Guided Learning**: Step-by-step instructions with explanations
- **Hands-On Practice**: Real examples and interactive exercises
- **Progress Tracking**: Track your learning progress and achievements
- **Adaptive Content**: Content adjusts based on your experience level

## How to Access Tutorials
1. From the main menu, select "Start Interactive Tutorial"
2. Choose a tutorial appropriate for your experience level
3. Follow the step-by-step instructions
4. Complete hands-on exercises to reinforce learning
                """,
                category="learning",
                tags=["tutorials", "education", "learning"],
                difficulty="all",
                related_topics=["getting_started", "achievements"],
                quick_actions=[
                    {"action": "show_tutorials", "label": "View Available Tutorials"},
                    {"action": "start_beginner_tutorial",
                        "label": "Start Beginner Tutorial"},
                    {"action": "show_progress", "label": "Show My Progress"},
                ],
            ),
            "tools_overview": HelpTopic(
                id="tools_overview",
                title="Security Tools Overview",
                content="""
# Security Tools in the Platform

This platform integrates three powerful open-source security tools for comprehensive monitoring.

## Zeek (Network Analysis)
**Purpose**: Monitors network traffic and extracts files
**What it does**:
- Analyzes all network communications in real-time
- Extracts files transferred over the network
- Creates detailed logs of network connections
- Provides visibility into network protocols and behavior

**When to use**: Monitoring network activity, investigating suspicious connections, extracting files for analysis

## YARA (Malware Detection)
**Purpose**: Detects malware and suspicious files
**What it does**:
- Scans files using pattern-matching rules
- Identifies known malware families and variants
- Detects suspicious file characteristics
- Provides detailed information about matches

**When to use**: Scanning extracted files, detecting malware, analyzing suspicious files

## Suricata (Intrusion Detection)
**Purpose**: Detects network intrusions and attacks
**What it does**:
- Monitors network traffic for attack patterns
- Detects intrusion attempts and suspicious behavior
- Generates real-time alerts for security events
- Can block malicious traffic (when configured as IPS)

**When to use**: Detecting network attacks, monitoring for intrusions, blocking malicious traffic

## How They Work Together
1. **Zeek** monitors network traffic and extracts files
2. **YARA** scans extracted files for malware
3. **Suricata** watches for attack patterns in the same traffic
4. **Alert Correlation** combines insights from all three tools

This layered approach provides comprehensive security coverage!
                """,
                category="tools",
                tags=["zeek", "yara", "suricata", "overview"],
                difficulty="beginner",
                related_topics=["zeek_help", "yara_help", "suricata_help"],
                quick_actions=[
                    {"action": "check_tool_status", "label": "Check Tool Status"},
                    {"action": "configure_tools", "label": "Configure Tools"},
                    {"action": "test_tools", "label": "Test Tool Detection"},
                ],
            ),
            "troubleshooting": HelpTopic(
                id="troubleshooting",
                title="Troubleshooting Common Issues",
                content="""
# Troubleshooting Guide

Common issues and their solutions for the educational security platform.

## Setup and Installation Issues

### "No tools configured" or "Tools not available"
**Symptoms**: Platform shows no security tools are available
**Solutions**:
1. Run the setup wizard: `python setup_wizard.py`
2. Install missing tools manually (see tool-specific help)
3. Check tool paths in configuration files

### "Permission denied" errors
**Symptoms**: Cannot access files or start services
**Solutions**:
1. Ensure you have appropriate permissions for the project directory
2. On Linux/macOS, you may need to run with sudo for network monitoring
3. Check that the virtual environment is activated

### "Port already in use" error
**Symptoms**: Web interface won't start
**Solutions**:
1. Check if another instance is running: `ps aux | grep python`
2. Kill existing processes or change the port in configuration
3. Default port is 8000, try changing to 8001 or 8080

## Detection and Monitoring Issues

### "No files being extracted"
**Symptoms**: No files appear in the extracted_files directory
**Solutions**:
1. Verify Zeek is properly configured and running
2. Check network interface configuration
3. Generate test traffic or use PCAP files for testing
4. Ensure you have permission to monitor the network interface

### "YARA rules not working"
**Symptoms**: No malware detections from YARA scanner
**Solutions**:
1. Check that YARA rules exist in the rules directory
2. Verify YARA Python module is installed: `pip list | grep yara`
3. Test with EICAR file to verify detection works
4. Check scanner logs for error messages

### "Web dashboard not showing data"
**Symptoms**: Dashboard loads but shows no alerts or data
**Solutions**:
1. Check that the API server is running
2. Verify database connections
3. Generate test data with EICAR file
4. Check browser console for JavaScript errors

## Performance Issues

### "Platform running slowly"
**Solutions**:
1. Reduce scan frequency in configuration
2. Limit file size for scanning
3. Ensure adequate system resources (RAM, CPU)
4. Check for large log files that need rotation

### "High CPU usage"
**Solutions**:
1. Reduce number of scanner threads
2. Limit network monitoring scope
3. Optimize YARA rules for better performance
4. Consider using more selective file scanning

## Getting Additional Help

### Log Files to Check
- **General platform logs**: `logs/yara_scan.log`
- **API server logs**: `logs/api.log`
- **Suricata logs**: `logs/suricata/`

### Useful Commands for Diagnosis
- Check running processes: `ps aux | grep -E "(python|zeek|suricata)"`
- Check port usage: `netstat -tlnp | grep 8000`
- Check system resources: `top` or `htop`
- Test network connectivity: `ping google.com`

### Getting Community Help
- Check GitHub issues for similar problems
- Join community discussions
- Provide log excerpts when asking for help (remove sensitive information)
                """,
                category="support",
                tags=["troubleshooting", "issues", "problems", "errors"],
                difficulty="all",
                related_topics=["setup", "tools_overview", "configuration"],
                quick_actions=[
                    {"action": "run_diagnostics", "label": "Run System Diagnostics"},
                    {"action": "check_logs", "label": "View Recent Logs"},
                    {"action": "restart_services", "label": "Restart Services"},
                ],
            ),
            "dashboard": HelpTopic(
                id="dashboard",
                title="Using the Web Dashboard",
                content="""
# Web Dashboard Guide

The web dashboard provides a centralized view of all security monitoring activity.

## Dashboard Sections

### Overview Page
- **Real-time status** of all security tools
- **Recent alerts** from YARA, Suricata, and correlation engine
- **System health** indicators and performance metrics
- **Quick actions** for common tasks

### Alerts and Detections
- **YARA detections**: Malware found in extracted files
- **Suricata alerts**: Network intrusion attempts and suspicious activity
- **Correlated events**: Related alerts from multiple tools
- **Alert details**: Click any alert for detailed information

### Network Analysis
- **Traffic overview**: Summary of network communications
- **File extractions**: Files captured from network traffic
- **Connection logs**: Detailed network connection information
- **Protocol analysis**: Breakdown of network protocols observed

### Tools Status
- **Zeek status**: Network monitoring activity and statistics
- **YARA scanner**: Scanning progress and detection statistics
- **Suricata**: IDS/IPS status and rule update information
- **API server**: System health and performance metrics

## Navigation Tips

### For Beginners
- Start with the Overview page for a high-level view
- Focus on the Alerts section to see detections
- Use the help tooltips (hover over ? icons)
- Don't worry about advanced metrics initially

### For Advanced Users
- Customize alert filters to focus on specific threats
- Use the search functionality to find specific events
- Export data for external analysis
- Configure custom dashboards for specific use cases

## Common Tasks

### Investigating an Alert
1. Click on the alert in the alerts list
2. Review the alert details and context
3. Check related events and correlations
4. Follow recommended response actions

### Monitoring System Health
1. Check the Overview page for system status
2. Review performance metrics in Tools Status
3. Monitor log file sizes and system resources
4. Verify all components are running properly

### Generating Test Data
1. Use the "Detection Demo" feature to create test alerts
2. Upload sample files for YARA scanning
3. Generate network traffic for Zeek analysis
4. Verify all tools are detecting properly

## Troubleshooting Dashboard Issues

### Dashboard won't load
- Check that the API server is running (main menu option)
- Verify port 8000 is accessible: http://localhost:8000
- Check browser console for JavaScript errors
- Try refreshing the page or clearing browser cache

### No data showing
- Ensure security tools are running and configured
- Generate test data with EICAR file
- Check that database is accessible
- Verify API endpoints are responding

### Slow performance
- Check system resources (CPU, memory, disk)
- Optimize database queries if needed
- Consider reducing real-time update frequency
- Clear old log data if disk space is low
                """,
                category="interface",
                tags=["dashboard", "web", "interface", "monitoring"],
                difficulty="beginner",
                related_topics=["alerts", "monitoring", "troubleshooting"],
                quick_actions=[
                    {"action": "open_dashboard", "label": "Open Web Dashboard"},
                    {"action": "demo_detection", "label": "Generate Test Data"},
                    {"action": "check_api_status", "label": "Check API Status"},
                ],
            ),
            "configuration": HelpTopic(
                id="configuration",
                title="Platform Configuration",
                content="""
# Platform Configuration Guide

Learn how to configure the educational security platform for your needs.

## Configuration Files

### Educational Configuration (`config/educational_config.json`)
Generated by the setup wizard, contains user-friendly settings:
- **Experience level**: Adjusts interface complexity
- **Learning goals**: Customizes available features
- **Tool paths**: Locations of security tools
- **Educational features**: Tutorial mode, guided workflows

### Default Configuration (`config/default_config.json`)
Enterprise-grade configuration with advanced options:
- **Detailed logging**: Comprehensive log settings
- **Performance tuning**: Thread counts, memory limits
- **Advanced features**: Correlation windows, API keys
- **Network settings**: Interface configuration, capture options

## Key Configuration Options

### User Experience Settings
```json
{
  "EXPERIENCE_LEVEL": "beginner|intermediate|advanced",
  "TUTORIAL_MODE": true,
  "BEGINNER_MODE": true,
  "SHOW_EXPLANATIONS": true
}
```

### Tool Configuration
```json
{
  "TOOLS_ENABLED": {
    "zeek": true,
    "yara": true,
    "suricata": true
  },
  "ZEEK_PATH": "/usr/local/bin/zeek",
  "SURICATA_PATH": "/usr/bin/suricata"
}
```

### Directory Settings
```json
{
  "EXTRACT_DIR": "./extracted_files",
  "RULES_DIR": "./rules",
  "LOG_DIR": "./logs",
  "DB_FILE": "./logs/alerts.db"
}
```

### Performance Settings
```json
{
  "SCAN_INTERVAL": 30,
  "MAX_FILE_SIZE": 20971520,
  "THREADS": 2,
  "DETAILED_LOGGING": false
}
```

## Beginner vs Advanced Mode

### Beginner Mode Features
- Simplified interface with fewer options
- Guided workflows and tutorials
- Automatic service startup
- Conservative performance settings
- Extensive explanations and help text

### Advanced Mode Features
- Full configuration access
- Manual service control
- Performance optimization options
- Detailed logging and metrics
- Advanced correlation settings

## Network Interface Configuration

### Automatic Detection
The setup wizard attempts to automatically detect your network interfaces.
Common interface names:
- **Linux**: eth0, wlan0, enp0s3
- **macOS**: en0, en1, utun0
- **Windows**: "Local Area Connection", "Wi-Fi"

### Manual Configuration
If automatic detection fails:
1. List available interfaces: `ip link show` (Linux) or `ifconfig` (macOS)
2. Update configuration file with correct interface name
3. Restart the platform

## Rule Management

### YARA Rules
- **Location**: `rules/active/` directory
- **Organization**: Subdirectories by malware type
- **Updates**: Manual or automatic rule updates
- **Custom rules**: Add your own detection rules

### Suricata Rules
- **Location**: `rules/suricata/` directory
- **Updates**: Automatic from online sources
- **Custom rules**: Add to `local.rules` file
- **Management**: Use `update_suricata_rules.sh` script

## Educational Features Configuration

### Tutorial System
```json
{
  "TUTORIAL_MODE": true,
  "GUIDED_WORKFLOWS": true,
  "ACHIEVEMENT_TRACKING": true,
  "PROGRESS_REPORTING": true
}
```

### Help System
```json
{
  "INTERACTIVE_HELP": true,
  "CONTEXT_AWARE_GUIDANCE": true,
  "BEGINNER_TIPS": true
}
```

## Troubleshooting Configuration Issues

### Invalid Configuration
- Check JSON syntax with online validator
- Ensure all required fields are present
- Verify file paths exist and are accessible
- Check permissions on configuration directories

### Tool Path Issues
- Use absolute paths when possible
- Verify tools are installed and in PATH
- Test tool execution manually
- Check platform-specific path formats

### Performance Problems
- Adjust thread counts based on CPU cores
- Increase scan intervals for slower systems
- Reduce file size limits if needed
- Monitor system resources during operation
                """,
                category="configuration",
                tags=["config", "setup", "customization", "performance"],
                difficulty="intermediate",
                related_topics=["setup", "troubleshooting", "tools_overview"],
                quick_actions=[
                    {"action": "edit_config", "label": "Edit Configuration"},
                    {"action": "validate_config", "label": "Validate Configuration"},
                    {"action": "reset_config", "label": "Reset to Defaults"},
                ],
            ),
        }

        return topics

    def show_help_menu(self) -> Optional[str]:
        """Show main help menu."""
        if self.console:
            # Create help menu with contextual suggestions
            self.console.print(
                "\n🎯 Interactive Help System", style="bold blue")

            # Show contextual help first
            if self.user_context["common_issues"]:
                self.console.print(
                    "\n⚠️ Detected Issues - Quick Help:", style="yellow")
                for issue in self.user_context["common_issues"]:
                    suggestion = self.get_contextual_suggestion(issue)
                    self.console.print(f"  • {suggestion}")

            # Show experience-appropriate topics
            level = self.user_context["experience_level"]
            topics = self.get_topics_for_level(level)

            table = Table(title=f"📚 Help Topics (for {level.title()} users)")
            table.add_column("ID", style="cyan")
            table.add_column("Topic", style="green")
            table.add_column("Category", style="yellow")
            table.add_column("Description", style="white")

            for i, (topic_id, topic) in enumerate(topics.items(), 1):
                description = topic.content.split("\n")[2].strip()[:60] + "..."
                table.add_row(str(i), topic.title,
                              topic.category.title(), description)

            self.console.print(table)

            # Add search and other options
            self.console.print("\nOther options:")
            self.console.print(
                "• Type 'search <keyword>' to search help topics")
            self.console.print("• Type 'quick' for quick help commands")
            self.console.print("• Type '0' to return to main menu")

            choice = Prompt.ask("Select topic or enter command", default="1")
        else:
            print("\nInteractive Help System")
            print("-" * 30)

            # Show contextual help
            if self.user_context["common_issues"]:
                print("\nDetected Issues - Quick Help:")
                for issue in self.user_context["common_issues"]:
                    suggestion = self.get_contextual_suggestion(issue)
                    print(f"  • {suggestion}")

            # Show help topics
            level = self.user_context["experience_level"]
            topics = self.get_topics_for_level(level)

            print(f"\nHelp Topics (for {level.title()} users):")
            for i, (topic_id, topic) in enumerate(topics.items(), 1):
                print(f"{i}. {topic.title} ({topic.category.title()})")

            print("\nOther options:")
            print("• Type 'search <keyword>' to search help topics")
            print("• Type 'quick' for quick help commands")
            print("• Type '0' to return to main menu")

            choice = input("Select topic or enter command: ").strip()

        return self.process_help_choice(choice, topics)

    def get_topics_for_level(self, level: str) -> Dict[str, HelpTopic]:
        """Get help topics appropriate for user's experience level."""
        if level == "beginner":
            relevant_topics = [
                "getting_started",
                "tutorials",
                "tools_overview",
                "dashboard",
                "troubleshooting",
            ]
        elif level == "intermediate":
            relevant_topics = [
                "tools_overview",
                "configuration",
                "troubleshooting",
                "tutorials",
                "dashboard",
            ]
        else:  # advanced
            relevant_topics = [
                "configuration",
                "troubleshooting",
                "tools_overview",
                "tutorials"]

        return {
            topic_id: self.help_topics[topic_id]
            for topic_id in relevant_topics
            if topic_id in self.help_topics
        }

    def get_contextual_suggestion(self, issue: str) -> str:
        """Get contextual suggestion for common issues."""
        suggestions = {
            "no_tools_configured": "Run 'python setup_wizard.py' to configure security tools",
            "first_time_user": "Start with the 'Getting Started' tutorial for new users",
            "missing_directories": "Some required directories are missing - check configuration",
        }
        return suggestions.get(issue, f"Issue detected: {issue}")

    def process_help_choice(
            self, choice: str, topics: Dict[str, HelpTopic]) -> Optional[str]:
        """Process user's help menu choice."""
        choice = choice.strip().lower()

        if choice == "0":
            return None
        elif choice.startswith("search "):
            keyword = choice[7:].strip()
            return self.search_help(keyword)
        elif choice == "quick":
            return self.show_quick_help()
        else:
            # Try to parse as topic number
            try:
                topic_index = int(choice) - 1
                topic_list = list(topics.keys())
                if 0 <= topic_index < len(topic_list):
                    return self.show_help_topic(topic_list[topic_index])
            except ValueError:
                pass

            # Try to match as topic name
            for topic_id, topic in topics.items():
                if choice in topic.title.lower() or choice == topic_id:
                    return self.show_help_topic(topic_id)

        if self.console:
            self.console.print(
                f"❌ Unknown help topic or command: {choice}", style="red")
        else:
            print(f"Unknown help topic or command: {choice}")

        return "menu"  # Return to menu

    def show_help_topic(self, topic_id: str) -> str:
        """Show detailed help for a specific topic."""
        if topic_id not in self.help_topics:
            self.log(f"Help topic '{topic_id}' not found", "error")
            return "menu"

        topic = self.help_topics[topic_id]

        if self.console:
            # Show topic content
            if topic.content.startswith("#"):
                # Render as markdown if rich is available
                content = Markdown(topic.content)
                self.console.print(content)
            else:
                panel = Panel(
                    topic.content.strip(),
                    title=f"📖 {topic.title}",
                    border_style="blue",
                    padding=(1, 2),
                )
                self.console.print(panel)

            # Show quick actions if available
            if topic.quick_actions:
                self.console.print("\n🚀 Quick Actions:", style="bold green")
                for i, action in enumerate(topic.quick_actions, 1):
                    self.console.print(f"{i}. {action['label']}")

                self.console.print("0. Back to help menu")

                action_choice = Prompt.ask(
                    "Select an action",
                    choices=[str(i)
                             for i in range(len(topic.quick_actions) + 1)],
                    default="0",
                )

                if action_choice != "0":
                    try:
                        action_index = int(action_choice) - 1
                        action = topic.quick_actions[action_index]
                        self.execute_quick_action(action["action"])
                    except (ValueError, IndexError):
                        pass
        else:
            print(f"\n=== {topic.title} ===")
            print(topic.content.strip())

            if topic.quick_actions:
                print("\nQuick Actions:")
                for i, action in enumerate(topic.quick_actions, 1):
                    print(f"{i}. {action['label']}")
                print("0. Back to help menu")

                action_choice = input("Select an action: ").strip()
                if action_choice != "0":
                    try:
                        action_index = int(action_choice) - 1
                        if 0 <= action_index < len(topic.quick_actions):
                            action = topic.quick_actions[action_index]
                            self.execute_quick_action(action["action"])
                    except (ValueError, IndexError):
                        pass

        return "menu"

    def search_help(self, keyword: str) -> str:
        """Search help topics for keyword."""
        results = []
        keyword_lower = keyword.lower()

        for topic_id, topic in self.help_topics.items():
            score = 0

            # Check title
            if keyword_lower in topic.title.lower():
                score += 10

            # Check content
            if keyword_lower in topic.content.lower():
                score += 5

            # Check tags
            for tag in topic.tags:
                if keyword_lower in tag.lower():
                    score += 3

            if score > 0:
                results.append((topic_id, topic, score))

        # Sort by relevance score
        results.sort(key=lambda x: x[2], reverse=True)

        if not results:
            self.log(f"No help topics found for '{keyword}'", "warning")
            return "menu"

        if self.console:
            table = Table(title=f"🔍 Search Results for '{keyword}'")
            table.add_column("ID", style="cyan")
            table.add_column("Topic", style="green")
            table.add_column("Relevance", style="yellow")
            table.add_column("Category", style="blue")

            for i, (topic_id, topic, score) in enumerate(results[:5], 1):
                relevance = "●" * min(score // 2, 5)
                table.add_row(str(i), topic.title, relevance,
                              topic.category.title())

            self.console.print(table)

            if len(results) > 5:
                self.console.print(f"... and {len(results) - 5} more results")

            choice = Prompt.ask(
                "Select a topic to view",
                choices=[str(i) for i in range(
                    1, min(len(results), 5) + 1)] + ["0"],
                default="0",
            )

            if choice != "0":
                try:
                    result_index = int(choice) - 1
                    topic_id = results[result_index][0]
                    return self.show_help_topic(topic_id)
                except (ValueError, IndexError):
                    pass
        else:
            print(f"\nSearch Results for '{keyword}':")
            print("-" * 40)
            for i, (topic_id, topic, score) in enumerate(results[:5], 1):
                print(f"{i}. {topic.title} ({topic.category.title()})")

            if len(results) > 5:
                print(f"... and {len(results) - 5} more results")

            choice = input("Select a topic to view (0 to return): ").strip()
            if choice != "0":
                try:
                    result_index = int(choice) - 1
                    if 0 <= result_index < min(len(results), 5):
                        topic_id = results[result_index][0]
                        return self.show_help_topic(topic_id)
                except (ValueError, IndexError):
                    pass

        return "menu"

    def show_quick_help(self) -> str:
        """Show quick help commands."""
        if self.console:
            quick_help_text = """
🚀 Quick Help Commands

**Platform Control:**
• python main.py --setup        → Run setup wizard
• python main.py --tutorial     → Start interactive tutorial
• python main.py --demo         → Run detection demonstration
• python main.py --web-only     → Start web interface only

**Tool Management:**
• python setup_wizard.py        → Configure security tools
• ./start_platform.sh           → Start complete platform (Linux/macOS)
• start_platform.bat            → Start complete platform (Windows)

**Troubleshooting:**
• Check logs in: logs/
• View tool status in web dashboard
• Run EICAR test to verify detection
• Check configuration: config/educational_config.json

**Learning Resources:**
• Tutorials available in main menu
• Documentation in docs/ folder
• Examples in EDUCATION/ folder
• Community help on GitHub

**Emergency Commands:**
• Ctrl+C to stop any running process
• pkill -f "python.*main.py" to stop all platform processes
• ps aux | grep python to see running processes
            """

            panel = Panel(
                quick_help_text.strip(),
                title="⚡ Quick Help Reference",
                border_style="green",
                padding=(1, 2),
            )
            self.console.print(panel)
        else:
            print("\nQuick Help Commands:")
            print("-" * 30)
            print("Platform Control:")
            print("• python main.py --setup        → Run setup wizard")
            print("• python main.py --tutorial     → Start interactive tutorial")
            print("• python main.py --demo         → Run detection demonstration")
            print("\nTool Management:")
            print("• python setup_wizard.py        → Configure security tools")
            print("• ./start_platform.sh           → Start complete platform")
            print("\nTroubleshooting:")
            print("• Check logs in: logs/")
            print("• View tool status in web dashboard")
            print("• Run EICAR test to verify detection")

        if self.console:
            Prompt.ask("Press Enter to continue", default="")
        else:
            input("Press Enter to continue...")

        return "menu"

    def execute_quick_action(self, action: str):
        """Execute a quick action from help topic."""
        try:
            if action == "run_setup":
                self.log("Starting setup wizard...")
                subprocess.Popen([sys.executable, "setup_wizard.py"])

            elif action == "start_tutorial":
                self.log("Starting tutorial system...")
                subprocess.Popen([sys.executable, "main.py", "--tutorial"])

            elif action == "open_dashboard":
                port = self.config.get("API_PORT", 8000)
                url = f"http://localhost:{port}"
                self.log(f"Opening dashboard at {url}")
                webbrowser.open(url)

            elif action == "demo_detection":
                self.log("Running detection demo...")
                subprocess.Popen([sys.executable, "main.py", "--demo"])

            elif action == "check_tool_status":
                self.show_tool_status()

            elif action == "run_diagnostics":
                self.run_system_diagnostics()

            elif action == "check_logs":
                self.show_recent_logs()

            else:
                self.log(
                    f"Quick action '{action}' not implemented yet", "warning")

        except Exception as e:
            self.log(f"Failed to execute action '{action}': {e}", "error")

    def show_tool_status(self):
        """Show current status of security tools."""
        if self.console:
            status_table = Table(title="🔧 Security Tools Status")
            status_table.add_column("Tool", style="cyan")
            status_table.add_column("Status", style="green")
            status_table.add_column("Details", style="yellow")

            tools_enabled = self.config.get("TOOLS_ENABLED", {})
            for tool, enabled in tools_enabled.items():
                status = "✅ Enabled" if enabled else "❌ Disabled"
                details = "Ready for use" if enabled else "Configuration required"
                status_table.add_row(tool.upper(), status, details)

            self.console.print(status_table)
        else:
            print("\nSecurity Tools Status:")
            print("-" * 30)
            tools_enabled = self.config.get("TOOLS_ENABLED", {})
            for tool, enabled in tools_enabled.items():
                status = "Enabled" if enabled else "Disabled"
                print(f"{tool.upper()}: {status}")

    def run_system_diagnostics(self):
        """Run basic system diagnostics."""
        self.log("Running system diagnostics...")

        diagnostics = []

        # Check Python version
        python_version = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        diagnostics.append(f"Python version: {python_version}")

        # Check project directory
        project_exists = self.project_root.exists()
        diagnostics.append(
            f"Project directory: {
                '✅ Found' if project_exists else '❌ Missing'}")

        # Check configuration
        config_path = self.project_root / "config" / "educational_config.json"
        config_exists = config_path.exists()
        diagnostics.append(
            f"Configuration: {'✅ Found' if config_exists else '❌ Missing'}")

        # Check virtual environment
        venv_path = self.project_root / "venv"
        venv_exists = venv_path.exists()
        diagnostics.append(
            f"Virtual environment: {
                '✅ Found' if venv_exists else '❌ Missing'}")

        # Display results
        if self.console:
            for diagnostic in diagnostics:
                self.console.print(f"• {diagnostic}")
        else:
            print("\nSystem Diagnostics:")
            for diagnostic in diagnostics:
                print(f"• {diagnostic}")

    def show_recent_logs(self):
        """Show recent log entries."""
        log_dir = Path(self.config.get("LOG_DIR", "logs"))

        if not log_dir.exists():
            self.log("Log directory not found", "warning")
            return

        # Find recent log files
        log_files = list(log_dir.glob("*.log"))
        if not log_files:
            self.log("No log files found", "warning")
            return

        # Show most recent entries from main log
        main_log = log_dir / "yara_scan.log"
        if main_log.exists():
            try:
                with open(main_log, "r") as f:
                    lines = f.readlines()
                    recent_lines = lines[-10:] if len(lines) > 10 else lines

                if self.console:
                    self.console.print(
                        "📋 Recent Log Entries:", style="bold blue")
                    for line in recent_lines:
                        self.console.print(f"  {line.strip()}")
                else:
                    print("\nRecent Log Entries:")
                    for line in recent_lines:
                        print(f"  {line.strip()}")

            except Exception as e:
                self.log(f"Error reading log file: {e}", "error")
        else:
            self.log("Main log file not found", "warning")

    def log(self, message: str, level: str = "info"):
        """Log help system messages."""
        if self.console:
            if level == "success":
                self.console.print(f"✅ {message}", style="green")
            elif level == "warning":
                self.console.print(f"⚠️ {message}", style="yellow")
            elif level == "error":
                self.console.print(f"❌ {message}", style="red")
            else:
                self.console.print(f"ℹ️ {message}", style="blue")
        else:
            print(f"[{level.upper()}] {message}")


def main():
    """Main function for testing help system."""
    # Example configuration
    config = {
        "EXPERIENCE_LEVEL": "beginner",
        "PROJECT_ROOT": Path(__file__).parent.absolute(),
        "TOOLS_ENABLED": {"zeek": True, "yara": True, "suricata": False},
        "API_PORT": 8000,
    }

    help_system = ContextualHelpSystem(config)

    while True:
        result = help_system.show_help_menu()
        if result is None:
            break


if __name__ == "__main__":
    main()
