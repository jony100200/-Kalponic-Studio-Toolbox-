#!/usr/bin/env python3
"""
🔍 Test File Verification Script
================================
This script verifies what test files were actually accessed and processed.
"""

import os
from pathlib import Path
from PIL import Image
import faster_whisper

# Test file paths
TEST_FILES_DIR = Path("E:/__Kalponic Studio Repositories/-Kalponic-Studio-Toolbox-/Apps/Universal Model Launcher/Testing")
WHISPER_MODEL_DIR = Path("O:/AI Models/TTS/deepdmlfaster-whisper-large-v3-turbo-ct2")

def verify_files():
    """🔍 Verify test files and their accessibility"""
    
    print("🔍 Test File Verification")
    print("=" * 50)
    
    # Check test directory
    print(f"📁 Test Directory: {TEST_FILES_DIR}")
    print(f"   Exists: {'✅' if TEST_FILES_DIR.exists() else '❌'}")
    
    if TEST_FILES_DIR.exists():
        print("\n📋 Files Found:")
        for file in TEST_FILES_DIR.iterdir():
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   📄 {file.name}: {size_mb:.1f} MB")
    
    print("\n" + "=" * 50)
    
    # Test image file
    image_path = TEST_FILES_DIR / "image test.png"
    print(f"🖼️ Image Test: {image_path.name}")
    
    if image_path.exists():
        try:
            image = Image.open(image_path)
            print(f"   ✅ Successfully opened with PIL")
            print(f"   📐 Dimensions: {image.size[0]}x{image.size[1]} pixels")
            print(f"   🎨 Format: {image.format}")
            print(f"   📊 Mode: {image.mode}")
        except Exception as e:
            print(f"   ❌ Failed to open: {e}")
    else:
        print(f"   ❌ File not found")
    
    print("\n" + "=" * 50)
    
    # Test audio file
    audio_path = TEST_FILES_DIR / "6.Local AI Model Launcher.mp3"
    print(f"🔊 Audio Test: {audio_path.name}")
    
    if audio_path.exists():
        size_mb = audio_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ File exists: {size_mb:.1f} MB")
        
        # Test Whisper model access
        if WHISPER_MODEL_DIR.exists():
            print(f"   🤖 Whisper model available: {WHISPER_MODEL_DIR}")
            try:
                # Load model and get a quick sample
                model = faster_whisper.WhisperModel(str(WHISPER_MODEL_DIR), device="cpu", compute_type="int8")
                print(f"   ✅ Whisper model loaded successfully")
                
                # Quick transcription test (first 10 seconds)
                segments, info = model.transcribe(str(audio_path), beam_size=1, no_speech_threshold=0.6, condition_on_previous_text=False)
                
                first_segment = next(segments, None)
                if first_segment:
                    print(f"   🎯 Sample transcription: '{first_segment.text.strip()}'")
                    print(f"   🌍 Detected language: {info.language} (confidence: {info.language_probability:.2f})")
                
                del model  # Cleanup
                
            except Exception as e:
                print(f"   ❌ Whisper test failed: {e}")
        else:
            print(f"   ❌ Whisper model not found at: {WHISPER_MODEL_DIR}")
    else:
        print(f"   ❌ File not found")
    
    print("\n" + "=" * 50)
    
    # Test script file
    script_path = TEST_FILES_DIR / "PlayerMovement.cs"
    print(f"📄 Script Test: {script_path.name}")
    
    if script_path.exists():
        size_kb = script_path.stat().st_size / 1024
        print(f"   ✅ File exists: {size_kb:.1f} KB")
        
        # Read first few lines
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
            print(f"   📝 First few lines:")
            for i, line in enumerate(lines, 1):
                print(f"      {i}: {line.strip()}")
        except Exception as e:
            print(f"   ❌ Failed to read: {e}")
    else:
        print(f"   ❌ File not found")

if __name__ == "__main__":
    verify_files()
