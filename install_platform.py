#!/usr/bin/env python3
"""
Zeek-YARA Educational Platform - One-Click Installation
Transforms complex enterprise toolkit into simple educational platform
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PlatformInstaller:
    """Cross-platform installer for educational security platform."""

    def __init__(self):
        self.platform = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.project_root = Path(__file__).parent.absolute()
        self.install_log = []

    def log(self, message: str, level: str = "INFO"):
        """Log installation progress."""
        log_entry = f"[{level}] {message}"
        print(log_entry)
        self.install_log.append(log_entry)

    def run_command(
        self, cmd: List[str], description: str, capture_output: bool = True
    ) -> Tuple[bool, str]:
        """Run system command with error handling."""
        try:
            self.log(f"Running: {description}")
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                success = result.returncode == 0
                output = result.stdout if success else result.stderr
            else:
                result = subprocess.run(cmd, check=False)
                success = result.returncode == 0
                output = ""

            if success:
                self.log(f"✅ {description} completed")
            else:
                self.log(f"❌ {description} failed: {output}", "ERROR")

            return success, output
        except Exception as e:
            error_msg = f"Exception during {description}: {str(e)}"
            self.log(error_msg, "ERROR")
            return False, error_msg

    def check_python_version(self) -> bool:
        """Check if Python version meets requirements."""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.log(
                f"✅ Python {
                    version.major}.{
                    version.minor}.{
                    version.micro} meets requirements"
            )
            return True
        else:
            self.log(
                f"❌ Python {
                    version.major}.{
                    version.minor}.{
                    version.micro} does not meet requirements (3.8+)",
                "ERROR",
            )
            return False

    def detect_package_manager(self) -> Optional[str]:
        """Detect available package manager for system dependencies."""
        managers = {
            "linux": ["apt-get", "yum", "dnf", "pacman", "zypper"],
            "darwin": ["brew", "port"],
            "windows": ["choco", "scoop"],
        }

        for manager in managers.get(self.platform, []):
            if shutil.which(manager):
                self.log(f"✅ Found package manager: {manager}")
                return manager

        self.log("⚠️ No package manager detected", "WARNING")
        return None

    def install_system_dependencies(self) -> bool:
        """Install system-level dependencies."""
        self.log("Installing system dependencies...")

        package_manager = self.detect_package_manager()
        if not package_manager:
            self.log("Cannot install system dependencies automatically", "WARNING")
            self.log("Please install these manually: git, cmake, build-essential/xcode", "WARNING")
            return True  # Continue anyway

        # Platform-specific dependency installation
        dependencies = self.get_platform_dependencies()

        for dep_name, commands in dependencies.items():
            cmd = commands.get(package_manager)
            if cmd:
                success, output = self.run_command(cmd, f"Installing {dep_name}")
                if not success:
                    self.log(f"Failed to install {dep_name}, continuing anyway", "WARNING")

        return True

    def get_platform_dependencies(self) -> Dict[str, Dict[str, List[str]]]:
        """Get platform-specific dependency installation commands."""
        return {
            "git": {
                "apt-get": ["sudo", "apt-get", "install", "-y", "git"],
                "yum": ["sudo", "yum", "install", "-y", "git"],
                "dnf": ["sudo", "dnf", "install", "-y", "git"],
                "brew": ["brew", "install", "git"],
                "choco": ["choco", "install", "git", "-y"],
                "scoop": ["scoop", "install", "git"],
            },
            "build-tools": {
                "apt-get": ["sudo", "apt-get", "install", "-y", "build-essential", "cmake"],
                "yum": ["sudo", "yum", "groupinstall", "-y", "Development Tools"],
                "dnf": ["sudo", "dnf", "groupinstall", "-y", "Development Tools"],
                "brew": ["brew", "install", "cmake"],
                "choco": ["choco", "install", "cmake", "visualstudio2019buildtools", "-y"],
                "scoop": ["scoop", "install", "cmake"],
            },
            "python-dev": {
                "apt-get": ["sudo", "apt-get", "install", "-y", "python3-dev", "python3-pip"],
                "yum": ["sudo", "yum", "install", "-y", "python3-devel", "python3-pip"],
                "dnf": ["sudo", "dnf", "install", "-y", "python3-devel", "python3-pip"],
                "brew": ["brew", "install", "python"],
                "choco": ["choco", "install", "python", "-y"],
                "scoop": ["scoop", "install", "python"],
            },
        }

    def create_virtual_environment(self) -> bool:
        """Create and set up virtual environment."""
        venv_path = self.project_root / "venv"

        if venv_path.exists():
            self.log("Virtual environment already exists, removing old one...")
            shutil.rmtree(venv_path)

        try:
            self.log("Creating virtual environment...")
            venv.create(venv_path, with_pip=True)
            self.log("✅ Virtual environment created")
            return True
        except Exception as e:
            self.log(f"❌ Failed to create virtual environment: {e}", "ERROR")
            return False

    def install_python_dependencies(self) -> bool:
        """Install Python dependencies in virtual environment."""
        venv_path = self.project_root / "venv"

        # Determine pip executable path
        if self.platform == "windows":
            pip_exe = venv_path / "Scripts" / "pip.exe"
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            pip_exe = venv_path / "bin" / "pip"
            python_exe = venv_path / "bin" / "python"

        # Upgrade pip first
        success, _ = self.run_command(
            [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip"
        )
        if not success:
            self.log("Failed to upgrade pip, continuing anyway", "WARNING")

        # Install requirements
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            success, output = self.run_command(
                [str(pip_exe), "install", "-r", str(requirements_file)],
                "Installing Python dependencies",
            )
            if not success:
                self.log("Failed to install some Python dependencies", "ERROR")
                return False
        else:
            self.log("requirements.txt not found, installing minimal dependencies")
            minimal_deps = [
                "yara-python>=4.2.0",
                "watchdog>=2.1.0",
                "python-magic>=0.4.24",
                "fastapi>=0.89.0",
                "uvicorn>=0.20.0",
                "pydantic>=1.10.0",
                "sqlalchemy>=2.0.0",
                "requests>=2.28.0",
                "psutil>=5.9.0",
                "rich>=12.0.0",
                "typer>=0.7.0",
            ]

            for dep in minimal_deps:
                success, _ = self.run_command([str(pip_exe), "install", dep], f"Installing {dep}")
                if not success:
                    self.log(f"Failed to install {dep}", "WARNING")

        return True

    def create_directories(self) -> bool:
        """Create necessary directories for the platform."""
        directories = [
            "extracted_files",
            "logs",
            "logs/suricata",
            "rules/active",
            "rules/suricata",
            "config",
        ]

        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.log(f"✅ Created directory: {directory}")

        return True

    def create_simplified_config(self) -> bool:
        """Create simplified configuration for educational use."""
        config_path = self.project_root / "config" / "educational_config.json"

        simple_config = {
            "# Educational Platform Configuration": "Simplified settings for learning",
            "PLATFORM_MODE": "educational",
            "AUTO_SETUP": True,
            "BEGINNER_MODE": True,
            "# File Locations (auto-detected)": "",
            "EXTRACT_DIR": str(self.project_root / "extracted_files"),
            "RULES_DIR": str(self.project_root / "rules"),
            "LOG_DIR": str(self.project_root / "logs"),
            "# Scanner Settings (beginner-friendly)": "",
            "MAX_FILE_SIZE": "20MB",
            "SCAN_INTERVAL": "30 seconds",
            "AUTO_START_SCANNER": True,
            "SHOW_DETAILED_LOGS": False,
            "# Security Tools (auto-detected)": "",
            "TOOLS_AUTO_DETECT": True,
            "ZEEK_ENABLED": True,
            "YARA_ENABLED": True,
            "SURICATA_ENABLED": True,
            "# API Settings": "",
            "API_ENABLED": True,
            "API_PORT": 8000,
            "API_HOST": "127.0.0.1",
            "WEB_INTERFACE": True,
            "# Educational Features": "",
            "TUTORIAL_MODE": True,
            "GUIDED_SETUP": True,
            "INTERACTIVE_HELP": True,
            "PROGRESS_TRACKING": True,
            "ACHIEVEMENT_SYSTEM": True,
        }

        try:
            with open(config_path, "w") as f:
                json.dump(simple_config, f, indent=4)
            self.log("✅ Created educational configuration")
            return True
        except Exception as e:
            self.log(f"❌ Failed to create configuration: {e}", "ERROR")
            return False

    def create_launcher_scripts(self) -> bool:
        """Create easy-to-use launcher scripts."""

        # Cross-platform launcher script
        if self.platform == "windows":
            launcher_content = """@echo off
