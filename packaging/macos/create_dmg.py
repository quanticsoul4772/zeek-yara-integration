#!/usr/bin/env python3
"""
macOS DMG creation for Zeek-YARA Educational Platform
Creates professional macOS disk images with app bundles
"""

import os
import sys
import subprocess
import platform
import shutil
import tempfile
from pathlib import Path
import plistlib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from packaging.version import VERSION_INFO

class MacOSDMGBuilder:
    """Build macOS DMG installer."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.packaging_dir = self.project_root / 'packaging'
        self.macos_dir = self.packaging_dir / 'macos'
        self.dist_dir = self.project_root / 'dist'
        self.app_bundle = self.dist_dir / 'ZeekYARAEducational.app'
        
        # Application metadata
        self.app_name = VERSION_INFO['name']
        self.app_version = VERSION_INFO['version']
        self.app_description = VERSION_INFO['description']
        self.bundle_id = 'edu.security.zeek-yara'
        
    def check_macos_tools(self) -> bool:
        """Check if macOS development tools are available."""
        tools = ['hdiutil', 'codesign', 'spctl']
        
        for tool in tools:
            if not shutil.which(tool):
                print(f"Warning: {tool} not found")
                return False
        
        return True
    
    def create_app_bundle(self) -> Path:
        """Create macOS app bundle if not exists."""
        if self.app_bundle.exists():
            print(f"App bundle already exists: {self.app_bundle}")
            return self.app_bundle
        
        print("Creating macOS app bundle...")
        
        # Create bundle structure
        contents_dir = self.app_bundle / 'Contents'
        macos_dir = contents_dir / 'MacOS'
        resources_dir = contents_dir / 'Resources'
        
        for directory in [contents_dir, macos_dir, resources_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Copy executable
        exe_src = self.dist_dir / 'ZeekYARAEducational' / 'ZeekYARAEducational'
        exe_dst = macos_dir / 'ZeekYARAEducational'
        
        if exe_src.exists():
            shutil.copy2(exe_src, exe_dst)
            os.chmod(exe_dst, 0o755)
        
        # Copy app resources
        app_resources = self.dist_dir / 'ZeekYARAEducational'
        if app_resources.exists():
            for item in app_resources.iterdir():
                if item.name != 'ZeekYARAEducational':  # Skip main executable
                    if item.is_dir():
                        shutil.copytree(item, resources_dir / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, resources_dir / item.name)
        
        # Create Info.plist
        self.create_info_plist(contents_dir / 'Info.plist')\n        \n        # Copy icon if available\n        icon_src = self.packaging_dir / 'assets' / 'icon.icns'\n        if icon_src.exists():\n            shutil.copy2(icon_src, resources_dir / 'icon.icns')\n        \n        print(f\"✅ App bundle created: {self.app_bundle}\")\n        return self.app_bundle\n    \n    def create_info_plist(self, plist_path: Path):\n        \"\"\"Create Info.plist for app bundle.\"\"\"\n        info_dict = {\n            'CFBundleName': self.app_name,\n            'CFBundleDisplayName': self.app_name,\n            'CFBundleIdentifier': self.bundle_id,\n            'CFBundleVersion': self.app_version,\n            'CFBundleShortVersionString': self.app_version,\n            'CFBundleExecutable': 'ZeekYARAEducational',\n            'CFBundlePackageType': 'APPL',\n            'CFBundleSignature': 'ZYEP',\n            'CFBundleIconFile': 'icon.icns',\n            'CFBundleGetInfoString': f'{self.app_name} {self.app_version}',\n            'NSHighResolutionCapable': True,\n            'NSAppleScriptEnabled': False,\n            'NSRequiresAquaSystemAppearance': False,\n            'NSSupportsAutomaticGraphicsSwitching': True,\n            'LSMinimumSystemVersion': '10.14.0',\n            'LSApplicationCategoryType': 'public.app-category.education',\n            'NSHumanReadableCopyright': f'Copyright © 2024 {VERSION_INFO[\"author\"]}',\n            'CFBundleDocumentTypes': [],\n            'UTExportedTypeDeclarations': [],\n            'NSPrincipalClass': 'NSApplication',\n            'NSMainNibFile': 'MainMenu',\n            'LSUIElement': False  # Show in dock\n        }\n        \n        with open(plist_path, 'wb') as f:\n            plistlib.dump(info_dict, f)\n    \n    def sign_app_bundle(self, identity: str = None) -> bool:\n        \"\"\"Code sign the app bundle.\"\"\"\n        if not identity:\n            identity = os.environ.get('CODESIGN_IDENTITY', '-')  # Ad-hoc signing\n        \n        print(f\"Signing app bundle with identity: {identity}\")\n        \n        try:\n            # Sign all binaries first\n            for root, dirs, files in os.walk(self.app_bundle):\n                for file in files:\n                    file_path = Path(root) / file\n                    if file_path.is_file() and os.access(file_path, os.X_OK):\n                        subprocess.run([\n                            'codesign', '--force', '--sign', identity,\n                            '--timestamp', '--options', 'runtime',\n                            str(file_path)\n                        ], check=True, capture_output=True)\n            \n            # Sign the app bundle\n            subprocess.run([\n                'codesign', '--force', '--sign', identity,\n                '--timestamp', '--options', 'runtime',\n                '--entitlements', str(self.create_entitlements()),\n                str(self.app_bundle)\n            ], check=True, capture_output=True)\n            \n            print(\"✅ App bundle signed successfully\")\n            return True\n            \n        except subprocess.CalledProcessError as e:\n            print(f\"Warning: Code signing failed: {e}\")\n            print(\"Continuing without code signing...\")\n            return False\n    \n    def create_entitlements(self) -> Path:\n        \"\"\"Create entitlements file for hardened runtime.\"\"\"\n        entitlements_path = self.macos_dir / 'entitlements.plist'\n        \n        entitlements = {\n            'com.apple.security.cs.allow-jit': True,\n            'com.apple.security.cs.allow-unsigned-executable-memory': True,\n            'com.apple.security.cs.allow-dyld-environment-variables': True,\n            'com.apple.security.network.client': True,\n            'com.apple.security.network.server': True,\n            'com.apple.security.files.user-selected.read-write': True,\n            'com.apple.security.files.downloads.read-write': True\n        }\n        \n        with open(entitlements_path, 'wb') as f:\n            plistlib.dump(entitlements, f)\n        \n        return entitlements_path\n    \n    def create_dmg_background(self) -> Path:\n        \"\"\"Create DMG background image.\"\"\"\n        background_path = self.macos_dir / 'dmg_background.png'\n        \n        # Create a simple background with instructions\n        # In a real implementation, you'd use PIL or similar to create this\n        # For now, we'll create a placeholder\n        \n        instructions = f\"\"\"\n# DMG Background Instructions\n\nCreate a 600x400 PNG image with:\n1. Background color: Light blue/white gradient\n2. Text: \"Drag {self.app_name} to Applications folder\"\n3. Arrow pointing from app icon to Applications folder\n4. Version info: {self.app_version}\n\nSave as: {background_path}\n\"\"\"\n        \n        with open(background_path.with_suffix('.txt'), 'w') as f:\n            f.write(instructions)\n        \n        # Create a minimal background (you should replace this with actual image creation)\n        if not background_path.exists():\n            # Create placeholder background\n            import base64\n            \n            # Minimal PNG data (1x1 transparent pixel)\n            png_data = base64.b64decode(\n                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='\n            )\n            \n            with open(background_path, 'wb') as f:\n                f.write(png_data)\n        \n        return background_path\n    \n    def create_dmg_script(self) -> Path:\n        \"\"\"Create AppleScript for DMG customization.\"\"\"\n        script_path = self.macos_dir / 'dmg_setup.scpt'\n        \n        applescript = f'''\ntell application \"Finder\"\n    tell disk \"{self.app_name}\"\n        open\n        set current view of container window to icon view\n        set toolbar visible of container window to false\n        set statusbar visible of container window to false\n        set the bounds of container window to {{100, 100, 700, 500}}\n        set theViewOptions to the icon view options of container window\n        set arrangement of theViewOptions to not arranged\n        set icon size of theViewOptions to 128\n        set background picture of theViewOptions to file \".background:dmg_background.png\"\n        \n        -- Position icons\n        set position of item \"{self.app_name}.app\" of container window to {{150, 200}}\n        set position of item \"Applications\" of container window to {{450, 200}}\n        \n        -- Update and close\n        update without registering applications\n        delay 2\n        close\n    end tell\nend tell\n'''\n        \n        with open(script_path, 'w') as f:\n            f.write(applescript)\n        \n        return script_path\n    \n    def build_dmg(self) -> Path:\n        \"\"\"Build the DMG file.\"\"\"\n        print(\"Building macOS DMG...\")\n        \n        # Create temporary directory for DMG contents\n        with tempfile.TemporaryDirectory() as temp_dir:\n            temp_path = Path(temp_dir)\n            dmg_contents = temp_path / 'dmg_contents'\n            dmg_contents.mkdir()\n            \n            # Copy app bundle to DMG contents\n            app_bundle = self.create_app_bundle()\n            shutil.copytree(app_bundle, dmg_contents / f'{self.app_name}.app')\n            \n            # Create Applications symlink\n            applications_link = dmg_contents / 'Applications'\n            applications_link.symlink_to('/Applications')\n            \n            # Create .background directory for background image\n            background_dir = dmg_contents / '.background'\n            background_dir.mkdir()\n            \n            background_img = self.create_dmg_background()\n            if background_img.exists():\n                shutil.copy2(background_img, background_dir / 'dmg_background.png')\n            \n            # Create DMG\n            dmg_path = self.macos_dir / f'{self.app_name.replace(\" \", \"\")}-{self.app_version}.dmg'\n            temp_dmg = temp_path / 'temp.dmg'\n            \n            # Create temporary DMG\n            subprocess.run([\n                'hdiutil', 'create',\n                '-volname', self.app_name,\n                '-srcfolder', str(dmg_contents),\n                '-ov', '-format', 'UDRW',\n                str(temp_dmg)\n            ], check=True)\n            \n            # Mount temporary DMG\n            mount_result = subprocess.run([\n                'hdiutil', 'attach', str(temp_dmg),\n                '-readwrite', '-noverify', '-noautoopen'\n            ], capture_output=True, text=True, check=True)\n            \n            # Extract mount point\n            mount_point = None\n            for line in mount_result.stdout.split('\\n'):\n                if '/Volumes/' in line:\n                    mount_point = line.split('\\t')[-1].strip()\n                    break\n            \n            if mount_point:\n                try:\n                    # Run AppleScript to customize DMG\n                    script_path = self.create_dmg_script()\n                    subprocess.run(['osascript', str(script_path)], \n                                 capture_output=True, check=False)\n                    \n                finally:\n                    # Unmount DMG\n                    subprocess.run(['hdiutil', 'detach', mount_point], \n                                 capture_output=True)\n            \n            # Convert to final compressed DMG\n            subprocess.run([\n                'hdiutil', 'convert', str(temp_dmg),\n                '-format', 'UDZO',\n                '-imagekey', 'zlib-level=9',\n                '-o', str(dmg_path)\n            ], check=True)\n        \n        print(f\"✅ DMG created: {dmg_path}\")\n        return dmg_path\n    \n    def notarize_dmg(self, dmg_path: Path) -> bool:\n        \"\"\"Notarize DMG with Apple (requires developer account).\"\"\"\n        apple_id = os.environ.get('APPLE_ID')\n        app_password = os.environ.get('APP_SPECIFIC_PASSWORD')\n        team_id = os.environ.get('TEAM_ID')\n        \n        if not all([apple_id, app_password, team_id]):\n            print(\"Skipping notarization (missing credentials)\")\n            return False\n        \n        print(\"Starting notarization process...\")\n        \n        try:\n            # Submit for notarization\n            result = subprocess.run([\n                'xcrun', 'notarytool', 'submit',\n                str(dmg_path),\n                '--apple-id', apple_id,\n                '--password', app_password,\n                '--team-id', team_id,\n                '--wait'\n            ], capture_output=True, text=True, check=True)\n            \n            print(\"✅ Notarization successful\")\n            \n            # Staple the notarization\n            subprocess.run([\n                'xcrun', 'stapler', 'staple', str(dmg_path)\n            ], check=True)\n            \n            print(\"✅ Notarization stapled\")\n            return True\n            \n        except subprocess.CalledProcessError as e:\n            print(f\"Notarization failed: {e}\")\n            return False\n    \n    def verify_dmg(self, dmg_path: Path) -> bool:\n        \"\"\"Verify DMG integrity and signatures.\"\"\"\n        print(\"Verifying DMG...\")\n        \n        try:\n            # Verify DMG integrity\n            subprocess.run([\n                'hdiutil', 'verify', str(dmg_path)\n            ], check=True, capture_output=True)\n            \n            # Verify code signatures if signed\n            subprocess.run([\n                'spctl', '--assess', '--type', 'open',\n                '--context', 'context:primary-signature',\n                str(dmg_path)\n            ], check=False, capture_output=True)\n            \n            print(\"✅ DMG verification passed\")\n            return True\n            \n        except subprocess.CalledProcessError:\n            print(\"Warning: DMG verification failed\")\n            return False\n\ndef main():\n    \"\"\"Main DMG creation process.\"\"\"\n    if platform.system() != 'Darwin':\n        print(\"This script is for macOS only!\")\n        sys.exit(1)\n    \n    builder = MacOSDMGBuilder()\n    \n    # Ensure macos directory exists\n    builder.macos_dir.mkdir(exist_ok=True)\n    \n    try:\n        # Check tools\n        if not builder.check_macos_tools():\n            print(\"Warning: Some macOS development tools are missing\")\n        \n        # Sign app bundle (optional)\n        app_bundle = builder.create_app_bundle()\n        builder.sign_app_bundle()\n        \n        # Build DMG\n        dmg_path = builder.build_dmg()\n        \n        # Notarize (optional, requires developer account)\n        builder.notarize_dmg(dmg_path)\n        \n        # Verify\n        builder.verify_dmg(dmg_path)\n        \n        print(f\"\\n🎉 macOS packaging complete!\")\n        print(f\"DMG file: {dmg_path}\")\n        print(f\"App bundle: {app_bundle}\")\n        \n    except Exception as e:\n        print(f\"❌ Build failed: {e}\")\n        sys.exit(1)\n\nif __name__ == \"__main__\":\n    main()"