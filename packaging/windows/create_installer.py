#!/usr/bin/env python3
"""
Windows MSI installer creation for Zeek-YARA Educational Platform
Uses WiX Toolset for professional Windows installers
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from packaging.version import VERSION_INFO

class WindowsInstallerBuilder:
    """Build Windows MSI installer using WiX Toolset."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.packaging_dir = self.project_root / 'packaging'
        self.windows_dir = self.packaging_dir / 'windows'
        self.dist_dir = self.project_root / 'dist'
        self.app_dir = self.dist_dir / 'ZeekYARAEducational'
        
        # Installer metadata
        self.app_name = VERSION_INFO['name']
        self.app_version = VERSION_INFO['version']
        self.app_description = VERSION_INFO['description']
        self.app_manufacturer = VERSION_INFO['author']
        self.app_url = VERSION_INFO['url']
        
        # Generate GUIDs for installer components
        self.upgrade_code = "{12345678-1234-1234-1234-123456789012}"
        self.product_code = "{87654321-4321-4321-4321-210987654321}"
        
    def check_wix_toolset(self) -> bool:
        """Check if WiX Toolset is installed."""
        try:
            result = subprocess.run(['candle', '-?'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def create_wix_source(self) -> Path:
        """Create WiX source file (.wxs)."""
        
        # Create WiX XML structure
        root = ET.Element('Wix', xmlns='http://schemas.microsoft.com/wix/2006/wi')
        
        # Product element
        product = ET.SubElement(root, 'Product', {
            'Id': self.product_code,
            'Name': self.app_name,
            'Language': '1033',
            'Version': self.app_version,
            'Manufacturer': self.app_manufacturer,
            'UpgradeCode': self.upgrade_code
        })
        
        # Package element
        ET.SubElement(product, 'Package', {
            'InstallerVersion': '200',
            'Compressed': 'yes',
            'InstallScope': 'perMachine',
            'Description': self.app_description,
            'Comments': f'{self.app_name} v{self.app_version}',
            'Manufacturer': self.app_manufacturer
        })
        
        # Media element
        ET.SubElement(product, 'Media', {
            'Id': '1',
            'Cabinet': 'media1.cab',
            'EmbedCab': 'yes'
        })
        
        # Major upgrade element
        ET.SubElement(product, 'MajorUpgrade', {
            'DowngradeErrorMessage': 'A newer version of [ProductName] is already installed.'
        })
        
        # Directory structure
        target_dir = ET.SubElement(product, 'Directory', {
            'Id': 'TARGETDIR',
            'Name': 'SourceDir'
        })
        
        program_files = ET.SubElement(target_dir, 'Directory', {
            'Id': 'ProgramFilesFolder'
        })
        
        install_dir = ET.SubElement(program_files, 'Directory', {
            'Id': 'INSTALLFOLDER',
            'Name': 'ZeekYARAEducational'
        })
        
        # Desktop folder
        ET.SubElement(target_dir, 'Directory', {
            'Id': 'DesktopFolder',
            'Name': 'Desktop'
        })
        
        # Start menu folder
        programs_menu = ET.SubElement(target_dir, 'Directory', {
            'Id': 'ProgramMenuFolder'
        })
        
        app_menu = ET.SubElement(programs_menu, 'Directory', {
            'Id': 'ApplicationProgramsFolder',\n            'Name': self.app_name\n        })\n        \n        # Components\n        main_component = ET.SubElement(product, 'ComponentGroup', {\n            'Id': 'ProductComponents',\n            'Directory': 'INSTALLFOLDER'\n        })\n        \n        # Add application files\n        self.add_application_files(main_component)\n        \n        # Features\n        feature = ET.SubElement(product, 'Feature', {\n            'Id': 'ProductFeature',\n            'Title': self.app_name,\n            'Level': '1'\n        })\n        \n        ET.SubElement(feature, 'ComponentGroupRef', {\n            'Id': 'ProductComponents'\n        })\n        \n        # UI\n        ET.SubElement(product, 'UIRef', {'Id': 'WixUI_InstallDir'})\n        ET.SubElement(product, 'Property', {\n            'Id': 'WIXUI_INSTALLDIR',\n            'Value': 'INSTALLFOLDER'\n        })\n        \n        # License\n        license_file = self.project_root / 'LICENSE'\n        if license_file.exists():\n            ET.SubElement(product, 'WixVariable', {\n                'Id': 'WixUILicenseRtf',\n                'Value': str(self.create_license_rtf())\n            })\n        \n        # Write WiX source file\n        wxs_path = self.windows_dir / 'installer.wxs'\n        self.write_pretty_xml(root, wxs_path)\n        \n        return wxs_path\n    \n    def add_application_files(self, parent):\n        \"\"\"Add application files to WiX component.\"\"\"\n        if not self.app_dir.exists():\n            raise FileNotFoundError(f\"Application directory not found: {self.app_dir}\")\n        \n        # Main executable component\n        exe_component = ET.SubElement(parent, 'Component', {\n            'Id': 'MainExecutable',\n            'Guid': '{11111111-1111-1111-1111-111111111111}'\n        })\n        \n        exe_file = self.app_dir / 'ZeekYARAEducational.exe'\n        if exe_file.exists():\n            ET.SubElement(exe_component, 'File', {\n                'Id': 'MainExe',\n                'Source': str(exe_file),\n                'KeyPath': 'yes',\n                'Checksum': 'yes'\n            })\n            \n            # Desktop shortcut\n            ET.SubElement(exe_component, 'Shortcut', {\n                'Id': 'DesktopShortcut',\n                'Directory': 'DesktopFolder',\n                'Name': self.app_name,\n                'Description': self.app_description,\n                'WorkingDirectory': 'INSTALLFOLDER',\n                'Icon': 'AppIcon.exe',\n                'IconIndex': '0'\n            })\n            \n            # Start menu shortcut\n            ET.SubElement(exe_component, 'Shortcut', {\n                'Id': 'StartMenuShortcut',\n                'Directory': 'ApplicationProgramsFolder',\n                'Name': self.app_name,\n                'Description': self.app_description,\n                'WorkingDirectory': 'INSTALLFOLDER',\n                'Icon': 'AppIcon.exe',\n                'IconIndex': '0'\n            })\n            \n            # Remove shortcuts on uninstall\n            ET.SubElement(exe_component, 'RemoveFolder', {\n                'Id': 'RemoveApplicationProgramsFolder',\n                'Directory': 'ApplicationProgramsFolder',\n                'On': 'uninstall'\n            })\n            \n            # Registry entry for Add/Remove Programs\n            ET.SubElement(exe_component, 'RegistryValue', {\n                'Root': 'HKCU',\n                'Key': 'Software\\\\[Manufacturer]\\\\[ProductName]',\n                'Name': 'installed',\n                'Type': 'integer',\n                'Value': '1',\n                'KeyPath': 'no'\n            })\n        \n        # Add all other files\n        self.add_directory_files(parent, self.app_dir, 'INSTALLFOLDER')\n        \n        # Icon\n        ET.SubElement(parent, 'Icon', {\n            'Id': 'AppIcon.exe',\n            'SourceFile': str(exe_file) if exe_file.exists() else ''\n        })\n    \n    def add_directory_files(self, parent, directory: Path, dir_id: str, component_prefix: str = \"\"):\n        \"\"\"Recursively add directory files to WiX component.\"\"\"\n        component_id = 0\n        \n        for item in directory.iterdir():\n            if item.is_file() and item.name != 'ZeekYARAEducational.exe':  # Skip main exe\n                component_id += 1\n                comp_id = f\"{component_prefix}File{component_id}\"\n                \n                component = ET.SubElement(parent, 'Component', {\n                    'Id': comp_id,\n                    'Guid': f'*'\n                })\n                \n                ET.SubElement(component, 'File', {\n                    'Id': f\"File{component_id}\",\n                    'Source': str(item),\n                    'KeyPath': 'yes'\n                })\n            \n            elif item.is_dir() and not item.name.startswith('.'):\n                # Create subdirectory\n                subdir = ET.SubElement(parent, 'Directory', {\n                    'Id': f\"{dir_id}_{item.name}\",\n                    'Name': item.name\n                })\n                \n                self.add_directory_files(parent, item, f\"{dir_id}_{item.name}\", f\"{component_prefix}{item.name}_\")\n    \n    def create_license_rtf(self) -> Path:\n        \"\"\"Create RTF license file for installer.\"\"\"\n        license_file = self.project_root / 'LICENSE'\n        rtf_file = self.windows_dir / 'license.rtf'\n        \n        if license_file.exists():\n            with open(license_file, 'r') as f:\n                license_text = f.read()\n        else:\n            license_text = f\"\"\"\n{self.app_name} License Agreement\n\nThis software is provided \"AS IS\" without warranty of any kind.\nPlease refer to the project repository for full license terms.\n\nRepository: {self.app_url}\n\"\"\"\n        \n        # Create simple RTF content\n        rtf_content = r\"\"\"{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs20\n\"\"\" + license_text.replace('\\n', '\\\\par ') + \"}\"\n        \n        with open(rtf_file, 'w') as f:\n            f.write(rtf_content)\n        \n        return rtf_file\n    \n    def write_pretty_xml(self, element, file_path: Path):\n        \"\"\"Write XML with pretty formatting.\"\"\"\n        rough_string = ET.tostring(element, 'unicode')\n        reparsed = minidom.parseString(rough_string)\n        pretty_xml = reparsed.toprettyxml(indent=\"  \")\n        \n        # Remove empty lines\n        lines = [line for line in pretty_xml.split('\\n') if line.strip()]\n        pretty_xml = '\\n'.join(lines)\n        \n        with open(file_path, 'w', encoding='utf-8') as f:\n            f.write(pretty_xml)\n    \n    def build_installer(self) -> Path:\n        \"\"\"Build the MSI installer.\"\"\"\n        print(\"Building Windows MSI installer...\")\n        \n        # Check WiX Toolset\n        if not self.check_wix_toolset():\n            print(\"ERROR: WiX Toolset not found!\")\n            print(\"Please install WiX Toolset from: https://wixtoolset.org/releases/\")\n            sys.exit(1)\n        \n        # Create WiX source\n        wxs_path = self.create_wix_source()\n        print(f\"Created WiX source: {wxs_path}\")\n        \n        # Compile WiX source to object file\n        wixobj_path = self.windows_dir / 'installer.wixobj'\n        print(\"Compiling WiX source...\")\n        \n        candle_cmd = [\n            'candle',\n            '-arch', 'x64',\n            '-out', str(wixobj_path),\n            str(wxs_path)\n        ]\n        \n        result = subprocess.run(candle_cmd, capture_output=True, text=True)\n        if result.returncode != 0:\n            print(f\"Candle compilation failed: {result.stderr}\")\n            sys.exit(1)\n        \n        # Link to create MSI\n        msi_path = self.windows_dir / f'{self.app_name.replace(\" \", \"\")}-{self.app_version}-x64.msi'\n        print(\"Linking MSI installer...\")\n        \n        light_cmd = [\n            'light',\n            '-ext', 'WixUIExtension',\n            '-out', str(msi_path),\n            str(wixobj_path)\n        ]\n        \n        result = subprocess.run(light_cmd, capture_output=True, text=True)\n        if result.returncode != 0:\n            print(f\"Light linking failed: {result.stderr}\")\n            sys.exit(1)\n        \n        print(f\"✅ MSI installer created: {msi_path}\")\n        return msi_path\n    \n    def create_portable_zip(self) -> Path:\n        \"\"\"Create portable ZIP distribution.\"\"\"\n        import zipfile\n        \n        print(\"Creating portable ZIP distribution...\")\n        \n        zip_path = self.windows_dir / f'{self.app_name.replace(\" \", \"\")}-{self.app_version}-portable.zip'\n        \n        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:\n            # Add all files from dist directory\n            for file_path in self.app_dir.rglob('*'):\n                if file_path.is_file():\n                    arcname = file_path.relative_to(self.app_dir)\n                    zipf.write(file_path, arcname)\n            \n            # Add README for portable version\n            readme_content = f\"\"\"\n{self.app_name} - Portable Version\n{'=' * 50}\n\nThis is a portable version that doesn't require installation.\n\nTo run:\n1. Extract this ZIP file to any folder\n2. Double-click ZeekYARAEducational.exe\n3. Follow the setup wizard on first run\n\nFor help and documentation:\n- Website: {self.app_url}\n- Documentation: {VERSION_INFO.get('documentation_url', '')}\n- Support: {VERSION_INFO.get('support_url', '')}\n\nVersion: {self.app_version}\nBuild Date: {VERSION_INFO.get('build_date', '')}\n\"\"\"\n            \n            zipf.writestr('README.txt', readme_content)\n        \n        print(f\"✅ Portable ZIP created: {zip_path}\")\n        return zip_path\n\ndef main():\n    \"\"\"Main installer creation process.\"\"\"\n    if platform.system() != 'Windows':\n        print(\"This script is for Windows only!\")\n        sys.exit(1)\n    \n    builder = WindowsInstallerBuilder()\n    \n    # Ensure windows directory exists\n    builder.windows_dir.mkdir(exist_ok=True)\n    \n    try:\n        # Build MSI installer\n        msi_path = builder.build_installer()\n        \n        # Create portable ZIP\n        zip_path = builder.create_portable_zip()\n        \n        print(\"\\n🎉 Windows packaging complete!\")\n        print(f\"MSI Installer: {msi_path}\")\n        print(f\"Portable ZIP: {zip_path}\")\n        \n    except Exception as e:\n        print(f\"❌ Build failed: {e}\")\n        sys.exit(1)\n\nif __name__ == \"__main__\":\n    main()"}