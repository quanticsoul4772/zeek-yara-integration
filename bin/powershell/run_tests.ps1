# Windows PowerShell equivalent of bin/run_tests.sh
# Comprehensive test runner for Zeek-YARA Integration Platform

param(
    [switch]$All,
    [switch]$Unit,
    [switch]$Integration,
    [switch]$Performance,
    [switch]$Suricata,
    [switch]$Coverage,
    [switch]$Verbose,
    [switch]$Help,
    [string]$TestPath = "",
    [int]$Jobs = 1
)

if ($Help) {
    Write-Host @"
Zeek-YARA Integration Test Runner (Windows PowerShell)

USAGE:
    .\run_tests.ps1 [OPTIONS]

OPTIONS:
    -All            Run all test categories
    -Unit           Run unit tests only
    -Integration    Run integration tests only
    -Performance    Run performance tests only
    -Suricata       Run Suricata-specific tests only
    -Coverage       Generate coverage report (HTML + XML)
    -Verbose        Verbose test output
    -TestPath       Run specific test file or directory
    -Jobs           Number of parallel test jobs (default: 1)
    -Help           Show this help message

EXAMPLES:
    .\run_tests.ps1 -All                    # Run all tests
    .\run_tests.ps1 -Unit -Coverage         # Unit tests with coverage
    .\run_tests.ps1 -Integration -Verbose   # Integration tests with verbose output
    .\run_tests.ps1 -TestPath tests\unit\test_scanner.py  # Run specific test file

MARKERS:
    unit            Fast, isolated component tests
    integration     Cross-component functionality tests
    performance     Load and timing tests
    suricata        Network integration tests

"@
    exit 0
}

$ErrorActionPreference = "Stop"

Write-Host "=== Zeek-YARA Integration Test Runner ===" -ForegroundColor Green
Write-Host "Windows PowerShell Test Execution" -ForegroundColor Cyan

# Function to check if virtual environment is active
function Test-VirtualEnvironment {
    return $env:VIRTUAL_ENV -ne $null
}

# Function to activate virtual environment
function Activate-VirtualEnvironment {
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Cyan
        & "venv\Scripts\Activate.ps1"
        return $true
    } else {
        Write-Warning "Virtual environment not found. Run setup.ps1 first."
        return $false
    }
}

