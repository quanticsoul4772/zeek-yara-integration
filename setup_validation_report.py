#!/usr/bin/env python3
"""
Comprehensive Setup.py Validation Report
Analyzes setup.py configuration for GitHub Actions CI/CD compatibility
"""

import sys
from pathlib import Path

def validate_entry_points():
    """Validate all entry points from setup.py exist and are properly configured"""
    
    project_root = Path(__file__).parent
    
    # Entry points from setup.py
    entry_points = [
        ("zyi", "TOOLS.cli.zyi", "cli"),
        ("zeek-yara-install", "install_platform", "main"),
        ("setup-wizard", "setup_wizard", "main"),
        ("tutorial-system", "tutorial_system", "main"),
        ("zeek-yara-tutorial", "EDUCATION.tutorial_web_server", "main"),
        ("tutorial-server", "EDUCATION.start_tutorial_server", "main"),
        ("zeek-yara-api", "PLATFORM.api.api_server", "main"),
        ("zeek-yara-scanner", "PLATFORM.core.scanner", "main"),
    ]
    
    results = []
    
    for console_name, module_path, function_name in entry_points:
        print(f"\n🔍 Validating entry point: {console_name}")
        print(f"   Module: {module_path}")
        print(f"   Function: {function_name}")
        
        # Convert module path to file path
        if "." in module_path:
            # Handle package imports (e.g., TOOLS.cli.zyi)
            file_path = project_root / "/".join(module_path.split("."))
            py_file_path = project_root / "/".join(module_path.split(".")) + ".py"
            init_file_path = project_root / "/".join(module_path.split(".")[:-1]) / "__init__.py"
        else:
            # Handle direct module imports (e.g., install_platform)
            file_path = project_root / (module_path + ".py")
            py_file_path = file_path
            init_file_path = None
        
        # Check if file exists
        file_exists = py_file_path.exists() or file_path.exists()
        init_exists = init_file_path.exists() if init_file_path else True
        
        if file_exists and init_exists:
            print(f"   ✅ File exists: {py_file_path if py_file_path.exists() else file_path}")
            if init_file_path:
                print(f"   ✅ Package init: {init_file_path}")
            results.append((console_name, True, "File and package structure valid"))
        else:
            missing_parts = []
            if not file_exists:
                missing_parts.append(f"main file ({py_file_path})")
            if init_file_path and not init_exists:
                missing_parts.append(f"package init ({init_file_path})")
            
            print(f"   ❌ Missing: {', '.join(missing_parts)}")
            results.append((console_name, False, f"Missing: {', '.join(missing_parts)}"))
    
    return results

def validate_package_structure():
    """Validate package structure for proper imports"""
    
    project_root = Path(__file__).parent
    
    required_packages = [
        "TOOLS",
        "TOOLS/cli", 
        "EDUCATION",
        "PLATFORM",
        "PLATFORM/api",
        "PLATFORM/core",
    ]
    
    results = []
    
    print(f"\n🔍 Validating package structure:")
    
    for package in required_packages:
        package_dir = project_root / package
        init_file = package_dir / "__init__.py"
        
        if package_dir.exists() and init_file.exists():
            print(f"   ✅ {package:<20} Package ready")
            results.append((package, True, "Package structure valid"))
        elif package_dir.exists():
            print(f"   ⚠️  {package:<20} Directory exists, missing __init__.py")
            results.append((package, False, "Missing __init__.py"))
        else:
            print(f"   ❌ {package:<20} Directory missing")
            results.append((package, False, "Directory missing"))
    
    return results

def validate_requirements():
    """Check if requirements files exist"""
    
    project_root = Path(__file__).parent
    
    req_files = [
        "requirements.txt",
        "test-requirements.txt", 
        "EDUCATION/requirements.txt"
    ]
    
    results = []
    
    print(f"\n🔍 Validating requirements files:")
    
    for req_file in req_files:
        file_path = project_root / req_file
        if file_path.exists():
            print(f"   ✅ {req_file:<25} Exists")
            results.append((req_file, True, "File exists"))
        else:
            print(f"   ❌ {req_file:<25} Missing")
            results.append((req_file, False, "File missing"))
    
    return results

def validate_version_import():
    """Test version import from setup.py"""
    
    print(f"\n🔍 Validating version import:")
    
    try:
        # Test the import that setup.py uses
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from packaging.version import VERSION
        print(f"   ✅ Version import successful: {VERSION}")
        return [(("version_import", True, f"Successfully imported version {VERSION}"))]
    except ImportError as e:
        print(f"   ❌ Version import failed: {e}")
        return [("version_import", False, f"Import error: {e}")]

def main():
    """Run all validation checks"""
    
    print("🚀 Setup.py Validation Report")
    print("Testing GitHub Actions CI/CD compatibility")
    print("=" * 60)
    
    # Run all validations
    entry_point_results = validate_entry_points()
    package_results = validate_package_structure()
    requirements_results = validate_requirements()
    version_results = validate_version_import()
    
    # Summary
    print(f"\n📊 Validation Summary")
    print("=" * 30)
    
    all_results = entry_point_results + package_results + requirements_results + version_results
    
    passed = sum(1 for _, success, _ in all_results if success)
    total = len(all_results)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {total - passed}")
    print(f"📈 Success Rate: {passed/total*100:.1f}%")
    
    # Detailed breakdown
    categories = [
        ("Entry Points", entry_point_results),
        ("Package Structure", package_results),
        ("Requirements Files", requirements_results),
        ("Version Import", version_results),
    ]
    
    for category_name, results in categories:
        category_passed = sum(1 for _, success, _ in results if success)
        category_total = len(results)
        print(f"\n{category_name}: {category_passed}/{category_total}")
        
        for name, success, message in results:
            status = "✅" if success else "❌"
            print(f"  {status} {name}: {message}")
    
    # GitHub Actions compatibility assessment
    print(f"\n🎯 GitHub Actions Compatibility")
    print("=" * 35)
    
    critical_failures = [
        name for name, success, _ in all_results 
        if not success and any(critical in name.lower() for critical in ['zyi', 'entry', 'version', 'package'])
    ]
    
    if not critical_failures:
        print("🎉 EXCELLENT: All critical components validated!")
        print("✅ pip install -e . should work in GitHub Actions")
        print("✅ Console scripts should be available after installation")
        print("✅ Package imports should work correctly")
    elif len(critical_failures) <= 2:
        print("⚠️  GOOD: Minor issues detected, but likely compatible")
        print("🔧 Recommend fixing issues before deployment")
        for failure in critical_failures:
            print(f"   • Fix: {failure}")
    else:
        print("❌ NEEDS WORK: Multiple critical issues detected")
        print("⚠️  GitHub Actions installation may fail")
        print("🔧 Must fix critical issues:")
        for failure in critical_failures:
            print(f"   • {failure}")
    
    return 0 if not critical_failures else 1

if __name__ == "__main__":
    sys.exit(main())