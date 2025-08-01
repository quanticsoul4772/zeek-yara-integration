#!/usr/bin/env python3
"""
Linux package creation for Zeek-YARA Educational Platform
Creates DEB, RPM, and AppImage packages for Linux distributions
"""

import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
from pathlib import Path

from packaging.version import VERSION_INFO

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class LinuxPackageBuilder:
    """Build Linux packages (DEB, RPM, AppImage)."""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.packaging_dir = self.project_root / "packaging"
        self.linux_dir = self.packaging_dir / "linux"
        self.dist_dir = self.project_root / "dist"
        self.app_dir = self.dist_dir / "ZeekYARAEducational"

        # Package metadata
        self.app_name = "zeek-yara-educational"
        self.app_display_name = VERSION_INFO["name"]
        self.app_version = VERSION_INFO["version"]
        self.app_description = VERSION_INFO["description"]
        self.app_author = VERSION_INFO["author"]
        self.app_url = VERSION_INFO["url"]
        self.app_maintainer = f"{self.app_author} <support@example.com>"

    def check_build_tools(self) -> dict:
        """Check available Linux packaging tools."""
        tools = {
            "dpkg-deb": shutil.which("dpkg-deb") is not None,
            "rpmbuild": shutil.which("rpmbuild") is not None,
            "fpm": shutil.which("fpm") is not None,
            "appimagetool": shutil.which("appimagetool") is not None,
        }

        return tools

    def create_desktop_file(self) -> str:
        """Create .desktop file for Linux desktop integration."""
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={self.app_display_name}
Comment={self.app_description}
Exec=/opt/{self.app_name}/ZeekYARAEducational
Icon={self.app_name}
Terminal=false
StartupNotify=true
Categories=Education;Security;Development;
Keywords=security;network;yara;zeek;education;
MimeType=application/x-yara;
StartupWMClass=ZeekYARAEducational
"""
        return desktop_content

    def create_systemd_service(self) -> str:
        """Create systemd service file for background operation."""
        service_content = f"""[Unit]
Description={self.app_display_name} Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=zeek-yara
Group=zeek-yara
WorkingDirectory=/opt/{self.app_name}
ExecStart=/opt/{self.app_name}/ZeekYARAEducational --web-only
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
        return service_content


def main():
    """Main Linux packaging process."""
    if platform.system() != "Linux":
        print("This script is for Linux only!")
        sys.exit(1)

    builder = LinuxPackageBuilder()

    # Ensure linux directory exists
    builder.linux_dir.mkdir(exist_ok=True)

    # Check available tools
    tools = builder.check_build_tools()
    print(f"Available packaging tools: {[k for k, v in tools.items() if v]}")

    print("Linux packaging functionality would be implemented here")


if __name__ == "__main__":
    main()
