# Cross-Platform Installation Guide

This guide provides detailed installation instructions for Windows, macOS, and Linux systems, with containerized deployment options.

## System Requirements

### Hardware Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 10GB disk space
- **Recommended**: 8GB RAM, 4 CPU cores, 20GB disk space
- **Network**: Internet connection for package downloads and rule updates

### Software Requirements
- **Python**: 3.12.5 or higher (critical requirement)
- **Git**: For repository cloning
- **Administrative privileges**: For system package installation

## Platform-Specific Installation

### Windows Installation

#### Method 1: Using Chocolatey (Recommended)

```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install python --version=3.12.5 -y
choco install git -y
choco install zeek -y  # Community package
choco install yara -y

# Verify installations
python --version
git --version
zeek --version
yara --version

# Clone repository
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration

# Run Windows setup script
powershell -ExecutionPolicy Bypass -File .\bin\setup.ps1
```

#### Method 2: Manual Installation

```powershell
# 1. Install Python 3.12.5
# Download from https://www.python.org/downloads/windows/
# Ensure "Add Python to PATH" is checked during installation

# 2. Install Git
# Download from https://git-scm.com/download/win

# 3. Install Zeek
# Download Windows build from https://zeek.org/get-zeek/
# Extract to C:\Program Files\Zeek

# 4. Install YARA
# Download from https://github.com/VirusTotal/yara/releases
# Extract to C:\Program Files\YARA

# 5. Install Suricata (optional)
# Download from https://suricata.io/download/
# Follow Windows installation guide

# 6. Set environment variables
$env:PATH += ";C:\Program Files\Zeek\bin"
$env:PATH += ";C:\Program Files\YARA"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, [EnvironmentVariableTarget]::User)

# 7. Clone and setup
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python install_platform.py
```

#### Windows-Specific Configuration

```powershell
# Create Windows directories
New-Item -ItemType Directory -Force -Path "extracted_files", "logs", "logs\suricata"

# Set Windows network interface (find with Get-NetAdapter)
Get-NetAdapter | Select-Object Name, InterfaceDescription
# Update config/default_config.json with correct interface name

# Test installation
.\TOOLS\cli\zyi.exe --version
.\TOOLS\cli\zyi.exe status
```

### macOS Installation

#### Method 1: Using Homebrew (Recommended)

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.12
brew install git
brew install zeek
brew install yara
brew install suricata  # Optional

# Verify installations
python3 --version  # Should show 3.12.x
git --version
zeek --version
yara --version

# Clone repository
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration

# Run setup
chmod +x bin/setup.sh
./bin/setup.sh
```

#### Method 2: Using pyenv (For specific Python version)

```bash
# Install pyenv
curl https://pyenv.run | bash

# Add to shell profile (.zshrc or .bash_profile)
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install Python 3.12.5
pyenv install 3.12.5
pyenv local 3.12.5

# Install other dependencies with Homebrew
brew install git zeek yara suricata

# Setup project
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python install_platform.py
```

#### macOS-Specific Configuration

```bash
# Find network interfaces
networksetup -listallhardwareports
ifconfig -l

# Common interface names on macOS:
# - en0: Ethernet/WiFi
# - en1: WiFi (on some systems)
# - lo0: Loopback

# Update configuration
vim config/default_config.json
# Set "SURICATA_INTERFACE": "en0" (or appropriate interface)

# Grant permissions for network monitoring
sudo chown root:admin /usr/local/bin/zeek
sudo chmod u+s /usr/local/bin/zeek

# Test installation
./TOOLS/cli/zyi --version
./TOOLS/cli/zyi status
```

### Linux Installation

#### Ubuntu/Debian

```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install Python 3.12.5 (if not available in repos, use deadsnakes PPA)
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev -y

# Install other dependencies
sudo apt install git build-essential -y

# Install Zeek
echo 'deb http://download.opensuse.org/repositories/security:/zeek/xUbuntu_22.04/ /' | sudo tee /etc/apt/sources.list.d/security:zeek.list
curl -fsSL https://download.opensuse.org/repositories/security:zeek/xUbuntu_22.04/Release.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/security_zeek.gpg > /dev/null
sudo apt update
sudo apt install zeek -y

# Install YARA
sudo apt install yara libyara-dev -y

# Install Suricata (optional)
sudo add-apt-repository ppa:oisf/suricata-stable -y
sudo apt update
sudo apt install suricata -y

# Clone and setup
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python install_platform.py
```

#### CentOS/RHEL/Fedora

```bash
# Install Python 3.12.5
sudo dnf install python3.12 python3.12-pip python3.12-devel -y

# Install dependencies
sudo dnf groupinstall "Development Tools" -y
sudo dnf install git -y

# Install Zeek (compile from source or use EPEL)
sudo dnf install epel-release -y
sudo dnf install zeek -y

# Install YARA
sudo dnf install yara yara-devel -y

# Install Suricata
sudo dnf install suricata -y

