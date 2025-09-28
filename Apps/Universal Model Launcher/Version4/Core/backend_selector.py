"""
Backend Selector Component - Smart Backend Choice (SOLID: Single Responsibility)

This component acts as the "coach" determining the optimal backend for each model.

🎯 Single Responsibility: Intelligent backend selection and model format detection
🏈 Core Function: Analyze model characteristics and select optimal inference backend
📊 Success Metrics: Accurate format detection, optimal performance selection, zero failed loads
"""

import os
import json
import logging
import mimetypes
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import hashlib

logger = logging.getLogger(__name__)

class ModelFormat(Enum):
    """Supported model formats (inspired by KoboldCpp's format detection)."""
    GGUF = "gguf"
    GGML = "ggml"  # Legacy support
    SAFETENSORS = "safetensors"
    PYTORCH = "pytorch"
    HUGGINGFACE = "huggingface"
    UNKNOWN = "unknown"

class BackendType(Enum):
    """Available backend types (inspired by Text Generation WebUI loaders)."""
    LLAMA_CPP = "llama.cpp"
    TRANSFORMERS = "transformers"
    KOBOLDCPP = "koboldcpp"
    TEXT_GEN_WEBUI = "text-generation-webui"
    EXLLAMAV2 = "exllamav2"
    AUTO = "auto"

@dataclass
class ModelCharacteristics:
    """Model characteristics for backend selection."""
    format: ModelFormat
    size_gb: float
    architecture: Optional[str] = None
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    parameter_count: Optional[str] = None
    requires_gpu: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BackendCapability:
    """Backend capability matrix (inspired by Text Generation WebUI loaders_and_params)."""
    backend: BackendType
    supported_formats: List[ModelFormat]
    max_model_size_gb: Optional[float] = None
    gpu_acceleration: bool = False
    cpu_inference: bool = True
    quantization_support: List[str] = field(default_factory=list)
    performance_score: int = 1  # 1-10 scale
    memory_efficiency: int = 1  # 1-10 scale
    features: List[str] = field(default_factory=list)

@dataclass
class BackendSelection:
    """Result of backend selection process."""
    backend: BackendType
    confidence: float  # 0.0 - 1.0
    reasoning: str
    model_characteristics: ModelCharacteristics
    fallback_options: List[BackendType] = field(default_factory=list)
    configuration_hints: Dict[str, Any] = field(default_factory=dict)

