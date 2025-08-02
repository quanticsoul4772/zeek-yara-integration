#!/usr/bin/env python3
"""
Windows MSI installer creation for Zeek-YARA Educational Platform
Uses WiX Toolset for professional Windows installers
"""

import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from packaging.version import VERSION_INFO

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class WindowsInstallerBuilder:
    """Build Windows MSI installer packages."""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.packaging_dir = self.project_root / "packaging"
        self.windows_dir = self.packaging_dir / "windows"
        self.dist_dir = self.project_root / "dist"
        self.app_dir = self.dist_dir / "ZeekYARAEducational"

        # Package metadata
        self.app_name = VERSION_INFO["name"]
        self.app_version = VERSION_INFO["version"]
        self.app_description = VERSION_INFO["description"]
        self.app_url = VERSION_INFO["url"]

    def check_wix_toolset(self) -> bool:
        """Check if WiX Toolset is available."""
        try:
            subprocess.run(["candle", "-?"], capture_output=True, check=True)
            subprocess.run(["light", "-?"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_wix_source(self) -> Path:
        """Create WiX source file for installer."""
        # Create basic WiX structure
        root = ET.Element("Wix", xmlns="http://schemas.microsoft.com/wix/2006/wi")

        product = ET.SubElement(
            root,
            "Product",
            {
                "Id": "*",
                "Name": self.app_name,
                "Language": "1033",
                "Version": self.app_version,
                "Manufacturer": VERSION_INFO["author"],
                "UpgradeCode": "{12345678-1234-1234-1234-123456789012}",
            },
        )

        # Package information
        ET.SubElement(
            product,
            "Package",
            {"InstallerVersion": "200", "Compressed": "yes", "InstallScope": "perMachine"},
        )

        # Media
        ET.SubElement(product, "MediaTemplate", {"EmbedCab": "yes"})

        # Directory structure
        target_dir = ET.SubElement(product, "Directory", {"Id": "TARGETDIR", "Name": "SourceDir"})

        program_files = ET.SubElement(target_dir, "Directory", {"Id": "ProgramFilesFolder"})

        install_folder = ET.SubElement(
            program_files, "Directory", {"Id": "INSTALLFOLDER", "Name": self.app_name}
        )

        # Write WiX source file
        wxs_path = self.windows_dir / "installer.wxs"
        self.write_pretty_xml(root, wxs_path)

        return wxs_path

    def write_pretty_xml(self, element, file_path: Path):
        """Write XML with pretty formatting."""
        rough_string = ET.tostring(element, "unicode")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        # Remove empty lines
        lines = [line for line in pretty_xml.split("\n") if line.strip()]
        pretty_xml = "\n".join(lines)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)


def main():
    """Main installer creation process."""
    if platform.system() != "Windows":
        print("This script is for Windows only!")
        sys.exit(1)

    builder = WindowsInstallerBuilder()

    # Ensure windows directory exists
    builder.windows_dir.mkdir(exist_ok=True)

    # Check WiX Toolset
    if not builder.check_wix_toolset():
        print("ERROR: WiX Toolset not found!")
        print("Please install WiX Toolset from: https://wixtoolset.org/releases/")
        sys.exit(1)

    print("Windows MSI installer functionality would be implemented here")


if __name__ == "__main__":
    main()
