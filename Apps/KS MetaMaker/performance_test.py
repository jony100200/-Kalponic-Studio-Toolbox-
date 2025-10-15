#!/usr/bin/env python3
"""
KS MetaMaker Performance Test
"""
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_performance():
    print("=== KS MetaMaker Performance Test ===\n")

    # Test 1: Basic file discovery
    print("1. File Discovery Test:")
    test_dir = Path('samples')
    start_time = time.time()
    images = list(test_dir.glob('*.png'))
    discover_time = time.time() - start_time
    print(f"   Found {len(images)} PNG files in {discover_time:.3f}s")

    # Test 2: Import times
    print("\n2. Import Performance:")
    start_time = time.time()
    from ks_metamaker.quality import QualityAssessor
    import_time = time.time() - start_time
    print(f"   QualityAssessor import: {import_time:.3f}s")

    start_time = time.time()
    from ks_metamaker.tagger import ImageTagger
    import_time = time.time() - start_time
    print(f"   ImageTagger import: {import_time:.3f}s")

    # Test 3: Quality assessment
    print("\n3. Quality Assessment Test:")
    assessor = QualityAssessor()
    if images:
        img_path = images[0]
        print(f"   Testing on: {img_path.name}")
        start_time = time.time()
        quality = assessor.assess_quality(img_path)
        assess_time = time.time() - start_time
        score = quality.get('quality_score', 'N/A')
        print(f"   Assessment time: {assess_time:.3f}s")
        print(f"   Quality score: {score}")

    # Test 4: Memory usage estimate
    print("\n4. System Requirements:")
    import psutil
    import os

    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"   Current memory usage: {memory_mb:.1f} MB")

    # Disk space check
    import shutil
    total, used, free = shutil.disk_usage(".")
    free_gb = free / (1024**3)
    print(f"   Free disk space: {free_gb:.1f} GB")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_performance()