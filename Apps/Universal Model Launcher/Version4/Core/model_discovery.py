"""
🔍 Model Discovery System
=========================
Role: Discover and catalog AI models from configured locations
SOLID: Single responsibility for model discovery and cataloging
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging
from dataclasses import dataclass, asdict

from .configuration_manager import get_config_manager

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredModel:
    """📋 Information about a discovered model"""
    name: str
    path: str
    size_bytes: int
    file_type: str
    backend_type: str
    model_type: str  # text, vision, audio, code
    parameters: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ModelDiscovery:
    """
    🔍 AI Model Discovery System
    ============================
    Role: Find and catalog models from configured directories
    Pattern: Configurable discovery with intelligent classification
    """
    
    def __init__(self):
        self.config = get_config_manager()
        self.discovered_models: Dict[str, DiscoveredModel] = {}
        self.model_database_path = Path("./models/discovered_models.json")
        self._ensure_database_directory()
    
    def _ensure_database_directory(self):
        """📁 Ensure model database directory exists"""
        self.model_database_path.parent.mkdir(parents=True, exist_ok=True)
    
    def discover_models(self, force_rescan: bool = False) -> Dict[str, DiscoveredModel]:
        """🔍 Discover models from configured locations"""
        logger.info("🔍 Starting model discovery...")
        
        if not force_rescan and self._load_cached_models():
            logger.info("✅ Using cached model discovery results")
            return self.discovered_models
        
        self.discovered_models.clear()
        
        # Get scan directories from configuration
        scan_directories = self.config.get_expanded_scan_directories()
        file_extensions = self.config.get_file_extensions()
        
        logger.info(f"📂 Scanning directories: {scan_directories}")
        logger.info(f"📄 Looking for extensions: {file_extensions}")
        
        # Scan each directory
        for directory in scan_directories:
            self._scan_directory(directory, file_extensions)
        
        # Add custom model locations
        self._add_custom_models()
        
        # Save discovered models to cache
        self._save_cached_models()
        
        logger.info(f"✅ Discovery complete: Found {len(self.discovered_models)} models")
        return self.discovered_models
    
    def _scan_directory(self, directory: str, extensions: List[str]):
        """📂 Scan a directory for model files"""
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                logger.debug(f"📂 Directory not found: {directory}")
                return
            
            logger.info(f"📂 Scanning: {directory}")
            
            # Get scanning configuration
            config = self.config.get_config_section("model_discovery")
            recursive = config.get("recursive_scan", True)
            max_depth = config.get("scan_depth", 3)
            ignore_dirs = set(config.get("ignore_directories", ["__pycache__", ".git"]))
            
            if recursive:
                self._scan_recursive(directory_path, extensions, ignore_dirs, max_depth, 0)
            else:
                self._scan_single_directory(directory_path, extensions)
                
        except Exception as e:
            logger.error(f"❌ Error scanning directory {directory}: {e}")
    
    def _scan_recursive(self, directory: Path, extensions: List[str], 
                       ignore_dirs: Set[str], max_depth: int, current_depth: int):
        """🔄 Recursively scan directory"""
        if current_depth >= max_depth:
            return
        
        try:
            for item in directory.iterdir():
                if item.is_dir() and item.name not in ignore_dirs:
                    self._scan_recursive(item, extensions, ignore_dirs, max_depth, current_depth + 1)
                elif item.is_file():
                    self._check_file(item, extensions)
        except PermissionError:
            logger.debug(f"⚠️ Permission denied: {directory}")
        except Exception as e:
            logger.debug(f"⚠️ Error scanning {directory}: {e}")
    
    def _scan_single_directory(self, directory: Path, extensions: List[str]):
        """📁 Scan single directory (non-recursive)"""
        try:
            for item in directory.iterdir():
                if item.is_file():
                    self._check_file(item, extensions)
        except Exception as e:
            logger.debug(f"⚠️ Error scanning {directory}: {e}")
    
    def _check_file(self, file_path: Path, extensions: List[str]):
        """📄 Check if file is a valid model"""
        try:
            # Check file extension
            if not any(file_path.name.lower().endswith(ext.lower()) for ext in extensions):
                return
            
            # Skip if already discovered
            if str(file_path) in [model.path for model in self.discovered_models.values()]:
                return
            
            # Get file information
            file_size = file_path.stat().st_size
            
            # Classify the model
            model_info = self._classify_model(file_path)
            
            # Create discovered model entry
            discovered_model = DiscoveredModel(
                name=model_info["name"],
                path=str(file_path),
                size_bytes=file_size,
                file_type=file_path.suffix.lower(),
                backend_type=model_info["backend"],
                model_type=model_info["type"],
                parameters=model_info.get("parameters"),
                description=model_info.get("description"),
                tags=model_info.get("tags", [])
            )
            
            # Add to discovered models
            self.discovered_models[discovered_model.name] = discovered_model
            logger.debug(f"📋 Discovered: {discovered_model.name} ({file_size // (1024*1024)} MB)")
            
        except Exception as e:
            logger.debug(f"⚠️ Error checking file {file_path}: {e}")
    
    def _classify_model(self, file_path: Path) -> Dict[str, str]:
        """🏷️ Classify model based on filename and path"""
        filename = file_path.name.lower()
        path_str = str(file_path).lower()
        
        # Determine model type from filename patterns
        model_type = "text"  # Default
        backend_type = "llama.cpp"  # Default
        parameters = None
        description = None
        tags = []
        
        # Model type classification
        if any(term in filename for term in ["clip", "vision", "vit", "bakllava", "moondream"]):
            model_type = "vision"
            tags.append("multimodal")
        elif any(term in filename for term in ["whisper", "audio", "speech"]):
            model_type = "audio"
            tags.append("transcription")
        elif any(term in filename for term in ["code", "llama", "starcoder", "codellama"]):
            model_type = "code"
            tags.append("programming")
        
        # Backend classification
        if filename.endswith(('.gguf', '.ggml')):
            backend_type = "llama.cpp"
        elif any(term in path_str for term in ["transformers", "hf", "huggingface"]):
            backend_type = "transformers"
        elif "whisper" in filename and not filename.endswith('.gguf'):
            backend_type = "whisper.cpp"
        
        # Parameter size detection
        param_patterns = ["7b", "13b", "30b", "65b", "70b", "8b", "3b", "1b", "2b"]
        for pattern in param_patterns:
            if pattern in filename:
                parameters = pattern.upper()
                break
        
        # Generate description
        model_name = file_path.stem
        if parameters:
            description = f"{parameters} parameter {model_type} model"
        else:
            description = f"{model_type.title()} model"
        
        # Add quality tags based on filename
        if any(term in filename for term in ["instruct", "chat", "it"]):
            tags.append("instruction-tuned")
        if any(term in filename for term in ["q4", "q5", "q8"]):
            tags.append("quantized")
        
        return {
            "name": model_name,
            "type": model_type,
            "backend": backend_type,
            "parameters": parameters,
            "description": description,
            "tags": tags
        }
    
    def _add_custom_models(self):
        """📍 Add custom model locations from configuration"""
        custom_locations = self.config.get_config_section("model_paths").get("custom_locations", {})
        
        for model_name, model_path in custom_locations.items():
            if not model_path:
                continue
            
            expanded_path = self.config.expand_path(model_path)
            path_obj = Path(expanded_path)
            
            if path_obj.exists():
                # Check if already discovered
                if model_name not in self.discovered_models:
                    try:
                        file_size = path_obj.stat().st_size if path_obj.is_file() else 0
                        model_info = self._classify_model(path_obj)
                        
                        discovered_model = DiscoveredModel(
                            name=model_name,
                            path=expanded_path,
                            size_bytes=file_size,
                            file_type=path_obj.suffix.lower() if path_obj.is_file() else "directory",
                            backend_type=model_info["backend"],
                            model_type=model_info["type"],
                            parameters=model_info.get("parameters"),
                            description=f"Custom: {model_info.get('description', '')}",
                            tags=model_info.get("tags", []) + ["custom"]
                        )
                        
                        self.discovered_models[model_name] = discovered_model
                        logger.info(f"📍 Added custom model: {model_name}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error adding custom model {model_name}: {e}")
            else:
                logger.warning(f"⚠️ Custom model path not found: {model_name} -> {expanded_path}")
    
    def _load_cached_models(self) -> bool:
        """📥 Load cached model discovery results"""
        try:
            if self.model_database_path.exists():
                with open(self.model_database_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                self.discovered_models = {}
                for name, model_data in cached_data.items():
                    self.discovered_models[name] = DiscoveredModel(**model_data)
                
                logger.info(f"📥 Loaded {len(self.discovered_models)} models from cache")
                return True
        except Exception as e:
            logger.debug(f"⚠️ Failed to load cached models: {e}")
        
        return False
    
    def _save_cached_models(self):
        """💾 Save discovered models to cache"""
        try:
            cached_data = {}
            for name, model in self.discovered_models.items():
                cached_data[name] = asdict(model)
            
            with open(self.model_database_path, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved {len(self.discovered_models)} models to cache")
        except Exception as e:
            logger.error(f"❌ Failed to save model cache: {e}")
    
    def get_models_by_type(self, model_type: str) -> List[DiscoveredModel]:
        """🏷️ Get models filtered by type"""
        return [model for model in self.discovered_models.values() if model.model_type == model_type]
    
    def get_models_by_backend(self, backend: str) -> List[DiscoveredModel]:
        """🔧 Get models filtered by backend"""
        return [model for model in self.discovered_models.values() if model.backend_type == backend]
    
    def search_models(self, query: str) -> List[DiscoveredModel]:
        """🔍 Search models by name or description"""
        query_lower = query.lower()
        results = []
        
        for model in self.discovered_models.values():
            if (query_lower in model.name.lower() or 
                (model.description and query_lower in model.description.lower()) or
                any(query_lower in tag.lower() for tag in model.tags)):
                results.append(model)
        
        return results
    
    def add_scan_directory_interactive(self, directory: str) -> bool:
        """📂 Add new scan directory and rescan"""
        try:
            expanded_dir = self.config.expand_path(directory)
            if Path(expanded_dir).exists():
                self.config.add_scan_directory(directory)
                logger.info(f"✅ Added scan directory: {directory}")
                return True
            else:
                logger.warning(f"⚠️ Directory does not exist: {expanded_dir}")
                return False
        except Exception as e:
            logger.error(f"❌ Error adding scan directory: {e}")
            return False
    
    def get_model_stats(self) -> Dict[str, any]:
        """📊 Get statistics about discovered models"""
        total_models = len(self.discovered_models)
        total_size = sum(model.size_bytes for model in self.discovered_models.values())
        
        type_counts = {}
        backend_counts = {}
        
        for model in self.discovered_models.values():
            type_counts[model.model_type] = type_counts.get(model.model_type, 0) + 1
            backend_counts[model.backend_type] = backend_counts.get(model.backend_type, 0) + 1
        
        return {
            "total_models": total_models,
            "total_size_gb": total_size / (1024**3),
            "types": type_counts,
            "backends": backend_counts
        }
    
    def discover_all_models(self):
        """🔍 GUI-compatible method to discover all models"""
        # Discover models with force rescan to get fresh data
        models = self.discover_models(force_rescan=False)
        
        # Convert to GUI-friendly format
        model_list = []
        for model_id, model in models.items():
            model_list.append({
                'id': model_id,
                'name': model.name,
                'path': model.path,
                'type': model.model_type,
                'backend': model.backend_type,
                'size_gb': round(model.size_bytes / (1024**3), 2),
                'parameters': model.parameters or 'Unknown',
                'tags': model.tags
            })
        
        return {
            'models': model_list,
            'count': len(model_list),
            'total_size_gb': sum(m['size_gb'] for m in model_list)
        }
