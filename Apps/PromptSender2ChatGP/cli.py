#!/usr/bin/env python3
"""
Command Line Interface for Prompt Sequencer
Provides quick access to testing and utility functions
"""

import argparse
import os
import sys
import logging
from datetime import datetime, timedelta
import time

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

def _build_sequencer(config: AppConfig):
    """Create a sequencer instance for CLI operations."""
    from src.core.sequencer import PromptSequencer
    return PromptSequencer(config)

def _wait_until(start_at: str):
    """Wait until a target schedule time."""
    if not start_at:
        return

    start_at = start_at.strip()
    now = datetime.now()
    target = None

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            target = datetime.strptime(start_at, fmt)
            break
        except ValueError:
            continue

    if target is None:
        # Daily time format HH:MM
        try:
            hh, mm = start_at.split(":")
            target = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            if target <= now:
                target = target + timedelta(days=1)
        except Exception:
            raise ValueError("Invalid --start-at format. Use 'YYYY-MM-DD HH:MM' or 'HH:MM'.")

    wait_seconds = (target - now).total_seconds()
    if wait_seconds > 0:
        print(f"Scheduled start at {target.strftime('%Y-%m-%d %H:%M:%S')} (waiting {int(wait_seconds)}s)")
        time.sleep(wait_seconds)

def _print_preflight(result: dict):
    """Pretty-print preflight output."""
    print(f"Mode: {result.get('mode')}")
    print(f"OK: {result.get('ok')}")
    print(f"Estimated items: {result.get('estimated_items')}")
    print(f"Estimated duration (sec): {result.get('estimated_duration_sec')}")

    errors = result.get("errors") or []
    warnings = result.get("warnings") or []
    info = result.get("info") or []

    if info:
        print("Info:")
        for line in info:
            print(f"  - {line}")
    if warnings:
        print("Warnings:")
        for line in warnings:
            print(f"  - {line}")
    if errors:
        print("Errors:")
        for line in errors:
            print(f"  - {line}")

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
        print(" Successfully focused window")
        
        # Test input box focus strategies
        print("Testing input box focus strategies...")
        input_success = detector.focus_input_box(retries=2)
        
        if input_success:
            print(" Successfully focused input box using keyboard navigation")
            print(" All focus tests passed - ready for automation!")
        else:
            print(" Could not auto-focus input box")
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
                print(" Test paste sent")
                
                input("Press Enter to clean up the test text...")
                for _ in range(len(test_text)):
                    pyautogui.press('backspace')
                
                pyperclip.copy(original)
                print(" Manual intervention test completed successfully")
                
            except Exception as e:
                print(f" Manual test failed: {e}")
    else:
        print(f" Failed to focus window containing: {args.window}")
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
        print(" Could not focus target window")
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
                print(f" {name} - SUCCESS")
            else:
                print(f" {name} - Failed verification")
                
        except Exception as e:
            print(f" {name} - Error: {e}")
        
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
            print(f"[OK] {dep}")
        except ImportError:
            print(f"[MISSING] {dep}")
            missing.append(dep)
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    else:
        print("\n[OK] All dependencies installed")
        return True

def test_prompt_parsing(args):
    """Test prompt parsing with different formats"""
    if not args.file:
        print("Error: Please specify a file to test with --file")
        return
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return
    
    print(f" Testing prompt parsing on: {args.file}")
    
    try:
        # Import the sequencer to use its parsing methods
        from src.core.sequencer import PromptSequencer
        from src.core.config import AppConfig
        
        config = AppConfig()
        sequencer = PromptSequencer(config)
        
        # Read file content
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n File content preview:")
        print("=" * 50)
        print(content[:200] + "..." if len(content) > 200 else content)
        print("=" * 50)
        
        # Parse prompts
        prompts = sequencer._parse_prompts(content)
        
        print(f"\n Found {len(prompts)} prompts:")
        print("-" * 50)
        
        for i, prompt_data in enumerate(prompts, 1):
            title = prompt_data.get('title', f'Prompt {i}')
            text = prompt_data['text']
            number = prompt_data.get('number', i)
            
            print(f"\n{i}. {title}")
            print(f"   Number: {number}")
            print(f"   Text: {text[:100]}{'...' if len(text) > 100 else ''}")
            print(f"   Length: {len(text)} characters")
        
        print(f"\n Ready to process {len(prompts)} prompts sequentially")
        
    except Exception as e:
        print(f" Error testing prompt parsing: {e}")