# Function to check pytest installation
function Test-PytestInstalled {
    try {
        python -m pytest --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Activate virtual environment if not already active
if (-not (Test-VirtualEnvironment)) {
    if (-not (Activate-VirtualEnvironment)) {
        exit 1
    }
}

# Check pytest installation
Write-Host "Checking test dependencies..." -ForegroundColor Cyan
if (-not (Test-PytestInstalled)) {
    Write-Host "Installing pytest..." -ForegroundColor Yellow
    pip install pytest pytest-cov pytest-html pytest-xvfb
}

# Ensure TESTING directory exists
if (-not (Test-Path "TESTING")) {
    New-Item -ItemType Directory -Path "TESTING" -Force | Out-Null
    Write-Host "Created TESTING directory" -ForegroundColor Green
}

# Build pytest command arguments
$pytestArgs = @()

# Test path selection
if ($TestPath) {
    $pytestArgs += $TestPath
} else {
    $pytestArgs += "tests/"
}

# Test category markers
if ($Unit) {
    $pytestArgs += @("-m", "unit")
    Write-Host "Running unit tests..." -ForegroundColor Cyan
} elseif ($Integration) {
    $pytestArgs += @("-m", "integration")  
    Write-Host "Running integration tests..." -ForegroundColor Cyan
} elseif ($Performance) {
    $pytestArgs += @("-m", "performance")
    Write-Host "Running performance tests..." -ForegroundColor Cyan
} elseif ($Suricata) {
    $pytestArgs += @("-m", "suricata")
    Write-Host "Running Suricata-specific tests..." -ForegroundColor Cyan
} elseif ($All) {
    Write-Host "Running all test categories..." -ForegroundColor Cyan
} else {
    # Default to unit tests if no category specified
    $pytestArgs += @("-m", "unit")
    Write-Host "Running unit tests (default)..." -ForegroundColor Cyan
}

# Coverage options
if ($Coverage) {
    $pytestArgs += @(
        "--cov=core",
        "--cov=utils", 
        "--cov=PLATFORM",
        "--cov=api",
        "--cov=suricata",
        "--cov-report=html:TESTING/coverage_html",
        "--cov-report=xml:TESTING/coverage.xml",
        "--cov-report=term-missing"
    )
    Write-Host "Coverage reporting enabled" -ForegroundColor Yellow
}

# Verbose output
if ($Verbose) {
    $pytestArgs += @("-v", "-s")
}

# Parallel execution
if ($Jobs -gt 1) {
    $pytestArgs += @("-n", $Jobs.ToString())
    Write-Host "Running tests with $Jobs parallel jobs" -ForegroundColor Yellow
}

# Additional pytest options
$pytestArgs += @(
    "--tb=short",
    "--strict-markers",
    "--junit-xml=TESTING/test-results.xml",
    "--html=TESTING/test-report.html",
    "--self-contained-html"
)

# Set test environment variables
$env:PYTEST_CURRENT_TEST = "true"
$env:ZYI_TEST_MODE = "true"
$env:ZYI_LOG_LEVEL = "DEBUG"

# Display test configuration
Write-Host ""
Write-Host "Test Configuration:" -ForegroundColor White
Write-Host "==================" -ForegroundColor White
Write-Host "Python: $(python --version)" -ForegroundColor Gray
Write-Host "Pytest: $(python -m pytest --version)" -ForegroundColor Gray
Write-Host "Working Directory: $(Get-Location)" -ForegroundColor Gray
Write-Host "Test Arguments: $($pytestArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

# Run tests
Write-Host "Executing tests..." -ForegroundColor Green
$testStartTime = Get-Date

try {
    python -m pytest @pytestArgs
    $testExitCode = $LASTEXITCODE
} catch {
    Write-Error "Test execution failed: $_"
    $testExitCode = 1
}

$testEndTime = Get-Date
$testDuration = $testEndTime - $testStartTime

# Test results summary
Write-Host ""
Write-Host "=== Test Results Summary ===" -ForegroundColor Green
Write-Host "Test Duration: $([math]::Round($testDuration.TotalSeconds, 2)) seconds" -ForegroundColor White

if ($testExitCode -eq 0) {
    Write-Host "Status: PASSED" -ForegroundColor Green
} else {
    Write-Host "Status: FAILED" -ForegroundColor Red
}

# Display output locations
Write-Host ""
Write-Host "Output Locations:" -ForegroundColor White
Write-Host "=================" -ForegroundColor White

if (Test-Path "TESTING/test-results.xml") {
    Write-Host "JUnit XML: TESTING/test-results.xml" -ForegroundColor Gray
}

if (Test-Path "TESTING/test-report.html") {
    Write-Host "HTML Report: TESTING/test-report.html" -ForegroundColor Gray
}

if ($Coverage) {
    if (Test-Path "TESTING/coverage_html/index.html") {
        Write-Host "Coverage HTML: TESTING/coverage_html/index.html" -ForegroundColor Gray
    }
    if (Test-Path "TESTING/coverage.xml") {
        Write-Host "Coverage XML: TESTING/coverage.xml" -ForegroundColor Gray
    }
}

# Performance metrics (if available)
if (Test-Path "TESTING/performance_results.json") {
    Write-Host "Performance Results: TESTING/performance_results.json" -ForegroundColor Gray
}

# Test result analysis
if ($testExitCode -eq 0) {
    Write-Host ""
    Write-Host "All tests completed successfully!" -ForegroundColor Green
    
    if ($Coverage) {
        Write-Host "Open TESTING/coverage_html/index.html to view detailed coverage report" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Some tests failed. Check the output above for details." -ForegroundColor Red
    Write-Host "Review TESTING/test-report.html for detailed test results" -ForegroundColor Yellow
}

# Cleanup environment variables
Remove-Item Env:PYTEST_CURRENT_TEST -ErrorAction SilentlyContinue
Remove-Item Env:ZYI_TEST_MODE -ErrorAction SilentlyContinue
Remove-Item Env:ZYI_LOG_LEVEL -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Test runner completed." -ForegroundColor Cyan

exit $testExitCode