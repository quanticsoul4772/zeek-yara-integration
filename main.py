#!/usr/bin/env python3
"""
Zeek-YARA Educational Platform - Main Application
User-friendly interface for security learning platform
"""

import argparse
import asyncio
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional

# Configure stdout encoding for Unicode compatibility
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # Fallback for older Python versions or restricted environments
        pass

try:
    from rich.align import Align
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Define dummy Console class for type hints when rich is not available
    class Console:
        pass

try:
    import uvicorn
    from fastapi import FastAPI

    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False


class ConfigManager:
    """Manages educational platform configuration."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_path = project_root / "config" / "educational_config.json"
        self.default_config_path = project_root / "config" / "default_config.json"
        self._config = None

    @property
    def config(self) -> Dict:
        """Get current configuration."""
        if self._config is None:
            self.load_config()
        return self._config

    def load_config(self):
        """Load configuration from files."""
        # Try educational config first
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self._config = json.load(f)
                return
            except Exception as e:
                print(f"Error loading educational config: {e}")

        # Fall back to default config
        if self.default_config_path.exists():
            try:
                with open(self.default_config_path, "r") as f:
                    self._config = json.load(f)
                # Add educational defaults
                self._config.update(
                    {
                        "PLATFORM_MODE": "educational",
                        "BEGINNER_MODE": True,
                        "TUTORIAL_MODE": True,
                        "WEB_INTERFACE": True,
                        "EXPERIENCE_LEVEL": "beginner",
                    }
                )
                return
            except Exception as e:
                print(f"Error loading default config: {e}")

        # Create minimal config
        self._config = self.create_minimal_config()

    def create_minimal_config(self) -> Dict:
        """Create minimal configuration for basic operation."""
        return {
            "PLATFORM_MODE": "educational",
            "BEGINNER_MODE": True,
            "TUTORIAL_MODE": True,
            "WEB_INTERFACE": True,
            "EXPERIENCE_LEVEL": "beginner",
            "PROJECT_ROOT": str(self.project_root),
            "EXTRACT_DIR": str(self.project_root / "extracted_files"),
            "RULES_DIR": str(self.project_root / "rules"),
            "LOG_DIR": str(self.project_root / "logs"),
            "API_ENABLED": True,
            "API_PORT": 8000,
            "API_HOST": "127.0.0.1",
            "TOOLS_ENABLED": {"zeek": False, "yara": False, "suricata": False},
        }

    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return not self.config_path.exists() or not self.config.get("SETUP_COMPLETED", False)

    def get_mode(self) -> str:
        """Get current platform mode."""
        return self.config.get("PLATFORM_MODE", "educational")

    def is_beginner_mode(self) -> bool:
        """Check if beginner mode is enabled."""
        return self.config.get("BEGINNER_MODE", True)

    def is_tutorial_mode(self) -> bool:
        """Check if tutorial mode is enabled."""
        return self.config.get("TUTORIAL_MODE", True)


class ServiceManager:
    """Manages platform services (API, scanners, etc.)."""

    def __init__(self, config: Dict, console: Optional[Console] = None):
        self.config = config
        self.console = console
        self.services = {}
        self.running = False

    def log(self, message: str, level: str = "info"):
        """Log messages."""
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

    async def start_api_server(self):
        """Start the API server."""
        if not self.config.get("API_ENABLED", True):
            return

        try:
            from api.api_server import app

            host = self.config.get("API_HOST", "127.0.0.1")
            port = self.config.get("API_PORT", 8000)

            self.log(f"Starting API server on {host}:{port}")

            # Start in background thread
            def run_server():
                uvicorn.run(app, host=host, port=port, log_level="warning")

            api_thread = threading.Thread(target=run_server, daemon=True)
            api_thread.start()
            self.services["api"] = api_thread

            # Give server time to start
            await asyncio.sleep(2)
            self.log("API server started", "success")

        except Exception as e:
            self.log(f"Failed to start API server: {e}", "error")

    def start_yara_scanner(self):
        """Start YARA scanner if available."""
        if not self.config.get("TOOLS_ENABLED", {}).get("yara", False):
            return

        try:
            from core.scanner import YaraScanner

            scanner = YaraScanner(self.config)
            scanner_thread = threading.Thread(
                target=scanner.start_monitoring, daemon=True)
            scanner_thread.start()
            self.services["yara_scanner"] = scanner_thread

            self.log("YARA scanner started", "success")

        except Exception as e:
            self.log(f"Failed to start YARA scanner: {e}", "error")

    def get_service_status(self) -> Dict[str, str]:
        """Get status of all services."""
        status = {}

        for service_name, service in self.services.items():
            if hasattr(service, "is_alive"):
                status[service_name] = "Running" if service.is_alive() else "Stopped"
            else:
                status[service_name] = "Unknown"

        return status


class TutorialSystem:
    """Interactive tutorial system for beginners."""

    def __init__(self, config: Dict, console: Optional[Console] = None):
        self.config = config
        self.console = console
        self.current_step = 0
        self.tutorial_steps = self.load_tutorial_steps()

    def load_tutorial_steps(self) -> List[Dict]:
        """Load tutorial steps based on experience level."""
        beginner_steps = [
            {
                "title": "Welcome to Network Security!",
                "content": """
