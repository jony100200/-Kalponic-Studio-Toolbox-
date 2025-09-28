#!/usr/bin/env python3
"""
🚀 Universal Model Launcher - Main Entry Point
========================================================================================
Purpose: Complete application orchestrator following SOLID & KISS principles
Pattern: Football Team Approach - Each component has single responsibility
========================================================================================
"""

import sys
import os
import signal
import time
import logging
import argparse
import traceback
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager

# Add Version4 to Python path for clean imports
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Core system components
from Core.system_manager import SystemManager
from Core.system_config import SystemConfig
from Core.hybrid_smart_loader import HybridSmartLoader
from loader.universal_loader import UniversalLoader
from loader.health_monitor import HealthMonitor
from loader.process_manager import ProcessManager

# API components (Phase 2)
from api.unified_server import UnifiedServer
from api.security_middleware import SecurityMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class UniversalModelLauncher:
    """
    🎯 Main Application Orchestrator
    ================================
    Role: Team Captain - Coordinates all components
    SOLID: Single responsibility for application lifecycle management
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Component initialization tracking
        self._components: Dict[str, Any] = {}
        self._initialized = False
        self._running = False
        
        # Signal handling
        self._setup_signal_handlers()
        
        logger.info("🚀 Universal Model Launcher initializing...")
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown on system signals"""
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, 'SIGBREAK'):  # Windows
            signal.signal(signal.SIGBREAK, signal_handler)
    
    async def initialize(self, enable_api: bool = True) -> bool:
        """
        🏗️ Initialize all system components in correct order
        ===================================================
        Order matters: Core → Loader → Health → Process → API
        """
        try:
            logger.info("📋 Starting component initialization...")
            
            # Phase 1: Core System Components
            logger.info("🔧 Initializing core components...")
            self._components['system_manager'] = SystemManager(str(self.config_dir))
            self._components['hybrid_smart_loader'] = HybridSmartLoader()
            self._components['universal_loader'] = UniversalLoader()
            self._components['health_monitor'] = HealthMonitor()
            self._components['process_manager'] = ProcessManager()
            
            # Validate core components
            if not self._components['system_manager'].is_ready:
                raise RuntimeError("❌ System Manager failed to initialize")
            
            logger.info("✅ Core components initialized successfully")
            
            # Phase 2: API Components (if enabled)
            if enable_api:
                logger.info("🌐 Initializing API components...")
                self._components['security'] = SecurityMiddleware()
                self._components['api_server'] = UnifiedServer()
                logger.info("✅ API components initialized successfully")
            
            # System health check
            await self._perform_health_check()
            
            self._initialized = True
            logger.info("🎉 All components initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _perform_health_check(self):
        """🏥 Comprehensive system health check"""
        logger.info("🏥 Performing system health check...")
        
        # Check system resources
        system_status = self._components['system_manager'].get_system_status()
        memory_info = system_status.get('memory_limits', {})
        total_memory = memory_info.get('total_gb', 'Unknown')
        logger.info(f"💾 Memory: {total_memory}GB")
        logger.info(f"🖥️  GPUs: {len(system_status.get('gpus', []))}")
        
        # Check health monitor
        health_status = self._components['health_monitor'].get_current_status()
        if not health_status.get('overall_status') == 'HEALTHY':
            logger.warning("⚠️  System health issues detected")
        
        # Check port availability
        port_status = self._components['system_manager'].ports.get_all_allocations()
        logger.info(f"🔌 Allocated ports: {len(port_status)}")
        
        logger.info("✅ Health check completed")
    
    async def start_server(self, host: str = "127.0.0.1", port: int = 8000) -> bool:
        """
        🌐 Start the API server
        =======================
        Only if API components are initialized
        """
        if 'api_server' not in self._components:
            logger.error("❌ API server not initialized. Use --enable-api flag.")
            return False
        
        try:
            logger.info(f"🚀 Starting API server on {host}:{port}")
            
            # Import uvicorn here to avoid dependency if not using API
            import uvicorn
            
            server = self._components['api_server']
            
            # Display endpoint information
            self._display_server_info(host, port)
            
            # Start server (this blocks)
            config = uvicorn.Config(
                server.app,
                host=host,
                port=port,
                log_level="info",
                reload=False
            )
            
            server_instance = uvicorn.Server(config)
            self._running = True
            
            await server_instance.serve()
            
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    def _display_server_info(self, host: str, port: int):
        """📋 Display server information"""
        print(f"\n{'='*60}")
        print(f"🚀 Universal Model Launcher - Server Running")
        print(f"{'='*60}")
        print(f"🌐 Server URL: http://{host}:{port}")
        print(f"📚 API Documentation: http://{host}:{port}/docs")
        print(f"🔍 Health Check: http://{host}:{port}/health")
        print(f"\n📋 Available Endpoints:")
        print(f"   • Native API:")
        print(f"     - POST /load_model     - Load a model")
        print(f"     - POST /unload_model   - Unload a model") 
        print(f"     - GET  /models         - List loaded models")
        print(f"     - GET  /health         - System health")
        print(f"   • OpenAI Compatible:")
        print(f"     - POST /v1/chat/completions  - Chat completions")
        print(f"     - POST /v1/completions       - Text completions")
        print(f"     - GET  /v1/models            - List models")
        print(f"   • WebSocket:")
        print(f"     - WS   /ws             - Real-time streaming")
        print(f"\n💡 Press Ctrl+C to stop the server")
        print(f"{'='*60}\n")
    
    def get_status(self) -> Dict[str, Any]:
        """📊 Get comprehensive system status"""
        if not self._initialized:
            return {"status": "not_initialized", "components": {}}
        
        status = {
            "status": "running" if self._running else "initialized",
            "components": {},
            "timestamp": time.time()
        }
        
        # Component status
        for name, component in self._components.items():
            if hasattr(component, 'get_system_status'):
                status["components"][name] = component.get_system_status()
            elif hasattr(component, 'is_ready'):
                status["components"][name] = {"ready": component.is_ready}
            else:
                status["components"][name] = {"initialized": True}
        
        return status
    
    async def shutdown(self):
        """🛑 Graceful shutdown of all components"""
        logger.info("🛑 Initiating graceful shutdown...")
        self._running = False
        
        try:
            # Shutdown in reverse order
            if 'process_manager' in self._components:
                logger.info("🔄 Stopping process manager...")
                # Process manager handles its own cleanup
            
            if 'health_monitor' in self._components:
                logger.info("🏥 Stopping health monitor...")
                # Health monitor cleanup if needed
            
            if 'universal_loader' in self._components:
                logger.info("📦 Unloading models...")
                loader = self._components['universal_loader']
                for model_id in list(loader.running_servers.keys()):
                    await asyncio.to_thread(loader.unload_model, model_id)
            
            logger.info("✅ Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        
        finally:
            # Force exit if needed
            import sys
            sys.exit(0)


def create_argument_parser() -> argparse.ArgumentParser:
    """📋 Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Universal Model Launcher - Your AI Model Management Solution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with API server
  python main.py --enable-api --port 8000
  
  # Core mode only (no API)
  python main.py --core-only
  
  # Custom configuration directory
  python main.py --config-dir ./custom_config
  
  # Debug mode
  python main.py --debug --enable-api
        """
    )
    
    # Core options
    parser.add_argument(
        '--config-dir', 
        default='config',
        help='Configuration directory (default: config)'
    )
    
    parser.add_argument(
        '--core-only',
        action='store_true',
        help='Initialize core components only (no API server)'
    )
    
    # API options
    api_group = parser.add_argument_group('API Server Options')
    api_group.add_argument(
        '--enable-api',
        action='store_true',
        default=True,
        help='Enable API server (default: True)'
    )
    
    api_group.add_argument(
        '--host',
        default='127.0.0.1',
        help='API server host (default: 127.0.0.1)'
    )
    
    api_group.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API server port (default: 8000)'
    )
    
    # Debug options
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version and exit'
    )
    
    return parser


async def main():
    """🚀 Main application entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle version
    if args.version:
        print("Universal Model Launcher v4.0.0")
        print("Phase 2: API & Communication Layer")
        return
    
    # Setup debug logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 Debug logging enabled")
    
    # Initialize launcher
    launcher = UniversalModelLauncher(config_dir=args.config_dir)
    
    # Initialize components
    enable_api = args.enable_api and not args.core_only
    success = await launcher.initialize(enable_api=enable_api)
    
    if not success:
        logger.error("❌ Failed to initialize Universal Model Launcher")
        sys.exit(1)
    
    # Core-only mode
    if args.core_only:
        logger.info("🎯 Running in core-only mode")
        logger.info("📊 System ready. Use launcher.get_status() for status.")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await launcher.shutdown()
        return
    
    # Start API server
    if enable_api:
        await launcher.start_server(host=args.host, port=args.port)
    else:
        logger.info("💡 Use --enable-api to start the API server")


if __name__ == "__main__":
    try:
        # Check Python version
        if sys.version_info < (3, 10):
            print("❌ Python 3.10+ required")
            sys.exit(1)
        
        # Run main application
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
