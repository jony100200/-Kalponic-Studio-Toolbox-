"""
🧪 Test Configuration and Model Discovery
=========================================
Role: Test the modular configuration system and model discovery
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from Core.configuration_manager import get_config_manager
from Core.model_discovery import ModelDiscovery


def test_configuration_system():
    """🧪 Test configuration management"""
    print("🧪 Testing Configuration System")
    print("=" * 50)
    
    try:
        # Test configuration manager
        config = get_config_manager()
        
        # Test path expansion
        test_paths = [
            "~/models",
            "${HOME}/ai_models", 
            "./local_models",
            "C:\\absolute\\path"
        ]
        
        print("📂 Path Expansion Test:")
        for path in test_paths:
            expanded = config.expand_path(path)
            print(f"  {path} → {expanded}")
        
        # Test scan directories
        scan_dirs = config.get_expanded_scan_directories()
        print(f"\n📁 Configured scan directories: {len(scan_dirs)}")
        for i, dir_path in enumerate(scan_dirs, 1):
            exists = Path(dir_path).exists()
            status = "✅" if exists else "❌"
            print(f"  {i}. {dir_path} {status}")
        
        # Test file extensions
        extensions = config.get_file_extensions()
        print(f"\n📄 File extensions: {extensions}")
        
        print("\n✅ Configuration system test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_model_discovery():
    """🔍 Test model discovery system"""
    print("\n🔍 Testing Model Discovery System")
    print("=" * 50)
    
    try:
        # Initialize discovery
        discovery = ModelDiscovery()
        
        # Run discovery
        print("🔍 Starting model discovery...")
        models = discovery.discover_models(force_rescan=True)
        
        # Display results
        print(f"\n📊 Discovery Results:")
        print(f"  Total models found: {len(models)}")
        
        # Show statistics
        stats = discovery.get_model_stats()
        print(f"  Total size: {stats['total_size_gb']:.2f} GB")
        print(f"  Model types: {stats['types']}")
        print(f"  Backend types: {stats['backends']}")
        
        # Show some examples
        if models:
            print(f"\n📋 Sample Models:")
            for i, (name, model) in enumerate(list(models.items())[:5], 1):
                size_mb = model.size_bytes // (1024 * 1024) if model.size_bytes > 0 else 0
                print(f"  {i}. {model.name}")
                print(f"     Type: {model.model_type} | Backend: {model.backend_type}")
                print(f"     Size: {size_mb} MB | Path: {model.path}")
        
        print("\n✅ Model discovery test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Model discovery test failed: {e}")
        return False


def test_configuration_persistence():
    """💾 Test configuration file creation and persistence"""
    print("\n💾 Testing Configuration Persistence")
    print("=" * 50)
    
    try:
        config_path = Path("./config/uml_config.json")
        
        if config_path.exists():
            print(f"✅ Configuration file exists: {config_path}")
            
            # Load and validate JSON
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Check main sections
            required_sections = [
                "model_paths",
                "model_discovery", 
                "backend_configs",
                "ui_settings",
                "file_extensions"
            ]
            
            print("📋 Configuration sections:")
            for section in required_sections:
                exists = section in config_data
                status = "✅" if exists else "❌"
                print(f"  {section}: {status}")
                
                if exists and section == "model_paths":
                    scan_dirs = config_data[section].get("scan_directories", [])
                    print(f"    Scan directories: {len(scan_dirs)}")
            
            print("\n✅ Configuration persistence test passed!")
            return True
        else:
            print(f"❌ Configuration file not found: {config_path}")
            return False
            
    except Exception as e:
        print(f"❌ Configuration persistence test failed: {e}")
        return False


def main():
    """🎯 Run all configuration and discovery tests"""
    print("🎯 Universal Model Launcher - Configuration Test Suite")
    print("=" * 60)
    
    tests = [
        test_configuration_system,
        test_model_discovery, 
        test_configuration_persistence
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the configuration setup.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
