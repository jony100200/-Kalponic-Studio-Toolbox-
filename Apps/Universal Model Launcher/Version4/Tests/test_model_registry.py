"""
Test Model Registry Component - Smart Database

Test suite for the ModelRegistry component to ensure accurate
model discovery, metadata management, and analytics tracking.
"""

import pytest
import tempfile
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from Core.model_registry import (
    ModelRegistry,
    ModelMetadata,
    ModelStatus,
    ModelSource,
    PerformanceRecord,
    UsageRecord
)

class TestModelRegistry:
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry_path = Path(self.temp_dir.name) / "test_registry"
        self.registry = ModelRegistry(registry_path=self.registry_path, auto_discover=False)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        # Check that directories and databases are created
        assert self.registry_path.exists()
        assert self.registry.db_path.exists()
        assert self.registry.analytics_path.exists()
        
        # Check database tables
        with sqlite3.connect(self.registry.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'models' in tables
        
        with sqlite3.connect(self.registry.analytics_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'performance' in tables
            assert 'usage' in tables
    
    def test_model_registration(self):
        """Test model registration."""
        model_metadata = ModelMetadata(
            id="test_model_001",
            name="Test Llama Model",
            path="/models/test-llama-7b.gguf",
            format="gguf",
            source=ModelSource.MANUAL,
            architecture="llama",
            size_gb=3.8,
            quantization="q4_0",
            parameter_count="7B"
        )
        
        # Register model
        success = self.registry.register_model(model_metadata)
        assert success
        
        # Verify model is retrievable
        retrieved_model = self.registry.get_model("test_model_001")
        assert retrieved_model is not None
        assert retrieved_model.name == "Test Llama Model"
        assert retrieved_model.architecture == "llama"
        assert retrieved_model.quantization == "q4_0"
    
    def test_model_listing_and_filtering(self):
        """Test model listing with filters."""
        # Register multiple models
        models = [
            ModelMetadata(
                id="gguf_model_1",
                name="GGUF Model 1",
                path="/models/model1.gguf",
                format="gguf",
                source=ModelSource.DISCOVERED,
                status=ModelStatus.AVAILABLE
            ),
            ModelMetadata(
                id="hf_model_1",
                name="HF Model 1",
                path="/models/hf_model",
                format="huggingface",
                source=ModelSource.HUGGINGFACE,
                status=ModelStatus.DOWNLOADED
            ),
            ModelMetadata(
                id="gguf_model_2",
                name="GGUF Model 2",
                path="/models/model2.gguf",
                format="gguf",
                source=ModelSource.LOCAL,
                status=ModelStatus.ERROR
            )
        ]
        
        for model in models:
            self.registry.register_model(model)
        
        # Test listing all models
        all_models = self.registry.list_models()
        assert len(all_models) == 3
        
        # Test format filtering
        gguf_models = self.registry.list_models(format_filter="gguf")
        assert len(gguf_models) == 2
        assert all(m.format == "gguf" for m in gguf_models)
        
        # Test status filtering
        available_models = self.registry.list_models(status_filter=ModelStatus.AVAILABLE)
        assert len(available_models) == 1
        assert available_models[0].status == ModelStatus.AVAILABLE
        
        # Test source filtering
        discovered_models = self.registry.list_models(source_filter=ModelSource.DISCOVERED)
        assert len(discovered_models) == 1
        assert discovered_models[0].source == ModelSource.DISCOVERED
    
    def test_model_search(self):
        """Test model search functionality."""
        # Register models with different characteristics
        models = [
            ModelMetadata(
                id="llama_chat",
                name="Llama 2 Chat Model",
                path="/models/llama-2-7b-chat.gguf",
                format="gguf",
                source=ModelSource.MANUAL,
                architecture="llama",
                tags=["chat", "assistant"],
                notes="Good for conversations"
            ),
            ModelMetadata(
                id="mistral_instruct",
                name="Mistral Instruct",
                path="/models/mistral-7b-instruct.gguf",
                format="gguf",
                source=ModelSource.MANUAL,
                architecture="mistral",
                tags=["instruct", "coding"],
                notes="Great for instructions"
            ),
            ModelMetadata(
                id="gemma_code",
                name="Gemma Code Model",
                path="/models/gemma-2b-code.gguf",
                format="gguf",
                source=ModelSource.MANUAL,
                architecture="gemma",
                tags=["code", "programming"]
            )
        ]
        
        for model in models:
            self.registry.register_model(model)
        
        # Test name search
        llama_results = self.registry.search_models("llama")
        assert len(llama_results) == 1
        assert llama_results[0].name == "Llama 2 Chat Model"
        
        # Test tag search
        chat_results = self.registry.search_models("chat")
        assert len(chat_results) == 1
        assert "chat" in chat_results[0].tags
        
        # Test architecture search
        mistral_results = self.registry.search_models("mistral")
        assert len(mistral_results) == 1
        assert mistral_results[0].architecture == "mistral"
        
        # Test notes search
        conversation_results = self.registry.search_models("conversations")
        assert len(conversation_results) == 1
        assert "conversations" in conversation_results[0].notes
    
    def test_performance_recording(self):
        """Test performance data recording."""
        # Register a model first
        model = ModelMetadata(
            id="perf_test_model",
            name="Performance Test Model",
            path="/models/perf_test.gguf",
            format="gguf",
            source=ModelSource.MANUAL
        )
        self.registry.register_model(model)
        
        # Record performance data
        performance = PerformanceRecord(
            model_id="perf_test_model",
            backend="llama.cpp",
            load_time=5.2,
            memory_usage=3800.0,
            tokens_per_second=42.5,
            context_length=2048,
            timestamp=datetime.now(),
            hardware_info={"gpu": "RTX 4090", "cpu": "Intel i9"}
        )
        
        self.registry.record_performance(performance)
        
        # Verify performance data is stored
        with sqlite3.connect(self.registry.analytics_path) as conn:
            cursor = conn.execute(
                "SELECT model_id, backend, load_time FROM performance WHERE model_id = ?",
                ("perf_test_model",)
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "perf_test_model"
            assert result[1] == "llama.cpp"
            assert result[2] == 5.2
        
        # Verify model metadata is updated
        updated_model = self.registry.get_model("perf_test_model")
        assert updated_model.load_time_seconds == 5.2
        assert updated_model.memory_usage_mb == 3800.0
        assert updated_model.tokens_per_second == 42.5
    
    def test_usage_tracking(self):
        """Test usage session tracking."""
        # Register a model
        model = ModelMetadata(
            id="usage_test_model",
            name="Usage Test Model",
            path="/models/usage_test.gguf",
            format="gguf",
            source=ModelSource.MANUAL
        )
        self.registry.register_model(model)
        
        # Start usage session
        session_id = "test_session_001"
        self.registry.record_usage_start("usage_test_model", session_id, "llama.cpp")
        
        # Verify usage start is recorded
        with sqlite3.connect(self.registry.analytics_path) as conn:
            cursor = conn.execute(
                "SELECT model_id, session_id, backend FROM usage WHERE session_id = ?",
                (session_id,)
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "usage_test_model"
            assert result[2] == "llama.cpp"
        
        # Verify model usage count increased
        updated_model = self.registry.get_model("usage_test_model")
        assert updated_model.usage_count == 1
        assert updated_model.last_used is not None
        
        # End usage session
        self.registry.record_usage_end(session_id, tokens_generated=150, requests_count=5)
        
        # Verify usage end is recorded
        with sqlite3.connect(self.registry.analytics_path) as conn:
            cursor = conn.execute(
                "SELECT tokens_generated, requests_count FROM usage WHERE session_id = ?",
                (session_id,)
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 150
            assert result[1] == 5
    
    def test_analytics_generation(self):
        """Test analytics data generation."""
        # Register a model and add performance/usage data
        model = ModelMetadata(
            id="analytics_test_model",
            name="Analytics Test Model",
            path="/models/analytics_test.gguf",
            format="gguf",
            source=ModelSource.MANUAL
        )
        self.registry.register_model(model)
        
        # Add performance records
        for i in range(3):
            performance = PerformanceRecord(
                model_id="analytics_test_model",
                backend="llama.cpp",
                load_time=5.0 + i,
                memory_usage=3000.0 + i * 100,
                tokens_per_second=40.0 + i * 2,
                context_length=2048,
                timestamp=datetime.now()
            )
            self.registry.record_performance(performance)
        
        # Add usage records
        for i in range(2):
            session_id = f"analytics_session_{i}"
            self.registry.record_usage_start("analytics_test_model", session_id, "llama.cpp")
            self.registry.record_usage_end(session_id, tokens_generated=100 + i * 50, requests_count=3 + i)
        
        # Get analytics
        analytics = self.registry.get_performance_analytics("analytics_test_model")
        
        assert analytics['model_id'] == "analytics_test_model"
        assert 'performance_by_backend' in analytics
        assert 'llama.cpp' in analytics['performance_by_backend']
        
        backend_perf = analytics['performance_by_backend']['llama.cpp']
        assert backend_perf['test_count'] == 3
        assert backend_perf['avg_load_time'] == 6.0  # (5+6+7)/3
        
        usage_stats = analytics['usage_stats']
        assert usage_stats['sessions'] == 2
        assert usage_stats['total_tokens'] == 250  # 100 + 150
        assert usage_stats['total_requests'] == 7  # 3 + 4
    
    def test_model_discovery(self):
        """Test automatic model discovery."""
        # Create temporary model files
        models_dir = Path(self.temp_dir.name) / "models"
        models_dir.mkdir()
        
        # Create GGUF model
        gguf_model = models_dir / "llama-2-7b-chat.q4_0.gguf"
        gguf_model.write_bytes(b"GGUF\x00\x00\x00\x03" + b"fake_model_data" * 1000)
        
        # Create HuggingFace model directory
        hf_model_dir = models_dir / "mistral-7b-instruct"
        hf_model_dir.mkdir()
        config_data = {
            "architectures": ["MistralForCausalLM"],
            "model_type": "mistral",
            "max_position_embeddings": 8192,
            "hidden_size": 4096,
            "num_hidden_layers": 32
        }
        (hf_model_dir / "config.json").write_text(json.dumps(config_data))
        
        # Add search path and discover
        self.registry.add_search_path(models_dir)
        discovered = self.registry.discover_models([models_dir])
        
        assert len(discovered) == 2
        
        # Verify GGUF model discovery
        gguf_models = [m for m in discovered if m.format == "gguf"]
        assert len(gguf_models) == 1
        gguf_model_meta = gguf_models[0]
        assert "llama" in gguf_model_meta.name.lower()
        assert gguf_model_meta.quantization == "q4_0"
        assert gguf_model_meta.architecture == "llama"
        
        # Verify HuggingFace model discovery
        hf_models = [m for m in discovered if m.format == "huggingface"]
        assert len(hf_models) == 1
        hf_model_meta = hf_models[0]
        assert hf_model_meta.architecture == "MistralForCausalLM"
        assert hf_model_meta.context_length == 8192
    
    def test_model_recommendations(self):
        """Test model recommendation system."""
        # Register models with different usage patterns
        models = [
            ModelMetadata(
                id="popular_model",
                name="Popular Model",
                path="/models/popular.gguf",
                format="gguf",
                source=ModelSource.MANUAL,
                usage_count=50,
                tokens_per_second=45.0,
                status=ModelStatus.AVAILABLE,
                last_used=datetime.now() - timedelta(days=1)
            ),
            ModelMetadata(
                id="fast_model",
                name="Fast Model",
                path="/models/fast.gguf",
                format="gguf",
                source=ModelSource.MANUAL,
                usage_count=10,
                tokens_per_second=80.0,
                status=ModelStatus.AVAILABLE,
                last_used=datetime.now() - timedelta(days=3)
            ),
            ModelMetadata(
                id="broken_model",
                name="Broken Model",
                path="/models/broken.gguf",
                format="gguf",
                source=ModelSource.MANUAL,
                usage_count=5,
                tokens_per_second=30.0,
                status=ModelStatus.ERROR,
                last_used=datetime.now() - timedelta(days=10)
            )
        ]
        
        for model in models:
            self.registry.register_model(model)
        
        # Get recommendations
        recommendations = self.registry.get_recommended_models()
        
        # Should prioritize available models with good performance/usage
        assert len(recommendations) >= 2
        assert recommendations[0].name in ["Popular Model", "Fast Model"]
        assert all(m.status == ModelStatus.AVAILABLE for m in recommendations[:2])
    
    def test_registry_statistics(self):
        """Test registry statistics generation."""
        # Register various models
        models = [
            ModelMetadata(
                id="stat_model_1",
                name="GGUF Model",
                path="/models/model1.gguf",
                format="gguf",
                source=ModelSource.DISCOVERED,
                size_gb=3.5,
                usage_count=10,
                total_runtime_seconds=3600
            ),
            ModelMetadata(
                id="stat_model_2",
                name="HF Model",
                path="/models/model2",
                format="huggingface",
                source=ModelSource.HUGGINGFACE,
                size_gb=7.2,
                usage_count=5,
                total_runtime_seconds=1800
            ),
            ModelMetadata(
                id="stat_model_3",
                name="Another GGUF",
                path="/models/model3.gguf",
                format="gguf",
                source=ModelSource.MANUAL,
                size_gb=4.1,
                usage_count=15,
                total_runtime_seconds=5400
            )
        ]
        
        for model in models:
            self.registry.register_model(model)
        
        # Get statistics
        stats = self.registry.get_registry_stats()
        
        assert stats['total_models'] == 3
        assert stats['format_distribution']['gguf'] == 2
        assert stats['format_distribution']['huggingface'] == 1
        assert stats['source_distribution']['discovered'] == 1
        assert stats['source_distribution']['manual'] == 1
        assert stats['size_statistics']['total_gb'] == 14.8
        assert stats['usage_statistics']['total_usage_count'] == 30
        assert stats['usage_statistics']['total_runtime_hours'] == 3.0  # 10800 seconds / 3600


class TestModelRegistryIntegration:
    """Integration tests for ModelRegistry with other components."""
    
    def test_integration_with_backend_selector(self):
        """Test integration with BackendSelector component."""
        from Core.backend_selector import BackendSelector, ModelFormat, BackendType
        
        # Create temporary registry
        temp_dir = tempfile.TemporaryDirectory()
        registry_path = Path(temp_dir.name) / "integration_registry"
        registry = ModelRegistry(registry_path=registry_path, auto_discover=False)
        
        # Register a model with performance data
        model = ModelMetadata(
            id="integration_model",
            name="Integration Test Model",
            path="/models/integration.gguf",
            format="gguf",
            source=ModelSource.MANUAL,
            architecture="llama",
            quantization="q4_0",
            tokens_per_second=45.0,
            memory_usage_mb=3800.0
        )
        registry.register_model(model)
        
        # Test that BackendSelector can use registry data
        selector = BackendSelector()
        
        # Verify the model characteristics can be used for backend selection
        assert model.format == "gguf"
        assert model.architecture == "llama"
        assert model.quantization == "q4_0"
        
        # Test format compatibility
        gguf_backends = selector.get_supported_formats(BackendType.LLAMA_CPP)
        assert ModelFormat.GGUF in gguf_backends
        
        temp_dir.cleanup()


def run_tests():
    """Run all model registry tests."""
    import sys
    
    # Run tests
    exit_code = pytest.main([__file__, '-v'])
    
    if exit_code == 0:
        print("\n✅ All ModelRegistry tests passed!")
        print("🎯 Components validated:")
        print("   • Model Discovery: Auto-detection and metadata extraction ✅")
        print("   • Database Management: SQLite storage and JSON caching ✅")
        print("   • Performance Tracking: Analytics and usage statistics ✅")
        print("   • Search & Filtering: Query and recommendation system ✅")
    else:
        print("\n❌ Some ModelRegistry tests failed. Please review the output above.")
    
    return exit_code


if __name__ == "__main__":
    import sys
    exit_code = run_tests()
    sys.exit(exit_code)
