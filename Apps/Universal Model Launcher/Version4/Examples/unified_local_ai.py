#!/usr/bin/env python3
"""
🎮 Unified Local AI Interface
===========================
Single interface for all local AI capabilities via Universal Model Launcher V4
Local-first: All processing happens locally, no external dependencies
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# Import our local AI services
from local_audio_transcriber import LocalAudioTranscriber
from local_image_analyzer import LocalImageAnalyzer
from local_code_analyzer import LocalCodeAnalyzer

class UnifiedLocalAI:
    """🚀 Unified interface for all local AI capabilities"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.audio_service = LocalAudioTranscriber(base_url)
        self.vision_service = LocalImageAnalyzer(base_url)
        self.code_service = LocalCodeAnalyzer(base_url)
        
    def check_services(self) -> Dict[str, bool]:
        """🔍 Check which AI services are available"""
        services = {
            "audio": self.audio_service.find_whisper_model() is not None,
            "vision": self.vision_service.find_vision_model() is not None,
            "code": self.code_service.find_code_model() is not None
        }
        return services
    
    def process_file(self, file_path: Path, task: str = "auto") -> Dict[str, Any]:
        """🎯 Automatically process any file type"""
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        # Auto-detect file type if task is "auto"
        if task == "auto":
            task = self._detect_task_from_file(file_path)
        
        # Route to appropriate service
        if task == "transcribe":
            return self.audio_service.transcribe_audio(file_path)
        elif task == "analyze_image":
            return self.vision_service.analyze_image(file_path)
        elif task == "analyze_code":
            return self.code_service.analyze_code(file_path)
        else:
            return {"error": f"Unknown task: {task}"}
    
    def _detect_task_from_file(self, file_path: Path) -> str:
        """🔍 Auto-detect what to do with a file based on extension"""
        suffix = file_path.suffix.lower()
        
        # Audio files
        if suffix in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
            return "transcribe"
        
        # Image files
        elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
            return "analyze_image"
        
        # Code files
        elif suffix in ['.py', '.js', '.cs', '.cpp', '.java', '.go', '.rs', '.php', '.rb']:
            return "analyze_code"
        
        # Default to code analysis for unknown text files
        else:
            return "analyze_code"

def main():
    """🎯 Command-line interface for unified local AI"""
    parser = argparse.ArgumentParser(description="Unified Local AI Interface")
    parser.add_argument("file", help="File to process")
    parser.add_argument("--task", choices=["auto", "transcribe", "analyze_image", "analyze_code"], 
                       default="auto", help="Task to perform")
    parser.add_argument("--url", default="http://127.0.0.1:8000", 
                       help="Universal Model Launcher base URL")
    
    args = parser.parse_args()
    
    # Initialize unified AI
    ai = UnifiedLocalAI(args.url)
    
    # Check available services
    print("🔍 Checking available AI services...")
    services = ai.check_services()
    
    for service, available in services.items():
        status = "✅" if available else "❌"
        print(f"  {status} {service.capitalize()}: {'Available' if available else 'No model loaded'}")
    
    if not any(services.values()):
        print("\n❌ No AI services available. Please load models in Universal Model Launcher V4 first.")
        return
    
    # Process file
    file_path = Path(args.file)
    print(f"\n🎯 Processing: {file_path.name}")
    
    result = ai.process_file(file_path, args.task)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Success!")
        
        # Display results based on task type
        if "transcription" in result or "srt_file" in result:
            print(f"📝 Transcription: {result.get('text', 'N/A')[:200]}...")
            if result.get('srt_file'):
                print(f"💾 SRT saved to: {result['srt_file']}")
                
        elif "description" in result:
            print(f"🖼️ Description: {result['description']}")
            if result.get('classification'):
                print(f"🏷️ Category: {result['classification']}")
                
        elif "analysis" in result:
            print(f"💻 Language: {result.get('language', 'Unknown')}")
            print(f"📊 Analysis:\n{result['analysis']}")
            if result.get('doc_file'):
                print(f"📚 Documentation: {result['doc_file']}")

if __name__ == "__main__":
    # Test mode if no arguments
    if len(sys.argv) == 1:
        print("🧪 Running test mode...")
        
        ai = UnifiedLocalAI()
        services = ai.check_services()
        
        print("Available services:")
        for service, available in services.items():
            print(f"  {service}: {available}")
        
        # Test files from Testing directory
        test_files = [
            Path("../Testing/6.Local AI Model Launcher.mp3"),
            Path("../Testing/image test.png"), 
            Path("../Testing/PlayerMovement.cs")
        ]
        
        for test_file in test_files:
            if test_file.exists():
                print(f"\n🧪 Testing {test_file.name}...")
                result = ai.process_file(test_file)
                if "error" not in result:
                    print("✅ Success")
                else:
                    print(f"❌ {result['error']}")
    else:
        main()