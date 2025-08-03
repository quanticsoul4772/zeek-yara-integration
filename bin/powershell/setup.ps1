# PowerShell Setup Script for Zeek-YARA Integration
# Windows equivalent of bin/setup.sh

param(
    [switch]$Force,
    [switch]$Development,
    [string]$PythonVersion = "3.12.5",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Zeek-YARA Integration Windows Setup Script

USAGE:
    .\setup.ps1 [OPTIONS]

OPTIONS:
    -Force          Force overwrite existing configurations
    -Development    Install development dependencies
    -PythonVersion  Specify Python version (default: 3.12.5)
    -Help           Show this help message

EXAMPLES:
    .\setup.ps1                    # Basic setup
    .\setup.ps1 -Development       # Development setup
    .\setup.ps1 -Force             # Force reinstall
"@
    exit 0
}

$ErrorActionPreference = "Stop"

Write-Host "=== Zeek-YARA Integration Windows Setup ===" -ForegroundColor Green
Write-Host "Setting up educational security platform on Windows..." -ForegroundColor Cyan

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to create directory if it doesn't exist
function New-DirectoryIfNotExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "Created directory: $Path" -ForegroundColor Green
    }
}

# Function to check command availability
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check administrator privileges
if (-not (Test-Administrator)) {
    Write-Warning "This script requires administrator privileges for system package installation."
    Write-Host "Please run PowerShell as Administrator or manually install dependencies." -ForegroundColor Yellow
}

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Cyan
if (Test-Command "python") {
    $pythonVersionOutput = python --version 2>&1
    Write-Host "Found: $pythonVersionOutput" -ForegroundColor Green
    
    # Extract version number
    $versionMatch = [regex]::Match($pythonVersionOutput, "(\d+\.\d+\.\d+)")
    if ($versionMatch.Success) {
        $currentVersion = [version]$versionMatch.Groups[1].Value
        $requiredVersion = [version]$PythonVersion
        
        if ($currentVersion -lt $requiredVersion) {
            Write-Warning "Python $PythonVersion or higher is required. Found: $currentVersion"
            Write-Host "Please install Python $PythonVersion from https://www.python.org/downloads/" -ForegroundColor Yellow
        }
    }
} else {
    Write-Error "Python not found. Please install Python $PythonVersion from https://www.python.org/downloads/"
    exit 1
}

# Check Git
Write-Host "Checking Git installation..." -ForegroundColor Cyan
if (Test-Command "git") {
    $gitVersion = git --version
    Write-Host "Found: $gitVersion" -ForegroundColor Green
} else {
    Write-Warning "Git not found. Please install Git from https://git-scm.com/download/win"
}

# Create required directories
Write-Host "Creating required directories..." -ForegroundColor Cyan
$directories = @(
    "extracted_files",
    "logs",
    "logs\suricata", 
    "rules\active",
    "rules\suricata",
    "DATA\persistent\databases",
    "DATA\persistent\cache",
    "TESTING"
)

foreach ($dir in $directories) {
    New-DirectoryIfNotExists $dir
}

# Create virtual environment
Write-Host "Setting up Python virtual environment..." -ForegroundColor Cyan
if ((Test-Path "venv") -and $Force) {
    Remove-Item -Recurse -Force "venv"
    Write-Host "Removed existing virtual environment" -ForegroundColor Yellow
}

if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "Created virtual environment" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
& "venv\Scripts\Activate.ps1"

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "Installed production dependencies" -ForegroundColor Green
}

if ($Development -and (Test-Path "test-requirements.txt")) {
    pip install -r test-requirements.txt
    Write-Host "Installed development dependencies" -ForegroundColor Green
}

# Install package in development mode
pip install -e .
Write-Host "Installed package in development mode" -ForegroundColor Green

# Check for optional dependencies
Write-Host "Checking optional dependencies..." -ForegroundColor Cyan