🎓 Welcome to your network security journey!

This tutorial will guide you through:
• Understanding network security basics
• Setting up your monitoring tools
• Detecting your first threats
• Learning with real examples

Click 'Next' when you're ready to begin!
                """,
                "action": "welcome",
                "duration": "2 minutes",
            },
            {
                "title": "Understanding the Platform",
                "content": """
🛠️ Your Security Toolkit

This platform combines three powerful tools:
• Zeek: Monitors network traffic and extracts files
• YARA: Detects malware in extracted files
• Suricata: Identifies network intrusions

Together, they provide comprehensive security monitoring!
                """,
                "action": "explain_tools",
                "duration": "3 minutes",
            },
            {
                "title": "First Detection Demo",
                "content": """
🚨 Let's Detect Some Threats!

We'll start with a safe test file (EICAR) that triggers our security tools.
This helps you understand how threat detection works.

Ready to see your tools in action?
                """,
                "action": "demo_detection",
                "duration": "5 minutes",
            },
            {
                "title": "Exploring the Dashboard",
                "content": """
📊 Your Security Dashboard

The web interface shows:
• Real-time alerts and detections
• Network traffic analysis
• File extraction results
• Learning progress

Let's explore each section together!
                """,
                "action": "explore_dashboard",
                "duration": "4 minutes",
            },
        ]

        return beginner_steps

    def show_tutorial_step(self, step_index: int) -> bool:
        """Show a tutorial step and return True if user wants to continue."""
        if step_index >= len(self.tutorial_steps):
            return False

        step = self.tutorial_steps[step_index]

        if self.console:
            panel = Panel(
                step["content"].strip(),
                title=f"📚 Tutorial: {step['title']} ({step_index + 1}/{len(self.tutorial_steps)})",
                subtitle=f"⏱️ Duration: {step['duration']}",
                border_style="blue",
                padding=(1, 2),
            )
            self.console.print(panel)

            # Execute step action
            self.execute_step_action(step["action"])

            if step_index < len(self.tutorial_steps) - 1:
                from rich.prompt import Confirm

                return Confirm.ask("Continue to next step?", default=True)
            else:
                self.console.print(
                    "🎉 Tutorial completed! You're ready to explore on your own.")
                return False
        else:
            print(f"\n=== Tutorial: {step['title']} ===")
            print(step["content"].strip())
            print(f"Duration: {step['duration']}")

            # Execute step action
            self.execute_step_action(step["action"])

            if step_index < len(self.tutorial_steps) - 1:
                response = input(
                    "Continue to next step? (y/n) [y]: ").strip().lower()
                return response != "n"
            else:
                print("Tutorial completed! You're ready to explore on your own.")
                return False

    def execute_step_action(self, action: str):
        """Execute action for tutorial step."""
        if action == "welcome":
            self.log("Welcome! Let's start your security learning journey.")

        elif action == "explain_tools":
            self.show_tools_explanation()

        elif action == "demo_detection":
            self.run_detection_demo()

        elif action == "explore_dashboard":
            self.open_dashboard()

    def show_tools_explanation(self):
        """Show detailed explanation of security tools."""
        if self.console:
            tools_table = Table(title="Your Security Tools")
            tools_table.add_column("Tool", style="cyan")
            tools_table.add_column("Purpose", style="green")
            tools_table.add_column("What it does", style="yellow")

            tools_table.add_row(
                "Zeek",
                "Network Monitoring",
                "Watches traffic, extracts files, logs connections")
            tools_table.add_row(
                "YARA",
                "Malware Detection",
                "Scans files for malicious patterns and signatures")
            tools_table.add_row(
                "Suricata",
                "Intrusion Detection",
                "Identifies network attacks and suspicious behavior",
            )

            self.console.print(tools_table)

    def run_detection_demo(self):
        """Run a simple detection demonstration."""
        self.log("Running detection demo with EICAR test file...")

        # Create EICAR test file for demonstration
        eicar_path = Path(self.config.get(
            "EXTRACT_DIR", "/tmp")) / "eicar_test.txt"
        eicar_content = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

        try:
            eicar_path.parent.mkdir(exist_ok=True)
            with open(eicar_path, "w") as f:
                f.write(eicar_content)

            self.log(f"Created test file: {eicar_path}", "success")
            self.log("This file will trigger YARA detection rules!")

        except Exception as e:
            self.log(f"Demo setup failed: {e}", "error")

    def open_dashboard(self):
        """Open the web dashboard."""
        try:
            port = self.config.get("API_PORT", 8000)
            url = f"http://localhost:{port}"

            self.log(f"Opening dashboard at {url}")
            webbrowser.open(url)

        except Exception as e:
            self.log(f"Failed to open dashboard: {e}", "error")

    def log(self, message: str, level: str = "info"):
        """Log tutorial messages."""
        if self.console:
            if level == "success":
                self.console.print(f"✅ {message}", style="green")
            elif level == "error":
                self.console.print(f"❌ {message}", style="red")
            else:
                self.console.print(f"📖 {message}", style="blue")
        else:
            print(f"[TUTORIAL] {message}")


class EducationalPlatform:
    """Main educational platform application."""

    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.console = Console() if RICH_AVAILABLE else None
        self.config_manager = ConfigManager(self.project_root)
        self.service_manager = ServiceManager(
            self.config_manager.config, self.console)
        self.tutorial_system = TutorialSystem(
            self.config_manager.config, self.console)
        self.running = False

    def show_welcome_banner(self):
        """Show welcome banner."""
        if self.console:
            banner_text = """
