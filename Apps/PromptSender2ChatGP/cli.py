#!/usr/bin/env python3
"""
Command Line Interface for Prompt Sequencer
Provides quick access to testing and utility functions
"""

import argparse
import os
import sys
import logging
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import AppConfig
from src.automation.automation import WindowDetector

def setup_logging(quiet=False):
    """Setup logging for CLI"""
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )

def list_windows(args):
    """List available windows"""
    detector = WindowDetector()
    windows = detector.find_windows()
    
    if windows:
        print("Available windows:")
        for i, window in enumerate(windows, 1):
            print(f"  {i}. {window}")
    else:
        print("No windows found")

def test_window_focus(args):
    """Test focusing a specific window with enhanced strategies"""
    if not args.window:
        print("Error: Please specify a window title substring with --window")
        return
    
    detector = WindowDetector()
    
    # Test window focus
    print(f"Testing window focus for: {args.window}")
    window_success = detector.focus_window(args.window)
    
    if window_success:
        print("✓ Successfully focused window")
        
        # Test input box focus strategies
        print("Testing input box focus strategies...")
        input_success = detector.focus_input_box(retries=2)
        
        if input_success:
            print("✓ Successfully focused input box using keyboard navigation")
            print("✓ All focus tests passed - ready for automation!")
        else:
            print("⚠ Could not auto-focus input box")
            print("  This may still work during automation with manual assistance")
            
            # Test manual intervention simulation
            print("\nTesting manual intervention workflow...")
            print("Please click inside the input box of the target application...")
            input("Press Enter when you've clicked in the input box...")
            
            # Test a simple paste operation
            try:
                import pyautogui
                import pyperclip
                
                original = pyperclip.paste()
                test_text = "<<<MANUAL TEST>>>"
                pyperclip.copy(test_text)
                
                pyautogui.hotkey('ctrl', 'v')
                print("✓ Test paste sent")
                
                input("Press Enter to clean up the test text...")
                for _ in range(len(test_text)):
                    pyautogui.press('backspace')
                
                pyperclip.copy(original)
                print("✓ Manual intervention test completed successfully")
                
            except Exception as e:
                print(f"✗ Manual test failed: {e}")
    else:
        print(f"✗ Failed to focus window containing: {args.window}")
        print("Available windows:")
        windows = detector.find_windows()
        for i, window in enumerate(windows[:10], 1):  # Show first 10
            print(f"  {i}. {window}")

def test_focus_strategies(args):
    """Test different input focus strategies"""
    if not args.window:
        print("Error: Please specify a window title substring with --window")
        return
    
    detector = WindowDetector()
    
    # Focus window first
    if not detector.focus_window(args.window):
        print("✗ Could not focus target window")
        return
    
    print("Testing focus strategies on target window...")
    
    # Test each strategy individually
    strategies = [
        ("Browser/Electron Strategy (Ctrl+L, Tab)", detector._browser_focus_strategy),
        ("Generic Strategy (Ctrl+K, /, Ctrl+F)", detector._generic_focus_strategy),
        ("Tab Navigation Strategy", detector._tab_navigation_strategy)
    ]
    
    for name, strategy in strategies:
        try:
            print(f"\nTesting: {name}")
            success = strategy()
            verification = detector._verify_input_focus()
            
            if success and verification:
                print(f"✓ {name} - SUCCESS")
            else:
                print(f"⚠ {name} - Failed verification")
                
        except Exception as e:
            print(f"✗ {name} - Error: {e}")
        
        input("Press Enter to test next strategy...")
    
    print("\nFocus strategy testing completed")

def show_config(args):
    """Show current configuration"""
    config = AppConfig()
    print("Current configuration:")
    for key, value in config.get_dict().items():
        print(f"  {key}: {value}")

