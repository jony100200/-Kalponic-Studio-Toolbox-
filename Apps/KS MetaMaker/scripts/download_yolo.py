#!/usr/bin/env python3
"""
Quick YOLO model download and conversion script
"""

import sys
from pathlib import Path

def download_yolo():
    """Download and convert YOLOv8n model"""
    try:
        from ultralytics import YOLO

        print("Downloading YOLOv8n model...")
        model = YOLO('yolov8n.pt')

        print("Converting to ONNX...")
        success = model.export(format='onnx', dynamic=True)

        if success:
            print("✅ Successfully downloaded and converted YOLOv8n.onnx")

            # Move to models directory
            models_dir = Path(__file__).parent.parent / "models"
            models_dir.mkdir(exist_ok=True)

            onnx_file = Path('yolov8n.onnx')
            target_file = models_dir / 'yolov11n.onnx'  # Use the expected filename

            if onnx_file.exists():
                onnx_file.rename(target_file)
                print(f"✅ Moved model to: {target_file}")
                print(f"   Size: {target_file.stat().st_size / (1024*1024):.1f}MB")
            else:
                print("❌ ONNX file not found after conversion")
        else:
            print("❌ Model conversion failed")

    except ImportError:
        print("❌ Ultralytics not installed. Install with: pip install ultralytics")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    download_yolo()