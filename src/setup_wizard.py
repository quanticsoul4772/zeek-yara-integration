#!/usr/bin/env python3
"""
Zeek-YARA Educational Platform - Interactive Setup Wizard
Auto-detects system capabilities and guides users through configuration
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import netifaces

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    
    # Define dummy Console class for type hints when rich is not available
    class Console:
        pass


class SystemDetector:
    """Detects system capabilities and available security tools."""

    def __init__(self):
        self.platform = platform.system().lower()
        self.console = Console() if RICH_AVAILABLE else None
        self.detected_tools = {}
        self.network_interfaces = []

    def log(self, message: str, style: str = "info"):
        """Log messages with optional styling."""
        if self.console:
            if style == "success":
                self.console.print(f"✅ {message}", style="green")
            elif style == "warning":
                self.console.print(f"⚠️ {message}", style="yellow")
            elif style == "error":
                self.console.print(f"❌ {message}", style="red")
            else:
                self.console.print(f"ℹ️ {message}", style="blue")
        else:
            print(f"[{style.upper()}] {message}")

    def check_command_available(self, command: str) -> Tuple[bool, str]:
        """Check if a command is available in PATH."""
        path = shutil.which(command)
        return path is not None, path or ""

    def get_command_version(self, command: str, version_arg: str = "--version") -> str:
        """Get version of a command."""
        try:
            result = subprocess.run(
                [command, version_arg], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]
            return "Unknown version"
        except BaseException:
            return "Version unavailable"

    def detect_zeek(self) -> Dict[str, any]:
        """Detect Zeek installation."""
        self.log("Detecting Zeek...")

        available, path = self.check_command_available("zeek")
        if not available:
            # Try alternative names
            available, path = self.check_command_available("bro")

        if available:
            version = self.get_command_version(os.path.basename(path))
            self.log(f"Found Zeek at {path}", "success")
            return {"available": True, "path": path, "version": version, "ready": True}
        else:
            self.log("Zeek not found in PATH", "warning")
            return {
                "available": False,
                "path": "",
                "version": "",
                "ready": False,
                "install_help": self.get_zeek_install_help(),
            }

    def detect_yara(self) -> Dict[str, any]:
        """Detect YARA installation."""
        self.log("Detecting YARA...")

        # Check for yara command
        available, path = self.check_command_available("yara")

        # Check for Python YARA module
        python_yara = False
        try:
            import yara

            python_yara = True
            version = getattr(yara, "__version__", "Unknown")
        except ImportError:
            version = ""

        if available or python_yara:
            self.log(
                f"Found YARA {'and Python module' if python_yara else ''}",
                "success",
            )
            return {
                "available": True,
                "path": path,
                "version": version,
                "python_module": python_yara,
                "ready": python_yara,  # Python module is what we need
            }
        else:
            self.log("YARA not found", "warning")
            return {
                "available": False,
                "path": "",
                "version": "",
                "python_module": False,
                "ready": False,
                "install_help": self.get_yara_install_help(),
            }

    def detect_suricata(self) -> Dict[str, any]:
        """Detect Suricata installation."""
        self.log("Detecting Suricata...")

        available, path = self.check_command_available("suricata")

        if available:
            version = self.get_command_version("suricata", "-V")
            self.log(f"Found Suricata at {path}", "success")
            return {"available": True, "path": path, "version": version, "ready": True}
        else:
            self.log("Suricata not found in PATH", "warning")
            return {
                "available": False,
                "path": "",
                "version": "",
                "ready": False,
                "install_help": self.get_suricata_install_help(),
            }

    def detect_network_interfaces(self) -> List[Dict[str, str]]:
        """Detect available network interfaces."""
        self.log("Detecting network interfaces...")

        interfaces = []
        try:
            for interface in netifaces.interfaces():
                # Skip loopback and virtual interfaces
                if interface.startswith(("lo", "docker", "veth", "br-")):
                    continue

                addrs = netifaces.ifaddresses(interface)
                ipv4_addrs = addrs.get(netifaces.AF_INET, [])

                if ipv4_addrs:
                    ip = ipv4_addrs[0].get("addr", "Unknown")
                    interfaces.append(
                        {
                            "name": interface,
                            "ip": ip,
                            "description": f"{interface} ({ip})",
                        }
                    )
        except Exception as e:
            self.log(f"Error detecting interfaces: {e}", "warning")
            # Fallback to common interface names
            common_interfaces = ["eth0", "en0", "wlan0", "WiFi", "Ethernet"]
            for iface in common_interfaces:
                if self.interface_exists(iface):
                    interfaces.append(
                        {
                            "name": iface,
                            "ip": "Auto-detect",
                            "description": f"{iface} (Auto-detect IP)",
                        }
                    )

        if interfaces:
            self.log(f"Found {len(interfaces)} network interfaces", "success")
        else:
            self.log("No suitable network interfaces found", "warning")

        return interfaces

    def interface_exists(self, interface: str) -> bool:
        """Check if network interface exists."""
        try:
            result = subprocess.run(
                ["ip", "link", "show", interface], capture_output=True, timeout=2
            )
            return result.returncode == 0
        except BaseException:
            try:
                result = subprocess.run(
                    ["ifconfig", interface], capture_output=True, timeout=2
                )
                return result.returncode == 0
            except BaseException:
                return False

    def get_zeek_install_help(self) -> str:
        """Get platform-specific Zeek installation instructions."""
        if self.platform == "darwin":
            return "Install with: brew install zeek"
        elif self.platform == "linux":
            return "Install with: sudo apt-get install zeek (Ubuntu/Debian) or sudo yum install zeek (CentOS/RHEL)"
        elif self.platform == "windows":
            return "Download from: https://zeek.org/get-zeek/"
        return "Visit: https://zeek.org/get-zeek/"

    def get_yara_install_help(self) -> str:
        """Get platform-specific YARA installation instructions."""
        return "Install Python module with: pip install yara-python"

    def get_suricata_install_help(self) -> str:
        """Get platform-specific Suricata installation instructions."""
        if self.platform == "darwin":
            return "Install with: brew install suricata"
        elif self.platform == "linux":
            return "Install with: sudo apt-get install suricata (Ubuntu/Debian) or sudo yum install suricata (CentOS/RHEL)"
        elif self.platform == "windows":
            return "Download from: https://suricata.io/download/"
        return "Visit: https://suricata.io/download/"


class SetupWizard:
    """Interactive setup wizard for educational platform."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.detector = SystemDetector()
        self.project_root = Path(__file__).parent.absolute()
        self.config = {}

    def show_welcome(self):
        """Show welcome message."""
        if self.console:
            welcome_text = """
🎓 Welcome to the Zeek-YARA Educational Platform Setup Wizard!

This wizard will:
• Detect your system capabilities
• Configure security tools automatically
• Set up beginner-friendly defaults
• Guide you through first-time configuration

The setup process takes about 2-3 minutes.
Let's transform this enterprise toolkit into your learning platform!
            """

            panel = Panel(
                welcome_text.strip(),
                title="Setup Wizard",
                border_style="blue",
                padding=(1, 2),
            )
            self.console.print(panel)
        else:
            print("=" * 60)
            print("Zeek-YARA Educational Platform Setup Wizard")
            print("=" * 60)
            print("This wizard will configure your educational security platform.")
            print("The setup process takes about 2-3 minutes.")
            print()

    def detect_system_capabilities(self) -> Dict[str, any]:
        """Run system detection with progress indication."""
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Detecting system capabilities...", total=4)

                # Detect each tool
                zeek_info = self.detector.detect_zeek()
                progress.advance(task)

                yara_info = self.detector.detect_yara()
                progress.advance(task)

                suricata_info = self.detector.detect_suricata()
                progress.advance(task)

                interfaces = self.detector.detect_network_interfaces()
                progress.advance(task)
        else:
            print("Detecting system capabilities...")
            zeek_info = self.detector.detect_zeek()
            yara_info = self.detector.detect_yara()
            suricata_info = self.detector.detect_suricata()
            interfaces = self.detector.detect_network_interfaces()

        return {
            "zeek": zeek_info,
            "yara": yara_info,
            "suricata": suricata_info,
            "interfaces": interfaces,
        }

    def show_detection_results(self, results: Dict[str, any]):
        """Display detection results in a nice table."""
        if self.console:
            table = Table(title="System Detection Results")
            table.add_column("Tool", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Version/Info", style="yellow")

            # Add tool rows
            for tool_name, info in results.items():
                if tool_name == "interfaces":
                    continue

                status = "✅ Ready" if info.get("ready", False) else "❌ Not Available"
                version = info.get("version", "N/A")
                table.add_row(tool_name.upper(), status, version)

            # Add interfaces info
            if results["interfaces"]:
                iface_info = f"{len(results['interfaces'])} available"
                table.add_row("Network Interfaces", "✅ Detected", iface_info)
            else:
                table.add_row(
                    "Network Interfaces", "❌ None Found", "Manual setup required"
                )

            self.console.print(table)
        else:
            print("\nSystem Detection Results:")
            print("-" * 40)
            for tool_name, info in results.items():
                if tool_name == "interfaces":
                    continue
                status = "Ready" if info.get("ready", False) else "Not Available"
                print(f"{tool_name.upper()}: {status}")

            if results["interfaces"]:
                print(f"Network Interfaces: {len(results['interfaces'])} available")
            else:
                print("Network Interfaces: None found")

    def get_user_preferences(self, results: Dict[str, any]) -> Dict[str, any]:
        """Get user preferences for platform configuration."""
        preferences = {}

        # Experience level
        if self.console:
            self.console.print("\n🎯 Configuration Questions", style="bold blue")
        else:
            print("\nConfiguration Questions:")

        if RICH_AVAILABLE:
            experience = Prompt.ask(
                "What's your experience level with network security?",
                choices=["beginner", "intermediate", "advanced"],
                default="beginner",
            )
        else:
            experience = (
                input(
                    "Experience level (beginner/intermediate/advanced) [beginner]: "
                ).strip()
                or "beginner"
            )

        preferences["experience_level"] = experience

        # Learning goals
        goals_text = """
What do you want to learn about? (Select primary focus)
1. Network traffic analysis
2. Malware detection
3. Intrusion detection
4. Security tool integration
5. All of the above
        """

        if self.console:
            self.console.print(goals_text)
        else:
            print(goals_text)

        if RICH_AVAILABLE:
            goal = Prompt.ask(
                "Choose your primary learning goal",
                choices=["1", "2", "3", "4", "5"],
                default="5",
            )
        else:
            goal = input("Choose your primary learning goal (1-5) [5]: ").strip() or "5"

        goal_mapping = {
            "1": "network_analysis",
            "2": "malware_detection",
            "3": "intrusion_detection",
            "4": "tool_integration",
            "5": "comprehensive",
        }
        preferences["learning_goal"] = goal_mapping.get(goal, "comprehensive")

        # Network interface selection
        if results["interfaces"]:
            if len(results["interfaces"]) == 1:
                preferences["network_interface"] = results["interfaces"][0]["name"]
                if self.console:
                    self.console.print(
                        f"Using network interface: {results['interfaces'][0]['description']}"
                    )
                else:
                    print(
                        f"Using network interface: {results['interfaces'][0]['description']}"
                    )
            else:
                if self.console:
                    self.console.print("\nAvailable network interfaces:")
                    for i, iface in enumerate(results["interfaces"], 1):
                        self.console.print(f"{i}. {iface['description']}")

                    choice = Prompt.ask(
                        "Select network interface",
                        choices=[
                            str(i) for i in range(1, len(results["interfaces"]) + 1)
                        ],
                        default="1",
                    )
                else:
                    print("\nAvailable network interfaces:")
                    for i, iface in enumerate(results["interfaces"], 1):
                        print(f"{i}. {iface['description']}")
                    choice = (
                        input(
                            f"Select interface (1-{len(results['interfaces'])}) [1]: "
                        ).strip()
                        or "1"
                    )

                try:
                    preferences["network_interface"] = results["interfaces"][
                        int(choice) - 1
                    ]["name"]
                except (ValueError, IndexError):
                    preferences["network_interface"] = results["interfaces"][0]["name"]
        else:
            preferences["network_interface"] = "auto"

        # Tutorial mode
        if RICH_AVAILABLE:
            tutorial_mode = Confirm.ask(
                "Enable interactive tutorials and guided learning?", default=True
            )
        else:
            response = (
                input("Enable interactive tutorials? (y/n) [y]: ").strip().lower()
            )
            tutorial_mode = response != "n"

        preferences["tutorial_mode"] = tutorial_mode

        # Web interface
        if RICH_AVAILABLE:
            web_interface = Confirm.ask("Enable web-based dashboard?", default=True)
        else:
            response = input("Enable web dashboard? (y/n) [y]: ").strip().lower()
            web_interface = response != "n"

        preferences["web_interface"] = web_interface

        return preferences

    def generate_config(
        self, results: Dict[str, any], preferences: Dict[str, any]
    ) -> Dict[str, any]:
        """Generate configuration based on detection results and preferences."""
        config = {
            "# Generated by Setup Wizard": "Educational Platform Configuration",
            "PLATFORM_MODE": "educational",
            "SETUP_COMPLETED": True,
            "SETUP_DATE": str(Path(__file__).stat().st_mtime),
            # User preferences
            "EXPERIENCE_LEVEL": preferences["experience_level"],
            "LEARNING_GOAL": preferences["learning_goal"],
            "TUTORIAL_MODE": preferences["tutorial_mode"],
            "WEB_INTERFACE": preferences["web_interface"],
            # Paths (auto-detected)
            "PROJECT_ROOT": str(self.project_root),
            "EXTRACT_DIR": str(self.project_root / "extracted_files"),
            "RULES_DIR": str(self.project_root / "rules"),
            "LOG_DIR": str(self.project_root / "logs"),
            "DB_FILE": str(self.project_root / "logs" / "educational_alerts.db"),
            # Tool configurations
            "TOOLS_ENABLED": {
                "zeek": results["zeek"]["ready"],
                "yara": results["yara"]["ready"],
                "suricata": results["suricata"]["ready"],
            },
            # Network settings
            "NETWORK_INTERFACE": preferences["network_interface"],
            # Educational features based on experience level
            "BEGINNER_MODE": preferences["experience_level"] == "beginner",
            "SHOW_EXPLANATIONS": preferences["experience_level"]
            in ["beginner", "intermediate"],
            "AUTO_START_SERVICES": preferences["experience_level"] == "beginner",
            "DETAILED_LOGGING": preferences["experience_level"] == "advanced",
            # API settings
            "API_ENABLED": True,
            "API_PORT": 8000,
            "API_HOST": "127.0.0.1",
            # Scanner settings (experience-based)
            "SCAN_INTERVAL": (
                30 if preferences["experience_level"] == "beginner" else 10
            ),
            "MAX_FILE_SIZE": 20971520,  # 20MB
            "THREADS": 2 if preferences["experience_level"] == "beginner" else 4,
            # Learning features
            "ACHIEVEMENT_TRACKING": True,
            "PROGRESS_REPORTING": True,
            "INTERACTIVE_HELP": True,
            "GUIDED_WORKFLOWS": preferences["experience_level"] == "beginner",
        }

        # Add tool-specific paths if available
        if results["zeek"]["ready"]:
            config["ZEEK_PATH"] = results["zeek"]["path"]
        if results["suricata"]["ready"]:
            config["SURICATA_PATH"] = results["suricata"]["path"]

        return config

    def save_config(self, config: Dict[str, any]) -> bool:
        """Save generated configuration to file."""
        config_path = self.project_root / "config" / "educational_config.json"

        try:
            # Ensure config directory exists
            config_path.parent.mkdir(exist_ok=True)

            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)

            if self.console:
                self.console.print(
                    f"✅ Configuration saved to {config_path}", style="green"
                )
            else:
                print(f"Configuration saved to {config_path}")

            return True
        except Exception as e:
            if self.console:
                self.console.print(f"❌ Failed to save configuration: {e}", style="red")
            else:
                print(f"Error saving configuration: {e}")
            return False

    def show_completion_summary(self, config: Dict[str, any]):
        """Show setup completion summary."""
        if self.console:
            summary_text = f"""
🎉 Setup Complete!

Your educational platform is configured with:
• Experience Level: {config['EXPERIENCE_LEVEL'].title()}
• Learning Goal: {config['LEARNING_GOAL'].replace('_', ' ').title()}
• Tutorial Mode: {'Enabled' if config['TUTORIAL_MODE'] else 'Disabled'}
• Web Interface: {'Enabled' if config['WEB_INTERFACE'] else 'Disabled'}

Ready tools:
{self._get_tools_summary(config)}

Next steps:
1. Run: python main.py
2. Open: http://localhost:8000
3. Follow the guided tutorial

Happy learning! 🛡️
            """

            panel = Panel(
                summary_text.strip(),
                title="Setup Complete",
                border_style="green",
                padding=(1, 2),
            )
            self.console.print(panel)
        else:
            print("\n" + "=" * 60)
            print("🎉 SETUP COMPLETE!")
            print("=" * 60)
            print(f"Experience Level: {config['EXPERIENCE_LEVEL'].title()}")
            print(
                f"Learning Goal: {config['LEARNING_GOAL'].replace( '_', ' ').title()}"
            )
            print(
                f"Tutorial Mode: {'Enabled' if config['TUTORIAL_MODE'] else 'Disabled'}"
            )
            print(
                f"Web Interface: {'Enabled' if config['WEB_INTERFACE'] else 'Disabled'}"
            )
            print("\nNext steps:")
            print("1. Run: python main.py")
            print("2. Open: http://localhost:8000")
            print("3. Follow the guided tutorial")
            print("\nHappy learning!")

    def _get_tools_summary(self, config: Dict[str, any]) -> str:
        """Get a summary of enabled tools."""
        tools = config.get("TOOLS_ENABLED", {})
        enabled = [tool.upper() for tool, status in tools.items() if status]
        if enabled:
            return "• " + "\n• ".join(enabled)
        return "• Manual tool installation required"

    def show_missing_tools_help(self, results: Dict[str, any]):
        """Show help for installing missing tools."""
        missing_tools = []

        for tool_name, info in results.items():
            if tool_name == "interfaces":
                continue
            if not info.get("ready", False):
                missing_tools.append((tool_name, info))

        if not missing_tools:
            return

        if self.console:
            self.console.print(
                "\n⚠️ Missing Tools Installation Help", style="yellow bold"
            )
        else:
            print("\nMissing Tools Installation Help:")
            print("-" * 40)

        for tool_name, info in missing_tools:
            help_text = info.get(
                "install_help", "Visit tool website for installation instructions"
            )
            if self.console:
                self.console.print(f"{tool_name.upper()}: {help_text}")
            else:
                print(f"{tool_name.upper()}: {help_text}")

    def run(self):
        """Run the complete setup wizard."""
        try:
            # Welcome
            self.show_welcome()

            # System detection
            results = self.detect_system_capabilities()
            self.show_detection_results(results)

            # Show help for missing tools
            self.show_missing_tools_help(results)

            # Get user preferences
            preferences = self.get_user_preferences(results)

            # Generate and save config
            config = self.generate_config(results, preferences)

            if self.save_config(config):
                self.show_completion_summary(config)
                return True
            else:
                return False

        except KeyboardInterrupt:
            if self.console:
                self.console.print("\n\n⏹️ Setup cancelled by user", style="yellow")
            else:
                print("\nSetup cancelled by user")
            return False
        except Exception as e:
            if self.console:
                self.console.print(f"\n❌ Setup failed: {e}", style="red")
            else:
                print(f"Setup failed: {e}")
            return False


def main():
    """Main setup wizard entry point."""
    wizard = SetupWizard()
    success = wizard.run()
    return 0 if success else 1


if __name__ == "__main__":
    # Install rich if not available
    if not RICH_AVAILABLE:
        print("Installing rich for better user experience...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "rich", "netifaces"]
            )
            print("Please run the setup wizard again for the best experience.")
            sys.exit(0)
        except BaseException:
            print("Continuing with basic interface...")

    sys.exit(main())
