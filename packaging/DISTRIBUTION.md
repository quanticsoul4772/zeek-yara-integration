# Zeek-YARA Educational Platform - Distribution Guide

This comprehensive guide covers all aspects of packaging, building, and distributing the Zeek-YARA Educational Platform across multiple platforms and package managers.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Build Requirements](#build-requirements)
4. [Platform-Specific Builds](#platform-specific-builds)
5. [Package Manager Distributions](#package-manager-distributions)
6. [Automated CI/CD](#automated-cicd)
7. [Desktop Integration](#desktop-integration)
8. [Auto-Update System](#auto-update-system)
9. [Troubleshooting](#troubleshooting)
10. [Development Workflow](#development-workflow)

## Overview

The Zeek-YARA Educational Platform provides multiple distribution methods to ensure zero-dependency installation across all platforms:

### Distribution Types

- **Native Installers**: Professional installers for each platform
  - Windows: MSI installers with WiX Toolset
  - macOS: DMG disk images with app bundles
  - Linux: DEB/RPM packages with systemd integration

- **Portable Applications**: No-installation-required bundles
  - Windows: ZIP archives and portable executables
  - macOS: Self-contained app bundles
  - Linux: AppImage universal binaries

- **Package Managers**: Easy installation through standard tools
  - Python: PyPI packages (`pip install zeek-yara-educational`)
  - Conda: Anaconda/Miniconda packages
  - Homebrew: macOS package manager integration
  - Linux: Repository packages for major distributions

## Quick Start

### For End Users

#### Windows
```powershell
# Download and run MSI installer
# Or use portable version - just extract and run
```

#### macOS
```bash
# Install via Homebrew (recommended)
brew install zeek-yara-educational

# Or download DMG and drag to Applications
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt install ./zeek-yara-educational_1.0.0_amd64.deb

# RHEL/CentOS/Fedora
sudo rpm -i zeek-yara-educational-1.0.0-1.x86_64.rpm

# AppImage (universal)
chmod +x ZeekYARAEducational-1.0.0-x86_64.AppImage
./ZeekYARAEducational-1.0.0-x86_64.AppImage

# Package managers
pip install zeek-yara-educational
conda install -c conda-forge zeek-yara-educational
```

### For Developers

```bash
# Clone and build
git clone https://github.com/your-org/zeek_yara_integration.git
cd zeek_yara_integration

# Build all packages
python packaging/build_all.py

# Or platform-specific
python packaging/pyinstaller_config.py
python packaging/windows/create_installer.py  # Windows only
python packaging/macos/create_dmg.py         # macOS only
python packaging/linux/create_packages.py    # Linux only
```

## Build Requirements

### Base Requirements (All Platforms)
- Python 3.8 or higher
- Git
- Internet connection (for dependencies)

### Platform-Specific Tools

#### Windows
- **PyInstaller**: `pip install pyinstaller`
- **WiX Toolset**: For MSI creation
  ```powershell
  choco install wixtoolset
  ```
- **Visual Studio Build Tools**: For native dependencies

#### macOS
- **Xcode Command Line Tools**: 
  ```bash
  xcode-select --install
  ```
- **Homebrew**: For dependencies
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```
- **create-dmg**: For DMG creation
  ```bash
  brew install create-dmg
  ```

#### Linux
- **Build essentials**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install build-essential dpkg-dev rpm
  
  # RHEL/CentOS/Fedora
  sudo yum groupinstall "Development Tools"
  sudo yum install rpm-build
  ```
- **AppImageTool**: Downloaded automatically

## Platform-Specific Builds

### Windows Builds

#### MSI Installer
```bash
# Prerequisites
python -m pip install pyinstaller

# Build executable
python packaging/pyinstaller_config.py
pyinstaller --clean --noconfirm packaging/ZeekYARAEducational.spec

# Create MSI installer (requires WiX Toolset)
python packaging/windows/create_installer.py
```

**Output**: `packaging/windows/ZeekYARAEducationalPlatform-1.0.0-x64.msi`

#### Portable ZIP
The MSI build process also creates a portable ZIP version automatically.

**Output**: `packaging/windows/ZeekYARAEducationalPlatform-1.0.0-portable.zip`

### macOS Builds

#### DMG Creation
```bash
# Build app bundle
python packaging/pyinstaller_config.py
pyinstaller --clean --noconfirm packaging/ZeekYARAEducational.spec

# Create DMG
python packaging/macos/create_dmg.py
```

**Output**: `packaging/macos/ZeekYARAEducationalPlatform-1.0.0.dmg`

#### Code Signing (Optional)
```bash
# Set environment variables for signing
export CODESIGN_IDENTITY="Developer ID Application: Your Name"
export APPLE_ID="your-apple-id@example.com"
export APP_SPECIFIC_PASSWORD="your-app-specific-password"
export TEAM_ID="your-team-id"

# Build with signing
python packaging/macos/create_dmg.py
```

### Linux Builds

#### Multiple Package Types
```bash
# Build all Linux packages
python packaging/linux/create_packages.py
```

**Outputs**:
- `packaging/linux/zeek-yara-educational_1.0.0_amd64.deb`
- `packaging/linux/zeek-yara-educational-1.0.0-1.x86_64.rpm`
- `packaging/linux/ZeekYARAEducationalPlatform-1.0.0-x86_64.AppImage`
- `packaging/linux/zeek-yara-educational-1.0.0-src.tar.gz`

#### Manual Installation (Source)
```bash
# Extract and install
tar -xzf zeek-yara-educational-1.0.0-src.tar.gz
cd zeek-yara-educational-1.0.0
sudo ./install.sh
```

## Package Manager Distributions

### PyPI (pip)

#### Setup
```bash
# Build distribution packages
cd packaging
python setup_distribution.py sdist bdist_wheel

# Upload to PyPI (requires account)
twine upload dist/*
```

#### Installation
```bash
# User installation
pip install zeek-yara-educational

# Development installation
pip install -e .[dev]
```

### Conda Forge

#### Recipe Location
`packaging/conda/meta.yaml`

#### Building
```bash
# Build conda package
conda build packaging/conda/

# Upload to conda-forge (requires PR to feedstock)
# See: https://conda-forge.org/docs/maintainer/adding_pkgs.html
```

#### Installation
```bash
conda install -c conda-forge zeek-yara-educational
```

### Homebrew

#### Formula Location
`packaging/homebrew/zeek-yara-educational.rb`

#### Installation
```bash
# Add tap (if custom repository)
brew tap your-org/homebrew-security

# Install
brew install zeek-yara-educational

# Or install from URL
brew install https://raw.githubusercontent.com/your-org/zeek_yara_integration/main/packaging/homebrew/zeek-yara-educational.rb
```

## Automated CI/CD

### GitHub Actions

#### Build Workflow
Location: `.github/workflows/build-and-release.yml`

**Triggers**:
- Push to tags (`v*`)
- Pull requests
- Manual workflow dispatch

**Matrix Strategy**:
- Windows (latest)
- macOS (latest)  
- Linux (Ubuntu latest)
- Python versions: 3.8, 3.9, 3.10, 3.11

#### Test Workflow
Location: `.github/workflows/test.yml`

**Features**:
- Multi-platform testing
- Code quality checks (Black, Flake8, MyPy)
- Security scanning (Bandit, Safety)
- Coverage reporting
- Performance benchmarks

#### Release Process
1. **Tag Creation**: Push version tag (`git tag v1.0.0`)
2. **Automated Build**: GitHub Actions builds all packages
3. **Release Creation**: Automatic GitHub release with assets
4. **Distribution**: Packages uploaded to respective repositories

### Secrets Configuration

Required GitHub Secrets:
```bash
# macOS Code Signing
MACOS_CERTIFICATE          # Base64 encoded certificate
MACOS_CERTIFICATE_PASSWORD # Certificate password
MACOS_KEYCHAIN_PASSWORD    # Keychain password
MACOS_CODESIGN_IDENTITY    # Signing identity
APPLE_ID                   # Apple ID for notarization
APP_SPECIFIC_PASSWORD      # App-specific password
TEAM_ID                    # Developer team ID

# Package Publishing
PYPI_API_TOKEN            # PyPI upload token
CONDA_TOKEN               # Anaconda upload token
```

## Desktop Integration

### Installation
```bash
# Install desktop integration
python packaging/desktop_integration.py --install

# Remove desktop integration
python packaging/desktop_integration.py --uninstall
```

### Features

#### Linux
- **Desktop Files**: Application menu entries
- **MIME Types**: File association for .yar, .yara, .rules
- **Icons**: Multiple sizes in hicolor theme
- **Right-click Actions**: Open with Zeek-YARA Educational

#### macOS
- **App Bundle**: Native macOS application
- **Spotlight Integration**: Searchable from Spotlight
- **Dock Integration**: Proper dock icon and menu

#### Windows
- **Start Menu**: Shortcuts in Start Menu
- **Desktop Shortcuts**: Optional desktop icons
- **File Associations**: Double-click to open .yar/.rules files
- **Context Menu**: Right-click integration

## Auto-Update System

### Features
- **Automatic Checking**: Configurable interval (default: 24 hours)
- **Secure Downloads**: Verification and backup before update
- **Platform Awareness**: Downloads appropriate package type
- **User Control**: Manual approval required for installation

### Usage
```bash
# Check for updates
python packaging/updater.py --check

# Download available update
python packaging/updater.py --download

# Install downloaded update
python packaging/updater.py --install update-file.ext

# Show update status
python packaging/updater.py --status

# Automatic check (used by main application)
python packaging/updater.py --auto
```

### Configuration
Update settings in application config:
```json
{
  "update_config": {
    "auto_check": true,
    "check_interval": 86400,
    "auto_download": false,
    "backup_before_update": true
  }
}
```

## Troubleshooting

### Common Build Issues

#### "PyInstaller failed to execute script"
```bash
# Solution: Check dependencies and paths
python -c "import main; import setup_wizard"  # Test imports
pyinstaller --debug=all your_script.py       # Debug mode
```

#### "WiX Toolset not found" (Windows)
```bash
# Install WiX Toolset
choco install wixtoolset
# Add to PATH or restart terminal
```

#### "Code signing failed" (macOS)
```bash
# Check certificate
security find-identity -v -p codesigning

# Verify environment variables
echo $CODESIGN_IDENTITY
```

#### "dpkg-deb: command not found" (Linux)
```bash
# Install packaging tools
sudo apt-get install dpkg-dev rpm build-essential
```

### Platform-Specific Issues

#### Windows
- **Antivirus False Positives**: Some AV software flags PyInstaller executables
  - **Solution**: Code signing certificate or AV whitelist
- **Permission Errors**: MSI installation requires admin rights
  - **Solution**: Run as administrator or use portable version

#### macOS
- **Gatekeeper Warnings**: Unsigned applications show security warnings
  - **Solution**: Code signing certificate or user override in System Preferences
- **Permission Issues**: Network monitoring requires privileges
  - **Solution**: Application requests permissions on first run

#### Linux
- **Missing Dependencies**: Some distributions lack required libraries
  - **Solution**: Install development packages or use AppImage
- **Desktop Integration**: Some desktop environments don't support standards
  - **Solution**: Manual shortcut creation

### Version Conflicts

#### Python Version Mismatch
```bash
# Check Python version
python --version

# Use specific Python version
python3.9 -m pip install zeek-yara-educational
```

#### Dependency Conflicts
```bash
# Use virtual environment
python -m venv zeek-yara-env
source zeek-yara-env/bin/activate  # Linux/macOS
# zeek-yara-env\Scripts\activate     # Windows
pip install zeek-yara-educational
```

## Development Workflow

### Setting Up Development Environment
```bash
# Clone repository
git clone https://github.com/your-org/zeek_yara_integration.git
cd zeek_yara_integration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate     # Windows

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run application
python main.py
```

### Building for Distribution

#### Local Development Build
```bash
# Build current platform only
python packaging/pyinstaller_config.py
```

#### Release Build Process
```bash
# 1. Update version
# Edit packaging/version.py

# 2. Update changelog
# Edit CHANGELOG.md

# 3. Create and push tag
git tag v1.0.0
git push origin v1.0.0

# 4. GitHub Actions will automatically:
#    - Build all platforms
#    - Run tests
#    - Create release
#    - Upload packages
```

### Testing Packages

#### Local Testing
```bash
# Test PyInstaller build
dist/ZeekYARAEducational/ZeekYARAEducational --help

# Test package installation
pip install dist/zeek_yara_educational-1.0.0-py3-none-any.whl
```

#### CI Testing
- All packages are tested automatically in CI
- Multiple Python versions and platforms
- Installation and basic functionality tests

### Release Checklist

Before creating a release:

- [ ] Update version in `packaging/version.py`
- [ ] Update `CHANGELOG.md`
- [ ] Run full test suite: `pytest`
- [ ] Test local builds on target platforms
- [ ] Update documentation if needed
- [ ] Create and push version tag
- [ ] Monitor CI/CD pipeline
- [ ] Test released packages
- [ ] Update package manager repositories if needed

## Support and Contributing

### Getting Help
- **Documentation**: [Project Wiki](https://github.com/your-org/zeek_yara_integration/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/zeek_yara_integration/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/zeek_yara_integration/discussions)

### Contributing to Distribution
1. Fork the repository
2. Create feature branch for packaging improvements
3. Test on target platforms
4. Submit pull request with detailed description
5. Include any new dependencies or build requirements

### Package Maintainers
Different package managers may have separate maintainers:
- **PyPI**: Managed by core team
- **Conda Forge**: Community-maintained feedstock
- **Homebrew**: Community-maintained formula
- **Linux Distros**: Distribution-specific maintainers

---

This distribution system ensures the Zeek-YARA Educational Platform can be easily installed and used by educators, students, and security professionals across all major platforms with minimal technical knowledge required.