def test_gui_responsive(args):
    """Test the responsive GUI design"""
    print(" Starting GUI Responsiveness Test...")
    print(" Try resizing the window and scrolling to test responsiveness!")
    
    try:
        import subprocess
        import sys
        subprocess.run([sys.executable, "test_gui_responsive.py"])
    except Exception as e:
        print(f"Error launching GUI test: {e}")

def run_preflight_command(args):
    """Run preflight checks for a selected mode."""
    config = AppConfig()
    if args.window is not None:
        config.target_window = args.window
    if args.dry_run:
        config.dry_run = True
    config.sanitize()

    sequencer = _build_sequencer(config)

    if args.mode == "text":
        folder = args.folder or config.text_input_folder
        result = sequencer.run_preflight(mode="text", input_folder=folder)
    elif args.mode == "image":
        folder = args.folder or config.image_input_folder
        prompt_file = args.prompt_file or config.global_prompt_file
        result = sequencer.run_preflight(mode="image", input_folder=folder, global_prompt_file=prompt_file)
    else:
        result = sequencer.run_preflight(mode="queue", queue_items=config.image_queue_items)

    _print_preflight(result)
    if not result.get("ok"):
        sys.exit(1)

def _apply_runtime_overrides(config: AppConfig, args):
    """Apply optional run-time CLI overrides."""
    if getattr(args, "profile", None):
        if not config.apply_profile(args.profile):
            print(f"Profile not found: {args.profile}")
            sys.exit(1)
    if getattr(args, "window", None) is not None:
        config.target_window = args.window
    if getattr(args, "dry_run", False):
        config.dry_run = True
    if getattr(args, "skip_duplicates", False):
        config.skip_duplicates = True
    config.sanitize()

def run_mode_command(args):
    """Run text/image/queue modes from CLI."""
    config = AppConfig()
    _apply_runtime_overrides(config, args)
    _wait_until(getattr(args, "start_at", ""))

    sequencer = _build_sequencer(config)
    if getattr(args, "preflight", False):
        if args.mode == "text":
            pre = sequencer.run_preflight("text", input_folder=args.folder or config.text_input_folder)
        elif args.mode == "image":
            pre = sequencer.run_preflight(
                "image",
                input_folder=args.folder or config.image_input_folder,
                global_prompt_file=args.prompt_file or config.global_prompt_file,
            )
        else:
            pre = sequencer.run_preflight("queue", queue_items=config.image_queue_items)
        _print_preflight(pre)
        if not pre.get("ok"):
            print("Preflight failed; aborting run.")
            return

    if args.mode == "text":
        folder = args.folder or config.text_input_folder
        if not folder:
            print("Text mode requires --folder or configured text_input_folder.")
            return
        sequencer.start_text_mode(folder)
    elif args.mode == "image":
        folder = args.folder or config.image_input_folder
        prompt_file = args.prompt_file or config.global_prompt_file
        if not folder:
            print("Image mode requires --folder or configured image_input_folder.")
            return
        sequencer.start_image_mode(folder, prompt_file or "")
    else:
        if getattr(args, "resume_snapshot", False):
            if not sequencer.resume_image_queue_from_snapshot():
                print("No resumable queue snapshot found.")
                return
        else:
            sequencer.start_image_queue_mode(config.image_queue_items)

    if sequencer.last_run_summary_file:
        print(f"Run summary: {sequencer.last_run_summary_file}")