# Setup project
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python install_platform.py
```

#### Arch Linux

```bash
# Install dependencies
sudo pacman -S python git base-devel zeek yara suricata

# Verify Python version
python --version  # Install python312 if needed

# Setup project
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python install_platform.py
```

#### Linux-Specific Configuration

```bash
# Find network interfaces
ip link show
ls /sys/class/net/

# Common interface names:
# - eth0, enp0s3: Ethernet
# - wlan0, wlp2s0: WiFi
# - lo: Loopback

# Set interface in configuration
sudo vim config/default_config.json
# Update "SURICATA_INTERFACE": "eth0" (or appropriate interface)

# Set permissions for network monitoring
sudo setcap cap_net_raw,cap_net_admin+eip $(which zeek)
sudo usermod -a -G pcap $USER

# Test installation
./TOOLS/cli/zyi --version
./TOOLS/cli/zyi status
```

## Container Deployment

### Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration

# Educational environment (default)
docker-compose up -d zyi-education

# Development environment
docker-compose up -d zyi-development

# With monitoring stack
docker-compose --profile monitoring up -d

# With logging stack
docker-compose --profile logging up -d

# Full stack with all services
docker-compose --profile monitoring --profile logging --profile jupyter up -d
```

### Manual Docker Build

```bash
# Build educational image
docker build -f DEPLOYMENT/docker/Dockerfile --target education -t zyi:education .

# Run educational container
docker run -d \
  --name zyi-education \
  -p 8000:8000 \
  -p 8080:8080 \
  -v zyi-educational-data:/app/DATA \
  -e ZYI_ENV=education \
  -e ZYI_SAFE_MODE=true \
  zyi:education

# Check status
docker exec zyi-education ./TOOLS/cli/zyi status
```

### Kubernetes Deployment

```bash
# Apply educational deployment
kubectl apply -f DEPLOYMENT/kubernetes/education/

# Check deployment status
kubectl get pods -l app=zyi-education
kubectl logs -l app=zyi-education

# Access services
kubectl port-forward svc/zyi-education 8000:8000
```

## Platform-Specific Tools

### Windows PowerShell Scripts

PowerShell equivalents for shell scripts are provided in `bin/powershell/`:

```powershell
# Equivalent commands
.\bin\powershell\run_tests.ps1 -All
.\bin\powershell\run_integrated.ps1 -Interface "Ethernet"
.\bin\powershell\setup.ps1
```

### Cross-Platform Python Scripts

Use Python scripts for full cross-platform compatibility:

```bash
# These work on all platforms
python bin/run_scanner.py
python bin/run_api.py --host 0.0.0.0 --port 8000
python bin/suricata_cli.py --interface eth0
```

## Verification and Testing

### Installation Verification

Run these commands on any platform to verify installation:

```bash
# 1. Check CLI tool
./TOOLS/cli/zyi --version
./TOOLS/cli/zyi info

# 2. Verify platform status  
./TOOLS/cli/zyi status

# 3. Run demo (cross-platform)
./TOOLS/cli/zyi demo run --tutorial basic-detection

# 4. Test API server
./TOOLS/cli/zyi api start --dev --port 8000 &
curl http://localhost:8000/status

# 5. Run test suite
./TOOLS/cli/zyi dev test
```

### Platform-Specific Tests

#### Windows
```powershell
# Windows-specific verification
Get-Process | Where-Object {$_.Name -match "zeek|yara|suricata"}
Test-NetConnection -ComputerName localhost -Port 8000
```

#### macOS/Linux
```bash
# Unix-specific verification
ps aux | grep -E "(zeek|yara|suricata)"
netstat -tlnp | grep 8000
lsof -i :8000
```

## Troubleshooting

### Common Cross-Platform Issues

#### Python Version Problems
```bash
# Check Python version across platforms
python --version    # Windows
python3 --version   # macOS/Linux

# Install correct version
# Windows: Download from python.org
# macOS: brew install python@3.12
# Linux: Use package manager or pyenv
```

#### Permission Issues
```bash
# Windows (run as Administrator)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# macOS/Linux
sudo chown -R $USER:$USER extracted_files logs
chmod +x ./TOOLS/cli/zyi
```

#### Network Interface Detection
```bash
# Windows
Get-NetAdapter | Select-Object Name, InterfaceDescription

# macOS
networksetup -listallhardwareports

# Linux
ip link show
```

#### Firewall Configuration
```bash
# Windows
New-NetFirewallRule -DisplayName "ZYI API" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow

# macOS
sudo pfctl -f /etc/pf.conf

# Linux (UFW)
sudo ufw allow 8000/tcp
```

### Getting Platform-Specific Help

- **Windows**: Check Event Viewer for application errors
- **macOS**: Use Console.app for system logs  
- **Linux**: Check journalctl and /var/log/ for system logs
- **Docker**: Use `docker logs <container>` for container logs

For additional support, see [GitHub Issues](https://github.com/quanticsoul4772/zeek-yara-integration/issues) with your platform details.