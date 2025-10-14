#!/usr/bin/env python3
"""
KS PDF Studio - API Server Startup Script
Launches the comprehensive REST API server for enterprise integrations.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import sys
import argparse
import signal
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'flask', 'flask-cors', 'requests', 'werkzeug',
        'reportlab', 'pillow', 'cryptography', 'sqlite3'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            elif package == 'reportlab':
                import reportlab
            elif package == 'pillow':
                import PIL
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install with: pip install -r requirements-api.txt")
        return False

    print("✅ All dependencies are installed")
    return True

def create_directories():
    """Create necessary directories for the API server."""
    directories = [
        "data/uploads",
        "data/outputs",
        "data/batch_outputs",
        "logs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def setup_environment():
    """Setup environment variables and configuration."""
    # Set default environment variables if not set
    env_vars = {
        'KS_API_SECRET_KEY': os.environ.get('KS_API_SECRET_KEY', os.urandom(32).hex()),
        'KS_WEBHOOK_SECRET': os.environ.get('KS_WEBHOOK_SECRET', os.urandom(32).hex()),
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'production'),
    }

    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"🔧 Set {key}")

    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write("# KS PDF Studio API Environment Variables\n")
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        print("📄 Created .env file with default configuration")

def start_api_server(host: str, port: int, debug: bool = False):
    """Start the API server."""
    try:
        from api_server import KSAPIServer

        print("🚀 Starting KS PDF Studio API Server...")
        print(f"📡 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"🐛 Debug mode: {debug}")
        print(f"🔑 API Key required for authentication")
        print()

        # Create and start server
        api_server = KSAPIServer(host=host, port=port, debug=debug)
        api_server.run()

    except ImportError as e:
        print(f"❌ Failed to import API server: {e}")
        print("Make sure all files are in the correct locations")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        sys.exit(1)

def start_webhook_server(host: str, port: int):
    """Start the webhook handler server."""
    try:
        from webhook_handler import create_webhook_app

        print("🚀 Starting KS PDF Studio Webhook Handler...")
        print(f"📡 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"🔐 Signature verification enabled")
        print()

        app = create_webhook_app()
        app.run(host=host, port=port, debug=False)

    except ImportError as e:
        print(f"❌ Failed to import webhook handler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start webhook server: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='KS PDF Studio API Server')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='Server port (default: 5000)')
    parser.add_argument('--webhook-port', type=int, default=5001, help='Webhook server port (default: 5001)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--setup-only', action='store_true', help='Only perform setup, do not start server')
    parser.add_argument('--webhook-only', action='store_true', help='Start only webhook server')
    parser.add_argument('--api-only', action='store_true', help='Start only API server')

    args = parser.parse_args()

    print("🎯 KS PDF Studio API Server Launcher")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup environment
    print("\n🔧 Setting up environment...")
    create_directories()
    setup_environment()

    if args.setup_only:
        print("\n✅ Setup completed successfully!")
        print("Run without --setup-only to start the server")
        return

    # Handle server startup
    if args.webhook_only:
        start_webhook_server(args.host, args.webhook_port)
    elif args.api_only:
        start_api_server(args.host, args.port, args.debug)
    else:
        # Start both servers (in production, these would typically run separately)
        print("\n📋 Starting both API and Webhook servers...")
        print("Note: In production, run these as separate processes/services")

        # For demo purposes, start API server
        # In production, you'd use a process manager like systemd or supervisor
        start_api_server(args.host, args.port, args.debug)

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\n\n🛑 Shutdown signal received")
    print("👋 Shutting down KS PDF Studio API Server...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Server shutdown requested by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)