echo Starting Zeek-YARA Educational Platform...
cd /d "%~dp0"
call venv\\Scripts\\activate.bat
python main.py %*
pause
"""
            launcher_path = self.project_root / "start_platform.bat"
        else:
            launcher_content = """#!/bin/bash
echo "Starting Zeek-YARA Educational Platform..."
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py "$@"
"""
            launcher_path = self.project_root / "start_platform.sh"

        try:
            with open(launcher_path, "w") as f:
                f.write(launcher_content)

            if self.platform != "windows":
                os.chmod(launcher_path, 0o755)

            self.log("✅ Created launcher script")
            return True
        except Exception as e:
            self.log(f"❌ Failed to create launcher script: {e}", "ERROR")
            return False

    def verify_installation(self) -> bool:
        """Verify that installation completed successfully."""
        self.log("Verifying installation...")

        # Check virtual environment
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            self.log("❌ Virtual environment not found", "ERROR")
            return False

        # Check Python in venv
        if self.platform == "windows":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"

        if not python_exe.exists():
            self.log("❌ Python not found in virtual environment", "ERROR")
            return False

        # Check key dependencies
        success, output = self.run_command(
            [str(python_exe), "-c", "import yara, fastapi, uvicorn; print('Dependencies OK')"],
            "Checking Python dependencies",
        )

        if not success:
            self.log("❌ Some Python dependencies missing", "ERROR")
            return False

        self.log("✅ Installation verification successful")
        return True

    def show_completion_message(self):
        """Show installation completion message with next steps."""
        print("\n" + "=" * 60)
        print("🎉 INSTALLATION COMPLETE!")
        print("=" * 60)
        print()
        print("Your Zeek-YARA Educational Platform is ready!")
        print()
        print("NEXT STEPS:")
        print("1. Run the setup wizard:")
        print("   python setup_wizard.py")
        print()
        print("2. Or start directly with:")
        if self.platform == "windows":
            print("   start_platform.bat")
        else:
            print("   ./start_platform.sh")
        print()
        print("3. Open your web browser to:")
        print("   http://localhost:8000")
        print()
        print("GETTING STARTED:")
        print("• The platform will guide you through first-time setup")
        print("• Tutorial mode is enabled by default")
        print("• All security tools will be auto-detected")
        print("• Check the EDUCATION/ folder for learning materials")
        print()
        print("NEED HELP?")
        print("• Documentation: docs/")
        print("• Community: GitHub Discussions")
        print("• Quick start: docs/tutorials/getting-started.md")
        print()
        print("Happy learning! 🛡️")
        print("=" * 60)


def main():
    """Main installation process."""
    print("🎓 Zeek-YARA Educational Platform Installer")
    print("Transforming enterprise security toolkit into educational platform...")
    print()

    installer = PlatformInstaller()

    # Installation steps
    steps = [
        ("Checking Python version", installer.check_python_version),
        ("Installing system dependencies", installer.install_system_dependencies),
        ("Creating virtual environment", installer.create_virtual_environment),
        ("Installing Python dependencies", installer.install_python_dependencies),
        ("Creating directories", installer.create_directories),
        ("Creating configuration", installer.create_simplified_config),
        ("Creating launcher scripts", installer.create_launcher_scripts),
        ("Verifying installation", installer.verify_installation),
    ]

    failed_steps = []

    for step_name, step_function in steps:
        print(f"\n📋 {step_name}...")
        success = step_function()
        if not success:
            failed_steps.append(step_name)

    # Show results
    if failed_steps:
        print(f"\n⚠️ Installation completed with {len(failed_steps)} issues:")
        for step in failed_steps:
            print(f"  • {step}")
        print("\nYou may need to manually resolve these issues.")
        print("Check the log messages above for details.")

        # Save installation log
        log_file = installer.project_root / "installation.log"
        with open(log_file, "w") as f:
            f.write("\n".join(installer.install_log))
        print(f"\nInstallation log saved to: {log_file}")
    else:
        installer.show_completion_message()

    return 0 if not failed_steps else 1


if __name__ == "__main__":
    sys.exit(main())