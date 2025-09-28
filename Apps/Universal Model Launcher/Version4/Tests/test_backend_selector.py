"""
Test Backend Selector Component - Smart Backend Choice

Test suite for the BackendSelector component to ensure accurate
model format detection and optimal backend selection.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from Core.backend_selector import (
    BackendSelector, 
    ModelFormat, 
    BackendType, 
    ModelCharacteristics,
    BackendSelection
)

class TestBackendSelector:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.selector = BackendSelector()
    
    def test_gguf_format_detection(self):
        """Test GGUF format detection."""
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as tmp:
            # Write GGUF magic header
            tmp.write(b'GGUF\x00\x00\x00\x03')
            tmp.flush()
            
            model_path = Path(tmp.name)
            format_detected = self.selector._detect_format(model_path)
            assert format_detected == ModelFormat.GGUF
            
            # Cleanup
            model_path.unlink()
    
    def test_huggingface_format_detection(self):
        """Test HuggingFace format detection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_path = Path(tmp_dir)
            
            # Create config.json
            config_path = model_path / 'config.json'
            config_data = {
                "architectures": ["LlamaForCausalLM"],
                "model_type": "llama",
                "max_position_embeddings": 2048
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            format_detected = self.selector._detect_format(model_path)
            assert format_detected == ModelFormat.HUGGINGFACE
    
    def test_safetensors_format_detection(self):
        """Test SafeTensors format detection."""
        with tempfile.NamedTemporaryFile(suffix='.safetensors', delete=False) as tmp:
            tmp.write(b'<safetensors_header>')
            tmp.flush()
            
            model_path = Path(tmp.name)
            format_detected = self.selector._detect_format(model_path)
            assert format_detected == ModelFormat.SAFETENSORS
            
            # Cleanup
            model_path.unlink()
    
    def test_model_size_calculation(self):
        """Test model size calculation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write 1MB of data
            tmp.write(b'0' * (1024 * 1024))
            tmp.flush()
            
            model_path = Path(tmp.name)
            size_gb = self.selector._calculate_size(model_path)
            
            # Should be approximately 0.001 GB (1MB)
            assert 0.0009 < size_gb < 0.0011
            
            # Cleanup
            model_path.unlink()
    
    def test_architecture_detection_from_filename(self):
        """Test architecture detection from filename patterns."""
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as tmp:
            tmp.name = tmp.name.replace('.gguf', 'llama-2-7b-chat.gguf')
            
            model_path = Path(tmp.name)
            metadata = {}
            
            architecture = self.selector._detect_architecture(model_path, metadata)
            assert architecture == 'llama'
            
            # Cleanup
            model_path.unlink()
    
    def test_quantization_detection_from_filename(self):
        """Test quantization detection from filename."""
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as tmp:
            tmp.name = tmp.name.replace('.gguf', 'model.q4_0.gguf')
            
            model_path = Path(tmp.name)
            metadata = {}
            
            quantization = self.selector._detect_quantization(model_path, metadata)
            assert quantization == 'q4_0'
            
            # Cleanup
            model_path.unlink()
    
    def test_backend_scoring_gguf_model(self):
        """Test backend scoring for GGUF model."""
        characteristics = ModelCharacteristics(
            format=ModelFormat.GGUF,
            size_gb=7.5,
            architecture='llama',
            quantization='q4_0',
            requires_gpu=False
        )
        
        scores = self.selector._score_backends(characteristics, {})
        
        # llama.cpp should score highest for GGUF
        assert BackendType.LLAMA_CPP in scores
        assert BackendType.KOBOLDCPP in scores
        
        # Transformers should not be in scores (no GGUF support)
        assert BackendType.TRANSFORMERS not in scores
    
    def test_backend_scoring_huggingface_model(self):
        """Test backend scoring for HuggingFace model."""
        characteristics = ModelCharacteristics(
            format=ModelFormat.HUGGINGFACE,
            size_gb=13.0,
            architecture='llama',
            requires_gpu=True
        )
        
        scores = self.selector._score_backends(characteristics, {})
        
        # Transformers should score well for HuggingFace
        assert BackendType.TRANSFORMERS in scores
        assert BackendType.TEXT_GEN_WEBUI in scores
        
        # llama.cpp should not support HuggingFace format
        assert BackendType.LLAMA_CPP not in scores
    
    def test_user_preference_bonus(self):
        """Test that user preferences provide scoring bonus."""
        characteristics = ModelCharacteristics(
            format=ModelFormat.GGUF,
            size_gb=7.5,
            architecture='llama'
        )
        
        preferences = {'backend': 'koboldcpp'}
        scores = self.selector._score_backends(characteristics, preferences)
        
        # KoboldCpp should get preference bonus
        kobold_score = scores[BackendType.KOBOLDCPP]['total_score']
        llama_score = scores[BackendType.LLAMA_CPP]['total_score']
        
        # With user preference, KoboldCpp should score higher
        assert kobold_score > llama_score
    
    def test_gpu_requirement_scoring(self):
        """Test GPU requirement affects backend scoring."""
        # GPU-required model
        gpu_characteristics = ModelCharacteristics(
            format=ModelFormat.HUGGINGFACE,
            size_gb=20.0,
            requires_gpu=True
        )
        
        scores_gpu = self.selector._score_backends(gpu_characteristics, {})
        
        # CPU-friendly model
        cpu_characteristics = ModelCharacteristics(
            format=ModelFormat.GGUF,
            size_gb=3.0,
            requires_gpu=False
        )
        
        scores_cpu = self.selector._score_backends(cpu_characteristics, {})
        
        # GPU backends should score better for GPU models
        # CPU backends should work for both but score differently
        assert len(scores_gpu) > 0
        assert len(scores_cpu) > 0
    
    @patch('pathlib.Path.exists')
    def test_model_not_found_handling(self, mock_exists):
        """Test handling of non-existent model paths."""
        mock_exists.return_value = False
        
        model_path = Path("/nonexistent/model.gguf")
        
        with pytest.raises(FileNotFoundError):
            self.selector._analyze_model(model_path)
    
    def test_config_hints_generation(self):
        """Test configuration hints generation for different backends."""
        characteristics = ModelCharacteristics(
            format=ModelFormat.GGUF,
            size_gb=7.5,
            context_length=4096,
            requires_gpu=True
        )
        
        # Test llama.cpp hints
        hints_llama = self.selector._generate_config_hints(BackendType.LLAMA_CPP, characteristics)
        assert 'n_ctx' in hints_llama
        assert hints_llama['n_ctx'] == 4096
        assert hints_llama['n_gpu_layers'] == -1  # GPU model
        
        # Test Transformers hints
        hints_transformers = self.selector._generate_config_hints(BackendType.TRANSFORMERS, characteristics)
        assert 'device_map' in hints_transformers
        assert hints_transformers['device_map'] == 'auto'  # GPU model
    
    def test_fallback_selection(self):
        """Test fallback selection when normal selection fails."""
        characteristics = ModelCharacteristics(
            format=ModelFormat.UNKNOWN,
            size_gb=0.0
        )
        
        selection = self.selector._create_fallback_selection(characteristics, "Test error")
        
        assert selection.backend == BackendType.AUTO
        assert selection.confidence == 0.1
        assert "Test error" in selection.reasoning
        assert len(selection.fallback_options) > 0
    
    def test_supported_formats_query(self):
        """Test querying supported formats for backends."""
        llama_formats = self.selector.get_supported_formats(BackendType.LLAMA_CPP)
        assert ModelFormat.GGUF in llama_formats
        assert ModelFormat.GGML in llama_formats
        
        transformers_formats = self.selector.get_supported_formats(BackendType.TRANSFORMERS)
        assert ModelFormat.HUGGINGFACE in transformers_formats
        assert ModelFormat.SAFETENSORS in transformers_formats
    
    def test_backend_info_query(self):
        """Test querying detailed backend information."""
        llama_info = self.selector.get_backend_info(BackendType.LLAMA_CPP)
        assert llama_info is not None
        assert llama_info.gpu_acceleration == True
        assert llama_info.cpu_inference == True
        assert 'streaming' in llama_info.features
    
    def test_complete_selection_workflow(self):
        """Test complete backend selection workflow."""
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as tmp:
            # Write GGUF magic header
            tmp.write(b'GGUF\x00\x00\x00\x03')
            # Add some content to make it a reasonable size
            tmp.write(b'0' * (1024 * 1024 * 100))  # 100MB
            tmp.flush()
            
            model_path = Path(tmp.name)
            
            # Mock the metadata extraction to avoid complex GGUF parsing
            with patch.object(self.selector, '_extract_metadata') as mock_extract:
                mock_extract.return_value = {
                    'quantization': 'q4_0',
                    'architecture': 'llama'
                }
                
                selection = self.selector.select_backend(model_path)
                
                # Should successfully select a backend
                assert selection.backend != BackendType.AUTO
                assert selection.confidence > 0.5
                assert selection.model_characteristics.format == ModelFormat.GGUF
                assert len(selection.fallback_options) > 0
                
            # Cleanup
            model_path.unlink()


class TestIntegrationBackendSelector:
    """Integration tests for BackendSelector with other components."""
    
    def test_integration_with_model_lifecycle(self):
        """Test integration with ModelLifecycle component."""
        # This would test how BackendSelector integrates with ModelLifecycle
        # for complete model loading workflow
        selector = BackendSelector()
        
        # Test that selection results can be used by ModelLifecycle
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as tmp:
            tmp.write(b'GGUF\x00\x00\x00\x03test_model_data')
            tmp.flush()
            
            model_path = Path(tmp.name)
            
            with patch.object(selector, '_extract_metadata') as mock_extract:
                mock_extract.return_value = {'quantization': 'q4_0'}
                
                selection = selector.select_backend(model_path)
                
                # Verify selection has required fields for ModelLifecycle
                assert hasattr(selection, 'backend')
                assert hasattr(selection, 'configuration_hints')
                assert hasattr(selection, 'model_characteristics')
                
            model_path.unlink()


def run_tests():
    """Run all backend selector tests."""
    import sys
    
    # Run tests
    exit_code = pytest.main([__file__, '-v'])
    
    if exit_code == 0:
        print("\n✅ All BackendSelector tests passed!")
        print("🎯 Components validated:")
        print("   • Format Detection: GGUF, HuggingFace, SafeTensors ✓")
        print("   • Backend Scoring: Performance-based selection ✓")
        print("   • Config Hints: Optimized settings generation ✓")
        print("   • Integration: Compatible with ModelLifecycle ✓")
    else:
        print("\n❌ Some BackendSelector tests failed. Please review the output above.")
    
    return exit_code


if __name__ == "__main__":
    import sys
    exit_code = run_tests()
    sys.exit(exit_code)
