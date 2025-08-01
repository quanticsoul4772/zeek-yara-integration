#!/usr/bin/env python3
"""
Desktop integration for Zeek-YARA Educational Platform
Creates shortcuts, file associations, and platform-specific integration
"""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class DesktopIntegrator:
    """Handles desktop integration across platforms."""

    def __init__(self):
        self.platform = platform.system().lower()
        self.project_root = PROJECT_ROOT
        self.assets_dir = self.project_root / "packaging" / "assets"

    def install_desktop_integration(self):
        """Install desktop integration for current platform."""
        if self.platform == "linux":
            self.install_linux_desktop()
        elif self.platform == "darwin":
            self.install_macos_desktop()
        elif self.platform == "windows":
            self.install_windows_desktop()
        else:
            print(f"Desktop integration not supported for {self.platform}")

    def install_linux_desktop(self):
        """Install Linux desktop integration."""
        print("Installing Linux desktop integration...")

        # Install desktop file
        self.install_linux_desktop_file()

        # Install icons
        self.install_linux_icons()

        # Install MIME types
        self.install_linux_mime_types()

        # Update desktop database
        self.update_linux_desktop_database()

        print("✅ Linux desktop integration installed")

    def install_linux_desktop_file(self):
        """Install .desktop file for Linux."""
        desktop_file = self.assets_dir / "zeek-yara-educational.desktop"

        # User applications directory
        user_apps_dir = Path.home() / ".local" / "share" / "applications"
        user_apps_dir.mkdir(parents=True, exist_ok=True)

        # Copy desktop file
        import shutil

        shutil.copy2(desktop_file, user_apps_dir /
                     "zeek-yara-educational.desktop")

        # Make executable
        desktop_target = user_apps_dir / "zeek-yara-educational.desktop"
        desktop_target.chmod(0o755)

        print("Installed desktop file")

    def install_linux_icons(self):
        """Install icons for Linux."""
        icon_sizes = [16, 24, 32, 48, 64, 128, 256]

        # Base directories
        user_icons_dir = Path.home() / ".local" / "share" / "icons" / "hicolor"
        user_icons_dir.mkdir(parents=True, exist_ok=True)

        for size in icon_sizes:
            size_dir = user_icons_dir / f"{size}x{size}" / "apps"
            size_dir.mkdir(parents=True, exist_ok=True)

            # Look for icon file
            icon_file = self.assets_dir / f"icon-{size}.png"
            if not icon_file.exists():
                icon_file = self.assets_dir / "icon.png"  # Fallback

            if icon_file.exists():
                import shutil

                shutil.copy2(icon_file, size_dir / "zeek-yara-educational.png")

        print("Installed icons")

    def install_linux_mime_types(self):
        """Install MIME type associations for Linux."""
        mime_xml = """<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
    <mime-type type="application/x-yara">
        <comment>YARA Rule</comment>
        <comment xml:lang="en">YARA Rule</comment>
        <glob pattern="*.yar"/>
        <glob pattern="*.yara"/>
        <magic priority="50">
            <match type="string" offset="0" value="rule "/>
        </magic>
    </mime-type>
    <mime-type type="application/x-suricata-rules">
        <comment>Suricata Rule</comment>
        <comment xml:lang="en">Suricata Rule</comment>
        <glob pattern="*.rules"/>
        <magic priority="50">
            <match type="string" offset="0" value="alert "/>
            <match type="string" offset="0" value="pass "/>
            <match type="string" offset="0" value="drop "/>
            <match type="string" offset="0" value="reject "/>
        </magic>
    </mime-type>
</mime-info>"""

        # User MIME directory
        user_mime_dir = Path.home() / ".local" / "share" / "mime" / "packages"
        user_mime_dir.mkdir(parents=True, exist_ok=True)

        # Write MIME XML
        mime_file = user_mime_dir / "zeek-yara-educational.xml"
        with open(mime_file, "w") as f:
            f.write(mime_xml)

        # Update MIME database
        try:
            subprocess.run(
                ["update-mime-database",
                    str(Path.home() / ".local" / "share" / "mime")],
                check=False,
                capture_output=True,
            )
        except FileNotFoundError:
            print("update-mime-database not found, MIME types may not work")

        print("Installed MIME types")

    def update_linux_desktop_database(self):
        """Update Linux desktop database."""
        try:
            subprocess.run(
                ["update-desktop-database",
                    str(Path.home() / ".local" / "share" / "applications")],
                check=False,
                capture_output=True,
            )
        except FileNotFoundError:
            print("update-desktop-database not found")

        try:
            subprocess.run(["gtk-update-icon-cache",
                            str(Path.home() / ".local" / "share" / "icons" / "hicolor"),
                            ],
                           check=False,
                           capture_output=True,
                           )
        except FileNotFoundError:
            print("gtk-update-icon-cache not found")

    def install_macos_desktop(self):
        """Install macOS desktop integration."""
        print("Installing macOS desktop integration...")

        # Create app bundle if it doesn't exist
        self.create_macos_app_bundle()

        # Install to Applications folder
        self.install_macos_app()

        print("✅ macOS desktop integration installed")

    def create_macos_app_bundle(self):
        """Create macOS app bundle."""
        app_name = "Zeek-YARA Educational.app"
        app_path = self.project_root / "dist" / app_name

        if app_path.exists():
            return app_path

        # Create app bundle structure
        contents_dir = app_path / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"

        for directory in [contents_dir, macos_dir, resources_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Create launcher script
        launcher_script = macos_dir / "Zeek-YARA Educational"
        launcher_content = f"""#!/bin/bash
cd "{self.project_root}"
python3 main.py "$@"
"""

        with open(launcher_script, "w") as f:
            f.write(launcher_content)

        launcher_script.chmod(0o755)

        # Create Info.plist
        info_plist = contents_dir / "Info.plist"
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Zeek-YARA Educational Platform</string>
    <key>CFBundleDisplayName</key>
    <string>Zeek-YARA Educational</string>
    <key>CFBundleIdentifier</key>
    <string>edu.security.zeek-yara</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>Zeek-YARA Educational</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.education</string>
</dict>
</plist>"""

        with open(info_plist, "w") as f:
            f.write(plist_content)

        # Copy icon if available
        icon_file = self.assets_dir / "icon.icns"
        if icon_file.exists():
            import shutil

            shutil.copy2(icon_file, resources_dir / "icon.icns")

        return app_path

    def install_macos_app(self):
        """Install app to Applications folder."""
        app_name = "Zeek-YARA Educational.app"
        source_app = self.project_root / "dist" / app_name
        dest_app = Path("/Applications") / app_name

        if source_app.exists():
            try:
                if dest_app.exists():
                    import shutil

                    shutil.rmtree(dest_app)

                import shutil

                shutil.copytree(source_app, dest_app)
                print(f"Installed app to {dest_app}")
            except PermissionError:
                print(
                    f"Permission denied. Please manually copy {source_app} to /Applications/")

    def install_windows_desktop(self):
        """Install Windows desktop integration."""
        print("Installing Windows desktop integration...")

        # Create desktop shortcut
        self.create_windows_desktop_shortcut()

        # Create start menu shortcut
        self.create_windows_start_menu_shortcut()

        # Register file associations
        self.register_windows_file_associations()

        print("✅ Windows desktop integration installed")

    def create_windows_desktop_shortcut(self):
        """Create Windows desktop shortcut."""
        try:
            import win32com.client

            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "Zeek-YARA Educational.lnk"

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = str(self.project_root / "main.py")
            shortcut.WorkingDirectory = str(self.project_root)
            shortcut.Description = "Zeek-YARA Educational Platform"

            # Set icon if available
            icon_file = self.assets_dir / "icon.ico"
            if icon_file.exists():
                shortcut.IconLocation = str(icon_file)

            shortcut.save()
            print("Created desktop shortcut")

        except ImportError:
            print("pywin32 not available, creating batch file shortcut")
            self.create_windows_batch_shortcut()

    def create_windows_batch_shortcut(self):
        """Create Windows batch file shortcut."""
        desktop = Path.home() / "Desktop"
        batch_path = desktop / "Zeek-YARA Educational.bat"

        batch_content = f"""@echo off
cd /d "{self.project_root}"
python main.py %*
pause
"""

        with open(batch_path, "w") as f:
            f.write(batch_content)

        print("Created batch file shortcut")

    def create_windows_start_menu_shortcut(self):
        """Create Windows Start Menu shortcut."""
        try:
            import win32com.client

            start_menu = (
                Path.home()
                / "AppData"
                / "Roaming"
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
            )
            start_menu.mkdir(parents=True, exist_ok=True)

            shortcut_path = start_menu / "Zeek-YARA Educational.lnk"

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = str(self.project_root / "main.py")
            shortcut.WorkingDirectory = str(self.project_root)
            shortcut.Description = "Zeek-YARA Educational Platform"

            # Set icon if available
            icon_file = self.assets_dir / "icon.ico"
            if icon_file.exists():
                shortcut.IconLocation = str(icon_file)

            shortcut.save()
            print("Created Start Menu shortcut")

        except ImportError:
            print("pywin32 not available, Start Menu shortcut not created")

    def register_windows_file_associations(self):
        """Register Windows file associations."""
        try:
            import winreg

            # YARA files
            self.register_windows_file_type(
                ".yar", "YARARule", "YARA Rule File")
            self.register_windows_file_type(
                ".yara", "YARARule", "YARA Rule File")

            # Suricata rules
            self.register_windows_file_type(
                ".rules", "SuricataRule", "Suricata Rule File")

            print("Registered file associations")

        except ImportError:
            print("winreg not available, file associations not registered")

    def register_windows_file_type(
            self,
            extension: str,
            prog_id: str,
            description: str):
        """Register a single Windows file type."""
        try:
            import winreg

            # Create extension key
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, extension) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, prog_id)

            # Create ProgID key
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, prog_id) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, description)

                # Create shell command
                with winreg.CreateKey(key, "shell\\open\\command") as cmd_key:
                    command = f'"{sys.executable}" "{self.project_root / "main.py"}" "%1"'
                    winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)

        except Exception as e:
            print(f"Failed to register {extension}: {e}")

    def uninstall_desktop_integration(self):
        """Remove desktop integration."""
        if self.platform == "linux":
            self.uninstall_linux_desktop()
        elif self.platform == "darwin":
            self.uninstall_macos_desktop()
        elif self.platform == "windows":
            self.uninstall_windows_desktop()

    def uninstall_linux_desktop(self):
        """Remove Linux desktop integration."""
        files_to_remove = [
            Path.home() / ".local" / "share" / "applications" /
            "zeek-yara-educational.desktop",
            Path.home() / ".local" / "share" / "mime" /
            "packages" / "zeek-yara-educational.xml",
        ]

        for file_path in files_to_remove:
            if file_path.exists():
                file_path.unlink()

        # Remove icons
        icons_dir = Path.home() / ".local" / "share" / "icons" / "hicolor"
        for size_dir in icons_dir.glob("*/apps"):
            icon_file = size_dir / "zeek-yara-educational.png"
            if icon_file.exists():
                icon_file.unlink()

        # Update databases
        self.update_linux_desktop_database()

        print("Removed Linux desktop integration")

    def uninstall_macos_desktop(self):
        """Remove macOS desktop integration."""
        app_path = Path("/Applications") / "Zeek-YARA Educational.app"
        if app_path.exists():
            import shutil

            shutil.rmtree(app_path)
            print("Removed macOS app")

    def uninstall_windows_desktop(self):
        """Remove Windows desktop integration."""
        shortcuts_to_remove = [
            Path.home() / "Desktop" / "Zeek-YARA Educational.lnk",
            Path.home() / "Desktop" / "Zeek-YARA Educational.bat",
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Zeek-YARA Educational.lnk",
        ]

        for shortcut in shortcuts_to_remove:
            if shortcut.exists():
                shortcut.unlink()

        print("Removed Windows shortcuts")


def main():
    """CLI interface for desktop integration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Desktop Integration for Zeek-YARA Educational Platform"
    )
    parser.add_argument("--install", action="store_true",
                        help="Install desktop integration")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove desktop integration")

    args = parser.parse_args()

    integrator = DesktopIntegrator()

    if args.install:
        integrator.install_desktop_integration()
    elif args.uninstall:
        integrator.uninstall_desktop_integration()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
