#!/usr/bin/env python3
"""
Test script to create default profiles
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ks_metamaker.profile_manager import get_profile_manager

def main():
    print("Creating default profiles...")
    pm = get_profile_manager()
    print(f"Profiles directory: {pm.profiles_dir}")
    pm.create_default_profiles()
    print("Default profiles created successfully!")

    # List created profiles
    profiles = pm.list_profiles()
    print(f"Available profiles: {profiles}")

if __name__ == "__main__":
    main()