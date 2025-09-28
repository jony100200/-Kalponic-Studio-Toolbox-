"""
Backend Selector Example Usage - Smart Backend Choice

This example demonstrates how to use the BackendSelector component
to intelligently choose the optimal backend for different model types.

Based on our analysis of KoboldCpp, Text Generation WebUI, and Transformers,
the BackendSelector acts as a "coach" making strategic decisions.
"""

import asyncio
import logging
from pathlib import Path
from Core.backend_selector import BackendSelector, ModelFormat, BackendType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demonstrate_backend_selection():
    """Demonstrate backend selection for various model scenarios."""
    
    print("🎯 Backend Selector Demo - Smart Backend Choice")
    print("=" * 50)
    
    # Initialize the selector
    selector = BackendSelector()
    
    # Example 1: GGUF Model (KoboldCpp/llama.cpp territory)
    print("\n🔹 Example 1: GGUF Quantized Model")
    print("-" * 30)
    
    # Simulate a GGUF model path (would be real in practice)
    gguf_model = Path("models/llama-2-7b-chat.q4_0.gguf")
    
    # For demo, we'll mock the analysis
    from unittest.mock import patch
    
    # Mock GGUF model characteristics
    with patch.object(selector, '_analyze_model') as mock_analyze:
        mock_analyze.return_value = type('MockCharacteristics', (), {
            'format': ModelFormat.GGUF,
            'size_gb': 3.9,
            'architecture': 'llama',
            'quantization': 'q4_0',
            'context_length': 4096,
            'parameter_count': '7B',
            'requires_gpu': False,
            'metadata': {'quantization': 'q4_0'}
        })()
        
        selection = selector.select_backend(gguf_model)
        
        print(f"📊 Model Analysis:")
        print(f"   Format: {selection.model_characteristics.format.value}")
        print(f"   Size: {selection.model_characteristics.size_gb:.1f}GB")
        print(f"   Architecture: {selection.model_characteristics.architecture}")
        print(f"   Quantization: {selection.model_characteristics.quantization}")
        
        print(f"\n🏆 Selected Backend: {selection.backend.value}")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Reasoning: {selection.reasoning}")
        
        print(f"\n⚙️ Configuration Hints:")
        for key, value in selection.configuration_hints.items():
            print(f"   {key}: {value}")
        
        print(f"\n🔄 Fallback Options:")
        for i, fallback in enumerate(selection.fallback_options, 1):
            print(f"   {i}. {fallback.value}")
    
    # Example 2: HuggingFace Model (Transformers territory)
    print("\n🔹 Example 2: HuggingFace Large Model")
    print("-" * 30)
    
    hf_model = Path("models/microsoft/DialoGPT-medium")
    
    with patch.object(selector, '_analyze_model') as mock_analyze:
        mock_analyze.return_value = type('MockCharacteristics', (), {
            'format': ModelFormat.HUGGINGFACE,
            'size_gb': 13.2,
            'architecture': 'gpt2',
            'quantization': None,
            'context_length': 1024,
            'parameter_count': '355M',
            'requires_gpu': True,
            'metadata': {'model_type': 'gpt2', 'torch_dtype': 'float16'}
        })()
        
        selection = selector.select_backend(hf_model)
        
        print(f"📊 Model Analysis:")
        print(f"   Format: {selection.model_characteristics.format.value}")
        print(f"   Size: {selection.model_characteristics.size_gb:.1f}GB")
        print(f"   Architecture: {selection.model_characteristics.architecture}")
        print(f"   GPU Required: {selection.model_characteristics.requires_gpu}")
        
        print(f"\n🏆 Selected Backend: {selection.backend.value}")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Reasoning: {selection.reasoning}")
        
        print(f"\n⚙️ Configuration Hints:")
        for key, value in selection.configuration_hints.items():
            print(f"   {key}: {value}")
    
    # Example 3: User Preference Override
    print("\n🔹 Example 3: User Preference Override")
    print("-" * 30)
    
    preferences = {'backend': 'koboldcpp'}
    
    with patch.object(selector, '_analyze_model') as mock_analyze:
        mock_analyze.return_value = type('MockCharacteristics', (), {
            'format': ModelFormat.GGUF,
            'size_gb': 6.8,
            'architecture': 'mistral',
            'quantization': 'q4_1',
            'context_length': 8192,
            'parameter_count': '7B',
            'requires_gpu': False,
            'metadata': {}
        })()
        
        selection = selector.select_backend(gguf_model, preferences)
        
        print(f"👤 User Preference: {preferences['backend']}")
        print(f"🏆 Selected Backend: {selection.backend.value}")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Reasoning: {selection.reasoning}")
    
    # Example 4: Format Compatibility Check
    print("\n🔹 Example 4: Backend Compatibility Matrix")
    print("-" * 30)
    
    print("📋 Backend Support Matrix:")
    
    backends = [BackendType.LLAMA_CPP, BackendType.TRANSFORMERS, BackendType.KOBOLDCPP, BackendType.TEXT_GEN_WEBUI]
    
    for backend in backends:
        supported_formats = selector.get_supported_formats(backend)
        backend_info = selector.get_backend_info(backend)
        
        print(f"\n🔧 {backend.value}:")
        print(f"   Formats: {[f.value for f in supported_formats]}")
        print(f"   GPU Support: {backend_info.gpu_acceleration}")
        print(f"   Performance Score: {backend_info.performance_score}/10")
        print(f"   Memory Efficiency: {backend_info.memory_efficiency}/10")
        print(f"   Features: {', '.join(backend_info.features[:3])}")
    
    # Example 5: Error Handling
    print("\n🔹 Example 5: Error Handling")
    print("-" * 30)
    
    nonexistent_model = Path("models/nonexistent.gguf")
    
    with patch.object(selector, '_analyze_model') as mock_analyze:
        mock_analyze.side_effect = FileNotFoundError("Model not found")
        
        selection = selector.select_backend(nonexistent_model)
        
        print(f"❌ Error Case:")
        print(f"   Backend: {selection.backend.value}")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Reasoning: {selection.reasoning}")
        print(f"   Fallbacks: {[b.value for b in selection.fallback_options]}")


