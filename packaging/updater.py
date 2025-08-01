#!/usr/bin/env python3
"""
Auto-update mechanism for Zeek-YARA Educational Platform
Handles version checking, downloading, and installing updates
"""

import asyncio
import hashlib
import json
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from packaging.version import VERSION_INFO, get_version
except ImportError:
    # Fallback version info
    VERSION_INFO = {"version": "1.0.0"}

    def get_version():
        return VERSION_INFO["version"]


class UpdateManager:
    """Manages application updates."""

    def __init__(self):
        self.current_version = get_version()
        self.platform = platform.system().lower()
        self.arch = platform.machine().lower()
        self.project_root = Path(__file__).parent.parent.absolute()

        # Update configuration
        self.update_config = {
            "check_url": "https://api.github.com/repos/your-org/zeek_yara_integration/releases/latest",
            "download_base": "https://github.com/your-org/zeek_yara_integration/releases/download",
            "check_interval": 86400,  # 24 hours
            "auto_check": True,
            "auto_download": False,  # Don't auto-install for security
            "backup_before_update": True,
        }

        # Cache directory for updates
        self.cache_dir = self.get_cache_directory()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_directory(self) -> Path:
        """Get platform-specific cache directory."""
        if self.platform == "windows":
            cache_base = Path(os.environ.get("LOCALAPPDATA", "~/.cache"))
        elif self.platform == "darwin":
            cache_base = Path("~/Library/Caches")
        else:
            cache_base = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache"))

        return cache_base.expanduser() / "zeek-yara-educational" / "updates"

    def get_update_info_file(self) -> Path:
        """Get path to update info cache file."""
        return self.cache_dir / "update_info.json"

    def save_update_info(self, info: Dict):
        """Save update information to cache."""
        try:
            with open(self.get_update_info_file(), "w") as f:
                json.dump(info, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save update info: {e}")

    def load_update_info(self) -> Optional[Dict]:
        """Load cached update information."""
        try:
            info_file = self.get_update_info_file()
            if info_file.exists():
                with open(info_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load update info: {e}")
        return None

    def should_check_for_updates(self) -> bool:
        """Check if it's time to check for updates."""
        if not self.update_config["auto_check"]:
            return False

        info = self.load_update_info()
        if not info:
            return True

        import time

        last_check = info.get("last_check", 0)
        return (time.time() - last_check) > self.update_config["check_interval"]

    async def check_for_updates(self) -> Optional[Dict]:
        """Check for available updates."""
        if not REQUESTS_AVAILABLE:
            print("Requests library not available, cannot check for updates")
            return None

        try:
            print("Checking for updates...")

            # Get latest release info from GitHub API
            response = requests.get(
                self.update_config["check_url"],
                timeout=30,
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")

            # Compare versions
            if self.is_newer_version(latest_version, self.current_version):
                update_info = {
                    "available": True,
                    "current_version": self.current_version,
                    "latest_version": latest_version,
                    "release_notes": release_data.get("body", ""),
                    "download_url": self.get_download_url(release_data),
                    "published_at": release_data.get("published_at"),
                    "last_check": time.time(),
                }

                self.save_update_info(update_info)
                return update_info
            else:
                update_info = {
                    "available": False,
                    "current_version": self.current_version,
                    "latest_version": latest_version,
                    "last_check": time.time(),
                }
                self.save_update_info(update_info)
                return update_info

        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None

    def is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings to determine if update is available."""
        try:
            from packaging import version

            return version.parse(latest) > version.parse(current)
        except ImportError:
            # Fallback to simple string comparison
            latest_parts = [int(x) for x in latest.split(".")]
            current_parts = [int(x) for x in current.split(".")]

            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return latest_parts > current_parts

    def get_download_url(self, release_data: Dict) -> Optional[str]:
        """Get appropriate download URL for current platform."""
        assets = release_data.get("assets", [])

        # Platform-specific file patterns
        patterns = {
            "windows": [".msi", ".zip"],
            "darwin": [".dmg"],
            "linux": [".deb", ".rpm", ".AppImage", ".tar.gz"],
        }

        platform_patterns = patterns.get(self.platform, [])

        for asset in assets:
            name = asset["name"].lower()
            for pattern in platform_patterns:
                if pattern in name and self.platform in name:
                    return asset["browser_download_url"]

        # Fallback to source tarball
        return release_data.get("tarball_url")

    async def download_update(self, download_url: str) -> Optional[Path]:
        """Download update file."""
        if not REQUESTS_AVAILABLE:
            print("Requests library not available, cannot download updates")
            return None

        try:
            print(f"Downloading update from {download_url}")

            # Get filename from URL
            filename = Path(urlparse(download_url).path).name
            if not filename:
                filename = f"update-{self.current_version}.download"

            download_path = self.cache_dir / filename

            # Download with progress
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\\rDownload progress: {progress:.1f}%", end="", flush=True)

            print("\\nDownload completed!")

            # Verify download
            if self.verify_download(download_path):
                return download_path
            else:
                print("Download verification failed")
                download_path.unlink()
                return None

        except Exception as e:
            print(f"Error downloading update: {e}")
            return None

    def verify_download(self, file_path: Path) -> bool:
        """Verify downloaded file integrity."""
        try:
            # Basic file size check
            if file_path.stat().st_size < 1024:  # Less than 1KB is suspicious
                return False

            # TODO: Add SHA256 verification if checksums are provided
            # For now, just check if file exists and has reasonable size
            return True

        except Exception as e:
            print(f"Error verifying download: {e}")
            return False

    def backup_current_installation(self) -> bool:
        """Create backup of current installation."""
        try:
            if not self.update_config["backup_before_update"]:
                return True

            backup_dir = self.cache_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            backup_name = f"backup-{self.current_version}-{int(time.time())}.tar.gz"
            backup_path = backup_dir / backup_name

            print(f"Creating backup: {backup_path}")

            # Create tarball of current installation
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(self.project_root, arcname="zeek-yara-educational")

            print("Backup created successfully")
            return True

        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def install_update(self, update_path: Path) -> bool:
        """Install downloaded update."""
        try:
            print(f"Installing update from {update_path}")

            # Create backup first
            if not self.backup_current_installation():
                print("Backup failed, aborting update")
                return False

            # Platform-specific installation
            if self.platform == "windows":
                return self.install_windows_update(update_path)
            elif self.platform == "darwin":
                return self.install_macos_update(update_path)
            else:
                return self.install_linux_update(update_path)

        except Exception as e:
            print(f"Error installing update: {e}")
            return False

    def install_windows_update(self, update_path: Path) -> bool:
        """Install Windows update (.msi or .zip)."""
        if update_path.suffix.lower() == ".msi":
            # Run MSI installer
            cmd = ["msiexec", "/i", str(update_path), "/qb"]
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0

        elif update_path.suffix.lower() == ".zip":
            # Extract ZIP and replace files
            with zipfile.ZipFile(update_path, "r") as zip_ref:
                zip_ref.extractall(self.project_root)
            return True

        return False

    def install_macos_update(self, update_path: Path) -> bool:
        """Install macOS update (.dmg)."""
        # Mount DMG and copy app bundle
        try:
            # Mount the DMG
            mount_result = subprocess.run(
                ["hdiutil", "attach", str(update_path), "-nobrowse", "-quiet"],
                capture_output=True,
                text=True,
            )

            if mount_result.returncode != 0:
                return False

            # Find mount point
            mount_point = None
            for line in mount_result.stdout.split("\\n"):
                if "/Volumes/" in line:
                    mount_point = line.split("\\t")[-1].strip()
                    break

            if not mount_point:
                return False

            try:
                # Copy app bundle
                app_source = Path(mount_point) / "Zeek-YARA Educational.app"
                app_dest = Path("/Applications") / "Zeek-YARA Educational.app"

                if app_source.exists():
                    if app_dest.exists():
                        import shutil

                        shutil.rmtree(app_dest)
                    shutil.copytree(app_source, app_dest)
                    return True

            finally:
                # Unmount DMG
                subprocess.run(["hdiutil", "detach", mount_point], capture_output=True)

        except Exception as e:
            print(f"Error installing macOS update: {e}")

        return False

    def install_linux_update(self, update_path: Path) -> bool:
        """Install Linux update (.deb, .rpm, .AppImage, etc.)."""
        suffix = update_path.suffix.lower()

        if suffix == ".deb":
            # Install DEB package
            cmd = ["sudo", "dpkg", "-i", str(update_path)]
            result = subprocess.run(cmd)
            return result.returncode == 0

        elif suffix == ".rpm":
            # Install RPM package
            cmd = ["sudo", "rpm", "-U", str(update_path)]
            result = subprocess.run(cmd)
            return result.returncode == 0

        elif suffix == ".appimage":
            # Replace AppImage
            current_appimage = self.find_current_appimage()
            if current_appimage:
                current_appimage.unlink()
                import shutil

                shutil.copy2(update_path, current_appimage)
                os.chmod(current_appimage, 0o755)
                return True

        elif ".tar.gz" in str(update_path):
            # Extract tarball and replace files
            with tarfile.open(update_path, "r:gz") as tar:
                tar.extractall(self.project_root.parent)
            return True

        return False

    def find_current_appimage(self) -> Optional[Path]:
        """Find current AppImage executable."""
        # Look for AppImage in common locations
        locations = [
            Path("~/Applications"),
            Path("/opt"),
            Path("/usr/local/bin"),
            Path("~/.local/bin"),
        ]

        for location in locations:
            location = location.expanduser()
            if location.exists():
                for file in location.glob("*ZeekYARA*.AppImage"):
                    return file

        return None

    async def auto_update_check(self):
        """Perform automatic update check if enabled."""
        if not self.should_check_for_updates():
            return

        update_info = await self.check_for_updates()

        if update_info and update_info.get("available"):
            print(f"\\n🎉 Update available!")
            print(f"Current version: {update_info['current_version']}")
            print(f"Latest version: {update_info['latest_version']}")

            if self.update_config["auto_download"]:
                download_url = update_info.get("download_url")
                if download_url:
                    update_file = await self.download_update(download_url)
                    if update_file:
                        print("Update downloaded successfully!")
                        print("Run with --install-update to install")
            else:
                print("Run with --check-updates to download and install")

    def get_update_status(self) -> Dict:
        """Get current update status."""
        info = self.load_update_info()
        if not info:
            return {"checked": False, "available": False, "current_version": self.current_version}

        return {
            "checked": True,
            "available": info.get("available", False),
            "current_version": self.current_version,
            "latest_version": info.get("latest_version"),
            "last_check": info.get("last_check"),
        }


# CLI interface for updates
async def main():
    """Main update CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Zeek-YARA Educational Platform Updater")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--download", action="store_true", help="Download available update")
    parser.add_argument("--install", metavar="FILE", help="Install update from file")
    parser.add_argument("--status", action="store_true", help="Show update status")
    parser.add_argument("--auto", action="store_true", help="Perform automatic update check")

    args = parser.parse_args()

    updater = UpdateManager()

    if args.status:
        status = updater.get_update_status()
        print(json.dumps(status, indent=2))

    elif args.check:
        update_info = await updater.check_for_updates()
        if update_info:
            print(json.dumps(update_info, indent=2))

    elif args.download:
        update_info = await updater.check_for_updates()
        if update_info and update_info.get("available"):
            download_url = update_info.get("download_url")
            if download_url:
                update_file = await updater.download_update(download_url)
                if update_file:
                    print(f"Update downloaded to: {update_file}")
        else:
            print("No updates available")

    elif args.install:
        update_path = Path(args.install)
        if update_path.exists():
            success = updater.install_update(update_path)
            if success:
                print("Update installed successfully!")
            else:
                print("Update installation failed")
        else:
            print(f"Update file not found: {update_path}")

    elif args.auto:
        await updater.auto_update_check()

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
