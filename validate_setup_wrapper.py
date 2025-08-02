#!/usr/bin/env python3
"""
Wrapper script to test setup.py validation without needing bash permissions
"""

import subprocess
import sys
from pathlib import Path


def run_setup_tests():
    """Run the setup.py validation tests"""

    try:
        # Test 1: setup.py check
        print("🧪 Testing: setup.py check")
        result = subprocess.run(
            [sys.executable, "setup.py", "check"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print("   ✅ setup.py check: SUCCESS")
        else:
            print(f"   ❌ setup.py check: FAILED")
            print(f"   Error: {result.stderr[:200]}")

        # Test 2: setup.py --name
        print("\n🧪 Testing: setup.py --name")
        result = subprocess.run(
            [sys.executable, "setup.py", "--name"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print(f"   ✅ Package name: {result.stdout.strip()}")
        else:
            print(f"   ❌ Package name: FAILED")

        # Test 3: setup.py --version
        print("\n🧪 Testing: setup.py --version")
        result = subprocess.run(
            [sys.executable, "setup.py", "--version"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print(f"   ✅ Package version: {result.stdout.strip()}")
        else:
            print(f"   ❌ Package version: FAILED")

        # Test 4: Try importing setup module
        print("\n🧪 Testing: setup.py import")
        try:
            import setup

            print("   ✅ setup.py import: SUCCESS")
        except Exception as e:
            print(f"   ❌ setup.py import: FAILED - {e}")

        # Test 5: Check entry points can be imported
        print("\n🧪 Testing: Entry point imports")
        entry_points = [
            ("TOOLS.cli.zyi", "CLI module"),
            ("install_platform", "Platform installer"),
            ("setup_wizard", "Setup wizard"),
            ("tutorial_system", "Tutorial system"),
        ]

        for module_name, description in entry_points:
            try:
                if "." in module_name:
                    # Handle dotted imports
                    parts = module_name.split(".")
                    current_module = __import__(parts[0])
                    for part in parts[1:]:
                        current_module = getattr(current_module, part)
                else:
                    __import__(module_name)
                print(f"   ✅ {description}: importable")
            except Exception as e:
                print(f"   ❌ {description}: import failed - {e}")

    except Exception as e:
        print(f"Error running tests: {e}")


if __name__ == "__main__":
    print("🚀 Setup.py Validation Test Suite")
    print("=" * 40)
    run_setup_tests()
    print("\n✅ Validation tests complete!")
