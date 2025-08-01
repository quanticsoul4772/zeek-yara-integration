#!/bin/bash

# Comprehensive Implementation Validation Script
# Tests all aspects of the reorganized ZYI platform

set -e

echo "🔍 ZYI Platform Implementation Validation"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo -e "${BLUE}[TEST $((++TESTS_RUN))]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️  INFO:${NC} $1"
}

# Test functions
test_directory_structure() {
    print_test "Validating directory structure"
    
    local required_dirs=(
        "EDUCATION"
        "PLATFORM"
        "TESTING"
        "DEPLOYMENT"
        "TOOLS"
        "CONFIGURATION"
        "RULES"
        "DATA"
        "DOCUMENTATION"
        "COMMUNITY"
        "INFRASTRUCTURE"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Directory exists: $dir"
        else
            print_failure "Missing directory: $dir"
        fi
    done
}

test_educational_content() {
    print_test "Validating educational content structure"
    
    local educational_dirs=(
        "EDUCATION/getting-started"
        "EDUCATION/tutorials"
        "EDUCATION/examples"
        "EDUCATION/explanations"
        "EDUCATION/certification"
        "EDUCATION/community"
    )
    
    for dir in "${educational_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Educational directory exists: $dir"
        else
            print_failure "Missing educational directory: $dir"
        fi
    done
    
    # Test for key educational files
    if [ -f "EDUCATION/README.md" ]; then
        print_success "Educational README exists"
    else
        print_failure "Missing EDUCATION/README.md"
    fi
    
    if [ -f "EDUCATION/getting-started/first-detection/README.md" ]; then
        print_success "First detection tutorial exists"
    else
        print_failure "Missing first detection tutorial"
    fi
}

test_platform_structure() {
    print_test "Validating platform code structure"
    
    local platform_dirs=(
        "PLATFORM/core"
        "PLATFORM/api"
        "PLATFORM/integrations"
        "PLATFORM/utils"
        "PLATFORM/plugins"
    )
    
    for dir in "${platform_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Platform directory exists: $dir"
        else
            print_failure "Missing platform directory: $dir"
        fi
    done
    
    # Check for plugin system
    if [ -f "PLATFORM/plugins/__init__.py" ]; then
        print_success "Plugin system initialized"
    else
        print_failure "Missing plugin system"
    fi
    
    if [ -f "PLATFORM/plugins/base.py" ]; then
        print_success "Plugin base classes exist"
    else
        print_failure "Missing plugin base classes"
    fi
}

test_cli_tool() {
    print_test "Validating CLI tool"
    
    if [ -f "TOOLS/cli/zyi" ]; then
        if [ -x "TOOLS/cli/zyi" ]; then
            print_success "CLI tool exists and is executable"
            
            # Test basic CLI functionality
            if ./TOOLS/cli/zyi --help > /dev/null 2>&1; then
                print_success "CLI tool help command works"
            else
                print_failure "CLI tool help command failed"
            fi
            
            if ./TOOLS/cli/zyi info > /dev/null 2>&1; then
                print_success "CLI info command works"
            else
                print_failure "CLI info command failed"
            fi
            
            if ./TOOLS/cli/zyi status > /dev/null 2>&1; then
                print_success "CLI status command works"
            else
                print_failure "CLI status command failed"
            fi
            
        else
            print_failure "CLI tool exists but is not executable"
        fi
    else
        print_failure "CLI tool missing: TOOLS/cli/zyi"
    fi
}

test_github_templates() {
    print_test "Validating GitHub templates and workflows"
    
    if [ -d ".github" ]; then
        print_success "GitHub directory exists"
        
        if [ -f ".github/ISSUE_TEMPLATE/bug_report.yml" ]; then
            print_success "Bug report template exists"
        else
            print_failure "Missing bug report template"
        fi
        
        if [ -f ".github/ISSUE_TEMPLATE/feature_request.yml" ]; then
            print_success "Feature request template exists"
        else
            print_failure "Missing feature request template"
        fi
        
        if [ -f ".github/workflows/ci.yml" ]; then
            print_success "CI workflow exists"
        else
            print_failure "Missing CI workflow"
        fi
        
    else
        print_failure "Missing .github directory"
    fi
}

test_deployment_configs() {
    print_test "Validating deployment configurations"
    
    if [ -f "DEPLOYMENT/docker/Dockerfile" ]; then
        print_success "Dockerfile exists"
    else
        print_failure "Missing Dockerfile"
    fi
    
    if [ -f "DEPLOYMENT/docker/docker-compose.yml" ]; then
        print_success "Docker Compose file exists"
    else
        print_failure "Missing Docker Compose file"
    fi
    
    # Test Dockerfile syntax
    if command -v docker > /dev/null 2>&1; then
        if docker build -f DEPLOYMENT/docker/Dockerfile --target education -t zyi:test . > /dev/null 2>&1; then
            print_success "Dockerfile builds successfully"
        else
            print_warning "Dockerfile build failed (dependencies may be missing)"
        fi
    else
        print_info "Docker not available, skipping build test"
    fi
}

test_configuration_structure() {
    print_test "Validating configuration structure"
    
    local config_dirs=(
        "CONFIGURATION/defaults"
        "CONFIGURATION/templates"
        "CONFIGURATION/schemas"
        "CONFIGURATION/examples"
    )
    
    for dir in "${config_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Configuration directory exists: $dir"
        else
            print_failure "Missing configuration directory: $dir"
        fi
    done
}

test_data_structure() {
    print_test "Validating data structure"
    
    local data_dirs=(
        "DATA/runtime"
        "DATA/persistent"
        "DATA/samples"
        "DATA/schemas"
    )
    
    for dir in "${data_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Data directory exists: $dir"
        else
            print_failure "Missing data directory: $dir"
        fi
    done
}

test_documentation_files() {
    print_test "Validating key documentation files"
    
    local required_docs=(
        "README.md"
        "PROJECT_PLAN.md"
        "PROJECT_STRUCTURE.md"
        "MIGRATION_STRATEGY.md"
        "AGILE_WORKFLOW.md"
        "CONTRIBUTING.md"
        "LICENSE"
    )
    
    for doc in "${required_docs[@]}"; do
        if [ -f "$doc" ]; then
            print_success "Documentation file exists: $doc"
        else
            print_failure "Missing documentation file: $doc"
        fi
    done
}

test_python_imports() {
    print_test "Testing Python import structure"
    
    # Test if Python can import from new structure
    export PYTHONPATH="$PWD/PLATFORM:$PYTHONPATH"
    
    if python3 -c "import sys; sys.path.insert(0, 'PLATFORM'); import plugins" 2>/dev/null; then
        print_success "Plugin system imports successfully"
    else
        print_failure "Plugin system import failed"
    fi
    
    # Test CLI tool Python execution
    if python3 -c "
import sys, os
sys.path.insert(0, 'PLATFORM')
cli_path = os.path.join(os.getcwd(), 'TOOLS', 'cli', 'zyi')
with open(cli_path, 'r') as f:
    content = f.read()
    if 'import click' in content and 'PROJECT_ROOT' in content:
        print('CLI imports look correct')
    else:
        exit(1)
" 2>/dev/null; then
        print_success "CLI tool Python structure is correct"
    else
        print_failure "CLI tool Python structure has issues"
    fi
}

test_demo_functionality() {
    print_test "Testing demo functionality"
    
    # Test EICAR demo
    if ./TOOLS/cli/zyi demo run --tutorial basic-detection > /dev/null 2>&1; then
        print_success "Basic detection demo runs successfully"
    else
        print_failure "Basic detection demo failed"
    fi
    
    # Test demo listing
    if ./TOOLS/cli/zyi demo run --list > /dev/null 2>&1; then
        print_success "Demo listing works"
    else
        print_failure "Demo listing failed"
    fi
}

test_file_permissions() {
    print_test "Validating file permissions"
    
    # Check that scripts are executable
    local scripts=(
        "TOOLS/cli/zyi"
        "TOOLS/scripts/testing/validate-implementation.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                print_success "Script is executable: $script"
            else
                print_failure "Script is not executable: $script"
            fi
        fi
    done
}

# Main validation execution
main() {
    echo "Starting comprehensive validation..."
    echo
    
    # Run all tests
    test_directory_structure
    echo
    
    test_educational_content
    echo
    
    test_platform_structure
    echo
    
    test_cli_tool
    echo
    
    test_github_templates
    echo
    
    test_deployment_configs
    echo
    
    test_configuration_structure
    echo
    
    test_data_structure
    echo
    
    test_documentation_files
    echo
    
    test_python_imports
    echo
    
    test_demo_functionality
    echo
    
    test_file_permissions
    echo
    
    # Summary
    echo "========================================="
    echo "🏁 VALIDATION SUMMARY"
    echo "========================================="
    echo "Total tests run: $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo
        echo -e "${GREEN}🎉 ALL VALIDATIONS PASSED!${NC}"
        echo "The ZYI platform reorganization is complete and ready for Phase 1."
        exit 0
    else
        echo
        echo -e "${RED}❌ VALIDATION FAILURES DETECTED${NC}"
        echo "Please address the failed tests before proceeding to Phase 1."
        exit 1
    fi
}

# Ensure we're in the project root
if [ ! -f "PROJECT_PLAN.md" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Run main validation
main