"""
Model Registry Component - Smart Database (SOLID: Single Responsibility)

This component acts as the "database manager" for model discovery and metadata.

🎯 Single Responsibility: Model discovery, metadata management, and usage analytics
🗄️ Core Function: Maintain comprehensive database of available models and their performance
📊 Success Metrics: Fast discovery, accurate metadata, reliable analytics tracking
"""

import os
import json
import sqlite3
import hashlib
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
import re

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    """Model availability status."""
    AVAILABLE = "available"
    DOWNLOADED = "downloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    MISSING = "missing"
    OUTDATED = "outdated"

class ModelSource(Enum):
    """Model source types."""
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    MANUAL = "manual"
    DISCOVERED = "discovered"
    REGISTRY = "registry"

@dataclass
class ModelMetadata:
    """Comprehensive model metadata."""
    # Basic Information
    id: str
    name: str
    path: str
    format: str  # gguf, safetensors, pytorch, etc.
    source: ModelSource
    
    # Model Characteristics
    architecture: Optional[str] = None
    size_gb: Optional[float] = None
    parameter_count: Optional[str] = None
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    
    # File Information
    filename: Optional[str] = None
    file_hash: Optional[str] = None
    last_modified: Optional[datetime] = None
    verified: bool = False
    
    # Performance Data
    load_time_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    tokens_per_second: Optional[float] = None
    
    # Usage Analytics
    usage_count: int = 0
    last_used: Optional[datetime] = None
    total_runtime_seconds: float = 0.0
    
    # Backend Compatibility
    compatible_backends: List[str] = field(default_factory=list)
    recommended_backend: Optional[str] = None
    
    # User Data
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    favorite: bool = False
    
    # Discovery Data
    discovered_at: Optional[datetime] = None
    auto_discovered: bool = False
    
    # Status
    status: ModelStatus = ModelStatus.AVAILABLE
    error_message: Optional[str] = None

@dataclass
class PerformanceRecord:
    """Performance tracking record."""
    model_id: str
    backend: str
    load_time: float
    memory_usage: float
    tokens_per_second: float
    context_length: int
    timestamp: datetime
    hardware_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UsageRecord:
    """Usage analytics record."""
    model_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    backend: str = ""
    tokens_generated: int = 0
    requests_count: int = 0
    error_count: int = 0

