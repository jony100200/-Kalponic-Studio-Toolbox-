"""
Test Suite for SOLID Model Management Components

Tests the 3-component approach:
- ModelLock: Single model enforcement 
- MemoryCleaner: Resource cleanup specialist
- ModelLifecycle: Orchestration conductor

🧪 Validation Focus: Component integration, edge cases, and real-world scenarios
🎯 Success Criteria: All tests pass, components work together seamlessly
"""

import pytest
import asyncio
import threading
import time
import tempfile
import subprocess
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import our components
from Core.model_lock import ModelLock, ModelInstance
from Core.memory_cleaner import MemoryCleaner, CleanupResult
from Core.model_lifecycle import ModelLifecycle, ModelConfig, ModelState

class TestModelLock:
    """Test the ModelLock component for single model enforcement."""
    
    def setup_method(self):
        self.lock = ModelLock()
    
    def test_single_model_enforcement(self):
        """Test that only one model can hold the lock at a time."""
        # Create two model instances
        model1 = ModelInstance(
            process_id=1001,
            model_name="llama-7b",
            port=5000,
            backend_type="koboldcpp"
        )
        
        model2 = ModelInstance(
            process_id=1002,
            model_name="gpt-3.5",
            port=5001,
            backend_type="text-generation-webui"
        )
        
        # First model should acquire lock
        assert self.lock.acquire_lock(model1) == True
        assert self.lock.is_locked() == True
        assert self.lock.get_current_model().model_name == "llama-7b"
        
        # Second model should be denied
        assert self.lock.acquire_lock(model2) == False
        assert self.lock.get_current_model().model_name == "llama-7b"  # Still first model
        
        # Release first model
        assert self.lock.release_lock(1001) == True
        assert self.lock.is_locked() == False
        
        # Now second model can acquire
        assert self.lock.acquire_lock(model2) == True
        assert self.lock.get_current_model().model_name == "gpt-3.5"
    
    def test_wrong_process_release(self):
        """Test that wrong process cannot release lock."""
        model = ModelInstance(
            process_id=1001,
            model_name="llama-7b",
            port=5000,
            backend_type="koboldcpp"
        )
        
        # Acquire lock
        assert self.lock.acquire_lock(model) == True
        
        # Wrong process tries to release
        assert self.lock.release_lock(9999) == False
        assert self.lock.is_locked() == True  # Still locked
        
        # Correct process releases
        assert self.lock.release_lock(1001) == True
        assert self.lock.is_locked() == False
    
    def test_force_release(self):
        """Test emergency force release functionality."""
        model = ModelInstance(
            process_id=1001,
            model_name="llama-7b",
            port=5000,
            backend_type="koboldcpp"
        )
        
        # Acquire lock
        assert self.lock.acquire_lock(model) == True
        
        # Force release
        assert self.lock.force_release("emergency cleanup") == True
        assert self.lock.is_locked() == False
        
        # Should be able to acquire new lock
        new_model = ModelInstance(
            process_id=1002,
            model_name="gpt-4",
            port=5001,
            backend_type="koboldcpp"
        )
        assert self.lock.acquire_lock(new_model) == True
    
    def test_thread_safety(self):
        """Test thread safety of the lock."""
        results = []
        
        def try_acquire_lock(model_id):
            model = ModelInstance(
                process_id=model_id,
                model_name=f"model-{model_id}",
                port=5000 + model_id,
                backend_type="koboldcpp"
            )
            success = self.lock.acquire_lock(model)
            results.append((model_id, success))
            
            if success:
                time.sleep(0.1)  # Hold lock briefly
                self.lock.release_lock(model_id)
        
        # Start multiple threads trying to acquire lock
        threads = []
        for i in range(5):
            thread = threading.Thread(target=try_acquire_lock, args=(1000 + i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Only one thread should have succeeded
        successes = [result[1] for result in results]
        assert sum(successes) == 1, f"Expected 1 success, got {sum(successes)}"

class TestMemoryCleaner:
    """Test the MemoryCleaner component for resource cleanup."""
    
    def setup_method(self):
        self.cleaner = MemoryCleaner()
    
    @patch('gc.collect')
    def test_cpu_memory_cleanup(self, mock_gc_collect):
        """Test CPU memory cleanup functionality."""
        # Mock memory measurements - need more values for all the calls
        with patch.object(self.cleaner, '_get_memory_usage', side_effect=[1000.0, 1000.0, 900.0, 900.0]):
            with patch.object(self.cleaner, '_get_gpu_memory_usage', return_value=0.0):
                result = self.cleaner.cleanup_after_model(
                    model_name="test-model",
                    aggressive=False
                )
        
        # Should call garbage collection
        mock_gc_collect.assert_called()
        
        # Should report memory freed
        assert result.memory_freed_mb == 100.0
        assert result.success == True
    
    @patch('Core.memory_cleaner.HAS_CUDA', True)
    @patch('Core.memory_cleaner.HAS_TORCH', True)
    def test_gpu_memory_cleanup(self):
        """Test GPU memory cleanup functionality."""
        # Mock torch module
        with patch('sys.modules', {'torch': MagicMock(), 'torch.cuda': MagicMock()}):
            # Mock GPU memory measurements and CPU memory
            with patch.object(self.cleaner, '_get_gpu_memory_usage', side_effect=[2000.0, 2000.0, 1500.0, 1500.0]):
                with patch.object(self.cleaner, '_get_memory_usage', side_effect=[1000.0, 1000.0, 1000.0, 1000.0]):
                    with patch.object(self.cleaner, '_cleanup_gpu_memory', return_value=500.0):
                        result = self.cleaner.cleanup_after_model(
                            model_name="test-model",
                            aggressive=True
                        )
        
        # Should call CUDA empty cache
        mock_empty_cache.assert_called()
        
        # Should report GPU memory freed
        assert result.gpu_memory_freed_mb == 500.0
    
    def test_cleanup_hooks(self):
        """Test custom cleanup hooks functionality."""
        hook_called = []
        
        def test_hook():
            hook_called.append(True)
        
        def failing_hook():
            raise Exception("Hook failed")
        
        # Register hooks
        self.cleaner.register_cleanup_hook(test_hook)
        self.cleaner.register_cleanup_hook(failing_hook)
        
        # Run cleanup
        result = self.cleaner.cleanup_after_model(model_name="test")
        
        # Good hook should have been called
        assert len(hook_called) == 1
        
        # Should report error from failing hook
        assert len(result.errors) >= 1
        assert "Hook failed" in str(result.errors)
    
    @patch('psutil.Process')
    def test_process_cleanup(self, mock_process_class):
        """Test process cleanup functionality."""
        # Mock process
        mock_process = Mock()
        mock_process.is_running.return_value = True
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = None
        mock_process_class.return_value = mock_process
        
        # Test cleanup
        result = self.cleaner.cleanup_after_model(
            process_id=1234,
            model_name="test-model"
        )
        
        # Should have attempted to terminate process
        mock_process.terminate.assert_called()

class TestModelLifecycle:
    """Test the ModelLifecycle orchestration component."""
    
    def setup_method(self):
        self.lock = ModelLock()
        self.cleaner = MemoryCleaner()
        self.lifecycle = ModelLifecycle(self.lock, self.cleaner)
    
    def test_initial_state(self):
        """Test initial lifecycle state."""
        status = self.lifecycle.get_status()
        assert status.state == ModelState.IDLE
        assert status.model_config is None
        assert status.process_id is None
    
    def test_config_validation(self):
        """Test model configuration validation."""
        # Create temporary model file
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        
        try:
            valid_config = ModelConfig(
                name="test-model",
                backend_type="koboldcpp",
                model_path=tmp_path,
                port=9999  # Use unlikely port
            )
            
            # Should validate successfully
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.lifecycle._validate_config(valid_config)
                )
                assert result == True
            finally:
                loop.close()
            
            # Invalid config (non-existent file)
            invalid_config = ModelConfig(
                name="test-model",
                backend_type="koboldcpp",
                model_path=Path("/nonexistent/model.gguf"),
                port=9999
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.lifecycle._validate_config(invalid_config)
                )
                assert result == False
            finally:
                loop.close()
                
        finally:
            # Cleanup
            if tmp_path.exists():
                tmp_path.unlink()
    
    def test_command_building(self):
        """Test command building for different backends."""
        config = ModelConfig(
            name="test-model",
            backend_type="koboldcpp",
            model_path=Path("/path/to/model.gguf"),
            port=5000,
            extra_args={"threads": 4, "gpu": True, "verbose": False}
        )
        
        cmd = self.lifecycle._build_command(config)
        
        # Convert paths to string for comparison on Windows
        cmd_str = ' '.join(cmd)
        expected_parts = [
            'python', 'koboldcpp.py',
            '--model', 'model.gguf',  # Just check filename not full path
            '--port', '5000',
            '--host', '0.0.0.0',
            '--threads', '4',
            '--gpu'
        ]
        
        # Check that all expected parts are in the command
        for part in expected_parts:
            assert part in cmd_str
        
        # verbose=False should not appear
        assert '--verbose' not in cmd
    
    def test_lifecycle_hooks(self):
        """Test lifecycle hook registration and execution."""
        hook_calls = []
        
        def before_load_hook(config):
            hook_calls.append(f"before_load:{config.name}")
        
        def after_load_hook(config, process):
            hook_calls.append(f"after_load:{config.name}")
        
        # Register hooks
        self.lifecycle.register_hook('before_load', before_load_hook)
        self.lifecycle.register_hook('after_load', after_load_hook)
        
        # Test hook execution
        config = ModelConfig(
            name="test-model",
            backend_type="koboldcpp", 
            model_path=Path("/tmp/model.gguf"),
            port=5000
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run hooks
            loop.run_until_complete(
                self.lifecycle._run_hooks('before_load', config)
            )
            loop.run_until_complete(
                self.lifecycle._run_hooks('after_load', config, Mock())
            )
        finally:
            loop.close()
        
        # Verify hooks were called
        assert "before_load:test-model" in hook_calls
        assert "after_load:test-model" in hook_calls

class TestIntegration:
    """Test integration between all three components."""
    
    def setup_method(self):
        self.lock = ModelLock()
        self.cleaner = MemoryCleaner()
        self.lifecycle = ModelLifecycle(self.lock, self.cleaner)
    
    def test_component_integration(self):
        """Test that all components work together properly."""
        # Test that lifecycle uses lock correctly
        assert self.lifecycle.model_lock is self.lock
        assert self.lifecycle.memory_cleaner is self.cleaner
        
        # Test initial states
        assert not self.lock.is_locked()
        assert self.lifecycle.get_status().state == ModelState.IDLE
        
        # Test mock model instance
        model = ModelInstance(
            process_id=1234,
            model_name="integration-test",
            port=5000,
            backend_type="koboldcpp"
        )
        
        # Acquire lock through model lock
        assert self.lock.acquire_lock(model) == True
        
        # Test cleanup
        cleanup_result = self.cleaner.cleanup_after_model(
            process_id=1234,
            model_name="integration-test"
        )
        
        assert cleanup_result.success == True
        
        # Release lock
        assert self.lock.release_lock(1234) == True
    
    def test_error_handling_integration(self):
        """Test error handling across components."""
        # Test lock with invalid process
        assert self.lock.release_lock(99999) == False
        
        # Test cleanup with non-existent process
        result = self.cleaner.cleanup_after_model(
            process_id=99999,
            model_name="non-existent"
        )
        # Should not fail, just report minimal cleanup
        assert isinstance(result, CleanupResult)

def run_tests():
    """Run all tests and report results."""
    import pytest
    import sys
    
    # Configure pytest for this specific test run
    args = [
        __file__,
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "-x"  # Stop on first failure
    ]
    
    print("🧪 Running SOLID Model Management Tests...")
    print("=" * 60)
    
    # Run tests
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ All tests passed! SOLID model management components are working correctly.")
        print("\n🎯 Component Summary:")
        print("   • ModelLock: Single model enforcement ✓")
        print("   • MemoryCleaner: Resource cleanup specialist ✓") 
        print("   • ModelLifecycle: Orchestration conductor ✓")
        print("   • Integration: All components work together ✓")
    else:
        print("\n❌ Some tests failed. Please review the output above.")
    
    return exit_code

if __name__ == "__main__":
    import sys
    exit_code = run_tests()
    sys.exit(exit_code)
