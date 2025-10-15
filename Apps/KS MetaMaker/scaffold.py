import os

# Base directory (current directory)
base_dir = "."

# Define the folder structure as a dictionary
# Keys are directory paths, values are lists of files or subdirs
structure = {
    "app": ["main.py", "ui", "widgets", "qss", "icons"],
    "ks_metamaker": ["__init__.py", "ingest.py", "classify.py", "tagger.py", "rename.py", "organize.py", "export.py", "quality.py", "utils", "registry"],
    "ks_metamaker/utils": ["hash_tools.py", "image_ops.py", "textclean.py", "logging.py", "config.py"],
    "ks_metamaker/registry": ["model_loader.py", "tag_templates.yml"],
    "models": ["openclip_vith14.onnx", "yolov11.onnx", "blip2.onnx"],
    "configs": ["config.yml", "presets"],
    "configs/presets": ["props.yml", "backgrounds.yml", "characters.yml"],
    "output": ["Run_YYYYMMDD_HHMM"],
    "output/Run_YYYYMMDD_HHMM": ["Props", "Backgrounds", "Characters", "metadata.json", "tags_summary.csv", "logs"],
    "tests": ["test_tagger.py", "test_rename.py", "test_quality.py", "data"],
    "scripts": ["download_models.py", "demo_run.sh", "bench.py"],
    "samples": [],
}

# Root level files
root_files = ["README.md", "pyproject.toml"]

def create_structure():
    # Create directories and files
    for dir_path, items in structure.items():
        full_dir_path = os.path.join(base_dir, dir_path)
        os.makedirs(full_dir_path, exist_ok=True)
        print(f"Created directory: {full_dir_path}")
        
        for item in items:
            full_item_path = os.path.join(full_dir_path, item)
            if "." in item:  # It's a file
                with open(full_item_path, 'w') as f:
                    f.write("")  # Create empty file
                print(f"Created file: {full_item_path}")
            else:  # It's a subdirectory
                os.makedirs(full_item_path, exist_ok=True)
                print(f"Created subdirectory: {full_item_path}")
    
    # Create root level files
    for file in root_files:
        full_file_path = os.path.join(base_dir, file)
        with open(full_file_path, 'w') as f:
            f.write("")
        print(f"Created file: {full_file_path}")

if __name__ == "__main__":
    create_structure()
    print("Scaffolding complete!")