#!/usr/bin/env python3
"""
PyInstaller configuration for Zeek-YARA Educational Platform
Creates portable, self-contained executables for all platforms
"""

import os
import platform
import sys
from pathlib import Path

# Get project root and platform info
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
PLATFORM = platform.system().lower()
ARCH = platform.machine().lower()

# Application metadata
from packaging.version import VERSION_INFO

# PyInstaller spec configuration
PYINSTALLER_CONFIG = {
    "name": "ZeekYARAEducational",
    "script": str(PROJECT_ROOT / "main.py"),
    "icon": str(PROJECT_ROOT / "packaging" / "assets" / "icon.ico"),
    "version_file": str(PROJECT_ROOT / "packaging" / "assets" / "version_info.txt"),
    "additional_files": [
        (str(PROJECT_ROOT / "EDUCATION"), "EDUCATION"),
        (str(PROJECT_ROOT / "docs"), "docs"),
        (str(PROJECT_ROOT / "rules" / "templates"), "rules/templates"),
        (str(PROJECT_ROOT / "config" / "default_config.json"), "config"),
        (str(PROJECT_ROOT / "packaging" / "assets"), "assets"),
    ],
    "hidden_imports": [
        "yara",
        "magic",
        "watchdog",
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "requests",
        "rich",
        "typer",
    ],
    "excluded_modules": [
        "tkinter",
        "matplotlib",
        "scipy",
        "numpy.distutils",
        "test",
        "tests",
    ],
    "console": True,  # Set to False for GUI-only version
    "onefile": False,  # Directory distribution for better performance
    "clean": True,
    "upx": False,  # Disable UPX compression for compatibility
}


def get_platform_specific_config():
    """Get platform-specific PyInstaller configuration."""
    config = PYINSTALLER_CONFIG.copy()

    if PLATFORM == "windows":
        config.update(
            {
                "icon": str(PROJECT_ROOT / "packaging" / "assets" / "icon.ico"),
                "version_file": str(PROJECT_ROOT / "packaging" / "assets" / "version_info.txt"),
                "runtime_tmpdir": None,  # Use temp directory
            }
        )
    elif PLATFORM == "darwin":
        config.update(
            {
                "icon": str(PROJECT_ROOT / "packaging" / "assets" / "icon.icns"),
                "bundle_identifier": "edu.security.zeek-yara",
                "codesign_identity": os.environ.get("CODESIGN_IDENTITY"),
            }
        )
    elif PLATFORM == "linux":
        config.update(
            {
                "icon": str(PROJECT_ROOT / "packaging" / "assets" / "icon.png"),
            }
        )

    return config


def create_spec_file():
    """Create PyInstaller spec file."""
    config = get_platform_specific_config()

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Zeek-YARA Educational Platform
Auto-generated from packaging configuration
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(r"{PROJECT_ROOT}")
sys.path.insert(0, str(project_root))

# Analysis configuration
block_cipher = None

