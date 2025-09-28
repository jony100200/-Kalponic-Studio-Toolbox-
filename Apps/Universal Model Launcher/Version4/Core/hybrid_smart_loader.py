"""
🏃‍♂️ Hybrid Smart Model Loader - Main System
Role: "Smart Orchestrator" - Coordinates all components for automatic model selection
SOLID Principle: Single Responsibility - High-level workflow coordination
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from .input_router import InputRouter, TaskType, InputAnalysis
from .hardware_detector import HardwareDetector
from .model_selector import ModelSelector, ModelRecommendation, ModelSize
from .model_registry import ModelRegistry, ModelMetadata
from .backend_selector import BackendSelector, BackendSelection

logger = logging.getLogger(__name__)


@dataclass
class SmartLoadingPlan:
    """Complete plan for automatic model loading"""
    input_analysis: InputAnalysis
    model_recommendation: ModelRecommendation
    available_models: List[ModelMetadata]
    selected_model: Optional[ModelMetadata]
    backend_selection: Optional[BackendSelection]
    confidence_score: float
    execution_plan: Dict[str, Any]


@dataclass
class BenchmarkResult:
    """Results from model performance benchmark"""
    model_id: str
    load_time_seconds: float
    tokens_per_second: float
    memory_usage_mb: float
    inference_quality: str
    benchmark_timestamp: float


class HybridSmartLoader:
    """
    Smart model loading system that automatically:
    1. Detects input type (text, image, audio, code, pdf)
    2. Analyzes hardware capabilities  
    3. Recommends optimal model size
    4. Selects best available model
    5. Loads with optimal backend
    """
    
    def __init__(self, model_registry: Optional[ModelRegistry] = None):
        self.input_router = InputRouter()
        self.hardware_detector = HardwareDetector()
        self.model_selector = ModelSelector(self.hardware_detector)
        self.backend_selector = BackendSelector()
        self.model_registry = model_registry or ModelRegistry()
        
        # State tracking
        self.current_model: Optional[str] = None
        self.loading_history: List[SmartLoadingPlan] = []
        self.benchmark_cache: Dict[str, BenchmarkResult] = {}
        
        logger.info("🧠 Hybrid Smart Loader initialized")
        
    def analyze_and_recommend(self, user_input: str, is_file_path: bool = False, 
                            quality_preference: float = 0.7) -> SmartLoadingPlan:
        """
        Analyze input and create complete loading plan.
        
        Args:
            user_input: Text or file path from user
            is_file_path: Whether input is a file path
            quality_preference: 0.0 (speed) to 1.0 (quality)
            
        Returns:
            SmartLoadingPlan with complete analysis and recommendations
        """
        logger.info(f"🔍 Analyzing input: {user_input[:100]}...")
        
        # Step 1: Analyze input type
        input_analysis = self.input_router.analyze_input(user_input, is_file_path)
        logger.info(f"📋 Detected task: {input_analysis.task_type.value} (confidence: {input_analysis.confidence:.2f})")
        
        # Step 2: Get model size recommendation
        model_recommendation = self.model_selector.select_model_size(
            input_analysis.task_type, quality_preference
        )
        logger.info(f"🎯 Recommended model size: {model_recommendation.recommended_size.value}")
        
        # Step 3: Find available models matching recommendation
        available_models = self._find_compatible_models(
            input_analysis.task_type, 
            model_recommendation.recommended_size
        )
        
        # Step 4: Select best model from available options
        selected_model = self._select_best_model(available_models, input_analysis.task_type)
        
        # Step 5: Get backend selection if model is available
        backend_selection = None
        if selected_model:
            backend_selection = self.backend_selector.select_backend(
                Path(selected_model.path)
            )
            logger.info(f"⚙️ Selected backend: {backend_selection.backend.value}")
        
        # Step 6: Calculate overall confidence
        confidence_score = self._calculate_overall_confidence(
            input_analysis, model_recommendation, selected_model
        )
        
        # Step 7: Create execution plan
        execution_plan = self._create_execution_plan(
            selected_model, backend_selection, model_recommendation
        )
        
        plan = SmartLoadingPlan(
            input_analysis=input_analysis,
            model_recommendation=model_recommendation,
            available_models=available_models,
            selected_model=selected_model,
            backend_selection=backend_selection,
            confidence_score=confidence_score,
            execution_plan=execution_plan
        )
        
        self.loading_history.append(plan)
        return plan
    
    def execute_loading_plan(self, plan: SmartLoadingPlan) -> Dict[str, Any]:
        """
        Execute the loading plan and return results.
        
        Args:
            plan: SmartLoadingPlan to execute
            
        Returns:
            Dict with loading results and status
        """
        if not plan.selected_model:
            return {
                'success': False,
                'error': 'No suitable model found',
                'recommendation': self._generate_manual_recommendation(plan)
            }
        
        try:
            logger.info(f"🚀 Loading model: {plan.selected_model.name}")
            
            # TODO: Integrate with universal_loader.py to actually load the model
            # For now, simulate loading
            load_start = time.time()
            
            # Simulate loading time based on model size
            model_size_gb = plan.selected_model.size_gb or 4.0
            simulated_load_time = min(30, model_size_gb * 2)  # 2 seconds per GB, max 30s
            
            # In real implementation, this would call universal_loader
            # loader_result = self.universal_loader.load_model(
            #     plan.selected_model.path,
            #     backend=plan.backend_selection.backend,
            #     **plan.execution_plan
            # )
            
            load_time = time.time() - load_start
            self.current_model = plan.selected_model.id
            
            return {
                'success': True,
                'model_id': plan.selected_model.id,
                'model_name': plan.selected_model.name,
                'backend': plan.backend_selection.backend.value if plan.backend_selection else 'unknown',
                'load_time': load_time,
                'confidence': plan.confidence_score,
                'task_type': plan.input_analysis.task_type.value,
                'reasoning': plan.model_recommendation.reasoning
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_options': plan.model_recommendation.fallback_options
            }
    
    def benchmark_model(self, model_id: str, duration_seconds: int = 5) -> BenchmarkResult:
        """
        Run performance benchmark on loaded model.
        
        Args:
            model_id: ID of model to benchmark
            duration_seconds: How long to run benchmark
            
        Returns:
            BenchmarkResult with performance metrics
        """
        if model_id in self.benchmark_cache:
            logger.info(f"📊 Using cached benchmark for {model_id}")
            return self.benchmark_cache[model_id]
        
        logger.info(f"🏃‍♂️ Running {duration_seconds}s benchmark on {model_id}")
        
        start_time = time.time()
        
        # TODO: Implement actual benchmark
        # For now, simulate based on model characteristics
        model = self.model_registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found in registry")
        
        # Simulate benchmark metrics
        simulated_tokens = duration_seconds * 20  # 20 tok/s average
        simulated_memory = (model.size_gb or 4.0) * 1024  # MB
        
        result = BenchmarkResult(
            model_id=model_id,
            load_time_seconds=2.5,  # Simulated
            tokens_per_second=simulated_tokens / duration_seconds,
            memory_usage_mb=simulated_memory,
            inference_quality="good",  # Would be measured in real benchmark
            benchmark_timestamp=start_time
        )
        
        self.benchmark_cache[model_id] = result
        logger.info(f"✅ Benchmark complete: {result.tokens_per_second:.1f} tok/s")
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        vram = self.model_selector._get_available_vram()
        ram = self.model_selector._get_available_ram()
        
        return {
            'hardware': {
                'vram_gb': vram,
                'ram_gb': ram,
                'gpu_available': vram > 0,
                'cpu_cores': self.hardware_detector.system_info.cpu_cores if self.hardware_detector.system_info else 'unknown'
            },
            'models': {
                'total_registered': len(self.model_registry.list_models()),
                'currently_loaded': self.current_model,
                'loading_history_count': len(self.loading_history)
            },
            'performance': {
                'benchmark_cache_size': len(self.benchmark_cache),
                'last_recommendation_confidence': self.loading_history[-1].confidence_score if self.loading_history else 0.0
            }
        }
    
    def _find_compatible_models(self, task_type: TaskType, preferred_size: ModelSize) -> List[ModelMetadata]:
        """Find models compatible with task and size requirements"""
        all_models = self.model_registry.list_models()
        
        # Filter by task compatibility (simplified - would need more sophisticated matching)
        compatible = []
        for model in all_models:
            # Basic compatibility check - in real implementation would be more sophisticated
            if task_type == TaskType.IMAGE and 'clip' in model.name.lower():
                compatible.append(model)
            elif task_type == TaskType.AUDIO and 'whisper' in model.name.lower():
                compatible.append(model)
            elif task_type in [TaskType.TEXT, TaskType.CODE, TaskType.PDF]:
                # Language models - check size compatibility
                if model.size_gb:
                    size_tier = self.model_selector.get_model_requirements(preferred_size)
                    if model.size_gb <= size_tier.min_vram_gb * 2:  # Allow some overhead
                        compatible.append(model)
        
        return compatible
    
    def _select_best_model(self, available_models: List[ModelMetadata], task_type: TaskType) -> Optional[ModelMetadata]:
        """Select the best model from available options"""
        if not available_models:
            return None
        
        # Score models based on various factors
        scored_models = []
        for model in available_models:
            score = 0.0
            
            # Prefer models with good performance history
            if model.tokens_per_second:
                score += min(50, model.tokens_per_second) / 50  # Normalize to 0-1
            
            # Prefer recently used models
            if model.last_used:
                days_since_use = (time.time() - model.last_used.timestamp()) / (24 * 3600)
                score += max(0, (30 - days_since_use) / 30)  # Decay over 30 days
            
            # Prefer models with higher usage count (proven working)
            score += min(10, model.usage_count) / 10
            
            # Prefer verified models
            if model.verified:
                score += 0.5
            
            scored_models.append((model, score))
        
        # Sort by score and return best
        scored_models.sort(key=lambda x: x[1], reverse=True)
        return scored_models[0][0]
    
    def _calculate_overall_confidence(self, input_analysis: InputAnalysis, 
                                    model_rec: ModelRecommendation, 
                                    selected_model: Optional[ModelMetadata]) -> float:
        """Calculate overall confidence in the recommendation"""
        confidence = 0.0
        
        # Input analysis confidence
        confidence += input_analysis.confidence * 0.3
        
        # Model recommendation confidence  
        confidence += model_rec.confidence * 0.4
        
        # Model availability factor
        if selected_model:
            confidence += 0.3
            # Boost if model has good track record
            if selected_model.verified and selected_model.usage_count > 0:
                confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_execution_plan(self, model: Optional[ModelMetadata], 
                             backend: Optional[BackendSelection],
                             recommendation: ModelRecommendation) -> Dict[str, Any]:
        """Create detailed execution plan for model loading"""
        if not model or not backend:
            return {'status': 'no_model_available'}
        
        return {
            'model_path': model.path,
            'backend': backend.backend.value,
            'gpu_layers': self._calculate_gpu_layers(recommendation),
            'context_length': 4096,  # Default
            'memory_target': recommendation.hardware_utilization.get('vram_usage', 0.8),
            'optimization_hints': backend.configuration_hints
        }
    
    def _calculate_gpu_layers(self, recommendation: ModelRecommendation) -> int:
        """Calculate optimal GPU layers based on VRAM usage"""
        vram_usage = recommendation.hardware_utilization.get('vram_usage', 0.0)
        
        if vram_usage <= 0.6:
            return -1  # Use all layers
        elif vram_usage <= 0.8:
            return 35  # Most layers
        elif vram_usage <= 0.9:
            return 20  # Some layers
        else:
            return 0   # CPU only
    
    def _generate_manual_recommendation(self, plan: SmartLoadingPlan) -> str:
        """Generate manual recommendation when no suitable model is found"""
        task = plan.input_analysis.task_type.value
        size = plan.model_recommendation.recommended_size.value
        
        return (f"No suitable {size} model found for {task} task. "
                f"Consider downloading a {size} model or try with a smaller model size.")