def watch_mode_command(args):
    """Watch folder and process new files periodically."""
    config = AppConfig()
    _apply_runtime_overrides(config, args)
    _wait_until(getattr(args, "start_at", ""))

    sequencer = _build_sequencer(config)
    folder = args.folder
    interval = max(1, int(args.interval))

    if not folder:
        print("Watch mode requires --folder.")
        return
    if not os.path.isdir(folder):
        print(f"Folder not found: {folder}")
        return

    print(f"Watching '{folder}' every {interval}s. Press Ctrl+C to stop.")
    try:
        while True:
            if args.mode == "text":
                has_items = any(name.lower().endswith(".txt") for name in os.listdir(folder))
                if has_items:
                    sequencer.start_text_mode(folder)
            else:
                has_items = any(
                    os.path.splitext(name)[1].lower() in {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
                    for name in os.listdir(folder)
                )
                if has_items:
                    sequencer.start_image_mode(folder, args.prompt_file or config.global_prompt_file or "")

            if args.once:
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        print("Watch stopped.")

def quick_test_command(args):
    """Run a single-item quick test without reorganizing source folders."""
    config = AppConfig()
    _apply_runtime_overrides(config, args)
    if getattr(args, "live", False) and not getattr(args, "dry_run", False):
        config.dry_run = False
    else:
        config.dry_run = True
    config.sanitize()

    sequencer = _build_sequencer(config)
    if args.mode == "text":
        folder = args.folder or config.text_input_folder
        if not folder or not os.path.isdir(folder):
            print("Quick test (text) needs a valid --folder.")
            return
        files = sorted([f for f in os.listdir(folder) if f.lower().endswith(".txt")])
        if not files:
            print("No .txt files found for quick test.")
            return
        file_path = os.path.join(folder, files[0])
        with open(file_path, "r", encoding="utf-8") as f:
            prompts = sequencer._parse_prompts(f.read())
        if not prompts:
            print("No prompts found in first text file.")
            return
        first_prompt = prompts[0]
        rendered = sequencer._apply_prompt_variables(
            first_prompt["text"],
            sequencer._build_prompt_context(
                mode="text",
                source_file=file_path,
                index=1,
                title=first_prompt.get("title", "Quick Test"),
            ),
        )
        ok = sequencer._send_text_prompt(rendered, 1, first_prompt.get("title", "Quick Test"))
        print("Quick test result:", "PASS" if ok else "FAIL")
    else:
        folder = args.folder or config.image_input_folder
        if not folder or not os.path.isdir(folder):
            print("Quick test (image) needs a valid --folder.")
            return
        images = sorted(
            [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}]
        )
        if not images:
            print("No images found for quick test.")
            return
        image_path = os.path.join(folder, images[0])
        prompt_file = args.prompt_file or config.global_prompt_file
        prompt_text = ""
        if prompt_file and os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_text = f.read().strip()
        prompt_text = sequencer._apply_prompt_variables(
            prompt_text,
            sequencer._build_prompt_context(mode="image", source_file=image_path, index=1, title=images[0]),
        )
        ok = sequencer._send_image_prompt(image_path, prompt_text, 1)
        print("Quick test result:", "PASS" if ok else "FAIL")

def profile_list_command(args):
    """List saved profiles."""
    config = AppConfig()
    names = config.list_profiles()
    if not names:
        print("No profiles saved.")
        return
    print("Profiles:")
    for name in names:
        print(f"  - {name}")

def profile_save_command(args):
    """Save current settings as profile."""
    config = AppConfig()
    if not config.save_profile(args.name):
        print("Profile name cannot be empty.")
        return
    config.save()
    print(f"Profile saved: {args.name}")

def profile_apply_command(args):
    """Apply a saved profile."""
    config = AppConfig()
    if not config.apply_profile(args.name):
        print(f"Profile not found: {args.name}")
        return
    config.save()
    print(f"Profile applied: {args.name}")

