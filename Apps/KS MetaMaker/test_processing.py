#!/usr/bin/env python3
"""
Test script for KS MetaMaker ProcessingWorker
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ks_metamaker.utils.config import Config
from ks_metamaker.ingest import ImageIngester
from ks_metamaker.tagger import ImageTagger
from ks_metamaker.rename import FileRenamer
from ks_metamaker.organize import FileOrganizer
from ks_metamaker.export import DatasetExporter

def test_processing_pipeline():
    """Test the full processing pipeline"""
    config = Config()
    input_dir = Path("test_input")
    output_dir = Path("test_output")

    print(f"Testing processing pipeline with input: {input_dir}, output: {output_dir}")

    try:
        # Initialize components
        ingester = ImageIngester(enable_quality_filter=False, enable_duplicate_detection=False)
        tagger = ImageTagger(config)
        renamer = FileRenamer(config)
        organizer = FileOrganizer(config, output_dir)
        exporter = DatasetExporter(config)

        # Ingest images
        print("Ingesting images...")
        print(f"Input dir exists: {input_dir.exists()}")
        if input_dir.exists():
            all_files = list(input_dir.rglob("*"))
            print(f"All files in input dir: {[str(p) for p in all_files]}")
        images = ingester.ingest(input_dir)
        print(f"Ingested {len(images)} images: {[str(p) for p in images]}")

        # Process each image
        results = {}
        for i, image_path in enumerate(images):
            print(f"\nProcessing image {i+1}/{len(images)}: {image_path}")

            # Tag image
            tags = tagger.tag(image_path)
            print(f"Tags: {tags}")

            # Rename and organize
            new_path = renamer.rename(image_path, tags)
            print(f"Renamed: {image_path.name} -> {new_path.name}")

            organized_path = organizer.organize(new_path, tags[0] if tags else "unknown")
            print(f"Organized: {new_path} -> {organized_path}")

            # Check if file was actually moved
            if organized_path.exists():
                print(f"✓ File exists at organized location: {organized_path}")
            else:
                print(f"✗ File NOT found at organized location: {organized_path}")

            # Export
            exporter.export(organized_path, tags)
            print(f"Exported data for {organized_path}")

            # Check if txt file was created
            txt_path = organized_path.with_suffix('.txt')
            if txt_path.exists():
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"✓ Created txt file: {txt_path}")
                print(f"  Content: {content}")
            else:
                print(f"✗ No txt file created at: {txt_path}")

            results[str(image_path)] = {
                'tags': tags,
                'new_path': str(organized_path)
            }

        # Finalize export
        print("\nFinalizing export...")
        exporter.finalize_export(output_dir)

        # Check for CSV file
        csv_path = output_dir / "tags_summary.csv"
        if csv_path.exists():
            print(f"✓ Created CSV file: {csv_path}")
        else:
            print(f"✗ No CSV file created at: {csv_path}")

        print(f"\nProcessing complete! Results: {results}")

    except Exception as e:
        print(f"Processing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_processing_pipeline()