a = Analysis(
    [r"{config['script']}"],
    pathex=[str(project_root)],
    binaries=[],
    datas={config['additional_files']},
    hiddenimports={config['hidden_imports']},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={config['excluded_modules']},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicates and optimize
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{config['name']}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={str(config['upx']).lower()},
    console={str(config['console']).lower()},
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity='{config.get('codesign_identity', '')}',
    entitlements_file=None,
'''

    # Add platform-specific icon
    if config.get("icon") and Path(config["icon"]).exists():
        spec_content += f"    icon=r\"{config['icon']}\",\n"

    # Add version file for Windows
    if PLATFORM == "windows" and config.get("version_file"):
        spec_content += f"    version=r\"{config['version_file']}\",\n"

    spec_content += """)

# Collect files for distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='{config['name']}',
)
"""

    # Add macOS app bundle configuration
    if PLATFORM == "darwin":
        spec_content += f"""
# macOS App Bundle
app = BUNDLE(
    coll,
    name='{config['name']}.app',
    icon=r"{config.get('icon', '')}",
    bundle_identifier='{config.get('bundle_identifier', 'edu.security.zeek-yara')}',
    version='{VERSION_INFO['version']}',
    info_plist={{
        'CFBundleName': '{VERSION_INFO['name']}',
        'CFBundleDisplayName': '{VERSION_INFO['name']}',
        'CFBundleIdentifier': '{config.get('bundle_identifier', 'edu.security.zeek-yara')}',
        'CFBundleVersion': '{VERSION_INFO['version']}',
        'CFBundleShortVersionString': '{VERSION_INFO['version']}',
        'CFBundleGetInfoString': '{VERSION_INFO['description']}',
        'NSHighResolutionCapable': True,
        'NSAppleScriptEnabled': False,
        'NSRequiresAquaSystemAppearance': False,
    }},
)
"""

    # Write spec file
    spec_path = PROJECT_ROOT / "packaging" / f'{config["name"]}.spec'
    with open(spec_path, "w") as f:
        f.write(spec_content)

    return spec_path


def create_build_script():
    """Create platform-specific build script."""
    config = get_platform_specific_config()

    if PLATFORM == "windows":
        script_content = f"""@echo off
REM Build script for Windows
echo Building Zeek-YARA Educational Platform for Windows...

set PROJECT_ROOT={PROJECT_ROOT}
set BUILD_DIR=%PROJECT_ROOT%\\dist
set SPEC_FILE=%PROJECT_ROOT%\\packaging\\{config["name"]}.spec

REM Clean previous builds
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

REM Create spec file
python "%PROJECT_ROOT%\\packaging\\pyinstaller_config.py"

REM Build with PyInstaller
pyinstaller --clean --noconfirm "%SPEC_FILE%"

REM Create installer
echo Creating Windows installer...
python "%PROJECT_ROOT%\\packaging\\windows\\create_installer.py"

echo Build complete!
pause
"""
        script_path = PROJECT_ROOT / "packaging" / "build_windows.bat"

    elif PLATFORM == "darwin":
        script_content = f"""#!/bin/bash
# Build script for macOS
echo "Building Zeek-YARA Educational Platform for macOS..."

PROJECT_ROOT="{PROJECT_ROOT}"
BUILD_DIR="$PROJECT_ROOT/dist"
SPEC_FILE="$PROJECT_ROOT/packaging/{config["name"]}.spec"

# Clean previous builds
rm -rf "$BUILD_DIR"

# Create spec file
python3 "$PROJECT_ROOT/packaging/pyinstaller_config.py"

# Build with PyInstaller
pyinstaller --clean --noconfirm "$SPEC_FILE"

# Create DMG
echo "Creating macOS DMG..."
python3 "$PROJECT_ROOT/packaging/macos/create_dmg.py"

echo "Build complete!"
"""
        script_path = PROJECT_ROOT / "packaging" / "build_macos.sh"

    else:  # Linux
        script_content = f"""#!/bin/bash
# Build script for Linux
echo "Building Zeek-YARA Educational Platform for Linux..."

PROJECT_ROOT="{PROJECT_ROOT}"
BUILD_DIR="$PROJECT_ROOT/dist"
SPEC_FILE="$PROJECT_ROOT/packaging/{config["name"]}.spec"

# Clean previous builds
rm -rf "$BUILD_DIR"

# Create spec file
python3 "$PROJECT_ROOT/packaging/pyinstaller_config.py"

# Build with PyInstaller
pyinstaller --clean --noconfirm "$SPEC_FILE"

# Create packages
echo "Creating Linux packages..."
python3 "$PROJECT_ROOT/packaging/linux/create_packages.py"

echo "Build complete!"
"""
        script_path = PROJECT_ROOT / "packaging" / "build_linux.sh"

    # Write build script
    with open(script_path, "w") as f:
        f.write(script_content)

    # Make executable on Unix systems
    if PLATFORM != "windows":
        os.chmod(script_path, 0o755)

    return script_path


if __name__ == "__main__":
    print("Creating PyInstaller configuration...")

    # Create spec file
    spec_path = create_spec_file()
    print(f"Created spec file: {spec_path}")

    # Create build script
    script_path = create_build_script()
    print(f"Created build script: {script_path}")

    print("PyInstaller configuration complete!")