def resume_queue_snapshot_command(args):
    """Resume queue processing from latest snapshot."""
    config = AppConfig()
    _apply_runtime_overrides(config, args)
    sequencer = _build_sequencer(config)
    ok = sequencer.resume_image_queue_from_snapshot()
    if not ok:
        print("No resumable queue snapshot found.")
        return
    if sequencer.last_run_summary_file:
        print(f"Run summary: {sequencer.last_run_summary_file}")

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

    # Preflight command
    preflight_parser = subparsers.add_parser('preflight', help='Run preflight checks')
    preflight_parser.add_argument('--mode', choices=['text', 'image', 'queue'], required=True,
                                 help='Mode to validate')
    preflight_parser.add_argument('--folder', help='Input folder (text/image modes)')
    preflight_parser.add_argument('--prompt-file', help='Global prompt file (image mode)')
    preflight_parser.add_argument('--window', help='Override target window')
    preflight_parser.add_argument('--dry-run', action='store_true', help='Enable dry-run for checks')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run sequencer mode from CLI')
    run_parser.add_argument('--mode', choices=['text', 'image', 'queue'], required=True,
                           help='Mode to execute')
    run_parser.add_argument('--folder', help='Input folder (text/image modes)')
    run_parser.add_argument('--prompt-file', help='Global prompt file (image mode)')
    run_parser.add_argument('--window', help='Override target window')
    run_parser.add_argument('--profile', help='Apply named profile before run')
    run_parser.add_argument('--dry-run', action='store_true', help='Simulate run without paste/move')
    run_parser.add_argument('--skip-duplicates', action='store_true', help='Skip previously processed items')
    run_parser.add_argument('--preflight', action='store_true', help='Run preflight before execution')
    run_parser.add_argument('--start-at', help="Schedule start time ('YYYY-MM-DD HH:MM' or 'HH:MM')")
    run_parser.add_argument('--resume-snapshot', action='store_true',
                           help='Resume queue mode from latest snapshot (queue mode only)')

    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Watch folder and process on interval')
    watch_parser.add_argument('--mode', choices=['text', 'image'], required=True,
                             help='Watch mode')
    watch_parser.add_argument('--folder', required=True, help='Folder to watch')
    watch_parser.add_argument('--prompt-file', help='Global prompt file (image mode)')
    watch_parser.add_argument('--interval', type=int, default=10, help='Polling interval in seconds')
    watch_parser.add_argument('--once', action='store_true', help='Run one polling cycle and exit')
    watch_parser.add_argument('--window', help='Override target window')
    watch_parser.add_argument('--profile', help='Apply named profile before watch')
    watch_parser.add_argument('--dry-run', action='store_true', help='Simulate actions only')
    watch_parser.add_argument('--skip-duplicates', action='store_true', help='Skip previously processed items')
    watch_parser.add_argument('--start-at', help="Schedule start time ('YYYY-MM-DD HH:MM' or 'HH:MM')")

    # Quick test command
    quick_parser = subparsers.add_parser('quick_test', help='Send a single prompt/image test item')
    quick_parser.add_argument('--mode', choices=['text', 'image'], required=True, help='Quick test mode')
    quick_parser.add_argument('--folder', help='Input folder')
    quick_parser.add_argument('--prompt-file', help='Global prompt file (image mode)')
    quick_parser.add_argument('--window', help='Override target window')
    quick_parser.add_argument('--profile', help='Apply named profile before test')
    quick_parser.add_argument('--live', action='store_true',
                             help='Run live (default is dry-run safe test)')
    quick_parser.add_argument('--dry-run', action='store_true',
                             help='Force dry-run even when --live is set')
    quick_parser.add_argument('--skip-duplicates', action='store_true', help='Skip previously processed items')

    # Profile commands
    profile_list_parser = subparsers.add_parser('profile_list', help='List saved config profiles')
    profile_save_parser = subparsers.add_parser('profile_save', help='Save current config as profile')
    profile_save_parser.add_argument('--name', required=True, help='Profile name')
    profile_apply_parser = subparsers.add_parser('profile_apply', help='Apply saved profile')
    profile_apply_parser.add_argument('--name', required=True, help='Profile name')

    # Resume queue snapshot command
    resume_snapshot_parser = subparsers.add_parser('resume_snapshot', help='Resume queue from snapshot')
    resume_snapshot_parser.add_argument('--window', help='Override target window')
    resume_snapshot_parser.add_argument('--profile', help='Apply named profile before resume')
    resume_snapshot_parser.add_argument('--dry-run', action='store_true', help='Simulate actions only')
    resume_snapshot_parser.add_argument('--skip-duplicates', action='store_true',
                                       help='Skip previously processed items')
    
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
        'test_parse': test_prompt_parsing,
        'preflight': run_preflight_command,
        'run': run_mode_command,
        'watch': watch_mode_command,
        'quick_test': quick_test_command,
        'profile_list': profile_list_command,
        'profile_save': profile_save_command,
        'profile_apply': profile_apply_command,
        'resume_snapshot': resume_queue_snapshot_command,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        print(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()