def create_sample_prompts(args):
    """Create sample prompt files for testing"""
    base_dir = args.directory or "test_prompts"
    os.makedirs(base_dir, exist_ok=True)
    
    # Create sample text files
    samples = {
        "nature.txt": [
            "A serene mountain lake at sunrise",
            "Ancient oak tree in a misty forest",
            "Wildflower meadow with butterflies"
        ],
        "sci_fi.txt": [
            "Futuristic space station orbiting Earth",
            "Robot exploring an alien planet",
            "Cyberpunk city with flying cars"
        ]
    }
    
    for filename, prompts in samples.items():
        filepath = os.path.join(base_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n---\n'.join(prompts))
        print(f"Created: {filepath}")
    
    # Create global prompt file
    global_prompt = os.path.join(base_dir, "global_prompt.txt")
    with open(global_prompt, 'w', encoding='utf-8') as f:
        f.write("High quality, detailed, professional artwork")
    print(f"Created: {global_prompt}")

def check_dependencies(args):
    """Check if all required dependencies are installed"""
    dependencies = [
        'customtkinter',
        'pyautogui', 
        'pyperclip',
        'pygetwindow',
        'PIL'  # Pillow imports as PIL
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep}")
            missing.append(dep)
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    else:
        print("\n✓ All dependencies installed")
        return True

def test_prompt_parsing(args):
    """Test prompt parsing with different formats"""
    if not args.file:
        print("Error: Please specify a file to test with --file")
        return
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return
    
    print(f"🧪 Testing prompt parsing on: {args.file}")
    
    try:
        # Import the sequencer to use its parsing methods
        from src.core.sequencer import PromptSequencer
        from src.core.config import AppConfig
        
        config = AppConfig()
        sequencer = PromptSequencer(config)
        
        # Read file content
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n📄 File content preview:")
        print("=" * 50)
        print(content[:200] + "..." if len(content) > 200 else content)
        print("=" * 50)
        
        # Parse prompts
        prompts = sequencer._parse_prompts(content)
        
        print(f"\n✅ Found {len(prompts)} prompts:")
        print("-" * 50)
        
        for i, prompt_data in enumerate(prompts, 1):
            title = prompt_data.get('title', f'Prompt {i}')
            text = prompt_data['text']
            number = prompt_data.get('number', i)
            
            print(f"\n{i}. {title}")
            print(f"   Number: {number}")
            print(f"   Text: {text[:100]}{'...' if len(text) > 100 else ''}")
            print(f"   Length: {len(text)} characters")
        
        print(f"\n🎯 Ready to process {len(prompts)} prompts sequentially")
        
    except Exception as e:
        print(f"❌ Error testing prompt parsing: {e}")

def test_gui_responsive(args):
    """Test the responsive GUI design"""
    print("🎯 Starting GUI Responsiveness Test...")
    print("💡 Try resizing the window and scrolling to test responsiveness!")
    
    try:
        import subprocess
        import sys
        subprocess.run([sys.executable, "test_gui_responsive.py"])
    except Exception as e:
        print(f"Error launching GUI test: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Prompt Sequencer CLI")
    parser.add_argument('--quiet', '-q', action='store_true', help="Quiet output")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List windows command
    list_parser = subparsers.add_parser('windows', help='List available windows')
    
    # Test window focus command
    focus_parser = subparsers.add_parser('focus', help='Test window focus with enhanced strategies')
    focus_parser.add_argument('--window', '-w', required=True, 
                             help='Window title substring to focus')
    
    # Test focus strategies command
    strategies_parser = subparsers.add_parser('strategies', help='Test individual focus strategies')
    strategies_parser.add_argument('--window', '-w', required=True,
                                  help='Window title substring to test strategies on')
    
    # Show config command
    config_parser = subparsers.add_parser('config', help='Show current configuration')
    
    # Create sample prompts command
    sample_parser = subparsers.add_parser('sample_prompts', help='Create sample prompt files')
    sample_parser.add_argument('--directory', '-d', default='test_prompts',
                              help='Directory to create samples in')
    
    # Check dependencies command
    deps_parser = subparsers.add_parser('deps', help='Check dependencies')
    
    # Test GUI responsiveness command
    gui_parser = subparsers.add_parser('test_gui', help='Test responsive GUI design')
    
    # Test prompt parsing command
    parse_parser = subparsers.add_parser('test_parse', help='Test prompt parsing')
    parse_parser.add_argument('--file', '-f', required=True,
                             help='File to test prompt parsing on')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup_logging(args.quiet)
    
    # Execute command
    commands = {
        'windows': list_windows,
        'focus': test_window_focus,
        'strategies': test_focus_strategies,
        'config': show_config,
        'sample_prompts': create_sample_prompts,
        'deps': check_dependencies,
        'test_gui': test_gui_responsive,
        'test_parse': test_prompt_parsing
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        print(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()
