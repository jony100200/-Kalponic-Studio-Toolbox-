"""
🧪 Test GUI Configuration Features
==================================
Role: Test GUI configuration and model discovery features
"""

import sys
from pathlib import Path
import time

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    # Test configuration system
    print("🧪 Testing Configuration Manager...")
    from Core.configuration_manager import get_config_manager
    config = get_config_manager()
    
    print(f"✅ Config file location: {config.config_file}")
    print(f"✅ Config file exists: {config.config_file.exists()}")
    
    # Test scan directories
    scan_dirs = config.get_expanded_scan_directories()
    print(f"✅ Configured scan directories: {len(scan_dirs)}")
    for i, dir_path in enumerate(scan_dirs[:3], 1):  # Show first 3
        exists = Path(dir_path).exists()
        status = "✅" if exists else "❌"
        print(f"  {i}. {dir_path} {status}")
    
    # Test model discovery
    print("\n🔍 Testing Model Discovery...")
    from Core.model_discovery import ModelDiscovery
    discovery = ModelDiscovery()
    
    # Force a fresh discovery
    models = discovery.discover_models(force_rescan=True)
    stats = discovery.get_model_stats()
    
    print(f"✅ Models discovered: {stats['total_models']}")
    print(f"✅ Total size: {stats['total_size_gb']:.2f} GB")
    print(f"✅ Model types: {stats['types']}")
    print(f"✅ Backend types: {stats['backends']}")
    
    # Test path addition
    print("\n📁 Testing Directory Addition...")
    test_dir = "./test_models"
    Path(test_dir).mkdir(exist_ok=True)
    
    if discovery.add_scan_directory_interactive(test_dir):
        print(f"✅ Successfully added test directory: {test_dir}")
    else:
        print(f"❌ Failed to add test directory: {test_dir}")
    
    print("\n🎉 Configuration and Discovery System Tests Complete!")
    print("\n🎮 GUI Features Available:")
    print("  📂 Model Browser Tab: View discovered models")
    print("  ⚙️ Settings Tab: Add model directories, open config file")
    print("  🔄 Refresh Models: Force re-discovery")
    print("  📁 Add Directory: Browse and add model paths")
    print("  ⚙️ Open Config: Edit uml_config.json directly")
    
    print(f"\n📄 Current Configuration File:")
    print(f"  Location: {config.config_file.absolute()}")
    print(f"  Scan Directories: {len(scan_dirs)}")
    print(f"  File Extensions: {config.get_file_extensions()}")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
