"""
🧪 GUI Model Discovery Debug Test
=================================
Role: Debug the GUI model discovery issue
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from Core.model_discovery import ModelDiscovery

def test_gui_discovery():
    print("🔍 Testing GUI Model Discovery...")
    
    try:
        # Initialize discovery system (same as GUI)
        discovery = ModelDiscovery()
        
        # Run discovery
        print("🔄 Running model discovery...")
        models = discovery.discover_models(force_rescan=True)
        
        print(f"✅ Discovery complete!")
        print(f"📊 Total models found: {len(models)}")
        
        # Show first few models
        if models:
            print("\n📋 Sample discovered models:")
            for i, (name, model) in enumerate(list(models.items())[:5], 1):
                size_mb = model.size_bytes // (1024 * 1024) if model.size_bytes > 0 else 0
                print(f"  {i}. {model.name}")
                print(f"     Type: {model.model_type} | Backend: {model.backend_type}")
                print(f"     Size: {size_mb} MB | Path: {model.path[:60]}...")
        else:
            print("❌ No models found!")
        
        # Check if the issue is with the GUI population logic
        print(f"\n🔍 Testing GUI logic...")
        print(f"📊 Models dict type: {type(models)}")
        print(f"📊 Models dict empty: {not models}")
        print(f"📊 Models dict keys: {list(models.keys())[:5]}")
        
        return models
        
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    models = test_gui_discovery()
    
    # Test the GUI logic condition
    discovered_models = getattr(type('MockGUI', (), {}), 'discovered_models', models)
    
    print(f"\n🎮 GUI Logic Test:")
    print(f"📊 discovered_models: {type(discovered_models)}")
    print(f"📊 not discovered_models: {not discovered_models}")
    print(f"📊 Would show placeholder: {not discovered_models}")
    
    if not discovered_models:
        print("❌ GUI would show 'Discovering models...' placeholder")
    else:
        print("✅ GUI should show model cards")
        print(f"📊 Would create {len(discovered_models)} model cards")