🎓 Zeek-YARA Educational Security Platform
═══════════════════════════════════════════

Transform enterprise security tools into your personal learning laboratory!

Learn network security through hands-on experience with:
• Network traffic analysis and monitoring
• Malware detection and analysis
• Intrusion detection and response
• Security tool integration

Perfect for students, educators, and security professionals.
            """

            panel = Panel(
                banner_text.strip(),
                title="🛡️ Educational Security Platform",
                border_style="bright_blue",
                padding=(1, 2),
            )
            self.console.print(panel)
        else:
            print("=" * 60)
            print("🎓 Zeek-YARA Educational Security Platform")
            print("=" * 60)
            print("Learn network security through hands-on experience!")
            print()

    def check_first_run(self) -> bool:
        """Check if this is first run and offer setup."""
        if self.config_manager.is_first_run():
            if self.console:
                self.console.print(
                    "🔧 First time setup required!", style="yellow bold")

                from rich.prompt import Confirm

                run_setup = Confirm.ask(
                    "Would you like to run the setup wizard?", default=True)
            else:
                print("First time setup required!")
                response = input(
                    "Run setup wizard? (y/n) [y]: ").strip().lower()
                run_setup = response != "n"

            if run_setup:
                self.log("Starting setup wizard...")
                try:
                    import subprocess

                    result = subprocess.run(
                        [sys.executable, "setup_wizard.py"], capture_output=False
                    )
                    if result.returncode == 0:
                        self.log("Setup completed successfully!", "success")
                        # Reload config
                        self.config_manager.load_config()
                        return True
                    else:
                        self.log("Setup failed or was cancelled", "warning")
                        return False
                except Exception as e:
                    self.log(f"Setup wizard error: {e}", "error")
                    return False
            else:
                self.log("Continuing with minimal configuration", "warning")
                return True

        return True

    def show_platform_status(self):
        """Show current platform status."""
        config = self.config_manager.config

        if self.console:
            # Create status table
            status_table = Table(title="Platform Status")
            status_table.add_column("Component", style="cyan")
            status_table.add_column("Status", style="green")
            status_table.add_column("Details", style="yellow")

            # Platform info
            mode = config.get("PLATFORM_MODE", "educational")
            experience = config.get("EXPERIENCE_LEVEL", "beginner")
            status_table.add_row(
                "Platform Mode", mode.title(), f"Experience: {experience}")

            # Tools status
            tools = config.get("TOOLS_ENABLED", {})
            for tool, enabled in tools.items():
                status = "✅ Ready" if enabled else "❌ Not Available"
                status_table.add_row(f"{tool.upper()}", status, "")

            # Services status
            service_status = self.service_manager.get_service_status()
            for service, status in service_status.items():
                status_table.add_row(
                    f"{service.replace('_', ' ').title()}", status, "")

            self.console.print(status_table)
        else:
            print("\nPlatform Status:")
            print("-" * 40)
            print(
                f"Mode: {config.get('PLATFORM_MODE', 'educational').title()}")
            print(
                f"Experience Level: {
                    config.get(
                        'EXPERIENCE_LEVEL',
                        'beginner').title()}")

            tools = config.get("TOOLS_ENABLED", {})
            print("\nTools:")
            for tool, enabled in tools.items():
                status = "Ready" if enabled else "Not Available"
                print(f"  {tool.upper()}: {status}")

    def show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        menu_options = []

        # Always available options
        menu_options.extend(
            [
                ("1", "View Platform Status", "status"),
                ("2", "Open Web Dashboard", "dashboard"),
                ("3", "Run Detection Demo", "demo"),
            ]
        )

        # Tutorial option for beginners
        if self.config_manager.is_tutorial_mode():
            menu_options.append(
                ("4", "Start Interactive Tutorial", "tutorial"))

        # Advanced options for experienced users
        if not self.config_manager.is_beginner_mode():
            menu_options.extend(
                [
                    ("5", "Configure Tools", "configure"),
                    ("6", "View Logs", "logs"),
                    ("7", "Advanced Settings", "advanced"),
                ]
            )

        # Always available
        menu_options.extend([("0", "Exit", "exit")])

        if self.console:
            self.console.print("\n🎯 Main Menu", style="bold blue")
            for key, description, _ in menu_options:
                self.console.print(f"{key}. {description}")

            from rich.prompt import Prompt

            choice = Prompt.ask(
                "Choose an option", choices=[
                    opt[0] for opt in menu_options], default="2")
        else:
            print("\nMain Menu:")
            for key, description, _ in menu_options:
                print(f"{key}. {description}")

            valid_choices = [opt[0] for opt in menu_options]
            choice = input(
                f"Choose an option ({
                    '/'.join(valid_choices)}) [2]: ").strip() or "2"

        # Return action for choice
        for key, _, action in menu_options:
            if key == choice:
                return action

        return "dashboard"  # Default

    def handle_menu_choice(self, action: str):
        """Handle user menu choice."""
        if action == "status":
            self.show_platform_status()

        elif action == "dashboard":
            self.open_dashboard()

        elif action == "demo":
            self.run_detection_demo()

        elif action == "tutorial":
            self.run_tutorial()

        elif action == "configure":
            self.configure_tools()

        elif action == "logs":
            self.view_logs()

        elif action == "advanced":
            self.show_advanced_settings()

        elif action == "exit":
            self.shutdown()
            return False

        return True

    def open_dashboard(self):
        """Open the web dashboard."""
        try:
            port = self.config_manager.config.get("API_PORT", 8000)
            url = f"http://localhost:{port}"

            self.log(f"Opening dashboard at {url}")
            webbrowser.open(url)

            if self.config_manager.is_beginner_mode():
                self.log(
                    "💡 Tip: The dashboard shows real-time security monitoring!",
                    "info")

        except Exception as e:
            self.log(f"Failed to open dashboard: {e}", "error")

    def run_detection_demo(self):
        """Run a detection demonstration."""
        self.log("Starting detection demo...")
        self.tutorial_system.run_detection_demo()

    def run_tutorial(self):
        """Run the interactive tutorial."""
        self.log("Starting interactive tutorial...")

        for i in range(len(self.tutorial_system.tutorial_steps)):
            if not self.tutorial_system.show_tutorial_step(i):
                break

    def configure_tools(self):
        """Show tool configuration options."""
        self.log("Tool configuration coming soon!", "info")

    def view_logs(self):
        """Show log viewing options."""
        self.log("Log viewer coming soon!", "info")

    def show_advanced_settings(self):
        """Show advanced settings."""
        self.log("Advanced settings coming soon!", "info")

    async def start_services(self):
        """Start platform services."""
        self.log("Starting platform services...")

        # Start API server
        await self.service_manager.start_api_server()

        # Start YARA scanner
        self.service_manager.start_yara_scanner()

        self.log("Platform services started", "success")

    def shutdown(self):
        """Shutdown the platform."""
        self.log("Shutting down platform...")
        self.running = False

    def log(self, message: str, level: str = "info"):
        """Log messages."""
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

    async def run(self):
        """Run the main application."""
        try:
            # Show welcome
            self.show_welcome_banner()

            # Check first run
            if not self.check_first_run():
                return

            # Start services
            await self.start_services()

            # Show initial status
            self.show_platform_status()

            # Auto-start tutorial for beginners
            if (
                self.config_manager.is_beginner_mode()
                and self.config_manager.is_tutorial_mode()
                and self.config_manager.is_first_run()
            ):

                if self.console:
                    from rich.prompt import Confirm

                    start_tutorial = Confirm.ask(
                        "Start the beginner tutorial?", default=True)
                else:
                    response = input(
                        "Start the beginner tutorial? (y/n) [y]: ").strip().lower()
                    start_tutorial = response != "n"

                if start_tutorial:
                    self.run_tutorial()

            # Main loop
            self.running = True
            while self.running:
                try:
                    action = self.show_main_menu()
                    if not self.handle_menu_choice(action):
                        break

                    # Pause between menu operations
                    if self.console:
                        from rich.prompt import Prompt

                        Prompt.ask("\nPress Enter to continue", default="")
                    else:
                        input("\nPress Enter to continue...")

                except KeyboardInterrupt:
                    self.log("\nReceived interrupt signal", "warning")
                    break

        except Exception as e:
            self.log(f"Application error: {e}", "error")
            raise
        finally:
            self.shutdown()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Zeek-YARA Educational Security Platform")
    parser.add_argument("--setup", action="store_true",
                        help="Run setup wizard")
    parser.add_argument("--demo", action="store_true",
                        help="Run detection demo")
    parser.add_argument("--tutorial", action="store_true",
                        help="Start tutorial")
    parser.add_argument("--web-only", action="store_true",
                        help="Start web interface only")

    args = parser.parse_args()

    # Handle special modes
    if args.setup:
        import subprocess

        return subprocess.call([sys.executable, "setup_wizard.py"])

    # Start main application
    platform = EducationalPlatform()

    if args.demo:
        platform.run_detection_demo()
        return 0

    if args.tutorial:
        platform.run_tutorial()
        return 0

    if args.web_only:
        asyncio.run(platform.service_manager.start_api_server())
        print("Web interface running. Press Ctrl+C to stop.")
        try:
            while True:
                asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        return 0

    # Run full platform
    try:
        asyncio.run(platform.run())
        return 0
    except KeyboardInterrupt:
        print("\nGoodbye! Happy learning! 🛡️")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