def demonstrate_integration_with_lifecycle():
    """Demonstrate how BackendSelector integrates with ModelLifecycle."""
    
    print("\n\n🔗 Integration with ModelLifecycle")
    print("=" * 40)
    
    from Core.model_lifecycle import ModelConfig
    from Core.model_lock import ModelLock
    from Core.memory_cleaner import MemoryCleaner
    
    # Initialize components
    selector = BackendSelector()
    model_lock = ModelLock()
    memory_cleaner = MemoryCleaner()
    
    print("🎯 Simulated Workflow:")
    print("1. BackendSelector analyzes model")
    print("2. Provides configuration hints")
    print("3. ModelLifecycle uses recommendations")
    
    # Simulate the workflow
    model_path = Path("models/example-7b.gguf")
    
    with patch.object(selector, '_analyze_model') as mock_analyze:
        mock_analyze.return_value = type('MockCharacteristics', (), {
            'format': ModelFormat.GGUF,
            'size_gb': 4.2,
            'architecture': 'llama',
            'quantization': 'q4_0',
            'context_length': 2048,
            'requires_gpu': False,
            'metadata': {}
        })()
        
        # Step 1: Get backend recommendation
        selection = selector.select_backend(model_path)
        
        print(f"\n📋 Backend Recommendation:")
        print(f"   Selected: {selection.backend.value}")
        print(f"   Confidence: {selection.confidence:.2f}")
        
        # Step 2: Create ModelConfig using hints
        config_hints = selection.configuration_hints
        
        model_config = ModelConfig(
            name="example-7b",
            backend_type=selection.backend.value,
            model_path=model_path,
            port=5000,
            extra_args=config_hints
        )
        
        print(f"\n⚙️ Generated ModelConfig:")
        print(f"   Backend: {model_config.backend_type}")
        print(f"   Port: {model_config.port}")
        print(f"   Extra Args: {model_config.extra_args}")
        
        print(f"\n✅ Ready for ModelLifecycle.load_model(config)")


def main():
    """Main demo function."""
    print("🚀 Starting Backend Selector Demonstration")
    
    try:
        # Run async demo
        asyncio.run(demonstrate_backend_selection())
        
        # Run integration demo
        demonstrate_integration_with_lifecycle()
        
        print("\n\n🎉 Demo Complete!")
        print("💡 Key Takeaways:")
        print("   • Smart format detection (GGUF, HuggingFace, SafeTensors)")
        print("   • Performance-based backend scoring")
        print("   • User preference support")
        print("   • Automatic configuration optimization")
        print("   • Seamless integration with ModelLifecycle")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
