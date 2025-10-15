#!/usr/bin/env python3
"""
Test script for tag normalization system
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config():
    from ks_metamaker.utils.config import Config
    c = Config.load()
    print(f'Config loaded with profile: {c.profile_name}')
    print(f'Available profiles: {c.get_available_profiles()}')
    print(f'Normalization available: {c.normalization is not None}')
    if c.normalization:
        print(f'NSFW filters: {c.normalization.taxonomy.nsfw_filters}')
        print(f'Priority tags: {c.normalization.taxonomy.priority_tags}')

def test_normalizer():
    from ks_metamaker.tag_normalizer import TagNormalizer
    from ks_metamaker.profile_manager import TagTaxonomy

    # Create a test taxonomy
    taxonomy = TagTaxonomy(
        synonyms={"car": ["automobile", "vehicle"], "building": ["structure", "edifice"]},
        categories={"car": "subject", "building": "composition"},
        nsfw_filters=["nsfw", "adult"],
        priority_tags=["car", "building"]
    )

    normalizer = TagNormalizer(taxonomy)

    # Test normalization
    test_tags = ["automobile", "structure", "nsfw", "car"]
    normalized = normalizer.normalize_tags(test_tags)

    print("Original tags:", test_tags)
    print("Normalized tags:", [tag.normalized for tag in normalized])

if __name__ == "__main__":
    print("Testing config system...")
    test_config()
    print("\nTesting normalizer...")
    test_normalizer()