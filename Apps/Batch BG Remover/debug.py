"""
Debug utilities for enhanced system
KISS principle: Simple debugging tools
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

from src.core import RemoverFactory, RemoverType, ProcessingEngine
from src.config import config


class SystemDiagnostics:
    """
    Simple diagnostic tools for debugging.
    
    KISS: Straightforward diagnostic methods
    SOLID: Single Responsibility - only diagnostics
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check if all dependencies are available."""
        results = {
            "status": "checking",
            "dependencies": {},
            "errors": []
        }
        
        try:
            # Check core dependencies
            import customtkinter
            results["dependencies"]["customtkinter"] = customtkinter.__version__
        except ImportError as e:
            results["errors"].append(f"CustomTkinter not available: {e}")
        
        try:
            from transparent_background import Remover
            results["dependencies"]["transparent_background"] = "available"
        except ImportError as e:
            results["errors"].append(f"transparent-background not available: {e}")
        
        try:
            from PIL import Image
            results["dependencies"]["PIL"] = Image.__version__
        except ImportError as e:
            results["errors"].append(f"PIL not available: {e}")
        
        results["status"] = "completed"
        return results
    
    def check_removers(self) -> Dict[str, Any]:
        """Check status of all background removers."""
        results = {
            "status": "checking",
            "removers": {},
            "errors": []
        }
        
        for remover_type in RemoverType:
            try:
                remover = RemoverFactory.create_remover(remover_type)
                info = remover.get_info()
                info["available"] = remover.is_available()
                results["removers"][remover_type.value] = info
                remover.cleanup()
            except Exception as e:
                results["errors"].append(f"Failed to check {remover_type.value}: {e}")
        
        results["status"] = "completed"
        return results
    
    def check_config(self) -> Dict[str, Any]:
        """Check configuration status."""
        results = {
            "status": "checking",
            "config_valid": False,
            "settings": {},
            "errors": []
        }
        
        try:
            results["config_valid"] = config.validate_all()
            results["settings"] = {
                "removal": config.removal_settings.__dict__,
                "ui": config.ui_settings.__dict__,
                "processing": config.processing_settings.__dict__
            }
        except Exception as e:
            results["errors"].append(f"Config check failed: {e}")
        
        results["status"] = "completed"
        return results
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """Run complete system diagnostic."""
        self.logger.info("Running full system diagnostic...")
        
        results = {
            "system": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": str(Path.cwd())
            },
            "dependencies": self.check_dependencies(),
            "removers": self.check_removers(),
            "config": self.check_config()
        }
        
        self.logger.info("Diagnostic completed")
        return results
    
    def print_diagnostic_report(self):
        """Print a formatted diagnostic report."""
        results = self.run_full_diagnostic()
        
        print("=" * 60)
        print("ENHANCED BATCH BG REMOVER - DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # System info
        print("\n🔧 SYSTEM INFO:")
        print(f"  Python: {results['system']['python_version']}")
        print(f"  Platform: {results['system']['platform']}")
        print(f"  Working Dir: {results['system']['working_directory']}")
        
        # Dependencies
        print("\n📦 DEPENDENCIES:")
        deps = results['dependencies']
        for name, version in deps.get('dependencies', {}).items():
            print(f"  ✅ {name}: {version}")
        
        for error in deps.get('errors', []):
            print(f"  ❌ {error}")
        
        # Removers
        print("\n🤖 AI MODELS:")
        removers = results['removers']
        for name, info in removers.get('removers', {}).items():
            status = "✅" if info.get('available', False) else "❌"
            print(f"  {status} {name}: {info.get('description', 'No description')}")
        
        for error in removers.get('errors', []):
            print(f"  ❌ {error}")
        
        # Config
        print("\n⚙️ CONFIGURATION:")
        config_info = results['config']
        if config_info.get('config_valid', False):
            print("  ✅ Configuration valid")
        else:
            print("  ❌ Configuration invalid")
        
        for error in config_info.get('errors', []):
            print(f"  ❌ {error}")
        
        print("\n" + "=" * 60)
        
        return results


def debug_processing_engine():
    """Debug the processing engine specifically."""
    print("\n🔍 DEBUGGING PROCESSING ENGINE...")
    
    try:
        engine = ProcessingEngine()
        print("✅ ProcessingEngine created successfully")
        
        info = engine.get_remover_info()
        print(f"✅ Active remover: {info.get('name', 'Unknown')}")
        print(f"   Status: {info.get('status', 'Unknown')}")
        
        engine.cleanup()
        print("✅ ProcessingEngine cleanup completed")
        
    except Exception as e:
        print(f"❌ ProcessingEngine error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main debug function."""
    # Set up logging for debug mode
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run diagnostics
    diagnostics = SystemDiagnostics()
    diagnostics.print_diagnostic_report()
    
    # Debug specific components
    debug_processing_engine()
    
    print("\n✅ Debug session completed!")


if __name__ == "__main__":
    main()