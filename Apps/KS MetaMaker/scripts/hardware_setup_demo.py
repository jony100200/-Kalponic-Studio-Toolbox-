#!/usr/bin/env python3
"""
KS MetaMaker - Hardware Setup Demo
==================================
Demonstrates the hardware detection and model recommendation system
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ks_metamaker.hardware_detector import HardwareDetector
from ks_metamaker.model_recommender import ModelRecommender
from ks_metamaker.model_downloader import ModelDownloader

def main():
    print("🖥️  KS MetaMaker - Hardware Setup Demo")
    print("=" * 50)

    # Detect hardware
    print("\n🔍 Detecting your hardware...")
    detector = HardwareDetector()
    profile = detector.get_system_profile()
    summary = detector.get_hardware_summary()

    print(f"\n✅ Detected Profile: {profile.upper()}")

    # Show hardware details
    sys_info = summary['system']
    print(f"   CPU: {sys_info['cpu_name']} ({sys_info['cpu_cores']} cores)")
    print(f"   RAM: {sys_info['total_ram_gb']} GB")

    if summary['gpus']:
        gpu = summary['gpus'][0]
        print(f"   GPU: {gpu['name']} ({gpu['memory_gb']} GB VRAM)")
    else:
        print("   GPU: None detected")

    # Get recommendations
    print(f"\n🎯 Recommending models for {profile.upper()} profile...")
    recommender = ModelRecommender()
    recommendation = recommender.get_recommendation(profile)

    print(f"\n📋 Recommended Models:")
    print(f"   Tagging:     {recommendation.tagging_model}")
    print(f"   Detection:   {recommendation.detection_model}")
    print(f"   Captioning:  {recommendation.captioning_model}")

    print(f"\n💡 {recommendation.reasoning}")

    # Ask user if they want to download (demo only)
    print(f"\n❓ In the actual GUI, you would see:")
    print(f"   'Detected GPU: {gpu['name'] if summary['gpus'] else 'None'} "
          f"({gpu['memory_gb'] if summary['gpus'] else 0} GB VRAM).")
    print("   Recommended models: "
          f"{recommendation.tagging_model.split('/')[-1]}, "
          f"{recommendation.detection_model.split('/')[-1]}, "
          f"{recommendation.captioning_model.split('/')[-1]}.")
    print("   Do you want to download these now?'")

    print(f"\n🔗 Download URLs:")
    for model_type, url in recommendation.download_urls.items():
        print(f"   {model_type}: {url}")

    print(f"\n✅ Demo completed! Use 'Setup → Hardware & AI Models' in the GUI to download models.")

if __name__ == "__main__":
    main()