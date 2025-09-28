"""Simple test to verify imports work"""
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Test basic imports
    print("Testing imports...")
    from Core.configuration_manager import ConfigurationManager
    print("✅ ConfigurationManager import successful")
    
    # Test initialization
    print("Testing initialization...")
    cm = ConfigurationManager()
    print("✅ ConfigurationManager initialized")
    
    # Test config file
    print(f"Config file path: {cm.config_file}")
    print(f"Config file exists: {cm.config_file.exists()}")
    
    # Force save
    cm.save_configuration()
    print("✅ Configuration saved")
    
    print(f"Config file exists after save: {cm.config_file.exists()}")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(traceback.format_exc())