class BackendSelector:
    """
    SOLID Component: Smart Backend Selection
    
    Analyzes model characteristics and intelligently selects the optimal
    backend for loading and inference. Acts like a "coach" making strategic
    decisions based on available resources and model requirements.
    
    Key Responsibilities:
    - Model format detection (GGUF, SafeTensors, PyTorch, etc.)
    - Hardware capability assessment  
    - Performance optimization selection
    - Fallback option generation
    """
    
    def __init__(self):
        self._capability_matrix = self._build_capability_matrix()
        self._format_detectors = self._build_format_detectors()
        self._architecture_hints = self._load_architecture_hints()
        
    def select_backend(self, model_path: Path, preferences: Optional[Dict] = None) -> BackendSelection:
        """
        Select optimal backend for the given model.
        
        Args:
            model_path: Path to model file or directory
            preferences: User preferences for backend selection
            
        Returns:
            BackendSelection with recommended backend and reasoning
        """
        preferences = preferences or {}
        
        try:
            # 1. Analyze model characteristics
            characteristics = self._analyze_model(model_path)
            logger.info(f"Detected model: {characteristics.format.value}, {characteristics.size_gb:.1f}GB")
            
            # 2. Score all compatible backends
            backend_scores = self._score_backends(characteristics, preferences)
            
            # 3. Select best backend with confidence
            if not backend_scores:
                return self._create_fallback_selection(characteristics, "No compatible backends found")
            
            best_backend, score_info = max(backend_scores.items(), key=lambda x: x[1]['total_score'])
            
            # 4. Generate fallback options
            fallback_options = [
                backend for backend, info in sorted(backend_scores.items(), 
                                                  key=lambda x: x[1]['total_score'], reverse=True)
                if backend != best_backend and info['total_score'] > 0.3
            ][:3]  # Top 3 alternatives
            
            # 5. Generate configuration hints
            config_hints = self._generate_config_hints(best_backend, characteristics)
            
            selection = BackendSelection(
                backend=best_backend,
                confidence=score_info['total_score'],
                reasoning=score_info['reasoning'],
                model_characteristics=characteristics,
                fallback_options=fallback_options,
                configuration_hints=config_hints
            )
            
            logger.info(f"Selected backend: {best_backend.value} (confidence: {selection.confidence:.2f})")
            return selection
            
        except Exception as e:
            error_msg = f"Backend selection failed: {str(e)}"
            logger.error(error_msg)
            return self._create_fallback_selection(
                ModelCharacteristics(ModelFormat.UNKNOWN, 0.0), 
                error_msg
            )
    
    def _analyze_model(self, model_path: Path) -> ModelCharacteristics:
        """
        Analyze model characteristics (inspired by KoboldCpp's format detection).
        
        Returns:
            ModelCharacteristics with detected format and metadata
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model path not found: {model_path}")
        
        # Detect format
        model_format = self._detect_format(model_path)
        
        # Calculate size
        size_gb = self._calculate_size(model_path)
        
        # Extract metadata based on format
        metadata = self._extract_metadata(model_path, model_format)
        
        # Determine architecture and other characteristics
        architecture = self._detect_architecture(model_path, metadata)
        quantization = self._detect_quantization(model_path, metadata)
        context_length = metadata.get('context_length')
        parameter_count = metadata.get('parameter_count')
        
        # Assess GPU requirements
        requires_gpu = size_gb > 8.0 or quantization in ['fp16', 'bf16']
        
        return ModelCharacteristics(
            format=model_format,
            size_gb=size_gb,
            architecture=architecture,
            quantization=quantization,
            context_length=context_length,
            parameter_count=parameter_count,
            requires_gpu=requires_gpu,
            metadata=metadata
        )
    
    def _detect_format(self, model_path: Path) -> ModelFormat:
        """
        Detect model format (inspired by KoboldCpp's check_file_format).
        
        Returns:
            ModelFormat enum value
        """
        if model_path.is_file():
            # Single file detection
            suffix = model_path.suffix.lower()
            
            if suffix == '.gguf':
                return ModelFormat.GGUF
            elif suffix in ['.ggml', '.bin'] and 'ggml' in model_path.name.lower():
                return ModelFormat.GGML
            elif suffix == '.safetensors':
                return ModelFormat.SAFETENSORS
            elif suffix in ['.bin', '.pt', '.pth']:
                # Check if it's PyTorch format
                if self._is_pytorch_format(model_path):
                    return ModelFormat.PYTORCH
            
            # Check file header for format identification
            return self._detect_format_by_header(model_path)
        
        elif model_path.is_dir():
            # Directory-based detection (HuggingFace format)
            if (model_path / 'config.json').exists():
                return ModelFormat.HUGGINGFACE
            elif any(f.suffix == '.gguf' for f in model_path.iterdir()):
                return ModelFormat.GGUF
            elif any(f.suffix == '.safetensors' for f in model_path.iterdir()):
                return ModelFormat.SAFETENSORS
        
        return ModelFormat.UNKNOWN
    
    def _detect_format_by_header(self, model_path: Path) -> ModelFormat:
        """Detect format by reading file header (KoboldCpp pattern)."""
        try:
            with open(model_path, 'rb') as f:
                header = f.read(16)
                
                # GGUF magic number
                if header.startswith(b'GGUF'):
                    return ModelFormat.GGUF
                
                # GGML magic number  
                if header.startswith(b'ggml'):
                    return ModelFormat.GGML
                
                # SafeTensors header
                if b'safetensors' in header or header.startswith(b'<safetensors'):
                    return ModelFormat.SAFETENSORS
                
                # PyTorch pickle magic
                if header.startswith(b'PK') or header.startswith(b'\x80\x02'):
                    return ModelFormat.PYTORCH
                    
        except Exception as e:
            logger.warning(f"Failed to read file header: {e}")
        
        return ModelFormat.UNKNOWN
    
    def _score_backends(self, characteristics: ModelCharacteristics, preferences: Dict) -> Dict[BackendType, Dict]:
        """
        Score all compatible backends based on model characteristics.
        
        Returns:
            Dictionary mapping backends to their scores and reasoning
        """
        scores = {}
        
        for capability in self._capability_matrix:
            if characteristics.format not in capability.supported_formats:
                continue  # Skip incompatible backends
            
            score_info = self._calculate_backend_score(capability, characteristics, preferences)
            if score_info['total_score'] > 0:
                scores[capability.backend] = score_info
        
        return scores
    
    def _calculate_backend_score(self, capability: BackendCapability, 
                               characteristics: ModelCharacteristics, 
                               preferences: Dict) -> Dict:
        """Calculate score for a specific backend."""
        score_factors = []
        reasoning_parts = []
        
        # Format compatibility (base requirement)
        if characteristics.format in capability.supported_formats:
            score_factors.append(1.0)
            reasoning_parts.append(f"supports {characteristics.format.value}")
        else:
            return {'total_score': 0.0, 'reasoning': "incompatible format"}
        
        # Size compatibility
        if capability.max_model_size_gb and characteristics.size_gb > capability.max_model_size_gb:
            score_factors.append(0.3)  # Penalty for oversized models
            reasoning_parts.append(f"model size {characteristics.size_gb:.1f}GB exceeds limit")
        else:
            score_factors.append(1.0)
        
        # GPU requirements
        if characteristics.requires_gpu and not capability.gpu_acceleration:
            score_factors.append(0.5)  # Penalty for GPU models on CPU backends
            reasoning_parts.append("GPU model on CPU backend")
        elif characteristics.requires_gpu and capability.gpu_acceleration:
            score_factors.append(1.2)  # Bonus for proper GPU support
            reasoning_parts.append("GPU acceleration available")
        
        # Quantization support
        if characteristics.quantization:
            if characteristics.quantization in capability.quantization_support:
                score_factors.append(1.1)  # Bonus for quantization support
                reasoning_parts.append(f"supports {characteristics.quantization}")
            else:
                score_factors.append(0.8)  # Minor penalty for unsupported quantization
        
        # Performance and efficiency scores
        score_factors.append(capability.performance_score / 10.0)
        score_factors.append(capability.memory_efficiency / 10.0)
        
        # User preferences
        preferred_backend = preferences.get('backend')
        if preferred_backend and capability.backend.value == preferred_backend:
            score_factors.append(1.3)  # Strong preference bonus
            reasoning_parts.append("user preference")
        
        # Calculate final score (geometric mean for balanced scoring)
        import math
        total_score = math.prod(score_factors) ** (1.0 / len(score_factors))
        total_score = min(total_score, 1.0)  # Cap at 1.0
        
        reasoning = f"{capability.backend.value}: " + ", ".join(reasoning_parts)
        
        return {
            'total_score': total_score,
            'reasoning': reasoning,
            'factors': score_factors
        }
    
    def _build_capability_matrix(self) -> List[BackendCapability]:
        """
        Build backend capability matrix (inspired by Text Generation WebUI loaders).
        
        Returns:
            List of BackendCapability objects
        """
        return [
            # llama.cpp - Excellent for GGUF models
            BackendCapability(
                backend=BackendType.LLAMA_CPP,
                supported_formats=[ModelFormat.GGUF, ModelFormat.GGML],
                max_model_size_gb=None,  # No hard limit
                gpu_acceleration=True,
                cpu_inference=True,
                quantization_support=['q4_0', 'q4_1', 'q5_0', 'q5_1', 'q8_0', 'f16', 'f32'],
                performance_score=9,
                memory_efficiency=9,
                features=['streaming', 'grammar', 'speculative_decoding']
            ),
            
            # Transformers - Universal HuggingFace support
            BackendCapability(
                backend=BackendType.TRANSFORMERS,
                supported_formats=[ModelFormat.HUGGINGFACE, ModelFormat.SAFETENSORS, ModelFormat.PYTORCH],
                max_model_size_gb=None,
                gpu_acceleration=True,
                cpu_inference=True,
                quantization_support=['4bit', '8bit', 'fp16', 'bf16', 'fp32'],
                performance_score=7,
                memory_efficiency=6,
                features=['training', 'fine_tuning', 'pipeline_api', 'extensive_models']
            ),
            
            # KoboldCpp - Specialized for creative writing
            BackendCapability(
                backend=BackendType.KOBOLDCPP,
                supported_formats=[ModelFormat.GGUF, ModelFormat.GGML],
                max_model_size_gb=200.0,
                gpu_acceleration=True,
                cpu_inference=True,
                quantization_support=['q4_0', 'q4_1', 'q5_0', 'q5_1', 'q8_0', 'f16'],
                performance_score=8,
                memory_efficiency=8,
                features=['creative_writing', 'story_generation', 'kobold_api', 'adventure_mode']
            ),
            
            # Text Generation WebUI - Feature-rich interface
            BackendCapability(
                backend=BackendType.TEXT_GEN_WEBUI,
                supported_formats=[ModelFormat.GGUF, ModelFormat.SAFETENSORS, ModelFormat.HUGGINGFACE],
                max_model_size_gb=None,
                gpu_acceleration=True,
                cpu_inference=True,
                quantization_support=['4bit', '8bit', 'gptq', 'awq', 'exl2'],
                performance_score=8,
                memory_efficiency=7,
                features=['web_interface', 'extensions', 'multiple_backends', 'character_chat']
            ),
            
            # ExLlamaV2 - High performance for large models
            BackendCapability(
                backend=BackendType.EXLLAMAV2,
                supported_formats=[ModelFormat.SAFETENSORS, ModelFormat.HUGGINGFACE],
                max_model_size_gb=None,
                gpu_acceleration=True,
                cpu_inference=False,  # GPU-only
                quantization_support=['exl2', 'gptq', 'fp16'],
                performance_score=10,
                memory_efficiency=8,
                features=['tensor_parallelism', 'speculative_decoding', 'flash_attention']
            )
        ]
    
    def _build_format_detectors(self) -> Dict[ModelFormat, callable]:
        """Build format-specific detection functions."""
        return {
            ModelFormat.GGUF: self._detect_gguf_metadata,
            ModelFormat.HUGGINGFACE: self._detect_hf_metadata,
            ModelFormat.SAFETENSORS: self._detect_safetensors_metadata,
            ModelFormat.PYTORCH: self._detect_pytorch_metadata
        }
    
    def _load_architecture_hints(self) -> Dict[str, str]:
        """
        Load architecture detection hints (inspired by Transformers AutoConfig).
        
        Returns:
            Dictionary mapping model indicators to architectures
        """
        return {
            'llama': 'llama',
            'mistral': 'mistral', 
            'gemma': 'gemma',
            'qwen': 'qwen',
            'phi': 'phi',
            'gpt': 'gpt',
            'bert': 'bert',
            'falcon': 'falcon',
            'mpt': 'mpt',
            'codellama': 'llama',
            'vicuna': 'llama',
            'alpaca': 'llama'
        }
    
    def _extract_metadata(self, model_path: Path, model_format: ModelFormat) -> Dict[str, Any]:
        """Extract metadata based on model format."""
        detector = self._format_detectors.get(model_format)
        if detector:
            try:
                return detector(model_path)
            except Exception as e:
                logger.warning(f"Failed to extract {model_format.value} metadata: {e}")
        
        return {}
    
    def _detect_gguf_metadata(self, model_path: Path) -> Dict[str, Any]:
        """Extract GGUF metadata (simplified version of KoboldCpp's approach)."""
        metadata = {}
        try:
            # This is a simplified implementation
            # In practice, you'd use the gguf library or implement proper GGUF parsing
            metadata['format_version'] = 'gguf'
            
            # Try to parse filename for hints
            filename = model_path.name.lower()
            if 'q4' in filename:
                metadata['quantization'] = 'q4_0'
            elif 'q8' in filename:
                metadata['quantization'] = 'q8_0'
            elif 'f16' in filename:
                metadata['quantization'] = 'f16'
                
        except Exception as e:
            logger.debug(f"GGUF metadata extraction failed: {e}")
        
        return metadata
    
    def _detect_hf_metadata(self, model_path: Path) -> Dict[str, Any]:
        """Extract HuggingFace metadata from config.json."""
        metadata = {}
        try:
            config_path = model_path / 'config.json' if model_path.is_dir() else None
            if config_path and config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                metadata.update({
                    'architecture': config.get('architectures', [None])[0],
                    'model_type': config.get('model_type'),
                    'context_length': config.get('max_position_embeddings'),
                    'vocab_size': config.get('vocab_size'),
                    'hidden_size': config.get('hidden_size'),
                    'num_layers': config.get('num_hidden_layers'),
                    'torch_dtype': config.get('torch_dtype')
                })
                
        except Exception as e:
            logger.debug(f"HuggingFace metadata extraction failed: {e}")
        
        return metadata
    
    def _detect_safetensors_metadata(self, model_path: Path) -> Dict[str, Any]:
        """Extract SafeTensors metadata."""
        # Simplified implementation - would need safetensors library for full parsing
        return {'format': 'safetensors'}
    
    def _detect_pytorch_metadata(self, model_path: Path) -> Dict[str, Any]:
        """Extract PyTorch metadata."""
        # Simplified implementation - would need torch for full parsing
        return {'format': 'pytorch'}
    
    def _detect_architecture(self, model_path: Path, metadata: Dict) -> Optional[str]:
        """Detect model architecture from various sources."""
        # From metadata
        if 'architecture' in metadata:
            return metadata['architecture']
        
        if 'model_type' in metadata:
            return metadata['model_type']
        
        # From filename patterns
        filename = model_path.name.lower()
        for hint, arch in self._architecture_hints.items():
            if hint in filename:
                return arch
        
        return None
    
    def _detect_quantization(self, model_path: Path, metadata: Dict) -> Optional[str]:
        """Detect quantization type."""
        # From metadata
        if 'quantization' in metadata:
            return metadata['quantization']
        
        if 'torch_dtype' in metadata:
            return metadata['torch_dtype']
        
        # From filename
        filename = model_path.name.lower()
        quant_patterns = {
            'q4_0': ['q4_0', 'q4.0'],
            'q4_1': ['q4_1', 'q4.1'], 
            'q8_0': ['q8_0', 'q8.0'],
            'fp16': ['fp16', 'f16'],
            'fp32': ['fp32', 'f32'],
            'int8': ['int8', '8bit'],
            'int4': ['int4', '4bit']
        }
        
        for quant_type, patterns in quant_patterns.items():
            if any(pattern in filename for pattern in patterns):
                return quant_type
        
        return None
    
    def _calculate_size(self, model_path: Path) -> float:
        """Calculate model size in GB."""
        try:
            if model_path.is_file():
                return model_path.stat().st_size / (1024**3)
            elif model_path.is_dir():
                total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                return total_size / (1024**3)
        except Exception as e:
            logger.warning(f"Failed to calculate model size: {e}")
        
        return 0.0
    
    def _is_pytorch_format(self, model_path: Path) -> bool:
        """Check if file is PyTorch format."""
        try:
            # Simple heuristic - check for pickle signature
            with open(model_path, 'rb') as f:
                header = f.read(10)
                return header.startswith(b'PK') or b'\x80' in header[:4]
        except:
            return False
    
    def _generate_config_hints(self, backend: BackendType, characteristics: ModelCharacteristics) -> Dict[str, Any]:
        """Generate configuration hints for the selected backend."""
        hints = {}
        
        if backend == BackendType.LLAMA_CPP:
            hints.update({
                'n_ctx': characteristics.context_length or 2048,
                'n_gpu_layers': -1 if characteristics.requires_gpu else 0,
                'use_mmap': True,
                'use_mlock': False
            })
            
            if characteristics.size_gb > 10:
                hints['n_batch'] = 512
            else:
                hints['n_batch'] = 1024
                
        elif backend == BackendType.TRANSFORMERS:
            hints.update({
                'torch_dtype': characteristics.quantization or 'auto',
                'device_map': 'auto' if characteristics.requires_gpu else 'cpu',
                'low_cpu_mem_usage': True
            })
            
            if characteristics.size_gb > 6:
                hints['load_in_8bit'] = True
                
        elif backend == BackendType.KOBOLDCPP:
            hints.update({
                'contextsize': characteristics.context_length or 2048,
                'threads': os.cpu_count() or 4,
                'usegpu': characteristics.requires_gpu
            })
            
        return hints
    
    def _create_fallback_selection(self, characteristics: ModelCharacteristics, error_msg: str) -> BackendSelection:
        """Create a fallback selection when optimal selection fails."""
        return BackendSelection(
            backend=BackendType.AUTO,
            confidence=0.1,
            reasoning=f"Fallback selection due to: {error_msg}",
            model_characteristics=characteristics,
            fallback_options=[BackendType.LLAMA_CPP, BackendType.TRANSFORMERS],
            configuration_hints={'error': error_msg}
        )
    
    def get_supported_formats(self, backend: BackendType) -> List[ModelFormat]:
        """Get supported formats for a specific backend."""
        for capability in self._capability_matrix:
            if capability.backend == backend:
                return capability.supported_formats
        return []
    
    def get_backend_info(self, backend: BackendType) -> Optional[BackendCapability]:
        """Get detailed information about a backend."""
        for capability in self._capability_matrix:
            if capability.backend == backend:
                return capability
        return None
