# Windows PowerShell equivalent of bin/run_integrated.sh
# Integrated system launcher for Zeek-YARA Integration Platform

param(
    [string]$Interface = "Ethernet",
    [string]$Read = "",
    [switch]$NoSuricata,
    [switch]$NoApi,
    [switch]$NoScanner,
    [switch]$NoZeek,
    [int]$Port = 8000,
    [string]$Host = "0.0.0.0",
    [switch]$Help,
    [switch]$Status,
    [switch]$Stop,
    [switch]$Cleanup
)

if ($Help) {
    Write-Host @"
Zeek-YARA Integration Platform Launcher (Windows PowerShell)

USAGE:
    .\run_integrated.ps1 [OPTIONS]

OPTIONS:
    -Interface STRING   Network interface for live monitoring (default: Ethernet)
    -Read STRING        PCAP file path for offline analysis
    -NoSuricata         Skip Suricata network monitoring
    -NoApi              Skip API server startup
    -NoScanner          Skip YARA file scanner
    -NoZeek             Skip Zeek file extraction
    -Port INT           API server port (default: 8000)
    -Host STRING        API server host (default: 0.0.0.0)
    -Status             Show platform component status
    -Stop               Stop all platform components
    -Cleanup            Clean up temporary files and processes
    -Help               Show this help message

EXAMPLES:
    # Start full platform on default interface
    .\run_integrated.ps1

    # Start with custom interface
    .\run_integrated.ps1 -Interface "Wi-Fi"

    # Analyze PCAP file
    .\run_integrated.ps1 -Read "C:\temp\capture.pcap"

    # Start without Suricata
    .\run_integrated.ps1 -NoSuricata

    # API server only
    .\run_integrated.ps1 -NoZeek -NoScanner -NoSuricata

    # Check platform status
    .\run_integrated.ps1 -Status

    # Stop all components
    .\run_integrated.ps1 -Stop

NOTES:
    - Requires administrator privileges for network monitoring
    - Network interface names can be found with: Get-NetAdapter
    - PCAP analysis doesn't require live network access
    - API will be available at http://localhost:8000 (or custom port)

"@
    exit 0
}

$ErrorActionPreference = "Stop"

# Global variables for process tracking
$global:ZeekProcess = $null
$global:ScannerProcess = $null
$global:ApiProcess = $null
$global:SuricataProcess = $null

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to check if virtual environment is active
function Test-VirtualEnvironment {
    return $env:VIRTUAL_ENV -ne $null
}