# Check Zeek
if (Test-Command "zeek") {
    $zeekVersion = zeek --version 2>&1
    Write-Host "Found Zeek: $zeekVersion" -ForegroundColor Green
} else {
    Write-Warning "Zeek not found. Install from https://zeek.org/get-zeek/ or use 'choco install zeek'"
}

# Check YARA
if (Test-Command "yara") {
    $yaraVersion = yara --version 2>&1
    Write-Host "Found YARA: $yaraVersion" -ForegroundColor Green
} else {
    Write-Warning "YARA not found. Install from https://github.com/VirusTotal/yara/releases or use 'choco install yara'"
}

# Check Suricata (optional)
if (Test-Command "suricata") {
    $suricataVersion = suricata --version 2>&1
    Write-Host "Found Suricata: $suricataVersion" -ForegroundColor Green
} else {
    Write-Host "Suricata not found (optional). Install from https://suricata.io/download/" -ForegroundColor Yellow
}

# Setup configuration files
Write-Host "Setting up configuration files..." -ForegroundColor Cyan

# Copy default configuration if it doesn't exist
if (-not (Test-Path "config\default_config.json") -or $Force) {
    if (Test-Path "CONFIGURATION\defaults\default_config.json") {
        Copy-Item "CONFIGURATION\defaults\default_config.json" "config\default_config.json" -Force
        Write-Host "Copied default configuration" -ForegroundColor Green
    }
}

# Create Windows-specific config adjustments
$configPath = "config\default_config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json
    
    # Update paths for Windows
    $config.EXTRACT_DIR = "extracted_files"
    $config.LOG_FILE = "logs\yara_scan.log"
    $config.DB_FILE = "logs\alerts.db"
    
    # Set Windows network interface (user will need to adjust)
    $config.SURICATA_INTERFACE = "Ethernet"
    
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
    Write-Host "Updated configuration for Windows" -ForegroundColor Green
}

# Make CLI tool executable (Windows equivalent - create batch wrapper)
$cliWrapperPath = "TOOLS\cli\zyi.bat"
if (-not (Test-Path $cliWrapperPath) -or $Force) {
    $batchContent = @"
@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\..\.."
python TOOLS\cli\zyi.py %*
"@
    $batchContent | Set-Content $cliWrapperPath
    Write-Host "Created Windows CLI wrapper: $cliWrapperPath" -ForegroundColor Green
}

# Test installation
Write-Host "Testing installation..." -ForegroundColor Cyan

try {
    # Test CLI tool
    $cliVersion = python TOOLS\cli\zyi.py --version 2>&1
    Write-Host "CLI tool version: $cliVersion" -ForegroundColor Green
    
    # Test platform status
    $status = python TOOLS\cli\zyi.py status 2>&1
    Write-Host "Platform status checked" -ForegroundColor Green
    
} catch {
    Write-Warning "CLI tool test failed: $_"
}

# Network interface detection
Write-Host "Detecting network interfaces..." -ForegroundColor Cyan
try {
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object Name, InterfaceDescription
    Write-Host "Available network interfaces:" -ForegroundColor Green
    $adapters | Format-Table -AutoSize
    
    Write-Host "Update SURICATA_INTERFACE in config\default_config.json with the appropriate interface name" -ForegroundColor Yellow
} catch {
    Write-Warning "Could not detect network interfaces: $_"
}

# Create Windows-specific helper scripts
Write-Host "Creating Windows helper scripts..." -ForegroundColor Cyan

