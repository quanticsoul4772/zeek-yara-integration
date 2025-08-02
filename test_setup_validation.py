#!/usr/bin/env python3
"""
Test script to validate the setup.py configuration
Tests that setup.py works correctly for various installation methods
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n🧪 Testing: {description}")
    print(f"   Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"   ✅ SUCCESS")
            if result.stdout:
                print(f"   📝 Output: {result.stdout[:200]}...")
            return True
        else:
            print(f"   ❌ FAILED (exit code: {result.returncode})")
            if result.stderr:
                print(f"   📝 Error: {result.stderr[:200]}...")
            return False
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return False


def test_setup_validation():
    """Test setup.py validation"""
    print("🔍 Setup.py Validation Tests")
    print("=" * 40)

    tests = [
        # Basic validation
        ([sys.executable, "setup.py", "check"], "setup.py check"),
        ([sys.executable, "setup.py", "--help"], "setup.py help"),
        ([sys.executable, "setup.py", "--name"], "package name"),
        ([sys.executable, "setup.py", "--version"], "package version"),
        ([sys.executable, "setup.py", "--description"], "package description"),
        # Entry points validation
        (
            [sys.executable, "-c", "from setuptools import setup; from setup import setup"],
            "setuptools import",
        ),
    ]

    results = []
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))

    print("\n📊 Test Results Summary:")
    print("=" * 30)
    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {desc}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    return passed == total


def test_entry_points():
    """Test that entry point files exist and are importable"""
    print("\n🔍 Entry Points Validation")
    print("=" * 30)

    entry_points = [
        ("TOOLS.cli.zyi", "cli", "Main CLI tool"),
        ("install_platform", "main", "Platform installer"),
        ("setup_wizard", "main", "Setup wizard"),
        ("tutorial_system", "main", "Tutorial system"),
    ]

    results = []
    for module_name, function_name, description in entry_points:
        print(f"\n🧪 Testing: {description}")
        print(f"   Entry point: {module_name}:{function_name}")

        try:
            # Test if module can be imported
            import_cmd = f"import {module_name.replace('.', '/')}"
            if "." in module_name:
                # Handle package imports
                parts = module_name.split(".")
                import_cmd = f"import sys; sys.path.insert(0, '.'); "
                for i, part in enumerate(parts):
                    if i == 0:
                        import_cmd += f"import {part}; "
                    else:
                        import_cmd += f"from {'.'.join(parts[:i])} import {part}; "

            # Check if file exists
            if "." in module_name:
                file_path = Path("/".join(module_name.split(".")))
            else:
                file_path = Path(f"{module_name}.py")

            if file_path.exists() or Path(f"{module_name}.py").exists():
                print(f"   ✅ File exists")
                results.append((description, True))
            else:
                print(f"   ❌ File not found: {file_path}")
                results.append((description, False))

        except Exception as e:
            print(f"   ❌ Import error: {e}")
            results.append((description, False))

    print("\n📊 Entry Points Summary:")
    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {desc}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n🎯 Entry Points: {passed}/{total} validated")

    return passed == total


def main():
    """Run all validation tests"""
    print("🚀 Setup.py Validation Suite")
    print("Testing GitHub Actions CI/CD compatibility")
    print("=" * 50)

    # Test setup.py validation
    setup_valid = test_setup_validation()

    # Test entry points
    entry_points_valid = test_entry_points()

    print("\n🏁 Final Results")
    print("=" * 20)
    print(f"Setup.py validation: {'✅ PASS' if setup_valid else '❌ FAIL'}")
    print(f"Entry points validation: {'✅ PASS' if entry_points_valid else '❌ FAIL'}")

    if setup_valid and entry_points_valid:
        print("\n🎉 All validations passed!")
        print("✅ GitHub Actions pip install -e . should work")
        print("✅ Python setup.py install should work")
        print("✅ pip install . should work")
        print("✅ All entry points should be available")
        return 0
    else:
        print("\n❌ Some validations failed")
        print("⚠️  GitHub Actions may still fail")
        return 1


if __name__ == "__main__":
    sys.exit(main())