# Function to activate virtual environment
function Activate-VirtualEnvironment {
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
        return $true
    } else {
        Write-Warning "Virtual environment not found. Run setup.ps1 first."
        return $false
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

# Function to check if port is available
function Test-Port {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

# Function to get platform component status
function Get-PlatformStatus {
    Write-Host "=== Platform Component Status ===" -ForegroundColor Green
    
    # Check processes
    $zeekRunning = Get-Process -Name "zeek" -ErrorAction SilentlyContinue
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
    $suricataRunning = Get-Process -Name "suricata" -ErrorAction SilentlyContinue
    
    Write-Host "Zeek: $($zeekRunning ? 'RUNNING' : 'STOPPED')" -ForegroundColor ($zeekRunning ? 'Green' : 'Red')
    Write-Host "Python processes: $($pythonProcesses.Count) running" -ForegroundColor Cyan
    Write-Host "Suricata: $($suricataRunning ? 'RUNNING' : 'STOPPED')" -ForegroundColor ($suricataRunning ? 'Green' : 'Red')
    
    # Check API endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/status" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "API Server: RUNNING (http://localhost:$Port)" -ForegroundColor Green
    } catch {
        Write-Host "API Server: STOPPED" -ForegroundColor Red
    }
    
    # Check log files
    Write-Host ""
    Write-Host "=== Log File Status ===" -ForegroundColor Green
    $logFiles = @("logs\yara_scan.log", "logs\api.log", "logs\suricata\eve.json")
    
    foreach ($logFile in $logFiles) {
        if (Test-Path $logFile) {
            $size = (Get-Item $logFile).Length
            Write-Host "$logFile`: $([math]::Round($size/1KB, 2)) KB" -ForegroundColor Gray
        } else {
            Write-Host "$logFile`: NOT FOUND" -ForegroundColor Yellow
        }
    }
    
    # Check database
    if (Test-Path "logs\alerts.db") {
        try {
            # Simple SQLite query to check if database is accessible
            $dbSize = (Get-Item "logs\alerts.db").Length
            Write-Host "alerts.db: $([math]::Round($dbSize/1KB, 2)) KB" -ForegroundColor Gray
        } catch {
            Write-Host "alerts.db: ERROR" -ForegroundColor Red
        }
    } else {
        Write-Host "alerts.db: NOT FOUND" -ForegroundColor Yellow
    }
}

# Function to stop all platform components
function Stop-PlatformComponents {
    Write-Host "Stopping all platform components..." -ForegroundColor Yellow
    
    # Stop tracked processes
    if ($global:ZeekProcess -and -not $global:ZeekProcess.HasExited) {
        $global:ZeekProcess.Kill()
        Write-Host "Stopped Zeek process" -ForegroundColor Red
    }
    
    if ($global:ScannerProcess -and -not $global:ScannerProcess.HasExited) {
        $global:ScannerProcess.Kill()
        Write-Host "Stopped Scanner process" -ForegroundColor Red
    }
    
    if ($global:ApiProcess -and -not $global:ApiProcess.HasExited) {
        $global:ApiProcess.Kill()
        Write-Host "Stopped API process" -ForegroundColor Red
    }
    
    if ($global:SuricataProcess -and -not $global:SuricataProcess.HasExited) {
        $global:SuricataProcess.Kill()
        Write-Host "Stopped Suricata process" -ForegroundColor Red
    }
    
    # Stop any remaining processes by name
    Get-Process -Name "zeek" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "suricata" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Stop Python processes that might be our components
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
    foreach ($proc in $pythonProcesses) {
        if ($proc.MainWindowTitle -match "yara|scanner|api") {
            $proc.Kill()
        }
    }
    
    Write-Host "All platform components stopped" -ForegroundColor Green
}

# Function to clean up temporary files
function Invoke-Cleanup {
    Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
    
    # Clean extracted files
    if (Test-Path "extracted_files") {
        Get-ChildItem "extracted_files" -File | Remove-Item -Force
        Write-Host "Cleaned extracted files" -ForegroundColor Gray
    }
    
    # Clean temporary Zeek files
    Get-ChildItem -Path "." -Filter "*.log" | Where-Object { $_.Name -match "zeek|conn|dns|http" } | Remove-Item -Force
    
    # Clean Python cache
    Get-ChildItem -Path "." -Recurse -Name "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path "." -Recurse -Name "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    
    Write-Host "Cleanup completed" -ForegroundColor Green
}

# Function to validate network interface
function Test-NetworkInterface {
    param([string]$InterfaceName)
    
    try {
        $adapter = Get-NetAdapter -Name $InterfaceName -ErrorAction Stop
        if ($adapter.Status -eq "Up") {
            return $true
        } else {
            Write-Warning "Interface '$InterfaceName' is not up (Status: $($adapter.Status))"
            return $false
        }
    } catch {
        Write-Warning "Interface '$InterfaceName' not found."
        Write-Host "Available interfaces:" -ForegroundColor Cyan
        Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object Name, InterfaceDescription | Format-Table -AutoSize
        return $false
    }
}

# Handle special operations
if ($Status) {
    Get-PlatformStatus
    exit 0
}

if ($Stop) {
    Stop-PlatformComponents
    exit 0
}

if ($Cleanup) {
    Stop-PlatformComponents
    Invoke-Cleanup
    exit 0
}

# Main platform startup
Write-Host "=== Zeek-YARA Integration Platform Launcher ===" -ForegroundColor Green
Write-Host "Windows PowerShell Version" -ForegroundColor Cyan

# Check prerequisites
if (-not (Test-Administrator) -and -not $Read) {
    Write-Warning "Administrator privileges recommended for live network monitoring."
    Write-Host "Consider running as Administrator or use -Read for PCAP analysis." -ForegroundColor Yellow
}

# Activate virtual environment
if (-not (Test-VirtualEnvironment)) {
    if (-not (Activate-VirtualEnvironment)) {
        exit 1
    }
}

# Validate network interface for live monitoring
if (-not $Read -and -not (Test-NetworkInterface $Interface)) {
    Write-Error "Invalid network interface: $Interface"
    exit 1
}

# Check port availability
if (-not (Test-Port $Port)) {
    Write-Warning "Port $Port is already in use. API server may fail to start."
}

# Create required directories
$directories = @("extracted_files", "logs", "logs\suricata")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Setup signal handler for graceful shutdown
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-PlatformComponents
}

Write-Host ""
Write-Host "Starting platform components..." -ForegroundColor Green

# Start YARA Scanner
if (-not $NoScanner) {
    Write-Host "Starting YARA file scanner..." -ForegroundColor Cyan
    try {
        $global:ScannerProcess = Start-Process -FilePath "python" -ArgumentList "bin\run_scanner.py" -NoNewWindow -PassThru
        Write-Host "✓ YARA scanner started (PID: $($global:ScannerProcess.Id))" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to start YARA scanner: $_"
    }
}