# Create run_tests.ps1
$runTestsScript = @"
# Windows PowerShell equivalent of run_tests.sh
param(
    [switch]`$All,
    [switch]`$Unit,
    [switch]`$Integration,
    [switch]`$Performance,
    [switch]`$Coverage,
    [switch]`$Verbose
)

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Build pytest command
`$pytestArgs = @("tests/")

if (`$Unit) { `$pytestArgs += @("-m", "unit") }
elseif (`$Integration) { `$pytestArgs += @("-m", "integration") }
elseif (`$Performance) { `$pytestArgs += @("-m", "performance") }

if (`$Coverage) {
    `$pytestArgs += @("--cov=core", "--cov=utils", "--cov=PLATFORM", "--cov-report=html", "--cov-report=xml")
}

if (`$Verbose) { `$pytestArgs += @("-v") }

# Run tests
python -m pytest @pytestArgs
"@

$runTestsScript | Set-Content "bin\powershell\run_tests.ps1"

# Create run_integrated.ps1  
$runIntegratedScript = @"
# Windows PowerShell equivalent of run_integrated.sh
param(
    [string]`$Interface = "Ethernet",
    [string]`$Read,
    [switch]`$NoSuricata,
    [switch]`$NoApi,
    [switch]`$NoScanner
)

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

Write-Host "Starting Zeek-YARA Integration Platform..." -ForegroundColor Green

# Start components based on parameters
if (-not `$NoScanner) {
    Start-Process -NoNewWindow python -ArgumentList "bin\run_scanner.py"
    Write-Host "Started YARA scanner" -ForegroundColor Cyan
}

if (-not `$NoApi) {
    Start-Process -NoNewWindow python -ArgumentList "bin\run_api.py", "--host", "0.0.0.0", "--port", "8000"
    Write-Host "Started API server on http://localhost:8000" -ForegroundColor Cyan
}

if (-not `$NoSuricata -and (Test-Command "suricata")) {
    if (`$Read) {
        Start-Process -NoNewWindow python -ArgumentList "bin\suricata_cli.py", "--pcap", `$Read
    } else {
        Start-Process -NoNewWindow python -ArgumentList "bin\suricata_cli.py", "--interface", `$Interface
    }
    Write-Host "Started Suricata monitoring" -ForegroundColor Cyan
}

# Start Zeek
if (`$Read) {
    Start-Process -NoNewWindow zeek -ArgumentList "-r", `$Read, "zeek\extract_files.zeek"
    Write-Host "Started Zeek with PCAP file: `$Read" -ForegroundColor Cyan
} else {
    Start-Process -NoNewWindow zeek -ArgumentList "-i", `$Interface, "zeek\extract_files.zeek"
    Write-Host "Started Zeek on interface: `$Interface" -ForegroundColor Cyan
}

Write-Host "Platform started. Press Ctrl+C to stop all components." -ForegroundColor Green
Write-Host "API available at: http://localhost:8000" -ForegroundColor Yellow
Write-Host "Logs location: logs\" -ForegroundColor Yellow

# Wait for user input to stop
Read-Host "Press Enter to stop all components"

# Stop all processes (simplified - user may need to manually stop)
Get-Process | Where-Object {`$_.ProcessName -match "zeek|yara|suricata|python"} | Stop-Process -Force
Write-Host "Stopped all components" -ForegroundColor Red
"@

$runIntegratedScript | Set-Content "bin\powershell\run_integrated.ps1"

Write-Host "Created Windows helper scripts in bin\powershell\" -ForegroundColor Green

# Final setup summary
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update network interface in config\default_config.json" -ForegroundColor White
Write-Host "2. Test the installation:" -ForegroundColor White
Write-Host "   python TOOLS\cli\zyi.py --version" -ForegroundColor Gray
Write-Host "   python TOOLS\cli\zyi.py status" -ForegroundColor Gray
Write-Host "   python TOOLS\cli\zyi.py demo run --tutorial basic-detection" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Optional: Install system dependencies:" -ForegroundColor White
Write-Host "   - Zeek: choco install zeek" -ForegroundColor Gray
Write-Host "   - YARA: choco install yara" -ForegroundColor Gray
Write-Host "   - Suricata: Download from https://suricata.io/download/" -ForegroundColor Gray
Write-Host ""
Write-Host "For help: python TOOLS\cli\zyi.py --help" -ForegroundColor Yellow
Write-Host "Documentation: https://github.com/quanticsoul4772/zeek-yara-integration/blob/main/README.md" -ForegroundColor Yellow

deactivate