#!/usr/bin/env python3
"""Test folder structure preservation logic"""
import os
import tempfile
import shutil
from pathlib import Path

def test_relative_path_preservation():
    """Test that relative path calculation works correctly"""
    # Create test structure
    with tempfile.TemporaryDirectory() as tmpdir:
        input_root = os.path.join(tmpdir, "input")
        output_root = os.path.join(tmpdir, "output")
        
        # Create nested input structure
        os.makedirs(os.path.join(input_root, "subfolder1", "subfolder2"))
        
        # Create test files
        test_file = os.path.join(input_root, "subfolder1", "subfolder2", "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Test relative path calculation (this is what _move_file_to_sent does)
        input_root_folder = input_root
        file_path = test_file
        
        file_dir = os.path.dirname(os.path.abspath(file_path))
        root_abs = os.path.abspath(input_root_folder)
        
        if file_dir.startswith(root_abs):
            relative_path = os.path.relpath(file_dir, root_abs)
            if relative_path == ".":
                relative_path = ""
        else:
            relative_path = ""
        
        print(f"Input root: {input_root}")
        print(f"File path: {file_path}")
        print(f"Relative path: {relative_path}")
        print(f"Expected: subfolder1{os.sep}subfolder2")
        assert relative_path == os.path.join('subfolder1', 'subfolder2'), "Relative path calculation failed!"
        print("✓ Relative path calculation correct")
        
        # Test output structure construction
        is_image = True
        custom_sent_images_dir = output_root
        failed = False
        
        base_dir = custom_sent_images_dir
        if relative_path:
            target_dir = os.path.join(base_dir, relative_path, "failed" if failed else "")
        else:
            target_dir = os.path.join(base_dir, "failed" if failed else "")
        
        target_dir = os.path.normpath(target_dir)
        expected_target = os.path.normpath(os.path.join(output_root, 'subfolder1', 'subfolder2'))
        print(f"\nTarget directory: {target_dir}")
        print(f"Expected: {expected_target}")
        assert target_dir == expected_target, "Target directory construction failed!"
        print("✓ Target directory construction correct")

def test_root_level_files():
    """Test files at root level (no subfolders)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_root = os.path.join(tmpdir, "input")
        output_root = os.path.join(tmpdir, "output")
        
        os.makedirs(input_root)
        
        # Create test file at root
        test_file = os.path.join(input_root, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Test relative path calculation for root file
        file_dir = os.path.dirname(os.path.abspath(test_file))
        root_abs = os.path.abspath(input_root)
        
        if file_dir.startswith(root_abs):
            relative_path = os.path.relpath(file_dir, root_abs)
            if relative_path == ".":
                relative_path = ""
        else:
            relative_path = ""
        
        print(f"\n--- Testing root-level files ---")
        print(f"File path: {test_file}")
        print(f"Relative path: '{relative_path}'")
        assert relative_path == "", "Root-level file should have empty relative path!"
        print("✓ Root-level file path handling correct")
        
        # Test that output structure stays at root
        base_dir = output_root
        if relative_path:
            target_dir = os.path.join(base_dir, relative_path)
        else:
            target_dir = base_dir
        
        target_dir = os.path.normpath(target_dir)
        expected_target = os.path.normpath(output_root)
        print(f"Target directory: {target_dir}")
        print(f"Expected: {expected_target}")
        assert target_dir == expected_target, "Root-level target directory should be at root!"
        print("✓ Root-level target directory correct")

if __name__ == "__main__":
    test_relative_path_preservation()
    test_root_level_files()
    print("\n" + "="*50)
    print("✓ All folder structure preservation tests passed!")
    print("="*50)