# Start API Server
if (-not $NoApi) {
    Write-Host "Starting API server..." -ForegroundColor Cyan
    try {
        $global:ApiProcess = Start-Process -FilePath "python" -ArgumentList "bin\run_api.py", "--host", $Host, "--port", $Port -NoNewWindow -PassThru
        Start-Sleep -Seconds 2  # Give API time to start
        Write-Host "✓ API server started (PID: $($global:ApiProcess.Id))" -ForegroundColor Green
        Write-Host "  URL: http://localhost:$Port" -ForegroundColor Yellow
    } catch {
        Write-Warning "Failed to start API server: $_"
    }
}

# Start Suricata
if (-not $NoSuricata -and (Test-Command "suricata")) {
    Write-Host "Starting Suricata..." -ForegroundColor Cyan
    try {
        if ($Read) {
            $global:SuricataProcess = Start-Process -FilePath "python" -ArgumentList "bin\suricata_cli.py", "--pcap", $Read -NoNewWindow -PassThru
            Write-Host "✓ Suricata started with PCAP: $Read" -ForegroundColor Green
        } else {
            $global:SuricataProcess = Start-Process -FilePath "python" -ArgumentList "bin\suricata_cli.py", "--interface", $Interface -NoNewWindow -PassThru
            Write-Host "✓ Suricata started on interface: $Interface" -ForegroundColor Green
        }
    } catch {
        Write-Warning "Failed to start Suricata: $_"
    }
} elseif (-not $NoSuricata) {
    Write-Warning "Suricata not found. Install from https://suricata.io/download/"
}

# Start Zeek
if (-not $NoZeek -and (Test-Command "zeek")) {
    Write-Host "Starting Zeek file extraction..." -ForegroundColor Cyan
    try {
        if ($Read) {
            $global:ZeekProcess = Start-Process -FilePath "zeek" -ArgumentList "-r", $Read, "zeek\extract_files.zeek" -NoNewWindow -PassThru
            Write-Host "✓ Zeek started with PCAP: $Read" -ForegroundColor Green
        } else {
            $global:ZeekProcess = Start-Process -FilePath "zeek" -ArgumentList "-i", $Interface, "zeek\extract_files.zeek" -NoNewWindow -PassThru
            Write-Host "✓ Zeek started on interface: $Interface" -ForegroundColor Green
        }
    } catch {
        Write-Warning "Failed to start Zeek: $_"
    }
} elseif (-not $NoZeek) {
    Write-Warning "Zeek not found. Install from https://zeek.org/get-zeek/"
}

# Display platform status
Write-Host ""
Write-Host "=== Platform Status ===" -ForegroundColor Green

if (-not $Read) {
    Write-Host "Network Interface: $Interface" -ForegroundColor White
} else {
    Write-Host "PCAP File: $Read" -ForegroundColor White
}

Write-Host "Extracted Files: extracted_files\" -ForegroundColor White
Write-Host "Logs Directory: logs\" -ForegroundColor White

if (-not $NoApi) {
    Write-Host "API Endpoints:" -ForegroundColor White
    Write-Host "  Status: http://localhost:$Port/status" -ForegroundColor Gray
    Write-Host "  Alerts: http://localhost:$Port/alerts" -ForegroundColor Gray
    Write-Host "  Docs: http://localhost:$Port/docs" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Platform is running. Monitor logs:" -ForegroundColor Yellow
Write-Host "  YARA Scanner: logs\yara_scan.log" -ForegroundColor Gray
Write-Host "  API Server: logs\api.log" -ForegroundColor Gray
Write-Host "  Suricata: logs\suricata\eve.json" -ForegroundColor Gray

Write-Host ""
Write-Host "Press Ctrl+C to stop all components or run with -Stop to stop manually." -ForegroundColor Cyan

# Wait for user input or process completion
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if any critical processes have exited
        if ($global:ApiProcess -and $global:ApiProcess.HasExited) {
            Write-Warning "API server process has exited"
            break
        }
        
        if ($global:ZeekProcess -and $global:ZeekProcess.HasExited -and $Read) {
            Write-Host "PCAP analysis completed" -ForegroundColor Green
            break
        }
    }
} catch [System.Management.Automation.PipelineStoppedException] {
    Write-Host "Received stop signal..." -ForegroundColor Yellow
} finally {
    Stop-PlatformComponents
    Write-Host "Platform shutdown complete" -ForegroundColor Green
}