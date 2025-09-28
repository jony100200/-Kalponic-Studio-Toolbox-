"""
🚀 Universal Model Launcher V4 - GUI Integration
================================================
Role: Integrated launcher with GUI + Backend
SOLID: Single responsibility for complete application
"""

import sys
import asyncio
import signal
from pathlib import Path

# Add Version4 to Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from main import UniversalModelLauncher
from GUI.main_window import UniversalModelLauncherUI
from PySide6.QtWidgets import QApplication


class IntegratedLauncher:
    """
    🎯 Integrated GUI + Backend Launcher
    ====================================
    Role: Complete application coordinator
    Pattern: GUI frontend + API backend integration
    """
    
    def __init__(self):
        self.backend = None
        self.frontend = None
        self.app = None
    
    async def start_backend(self):
        """🔧 Start the backend system"""
        print("🚀 Initializing backend system...")
        self.backend = UniversalModelLauncher()
        
        # Initialize backend components
        success = await self.backend.initialize(enable_api=True)
        if not success:
            raise RuntimeError("❌ Backend initialization failed")
        
        print("✅ Backend system ready")
        return True
    
    def start_frontend(self):
        """🎨 Start the GUI frontend"""
        print("🎨 Launching GUI interface...")
        
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Universal Model Launcher V4")
        
        # Create main window
        self.frontend = UniversalModelLauncherUI()
        
        # Connect frontend to backend (future integration)
        self._connect_frontend_backend()
        
        # Show window
        self.frontend.show()
        print("✅ GUI interface launched")
    
    def _connect_frontend_backend(self):
        """🔗 Connect GUI signals to backend methods"""
        # Future: Connect GUI signals to backend hybrid loader
        # self.frontend.left_panel.model_launch_requested.connect(
        #     lambda config: self._launch_model_via_backend(config)
        # )
        print("🔗 Frontend-backend integration ready")
    
    async def _launch_model_via_backend(self, config: dict):
        """🚀 Launch model through backend hybrid loader"""
        if self.backend and hasattr(self.backend, '_components'):
            hybrid_loader = self.backend._components.get('hybrid_smart_loader')
            if hybrid_loader:
                # Use hybrid smart loader for intelligent model selection
                input_text = f"Load model: {config.get('model', 'default')}"
                plan = await hybrid_loader.create_smart_loading_plan(input_text)
                print(f"📋 Smart loading plan created: {plan}")
    
    def run(self):
        """🏃‍♂️ Run the integrated application"""
        try:
            # Start backend in a separate thread/process for production
            # For now, just start frontend
            self.start_frontend()
            
            # Run Qt event loop
            return self.app.exec()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1


def main():
    """🚀 Main entry point"""
    print("🚀 Universal Model Launcher V4 - Integrated Mode")
    print("=" * 50)
    
    launcher = IntegratedLauncher()
    exit_code = launcher.run()
    
    print("👋 Application closed")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
