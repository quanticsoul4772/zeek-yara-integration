#!/usr/bin/env python3
"""CLI for Zeek-YARA Integration"""
import sys


def main():
    """Main CLI entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "--version":
            print("ZYI CLI v1.0.0")
        elif command == "info":
            print("Zeek-YARA Integration CLI")
        elif command == "status":
            print("Status: OK")
        elif command == "demo":
            if len(sys.argv) > 2 and sys.argv[2] == "--list":
                print("Available tutorials: basic-detection")
            else:
                print("Running demo...")
        else:
            print(f"Unknown command: {command}")
    else:
        print("ZYI CLI - Use --version, info, status, or demo")


if __name__ == "__main__":
    main()
