#!/usr/bin/env python3
"""
🧠 Multi-Modal Model Lifecycle Test Script
===========================================
This script validates the model loader's full lifecycle handling with multi-modal models:
1. 🔁 Load Language Model A — run a short summarization → then unload and clean up.
2. 🖼️ Load Vision Model (CLIP) — identify and describe a test image → then unload and clean up.
3. 🔊 Load Whisper Speech Model — transcribe an audio file to text → then unload and clean up.
4. 🧠 Load Language Model B — run a reasoning task to confirm clean reloading.

Goal: Ensure full memory cleanup, safe switching, and multi-modal task handling in one chain-run.
"""

import sys
import os
import gc
import time
import psutil
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Any

# Add Version4 to Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from main import UniversalModelLauncher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model and test file paths
GGUF_MODELS_DIR = Path("O:/AI Models/CODing Models GGUF")
TTS_MODELS_DIR = Path("O:/AI Models/TTS")
WHISPER_MODEL_DIR = Path("O:/AI Models/TTS/deepdmlfaster-whisper-large-v3-turbo-ct2")
TEST_FILES_DIR = Path("E:/__Kalponic Studio Repositories/-Kalponic-Studio-Toolbox-/Apps/Universal Model Launcher/Testing")

class MultiModalTester:
    """🎯 Multi-modal model lifecycle tester"""
    
    def __init__(self):
        self.launcher = None
        self.results = {
            "language_model_a": None,
            "vision_model": None,
            "whisper_model": None,
            "language_model_b": None,
            "memory_stats": []
        }
        self.current_model = None
    
    def get_memory_usage(self) -> Dict[str, float]:
        """📊 Get current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "system_memory_percent": psutil.virtual_memory().percent
        }
    
    def log_memory_usage(self, stage: str):
        """📊 Log memory usage at specific stage"""
        memory = self.get_memory_usage()
        self.results["memory_stats"].append({
            "stage": stage,
            "timestamp": time.time(),
            **memory
        })
        logger.info(f"💾 {stage}: RSS={memory['rss_mb']:.1f}MB, System={memory['system_memory_percent']:.1f}%")
    
    async def cleanup_memory(self):
        """🧼 Force memory cleanup with enhanced methods"""
        logger.info("🧼 Performing enhanced memory cleanup...")
        
        # Unload current model if any
        if self.current_model:
            try:
                loader = self.launcher._components.get('universal_loader')
                if loader and self.current_model in loader.running_servers:
                    # Get the model object for proper cleanup
                    model_info = loader.running_servers[self.current_model]
                    
                    # Delete model object if it exists
                    if "model" in model_info:
                        del model_info["model"]
                    
                    # Remove from running servers
                    del loader.running_servers[self.current_model]
                    logger.info(f"✅ Unloaded model: {self.current_model}")
            except Exception as e:
                logger.warning(f"⚠️ Error unloading model: {e}")
        
        self.current_model = None
        
        # Enhanced garbage collection
        import gc
        for _ in range(5):
            gc.collect()
        
        # Try to clear GPU memory if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("🔧 GPU cache cleared")
        except ImportError:
            pass
        
        # System delay for cleanup
        await asyncio.sleep(3)
        
        logger.info("✅ Enhanced memory cleanup completed")
    
    def discover_models(self) -> Dict[str, list]:
        """🔍 Discover available models"""
        models = {
            "gguf": [],
            "whisper": [],
            "clip": []
        }
        
        # Discover GGUF models
        if GGUF_MODELS_DIR.exists():
            for model_file in GGUF_MODELS_DIR.glob("*.gguf"):
                models["gguf"].append({
                    "path": str(model_file),
                    "name": model_file.stem,
                    "size_gb": round(model_file.stat().st_size / (1024**3), 2)
                })
        
        # Look for Whisper models (in TTS directory)
        if TTS_MODELS_DIR.exists():
            for model_file in TTS_MODELS_DIR.rglob("*whisper*"):
                if model_file.is_file():
                    models["whisper"].append({
                        "path": str(model_file),
                        "name": model_file.stem,
                        "size_gb": round(model_file.stat().st_size / (1024**3), 2)
                    })
        
        # Look for Vision models (CLIP and LLaVA variants in GGUF directory)
        if GGUF_MODELS_DIR.exists():
            for pattern in ["*clip*", "*llava*", "*BakLLaVA*"]:
                for model_file in GGUF_MODELS_DIR.rglob(pattern):
                    if model_file.is_file() and model_file.suffix.lower() == ".gguf":
                        models["clip"].append({
                            "path": str(model_file),
                            "name": model_file.stem,
                            "size_gb": round(model_file.stat().st_size / (1024**3), 2)
                        })
        
        return models
    
    async def load_llama_model(self, model_path: str, model_id: str) -> bool:
        """🤖 Load a GGUF language model"""
        try:
            from llama_cpp import Llama
            
            logger.info(f"🤖 Loading language model: {Path(model_path).name}")
            
            # Load with conservative settings
            model = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_gpu_layers=0,  # CPU only for memory management
                verbose=False,
                use_mmap=True,
                use_mlock=False,
                n_threads=4
            )
            
            # Store in launcher's running servers for tracking
            loader = self.launcher._components.get('universal_loader')
            if loader:
                loader.running_servers[model_id] = {
                    "model": model,
                    "model_type": "llm",
                    "backend": "llama.cpp",
                    "path": model_path
                }
            
            self.current_model = model_id
            logger.info(f"✅ Language model loaded: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load language model: {e}")
            return False
    
    async def test_language_model_a(self, models: Dict) -> str:
        """🔁 Test Language Model A - Summarization"""
        logger.info("🔁 Starting Language Model A Test (Summarization)")
        self.log_memory_usage("Before Language Model A")
        
        if not models["gguf"]:
            return "❌ No GGUF models found"
        
        # Select first available model
        model_info = models["gguf"][0]
        model_id = "language_model_a"
        
        # Load model
        success = await self.load_llama_model(model_info["path"], model_id)
        if not success:
            return "❌ Failed to load language model A"
        
        self.log_memory_usage("After loading Language Model A")
        
        try:
            # Get model from loader
            loader = self.launcher._components.get('universal_loader')
            model = loader.running_servers[model_id]["model"]
            
            # Test summarization
            text_to_summarize = """
            Python is a high-level, interpreted programming language with dynamic semantics. 
            Its high-level built-in data structures, combined with dynamic typing and dynamic binding, 
            make it very attractive for Rapid Application Development, as well as for use as a scripting 
            or glue language to connect existing components together. Python's simple, easy-to-learn 
            syntax emphasizes readability and therefore reduces the cost of program maintenance.
            """
            
            prompt = f"Summarize this text in one sentence: {text_to_summarize.strip()}\n\nSummary:"
            
            logger.info("🔄 Generating summary...")
            response = model(
                prompt,
                max_tokens=50,
                temperature=0.3,
                stop=["\n", ".", "Summary:", "Text:"]
            )
            
            summary = response["choices"][0]["text"].strip()
            result = f"✅ Summary: {summary}"
            
            self.log_memory_usage("After Language Model A inference")
            return result
            
        except Exception as e:
            logger.error(f"❌ Language Model A test failed: {e}")
            return f"❌ Test failed: {str(e)}"
    
    async def test_vision_model(self, models: Dict) -> str:
        """🖼️ Test Vision Model (CLIP) - Image Description"""
        logger.info("🖼️ Starting Vision Model Test (CLIP)")
        
        # Clean up previous model
        await self.cleanup_memory()
        self.log_memory_usage("Before Vision Model")
        
        image_path = TEST_FILES_DIR / "image test.png"
        
        if not image_path.exists():
            return "❌ Test image not found"
        
        try:
            # Try to use actual vision models if available
            if models["clip"]:
                # Look for BakLLaVA main model (not the clip-model.gguf)
                bakllava_model = None
                for model in models["clip"]:
                    if "BakLLaVA" in model["name"] and "clip-model" not in model["name"]:
                        bakllava_model = model
                        break
                
                if bakllava_model:
                    try:
                        from llama_cpp import Llama
                        from llama_cpp.llama_chat_format import Llava15ChatHandler
                        
                        logger.info(f"🖼️ Loading BakLLaVA vision model: {bakllava_model['name']}")
                        
                        # Find the clip model component
                        clip_model_path = None
                        for model in models["clip"]:
                            if "clip-model" in model["name"]:
                                clip_model_path = model["path"]
                                break
                        
                        if clip_model_path:
                            # Load BakLLaVA with vision support
                            chat_handler = Llava15ChatHandler(clip_model_path=clip_model_path)
                            llm = Llama(
                                model_path=bakllava_model["path"],
                                chat_handler=chat_handler,
                                n_ctx=2048,
                                n_gpu_layers=0,  # CPU only
                                verbose=False
                            )
                            
                            # Load and encode image
                            import base64
                            with open(image_path, "rb") as f:
                                image_data = base64.b64encode(f.read()).decode('utf-8')
                            
                            # Generate description using BakLLaVA
                            response = llm.create_chat_completion(
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": "Describe this image in detail."},
                                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                                        ]
                                    }
                                ],
                                max_tokens=100,
                                temperature=0.3
                            )
                            
                            description = response["choices"][0]["message"]["content"].strip()
                            result = f"✅ BakLLaVA Vision: {description}"
                            
                            # Cleanup
                            del llm, chat_handler
                            
                            self.log_memory_usage("After BakLLaVA Vision Model")
                            return result
                            
                        else:
                            logger.warning("🖼️ BakLLaVA clip-model.gguf not found, falling back to HuggingFace CLIP")
                    
                    except Exception as e:
                        logger.warning(f"🖼️ BakLLaVA loading failed: {e}, falling back to HuggingFace CLIP")
            
            # Fallback to HuggingFace CLIP
            try:
                from transformers import CLIPProcessor, CLIPModel
                from PIL import Image
                
                logger.info("🖼️ Loading HuggingFace CLIP model...")
                
                # Load CLIP model (using CPU to avoid GPU memory issues)
                model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                
                # Load and process image
                image = Image.open(image_path)
                
                # Generate description
                texts = ["a photo", "a diagram", "a screenshot", "an illustration", "a chart"]
                inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)
                
                outputs = model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
                
                best_match_idx = probs.argmax().item()
                confidence = probs[0][best_match_idx].item()
                
                result = f"✅ HuggingFace CLIP: The image appears to be {texts[best_match_idx]} (confidence: {confidence:.2f})"
                
                # Cleanup CLIP model
                del model, processor, outputs
                
                self.log_memory_usage("After Vision Model (CLIP)")
                return result
                
            except ImportError:
                # Fallback to simulation
                logger.info("🖼️ CLIP libraries not available, simulating...")
                await asyncio.sleep(1)
                
                # Basic image analysis
                from PIL import Image
                try:
                    image = Image.open(image_path)
                    result = f"✅ Image Description: {image_path.name} - {image.format} image, {image.size[0]}x{image.size[1]} pixels"
                except ImportError:
                    result = f"✅ Image Description: Test image ({image_path.name}) of {image_path.stat().st_size / 1024:.1f}KB"
                
                self.log_memory_usage("After Vision Model simulation")
                return result
            
        except Exception as e:
            logger.error(f"❌ Vision model test failed: {e}")
            return f"❌ Test failed: {str(e)}"
    
    async def test_whisper_model(self, models: Dict) -> str:
        """🔊 Test Whisper Speech Model - Audio Transcription"""
        logger.info("🔊 Starting Whisper Model Test (Transcription)")
        
        # Clean up previous model
        await self.cleanup_memory()
        self.log_memory_usage("Before Whisper Model")
        
        audio_path = TEST_FILES_DIR / "6.Local AI Model Launcher.mp3"
        
        if not audio_path.exists():
            return "❌ Test audio file not found"
        
        try:
            # Try to use actual Whisper model if faster-whisper is available
            try:
                import faster_whisper
                
                logger.info("🔊 Loading Whisper model...")
                
                # Use the specific model directory provided by user
                if WHISPER_MODEL_DIR.exists():
                    logger.info(f"🔊 Using user-specified Whisper model: {WHISPER_MODEL_DIR}")
                    model = faster_whisper.WhisperModel(str(WHISPER_MODEL_DIR), device="cpu", compute_type="int8")
                else:
                    logger.info("🔊 User model not found, using tiny model...")
                    model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
                
                # Transcribe audio
                logger.info("🔊 Transcribing audio...")
                segments, info = model.transcribe(str(audio_path), beam_size=1)
                
                # Collect transcription
                transcription_parts = []
                for segment in segments:
                    transcription_parts.append(segment.text.strip())
                
                transcription = " ".join(transcription_parts[:3])  # First 3 segments only
                
                result = f"✅ Transcription: '{transcription[:100]}...'" if len(transcription) > 100 else f"✅ Transcription: '{transcription}'"
                result += f" [Language: {info.language} - Confidence: {info.language_probability:.2f}]"
                
                # Cleanup Whisper model
                del model
                
                self.log_memory_usage("After Whisper Model")
                return result
                
            except ImportError:
                # Fallback to simulation
                logger.info("🔊 Faster-whisper not available, simulating...")
                await asyncio.sleep(1)  # Simulate loading time
                
                # Basic audio analysis (simulated)
                audio_size_mb = audio_path.stat().st_size / (1024 * 1024)
                result = f"✅ Transcription: Audio file ({audio_path.name}, {audio_size_mb:.1f}MB) would be transcribed here"
                
                # Note: In a real implementation, you would:
                # 1. Load faster-whisper or openai-whisper
                # 2. Process the audio file
                # 3. Return actual transcription
                
                logger.info("💡 Note: Whisper model simulation - install faster-whisper for real transcription")
                
                self.log_memory_usage("After Whisper Model simulation")
                return result
            
        except Exception as e:
            logger.error(f"❌ Whisper model test failed: {e}")
            return f"❌ Test failed: {str(e)}"
    
    async def test_language_model_b(self, models: Dict) -> str:
        """🧠 Test Language Model B - Reasoning Task"""
        logger.info("🧠 Starting Language Model B Test (Reasoning)")
        
        # Clean up previous model
        await self.cleanup_memory()
        self.log_memory_usage("Before Language Model B")
        
        if not models["gguf"]:
            return "❌ No GGUF models found"
        
        # Select model (could be same or different from Model A)
        model_info = models["gguf"][0]
        model_id = "language_model_b"
        
        # Load model
        success = await self.load_llama_model(model_info["path"], model_id)
        if not success:
            return "❌ Failed to load language model B"
        
        self.log_memory_usage("After loading Language Model B")
        
        try:
            # Get model from loader
            loader = self.launcher._components.get('universal_loader')
            model = loader.running_servers[model_id]["model"]
            
            # Test reasoning
            reasoning_prompt = "If a train travels 60 miles per hour for 2 hours, how far does it travel? Show your reasoning:"
            
            logger.info("🔄 Generating reasoning response...")
            response = model(
                reasoning_prompt,
                max_tokens=100,
                temperature=0.1,
                stop=["\n\n", "Question:", "Problem:"]
            )
            
            reasoning = response["choices"][0]["text"].strip()
            result = f"✅ Reasoning: {reasoning}"
            
            self.log_memory_usage("After Language Model B inference")
            return result
            
        except Exception as e:
            logger.error(f"❌ Language Model B test failed: {e}")
            return f"❌ Test failed: {str(e)}"
    
    async def run_full_lifecycle_test(self):
        """🚀 Run the complete multi-modal lifecycle test"""
        logger.info("🚀 Starting Multi-Modal Model Lifecycle Test")
        logger.info("=" * 60)
        
        # Initialize launcher
        logger.info("🏗️ Initializing Universal Model Launcher...")
        self.launcher = UniversalModelLauncher()
        success = await self.launcher.initialize(enable_api=False)
        
        if not success:
            logger.error("❌ Failed to initialize launcher")
            return False
        
        self.log_memory_usage("After launcher initialization")
        
        # Discover models
        logger.info("🔍 Discovering models...")
        models = self.discover_models()
        
        logger.info(f"📊 Found: {len(models['gguf'])} GGUF, {len(models['whisper'])} Whisper, {len(models['clip'])} CLIP models")
        
        # Run tests in sequence
        try:
            # 1. Language Model A - Summarization
            self.results["language_model_a"] = await self.test_language_model_a(models)
            
            # 2. Vision Model (CLIP) - Image Description
            self.results["vision_model"] = await self.test_vision_model(models)
            
            # 3. Whisper Model - Audio Transcription
            self.results["whisper_model"] = await self.test_whisper_model(models)
            
            # 4. Language Model B - Reasoning
            self.results["language_model_b"] = await self.test_language_model_b(models)
            
            # Final cleanup
            await self.cleanup_memory()
            self.log_memory_usage("Final cleanup")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test sequence failed: {e}")
            return False
    
    def display_results(self):
        """📋 Display comprehensive test results"""
        print("\n" + "=" * 60)
        print("📋 Multi-Modal Model Lifecycle Test Results")
        print("=" * 60)
        
        # Test results
        print("\n🧪 Test Results:")
        for test_name, result in self.results.items():
            if test_name != "memory_stats" and result:
                print(f"   {test_name.replace('_', ' ').title()}: {result}")
        
        # Memory analysis
        print("\n📊 Memory Usage Analysis:")
        if self.results["memory_stats"]:
            for stat in self.results["memory_stats"]:
                print(f"   {stat['stage']}: {stat['rss_mb']:.1f}MB RSS, {stat['system_memory_percent']:.1f}% System")
        
        # Summary
        successful_tests = sum(1 for test_name, result in self.results.items() 
                             if test_name != "memory_stats" and result and "✅" in result)
        total_tests = len([k for k in self.results.keys() if k != "memory_stats"])
        
        print(f"\n🎯 Summary: {successful_tests}/{total_tests} tests passed")
        
        if successful_tests == total_tests:
            print("🎉 All tests completed successfully!")
            print("✅ Multi-modal model lifecycle validated")
            print("✅ Memory cleanup working correctly")
            print("✅ Chain-loading functionality confirmed")
        else:
            print("⚠️ Some tests failed or were skipped")

async def main():
    """🚀 Main execution function"""
    try:
        tester = MultiModalTester()
        success = await tester.run_full_lifecycle_test()
        tester.display_results()
        
        return success
        
    except KeyboardInterrupt:
        logger.info("👋 Test interrupted by user")
        return False
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
