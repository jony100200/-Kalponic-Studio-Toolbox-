#!/usr/bin/env python3
"""
Universal Model Launcher - Phase 2 Server Startup
"""

import uvicorn
import sys
import os

# Add the Version4 directory to Python path
sys.path.append(os.path.abspath('.'))

from api.unified_server import UnifiedServer

def main():
    """Start the Universal Model Launcher API server"""
    print("🚀 Starting Universal Model Launcher API Server...")
    print("📡 Phase 2: API & Communication Layer")
    print("=" * 50)
    
    # Create server instance
    server = UnifiedServer(host="127.0.0.1", port=8000)
    
    print(f"🌐 Server starting on http://127.0.0.1:8000")
    print("📋 Available endpoints:")
    print("   • Native API: /load_model, /unload_model, /health")
    print("   • OpenAI API: /v1/chat/completions, /v1/completions")
    print("   • WebSocket: /ws")
    print("   • Docs: /docs")
    print("\n💡 Use Ctrl+C to stop the server")
    
    # Start server
    uvicorn.run(
        server.app,
        host=server.host,
        port=server.port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