class ModelRegistry:
    """
    SOLID Component: Smart Model Database
    
    Manages comprehensive model discovery, metadata, and analytics tracking.
    Acts like a "database administrator" maintaining the complete catalog
    of available models with their performance characteristics.
    
    Key Responsibilities:
    - Auto-discovery of models in specified directories
    - Metadata extraction and storage
    - Performance tracking and analytics
    - Usage statistics and recommendations
    """
    
    def __init__(self, registry_path: Optional[Path] = None, auto_discover: bool = True):
        self.registry_path = registry_path or Path.cwd() / "models" / "registry"
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # Storage paths
        self.db_path = self.registry_path / "models.db"
        self.metadata_path = self.registry_path / "metadata.json"
        self.analytics_path = self.registry_path / "analytics.db"
        
        # Discovery settings
        self.search_paths = []
        self.auto_discover = auto_discover
        self.discovery_patterns = self._build_discovery_patterns()
        
        # Cache and locks
        self._models_cache: Dict[str, ModelMetadata] = {}
        self._cache_lock = threading.RLock()
        self._db_lock = threading.Lock()
        
        # Initialize storage
        self._init_database()
        self._load_models_cache()
        
        if auto_discover:
            self.discover_models()
    
    def _build_discovery_patterns(self) -> Dict[str, List[str]]:
        """
        Build model discovery patterns.
        
        Returns:
            Dictionary mapping formats to file patterns
        """
        return {
            'gguf': ['*.gguf'],
            'ggml': ['*.ggml', '*.bin'],
            'safetensors': ['*.safetensors', 'model.safetensors'],
            'pytorch': ['*.pt', '*.pth', 'pytorch_model.bin'],
            'huggingface': ['config.json'],  # Directory indicator
            'transformers': ['config.json', 'pytorch_model.bin']
        }
    
    def _init_database(self) -> None:
        """Initialize SQLite databases for models and analytics."""
        try:
            # Models database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS models (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
                        format TEXT NOT NULL,
                        source TEXT NOT NULL,
                        metadata_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_models_format ON models(format)
                ''')
            
            # Analytics database
            with sqlite3.connect(self.analytics_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id TEXT NOT NULL,
                        backend TEXT NOT NULL,
                        load_time REAL,
                        memory_usage REAL,
                        tokens_per_second REAL,
                        context_length INTEGER,
                        hardware_info TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        backend TEXT,
                        tokens_generated INTEGER DEFAULT 0,
                        requests_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_performance_model ON performance(model_id)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_usage_model ON usage(model_id)
                ''')
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def add_search_path(self, path: Union[str, Path]) -> None:
        """Add a directory to search for models."""
        search_path = Path(path)
        if search_path.exists() and search_path.is_dir():
            if search_path not in self.search_paths:
                self.search_paths.append(search_path)
                logger.info(f"Added search path: {search_path}")
                
                if self.auto_discover:
                    self.discover_models([search_path])
        else:
            logger.warning(f"Search path does not exist: {search_path}")
    
    def discover_models(self, search_paths: Optional[List[Path]] = None) -> List[ModelMetadata]:
        """
        Auto-discover models in search paths.
        
        Args:
            search_paths: Optional list of paths to search
            
        Returns:
            List of newly discovered models
        """
        paths_to_search = search_paths or self.search_paths
        if not paths_to_search:
            logger.info("No search paths configured for model discovery")
            return []
        
        discovered_models = []
        
        for search_path in paths_to_search:
            if not search_path.exists():
                continue
                
            logger.info(f"Discovering models in: {search_path}")
            
            # Discover different model formats
            for format_type, patterns in self.discovery_patterns.items():
                for pattern in patterns:
                    for model_path in search_path.rglob(pattern):
                        try:
                            model_metadata = self._analyze_discovered_model(model_path, format_type)
                            if model_metadata and model_metadata.id not in self._models_cache:
                                discovered_models.append(model_metadata)
                                self.register_model(model_metadata)
                                logger.info(f"Discovered model: {model_metadata.name}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to analyze model {model_path}: {e}")
        
        logger.info(f"Discovery complete: {len(discovered_models)} new models found")
        return discovered_models
    
    def _analyze_discovered_model(self, model_path: Path, format_hint: str) -> Optional[ModelMetadata]:
        """
        Analyze discovered model file/directory.
        
        Args:
            model_path: Path to model file or directory
            format_hint: Hint about the model format
            
        Returns:
            ModelMetadata if analysis successful
        """
        try:
            # Generate unique ID
            model_id = self._generate_model_id(model_path)
            
            # Basic information
            if model_path.is_file():
                name = model_path.stem
                size_gb = model_path.stat().st_size / (1024**3)
                filename = model_path.name
            else:
                name = model_path.name
                size_gb = self._calculate_directory_size(model_path)
                filename = None
            
            # Extract metadata based on format
            metadata = self._extract_model_metadata(model_path, format_hint)
            
            # Create model metadata
            model_metadata = ModelMetadata(
                id=model_id,
                name=name,
                path=str(model_path),
                format=self._detect_actual_format(model_path, format_hint),
                source=ModelSource.DISCOVERED,
                size_gb=size_gb,
                filename=filename,
                file_hash=self._calculate_file_hash(model_path) if model_path.is_file() else None,
                last_modified=datetime.fromtimestamp(model_path.stat().st_mtime),
                discovered_at=datetime.now(),
                auto_discovered=True,
                status=ModelStatus.AVAILABLE,
                **metadata
            )
            
            return model_metadata
            
        except Exception as e:
            logger.error(f"Failed to analyze model {model_path}: {e}")
            return None
    
    def _extract_model_metadata(self, model_path: Path, format_hint: str) -> Dict[str, Any]:
        """Extract format-specific metadata."""
        metadata = {}
        
        try:
            if format_hint == 'huggingface' and model_path.is_dir():
                # HuggingFace model directory
                config_path = model_path / 'config.json'
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    metadata.update({
                        'architecture': config.get('architectures', [None])[0],
                        'context_length': config.get('max_position_embeddings'),
                        'parameter_count': self._estimate_parameters(config),
                        'quantization': config.get('torch_dtype', 'unknown')
                    })
                    
            elif format_hint in ['gguf', 'ggml'] and model_path.is_file():
                # GGUF/GGML models - extract from filename
                filename = model_path.name.lower()
                
                # Extract quantization
                if 'q4_0' in filename:
                    metadata['quantization'] = 'q4_0'
                elif 'q4_1' in filename:
                    metadata['quantization'] = 'q4_1'
                elif 'q8_0' in filename:
                    metadata['quantization'] = 'q8_0'
                elif 'f16' in filename:
                    metadata['quantization'] = 'f16'
                
                # Extract architecture hints
                for arch_hint in ['llama', 'mistral', 'gemma', 'qwen', 'phi']:
                    if arch_hint in filename:
                        metadata['architecture'] = arch_hint
                        break
                
                # Extract parameter count
                param_match = re.search(r'(\d+)b', filename)
                if param_match:
                    metadata['parameter_count'] = f"{param_match.group(1)}B"
                    
        except Exception as e:
            logger.debug(f"Metadata extraction failed for {model_path}: {e}")
        
        return metadata
    
    def register_model(self, model_metadata: ModelMetadata) -> bool:
        """
        Register a model in the registry.
        
        Args:
            model_metadata: Model metadata to register
            
        Returns:
            True if registration successful
        """
        try:
            with self._cache_lock:
                # Update cache
                self._models_cache[model_metadata.id] = model_metadata
                
                # Save to database
                with self._db_lock:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute('''
                            INSERT OR REPLACE INTO models 
                            (id, name, path, format, source, metadata_json, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            model_metadata.id,
                            model_metadata.name,
                            model_metadata.path,
                            model_metadata.format,
                            model_metadata.source.value,
                            json.dumps(asdict(model_metadata), default=str),
                            datetime.now().isoformat()
                        ))
                
                # Save cache to JSON
                self._save_models_cache()
                
                logger.info(f"Registered model: {model_metadata.name} ({model_metadata.id})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to register model {model_metadata.name}: {e}")
            return False
    
    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID."""
        with self._cache_lock:
            return self._models_cache.get(model_id)
    
    def list_models(self, 
                   format_filter: Optional[str] = None,
                   status_filter: Optional[ModelStatus] = None,
                   source_filter: Optional[ModelSource] = None) -> List[ModelMetadata]:
        """
        List models with optional filtering.
        
        Args:
            format_filter: Filter by model format
            status_filter: Filter by model status
            source_filter: Filter by model source
            
        Returns:
            List of matching models
        """
        with self._cache_lock:
            models = list(self._models_cache.values())
            
            if format_filter:
                models = [m for m in models if m.format == format_filter]
            
            if status_filter:
                models = [m for m in models if m.status == status_filter]
            
            if source_filter:
                models = [m for m in models if m.source == source_filter]
            
            return sorted(models, key=lambda x: x.last_used or datetime.min, reverse=True)
    
    def search_models(self, query: str) -> List[ModelMetadata]:
        """
        Search models by name, tags, or notes.
        
        Args:
            query: Search query
            
        Returns:
            List of matching models
        """
        query = query.lower()
        results = []
        
        with self._cache_lock:
            for model in self._models_cache.values():
                if (query in model.name.lower() or
                    any(query in tag.lower() for tag in model.tags) or
                    (model.notes and query in model.notes.lower()) or
                    (model.architecture and query in model.architecture.lower())):
                    results.append(model)
        
        return sorted(results, key=lambda x: x.usage_count, reverse=True)
    
    def update_model_status(self, model_id: str, status: ModelStatus, error_message: Optional[str] = None) -> bool:
        """Update model status."""
        model = self.get_model(model_id)
        if not model:
            return False
        
        model.status = status
        model.error_message = error_message
        
        return self.register_model(model)
    
    def record_performance(self, performance_record: PerformanceRecord) -> None:
        """
        Record model performance data.
        
        Args:
            performance_record: Performance data to record
        """
        try:
            with sqlite3.connect(self.analytics_path) as conn:
                conn.execute('''
                    INSERT INTO performance 
                    (model_id, backend, load_time, memory_usage, tokens_per_second, 
                     context_length, hardware_info, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    performance_record.model_id,
                    performance_record.backend,
                    performance_record.load_time,
                    performance_record.memory_usage,
                    performance_record.tokens_per_second,
                    performance_record.context_length,
                    json.dumps(performance_record.hardware_info),
                    performance_record.timestamp.isoformat()
                ))
            
            # Update model metadata with latest performance
            model = self.get_model(performance_record.model_id)
            if model:
                model.load_time_seconds = performance_record.load_time
                model.memory_usage_mb = performance_record.memory_usage
                model.tokens_per_second = performance_record.tokens_per_second
                self.register_model(model)
                
        except Exception as e:
            logger.error(f"Failed to record performance: {e}")
    
    def record_usage_start(self, model_id: str, session_id: str, backend: str) -> None:
        """Record the start of a model usage session."""
        try:
            usage_record = UsageRecord(
                model_id=model_id,
                session_id=session_id,
                start_time=datetime.now(),
                backend=backend
            )
            
            with sqlite3.connect(self.analytics_path) as conn:
                conn.execute('''
                    INSERT INTO usage 
                    (model_id, session_id, start_time, backend)
                    VALUES (?, ?, ?, ?)
                ''', (
                    usage_record.model_id,
                    usage_record.session_id,
                    usage_record.start_time.isoformat(),
                    usage_record.backend
                ))
            
            # Update model metadata
            model = self.get_model(model_id)
            if model:
                model.usage_count += 1
                model.last_used = datetime.now()
                self.register_model(model)
                
        except Exception as e:
            logger.error(f"Failed to record usage start: {e}")
    
    def record_usage_end(self, session_id: str, tokens_generated: int = 0, 
                        requests_count: int = 0, error_count: int = 0) -> None:
        """Record the end of a model usage session."""
        try:
            with sqlite3.connect(self.analytics_path) as conn:
                cursor = conn.execute('''
                    SELECT model_id, start_time FROM usage 
                    WHERE session_id = ? AND end_time IS NULL
                    ORDER BY start_time DESC LIMIT 1
                ''', (session_id,))
                
                result = cursor.fetchone()
                if result:
                    model_id, start_time_str = result
                    start_time = datetime.fromisoformat(start_time_str)
                    end_time = datetime.now()
                    runtime = (end_time - start_time).total_seconds()
                    
                    conn.execute('''
                        UPDATE usage SET 
                        end_time = ?, tokens_generated = ?, 
                        requests_count = ?, error_count = ?
                        WHERE session_id = ? AND end_time IS NULL
                    ''', (
                        end_time.isoformat(),
                        tokens_generated,
                        requests_count,
                        error_count,
                        session_id
                    ))
                    
                    # Update model total runtime
                    model = self.get_model(model_id)
                    if model:
                        model.total_runtime_seconds += runtime
                        self.register_model(model)
                
        except Exception as e:
            logger.error(f"Failed to record usage end: {e}")
    
    def get_performance_analytics(self, model_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get performance analytics for a model.
        
        Args:
            model_id: Model ID
            days: Number of days to analyze
            
        Returns:
            Performance analytics dictionary
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.analytics_path) as conn:
                # Performance stats
                cursor = conn.execute('''
                    SELECT backend, AVG(load_time), AVG(memory_usage), AVG(tokens_per_second),
                           COUNT(*) as test_count
                    FROM performance 
                    WHERE model_id = ? AND timestamp > ?
                    GROUP BY backend
                ''', (model_id, cutoff_date.isoformat()))
                
                performance_by_backend = {}
                for row in cursor.fetchall():
                    backend, avg_load, avg_memory, avg_tps, count = row
                    performance_by_backend[backend] = {
                        'avg_load_time': avg_load,
                        'avg_memory_usage': avg_memory,
                        'avg_tokens_per_second': avg_tps,
                        'test_count': count
                    }
                
                # Usage stats
                cursor = conn.execute('''
                    SELECT COUNT(*) as sessions, SUM(tokens_generated) as total_tokens,
                           SUM(requests_count) as total_requests, SUM(error_count) as total_errors
                    FROM usage 
                    WHERE model_id = ? AND start_time > ?
                ''', (model_id, cutoff_date.isoformat()))
                
                usage_stats = cursor.fetchone()
                
                return {
                    'model_id': model_id,
                    'period_days': days,
                    'performance_by_backend': performance_by_backend,
                    'usage_stats': {
                        'sessions': usage_stats[0] or 0,
                        'total_tokens': usage_stats[1] or 0,
                        'total_requests': usage_stats[2] or 0,
                        'total_errors': usage_stats[3] or 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get analytics for {model_id}: {e}")
            return {}
    
    def get_popular_models(self, limit: int = 10) -> List[ModelMetadata]:
        """Get most popular models by usage count."""
        with self._cache_lock:
            models = list(self._models_cache.values())
            return sorted(models, key=lambda x: x.usage_count, reverse=True)[:limit]
    
    def get_recommended_models(self, format_preference: Optional[str] = None) -> List[ModelMetadata]:
        """
        Get recommended models based on performance and usage.
        
        Args:
            format_preference: Preferred model format
            
        Returns:
            List of recommended models
        """
        models = self.list_models(format_filter=format_preference)
        
        # Score models based on multiple factors
        scored_models = []
        for model in models:
            score = 0
            
            # Usage popularity (40% weight)
            if model.usage_count > 0:
                score += model.usage_count * 0.4
            
            # Performance (30% weight)
            if model.tokens_per_second:
                score += (model.tokens_per_second / 50.0) * 0.3  # Normalize around 50 tps
            
            # Reliability (20% weight)
            if model.status == ModelStatus.AVAILABLE:
                score += 20
            
            # Recency (10% weight)
            if model.last_used:
                days_since_use = (datetime.now() - model.last_used).days
                score += max(0, 10 - days_since_use) * 0.1
            
            scored_models.append((model, score))
        
        # Sort by score and return top models
        scored_models.sort(key=lambda x: x[1], reverse=True)
        return [model for model, score in scored_models[:10]]
    
    def _generate_model_id(self, model_path: Path) -> str:
        """Generate unique model ID from path."""
        path_str = str(model_path.absolute())
        return hashlib.md5(path_str.encode()).hexdigest()[:16]
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file (GPT4All pattern)."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _calculate_directory_size(self, dir_path: Path) -> float:
        """Calculate total size of directory in GB."""
        try:
            total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
            return total_size / (1024**3)
        except Exception:
            return 0.0
    
    def _detect_actual_format(self, model_path: Path, format_hint: str) -> str:
        """Detect the actual model format."""
        if model_path.is_file():
            suffix = model_path.suffix.lower()
            if suffix == '.gguf':
                return 'gguf'
            elif suffix == '.safetensors':
                return 'safetensors'
            elif suffix in ['.pt', '.pth']:
                return 'pytorch'
            elif suffix == '.bin':
                # Could be GGML or PyTorch
                return 'ggml' if 'ggml' in model_path.name.lower() else 'pytorch'
        elif model_path.is_dir():
            if (model_path / 'config.json').exists():
                return 'huggingface'
        
        return format_hint
    
    def _estimate_parameters(self, config: Dict) -> str:
        """Estimate parameter count from model config."""
        try:
            vocab_size = config.get('vocab_size', 32000)
            hidden_size = config.get('hidden_size', 4096)
            num_layers = config.get('num_hidden_layers', 32)
            
            # Rough estimation
            embedding_params = vocab_size * hidden_size
            layer_params = num_layers * (hidden_size * hidden_size * 8)  # Simplified
            total_params = (embedding_params + layer_params) / 1e9
            
            if total_params > 50:
                return f"{int(total_params)}B"
            elif total_params > 1:
                return f"{total_params:.1f}B"
            else:
                return f"{int(total_params * 1000)}M"
                
        except Exception:
            return "unknown"
    
    def _load_models_cache(self) -> None:
        """Load models cache from storage."""
        try:
            # Load from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT metadata_json FROM models')
                for (metadata_json,) in cursor.fetchall():
                    model_data = json.loads(metadata_json)
                    
                    # Convert datetime strings back to datetime objects
                    for date_field in ['last_modified', 'last_used', 'discovered_at']:
                        if model_data.get(date_field):
                            model_data[date_field] = datetime.fromisoformat(model_data[date_field])
                    
                    # Convert enums
                    model_data['source'] = ModelSource(model_data['source'])
                    model_data['status'] = ModelStatus(model_data['status'])
                    
                    model = ModelMetadata(**model_data)
                    self._models_cache[model.id] = model
                    
            logger.info(f"Loaded {len(self._models_cache)} models from cache")
            
        except Exception as e:
            logger.warning(f"Failed to load models cache: {e}")
    
    def _save_models_cache(self) -> None:
        """Save models cache to JSON file."""
        try:
            cache_data = {}
            for model_id, model in self._models_cache.items():
                cache_data[model_id] = asdict(model)
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.warning(f"Failed to save models cache: {e}")
    
    def export_registry(self, export_path: Path) -> bool:
        """Export complete registry to a file."""
        try:
            export_data = {
                'metadata': {model_id: asdict(model) for model_id, model in self._models_cache.items()},
                'export_time': datetime.now().isoformat(),
                'total_models': len(self._models_cache)
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Registry exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export registry: {e}")
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics."""
        with self._cache_lock:
            models = list(self._models_cache.values())
            
            # Format distribution
            format_counts = {}
            for model in models:
                format_counts[model.format] = format_counts.get(model.format, 0) + 1
            
            # Source distribution
            source_counts = {}
            for model in models:
                source_counts[model.source.value] = source_counts.get(model.source.value, 0) + 1
            
            # Status distribution
            status_counts = {}
            for model in models:
                status_counts[model.status.value] = status_counts.get(model.status.value, 0) + 1
            
            # Size statistics
            sizes = [m.size_gb for m in models if m.size_gb is not None]
            
            return {
                'total_models': len(models),
                'format_distribution': format_counts,
                'source_distribution': source_counts,
                'status_distribution': status_counts,
                'size_statistics': {
                    'total_gb': sum(sizes),
                    'average_gb': sum(sizes) / len(sizes) if sizes else 0,
                    'largest_gb': max(sizes) if sizes else 0,
                    'smallest_gb': min(sizes) if sizes else 0
                },
                'usage_statistics': {
                    'total_usage_count': sum(m.usage_count for m in models),
                    'total_runtime_hours': sum(m.total_runtime_seconds for m in models) / 3600,
                    'most_used_model': max(models, key=lambda x: x.usage_count).name if models else None
                }
            }
