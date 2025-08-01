#!/usr/bin/env python3
"""
Tutorial Server Startup Script
Simplified script to start the interactive tutorial web server
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tutorial_web_server import TutorialWebServer
except ImportError:
    print("Error: Could not import tutorial_web_server. Please check your installation.")
    sys.exit(1)

def main():
    """Start the tutorial web server with proper configuration."""
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Configuration
    config = {
        'PROJECT_ROOT': project_root,
        'EXPERIENCE_LEVEL': 'beginner',
        'TUTORIAL_MODE': True,
        'WEB_INTERFACE': True,
        'EXTRACT_DIR': project_root / 'extracted_files',
        'LOG_DIR': project_root / 'logs',
        'RULES_DIR': project_root / 'rules',
    }
    
    print("🎓 Starting Security Learning Platform Tutorial Server")
    print(f"📁 Project Root: {project_root}")
    print(f"🌐 Web Interface: http://localhost:8001")
    print("📚 Features Available:")
    print("   • Interactive Network Security Fundamentals Tutorial")
    print("   • Hands-on EICAR Detection Exercise") 
    print("   • Real-time Progress Tracking")
    print("   • Achievement System")
    print("   • Visual Learning Aids")
    print("   • Knowledge Assessments")
    print()
    
    try:
        # Create server instance
        server = TutorialWebServer(config)
        
        # Ensure directories exist
        (project_root / "EDUCATION" / "templates").mkdir(parents=True, exist_ok=True)
        (project_root / "EDUCATION" / "static").mkdir(parents=True, exist_ok=True)
        
        print("🚀 Starting web server on http://localhost:8001")
        print("📖 Access the tutorial dashboard at: http://localhost:8001")
        print("🛑 Press Ctrl+C to stop the server")
        print()
        
        # Start the server
        server.run(host="127.0.0.1", port=8001)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Tutorial server stopped by user")
        print("Thank you for using the Security Learning Platform!")
        
    except ImportError as e:
        print(f"\n❌ Missing dependencies: {e}")
        print("Please install required packages:")
        print("pip install fastapi uvicorn jinja2")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("Please check the configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()