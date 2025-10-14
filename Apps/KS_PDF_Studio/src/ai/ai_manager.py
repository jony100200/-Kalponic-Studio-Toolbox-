"""
KS PDF Studio - AI Integration Module
AI-powered content generation and image processing for tutorial creation.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import warnings

from transformers import (
    pipeline, AutoTokenizer, AutoModelForCausalLM,
    CLIPProcessor, CLIPModel, AutoImageProcessor
)
import torch
from PIL import Image as PILImage
import requests
from tqdm import tqdm


class AIModelManager:
    """
    Manages AI model loading, caching, and inference for KS PDF Studio.

    Features:
    - Lazy model loading to save memory
    - Automatic model downloading with user consent
    - Local caching for offline use
    - GPU acceleration when available
    - Model size optimization
    """

    # Model configurations
    MODELS = {
        'distilbart': {
            'name': 'sshleifer/distilbart-cnn-12-6',
            'type': 'summarization',
            'size_mb': 300,
            'description': 'Content generation and summarization'
        },
        'clip': {
            'name': 'openai/clip-vit-base-patch32',
            'type': 'vision',
            'size_mb': 600,
            'description': 'Image-text matching and relevance scoring'
        }
    }

    def __init__(self, cache_dir: Optional[Union[str, Path]] = None, device: str = 'auto'):
        """
        Initialize the AI model manager.

        Args:
            cache_dir: Directory for model caching
            device: Device for inference ('auto', 'cpu', 'cuda')
        """
        # Default to a project-local models folder so models are stored inside the application
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # place models folder next to the src package root
            project_root = Path(__file__).resolve().parents[1]
            self.cache_dir = project_root / 'models'

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Determine device
        if device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        # Model instances (lazy loaded)
        self._models = {}
        self._tokenizers = {}
        self._processors = {}

        # Configuration
        self.config_file = self.cache_dir / 'config.json'
        self._load_config()

        print(f"🤖 AI Model Manager initialized (device: {self.device})")

    def _load_config(self) -> None:
        """Load model configuration and download status."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}

        # Initialize default config
        for model_key, model_info in self.MODELS.items():
            if model_key not in self.config:
                self.config[model_key] = {
                    'downloaded': False,
                    'version': None,
                    'last_used': None,
                    'size_mb': model_info['size_mb']
                }

    def _save_config(self) -> None:
        """Save model configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def is_model_available(self, model_key: str) -> bool:
        """
        Check if a model is downloaded and available.

        Args:
            model_key: Model identifier ('distilbart' or 'clip')

        Returns:
            bool: True if model is available
        """
        if model_key not in self.MODELS:
            return False

        return self.config.get(model_key, {}).get('downloaded', False)

    def download_model(self, model_key: str, show_progress: bool = True) -> bool:
        """
        Download and cache a model.

        Args:
            model_key: Model to download
            show_progress: Show download progress

        Returns:
            bool: True if download successful
        """
        if model_key not in self.MODELS:
            raise ValueError(f"Unknown model: {model_key}")

        if self.is_model_available(model_key):
            print(f"✅ Model {model_key} already available")
            return True

        model_info = self.MODELS[model_key]
        print(f"📥 Downloading {model_key} ({model_info['size_mb']}MB)...")

        try:
            # Download based on model type
            if model_key == 'distilbart':
                self._download_distilbart(show_progress)
            elif model_key == 'clip':
                self._download_clip(show_progress)

            # Update config
            self.config[model_key]['downloaded'] = True
            self.config[model_key]['version'] = 'latest'
            self._save_config()

            print(f"✅ Model {model_key} downloaded successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to download {model_key}: {e}")
            return False

    def _download_distilbart(self, show_progress: bool = True) -> None:
        """Download DistilBART model."""
        model_name = self.MODELS['distilbart']['name']

        # Create summarization pipeline (downloads model automatically)
        self._models['distilbart'] = pipeline(
            'summarization',
            model=model_name,
            device=0 if self.device == 'cuda' else -1
        )

    def _download_clip(self, show_progress: bool = True) -> None:
        """Download CLIP model."""
        model_name = self.MODELS['clip']['name']

        # Download model and processor
        self._models['clip'] = CLIPModel.from_pretrained(model_name)
        self._processors['clip'] = CLIPProcessor.from_pretrained(model_name)

        # Move to device
        if self.device == 'cuda':
            self._models['clip'] = self._models['clip'].to('cuda')

    def load_model(self, model_key: str) -> bool:
        """
        Load a model into memory.

        Args:
            model_key: Model to load

        Returns:
            bool: True if loaded successfully
        """
        if model_key not in self.MODELS:
            raise ValueError(f"Unknown model: {model_key}")

        if not self.is_model_available(model_key):
            raise RuntimeError(f"Model {model_key} not downloaded. Call download_model() first.")

        if model_key in self._models:
            # Already loaded
            return True

        try:
            if model_key == 'distilbart':
                self._load_distilbart()
            elif model_key == 'clip':
                self._load_clip()

            # Update last used timestamp
            import time
            self.config[model_key]['last_used'] = time.time()
            self._save_config()

            return True

        except Exception as e:
            print(f"❌ Failed to load {model_key}: {e}")
            return False

    def _load_distilbart(self) -> None:
        """Load DistilBART model."""
        if 'distilbart' not in self._models:
            model_name = self.MODELS['distilbart']['name']
            self._models['distilbart'] = pipeline(
                'summarization',
                model=model_name,
                device=0 if self.device == 'cuda' else -1
            )

    def _load_clip(self) -> None:
        """Load CLIP model."""
        if 'clip' not in self._models:
            model_name = self.MODELS['clip']['name']
            self._models['clip'] = CLIPModel.from_pretrained(model_name)
            self._processors['clip'] = CLIPProcessor.from_pretrained(model_name)

            if self.device == 'cuda':
                self._models['clip'] = self._models['clip'].to('cuda')

    def unload_model(self, model_key: str) -> None:
        """
        Unload a model from memory to free resources.

        Args:
            model_key: Model to unload
        """
        if model_key in self._models:
            del self._models[model_key]

        if model_key in self._processors:
            del self._processors[model_key]

        # Force garbage collection
        import gc
        gc.collect()

        if self.device == 'cuda':
            torch.cuda.empty_cache()

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models."""
        info = {
            'device': self.device,
            'cache_dir': str(self.cache_dir),
            'models': {}
        }

        for model_key, model_info in self.MODELS.items():
            info['models'][model_key] = {
                'available': self.is_model_available(model_key),
                'size_mb': model_info['size_mb'],
                'description': model_info['description'],
                'loaded': model_key in self._models,
                'type': model_info['type']
            }

        return info

    @property
    def models(self) -> Dict[str, Dict[str, Any]]:
        """Get available models information."""
        return self.get_model_info()['models']

    def cleanup_cache(self, max_age_days: int = 30) -> int:
        """
        Clean up old cached models.

        Args:
            max_age_days: Maximum age in days for cached models

        Returns:
            int: Number of files cleaned up
        """
        # This is a simplified cleanup - in practice, you'd want more sophisticated cache management
        cleaned = 0

        try:
            import time
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

            for model_key in self.config:
                last_used = self.config[model_key].get('last_used')
                if last_used and last_used < cutoff_time:
                    # Unload if loaded
                    self.unload_model(model_key)
                    # Reset downloaded status (will require re-download)
                    self.config[model_key]['downloaded'] = False
                    cleaned += 1

            if cleaned > 0:
                self._save_config()

        except Exception as e:
            print(f"Cache cleanup failed: {e}")

        return cleaned


class ContentGenerator:
    """
    AI-powered content generation for tutorials using DistilBART.
    """

    def __init__(self, model_manager: AIModelManager):
        """
        Initialize content generator.

        Args:
            model_manager: AIModelManager instance
        """
        self.model_manager = model_manager
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load content generation templates."""
        return {
            'tutorial_intro': "Write an engaging introduction for a tutorial about {topic}. Include what readers will learn and why it's important.",

            'section_content': "Expand on the following section topic for a tutorial: {topic}. Provide detailed explanations, examples, and practical advice.",

            'code_explanation': "Explain the following code concept in simple terms for beginners: {concept}. Include examples and common use cases.",

            'conclusion': "Write a conclusion for a tutorial about {topic}. Summarize key points and suggest next steps for learning.",

            'exercise': "Create a practical exercise for learning {topic}. Include instructions, expected output, and hints.",

            'troubleshooting': "Write a troubleshooting section for common issues with {topic}. Include symptoms, causes, and solutions."
        }

    def generate_content(
        self,
        prompt: str,
        content_type: str = 'general',
        max_length: int = 200,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate tutorial content using AI.

        Args:
            prompt: Input prompt or topic
            content_type: Type of content ('intro', 'section', 'code', 'conclusion', etc.)
            max_length: Maximum length of generated content
            temperature: Creativity level (0.0-1.0)

        Returns:
            Dict with generated content and metadata
        """
        if not self.model_manager.is_model_available('distilbart'):
            raise RuntimeError("DistilBART model not available. Please download it first.")

        # Load model if not already loaded
        self.model_manager.load_model('distilbart')

        try:
            # Prepare prompt
            if content_type in self.templates:
                full_prompt = self.templates[content_type].format(topic=prompt)
            else:
                full_prompt = prompt

            # Generate content
            generator = self.model_manager._models['distilbart']

            result = generator(
                full_prompt,
                max_length=max_length,
                min_length=max(50, max_length // 4),
                do_sample=temperature > 0,
                temperature=temperature,
                num_return_sequences=1,
                truncation=True
            )

            generated_text = result[0]['summary_text']

            return {
                'content': generated_text,
                'type': content_type,
                'prompt': prompt,
                'length': len(generated_text),
                'model': 'distilbart',
                'parameters': {
                    'max_length': max_length,
                    'temperature': temperature
                }
            }

        except Exception as e:
            return {
                'error': str(e),
                'content': '',
                'type': content_type,
                'prompt': prompt
            }

    def expand_outline(self, outline: List[str]) -> List[Dict[str, Any]]:
        """
        Expand a tutorial outline into detailed sections.

        Args:
            outline: List of section titles

        Returns:
            List of expanded sections with content
        """
        expanded_sections = []

        for section_title in outline:
            section_content = self.generate_content(
                section_title,
                content_type='section_content',
                max_length=300
            )

            expanded_sections.append({
                'title': section_title,
                'content': section_content.get('content', ''),
                'type': 'section',
                'generated': True
            })

        return expanded_sections

    def create_tutorial_structure(
        self,
        topic: str,
        difficulty: str = 'beginner'
    ) -> Dict[str, Any]:
        """
        Create a complete tutorial structure for a topic.

        Args:
            topic: Main tutorial topic
            difficulty: Difficulty level ('beginner', 'intermediate', 'advanced')

        Returns:
            Complete tutorial structure
        """
        # Generate introduction
        intro = self.generate_content(topic, 'tutorial_intro', max_length=150)

        # Generate main sections based on difficulty
        sections = []
        if difficulty == 'beginner':
            section_templates = [
                f"Getting Started with {topic}",
                f"Basic Concepts in {topic}",
                f"First {topic} Project",
                f"Common {topic} Patterns"
            ]
        elif difficulty == 'intermediate':
            section_templates = [
                f"Advanced {topic} Techniques",
                f"{topic} Best Practices",
                f"Real-world {topic} Applications",
                f"Debugging {topic} Issues"
            ]
        else:  # advanced
            section_templates = [
                f"Expert {topic} Strategies",
                f"{topic} Performance Optimization",
                f"Custom {topic} Implementations",
                f"{topic} Architecture Patterns"
            ]

        for section_title in section_templates:
            section = self.generate_content(section_title, 'section_content', max_length=250)
            sections.append({
                'title': section_title,
                'content': section.get('content', ''),
                'level': 2
            })

        # Generate conclusion
        conclusion = self.generate_content(topic, 'conclusion', max_length=150)

        return {
            'title': f"{topic} Tutorial",
            'difficulty': difficulty,
            'introduction': intro.get('content', ''),
            'sections': sections,
            'conclusion': conclusion.get('content', ''),
            'generated': True,
            'topic': topic
        }


class ImageMatcher:
    """
    CLIP-powered image-text matching for tutorial content.
    """

    def __init__(self, model_manager: AIModelManager):
        """
        Initialize image matcher.

        Args:
            model_manager: AIModelManager instance
        """
        self.model_manager = model_manager

    def find_relevant_images(
        self,
        text_content: str,
        image_paths: List[Union[str, Path]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find images most relevant to the given text content.

        Args:
            text_content: Text content to match against
            image_paths: List of image file paths
            top_k: Number of top matches to return

        Returns:
            List of matched images with relevance scores
        """
        if not self.model_manager.is_model_available('clip'):
            raise RuntimeError("CLIP model not available. Please download it first.")

        # Load model if not already loaded
        self.model_manager.load_model('clip')

        try:
            model = self.model_manager._models['clip']
            processor = self.model_manager._processors['clip']

            # Process text
            text_inputs = processor(text=text_content, return_tensors="pt", padding=True, truncation=True)
            if self.model_manager.device == 'cuda':
                text_inputs = {k: v.to('cuda') for k, v in text_inputs.items()}

            with torch.no_grad():
                text_features = model.get_text_features(**text_inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Process images and calculate similarities
            image_matches = []

            for image_path in image_paths:
                try:
                    # Load and process image
                    image = PILImage.open(image_path).convert('RGB')
                    image_inputs = processor(images=image, return_tensors="pt")
                    if self.model_manager.device == 'cuda':
                        image_inputs = {k: v.to('cuda') for k, v in image_inputs.items()}

                    with torch.no_grad():
                        image_features = model.get_image_features(**image_inputs)
                        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

                        # Calculate similarity
                        similarity = torch.cosine_similarity(text_features, image_features).item()

                    image_matches.append({
                        'path': str(image_path),
                        'filename': Path(image_path).name,
                        'similarity': similarity,
                        'relevance_score': similarity  # Could be enhanced with additional scoring
                    })

                except Exception as e:
                    print(f"Failed to process image {image_path}: {e}")
                    continue

            # Sort by similarity and return top matches
            image_matches.sort(key=lambda x: x['similarity'], reverse=True)
            return image_matches[:top_k]

        except Exception as e:
            print(f"Image matching failed: {e}")
            return []

    def suggest_image_placement(
        self,
        markdown_content: str,
        available_images: List[Union[str, Path]]
    ) -> List[Dict[str, Any]]:
        """
        Suggest where to place images in markdown content.

        Args:
            markdown_content: Markdown content
            available_images: List of available image paths

        Returns:
            List of placement suggestions
        """
        # Extract text sections from markdown
        sections = self._extract_markdown_sections(markdown_content)

        suggestions = []

        for section in sections:
            if len(section['text']) > 50:  # Only process substantial sections
                matches = self.find_relevant_images(section['text'], available_images, top_k=3)

                if matches and matches[0]['similarity'] > 0.2:  # Minimum relevance threshold
                    suggestions.append({
                        'section_title': section['title'],
                        'section_level': section['level'],
                        'suggested_image': matches[0]['path'],
                        'confidence': matches[0]['similarity'],
                        'alternatives': [m['path'] for m in matches[1:]]
                    })

        return suggestions

    def _extract_markdown_sections(self, markdown_content: str) -> List[Dict[str, str]]:
        """Extract sections and their text content from markdown."""
        sections = []
        lines = markdown_content.split('\n')

        current_section = {'title': 'Introduction', 'text': '', 'level': 1}

        for line in lines:
            line = line.strip()

            # Check for headers
            if line.startswith('#'):
                # Save previous section
                if current_section['text'].strip():
                    sections.append(current_section)

                # Start new section
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                current_section = {
                    'title': title,
                    'text': '',
                    'level': level
                }
            else:
                # Add content to current section
                if line:
                    current_section['text'] += line + ' '

        # Add final section
        if current_section['text'].strip():
            sections.append(current_section)

        return sections


# Convenience functions
def initialize_ai_manager(cache_dir: Optional[str] = None) -> AIModelManager:
    """Initialize AI model manager."""
    return AIModelManager(cache_dir)


def generate_tutorial_content(topic: str, **kwargs) -> Dict[str, Any]:
    """Quick function to generate tutorial content."""
    manager = AIModelManager()
    generator = ContentGenerator(manager)
    return generator.generate_content(topic, **kwargs)


def find_best_images(text: str, images: List[str], **kwargs) -> List[Dict[str, Any]]:
    """Quick function to find relevant images."""
    manager = AIModelManager()
    matcher = ImageMatcher(manager)
    return matcher.find_relevant_images(text, images, **kwargs)


if __name__ == "__main__":
    # Test the AI integration
    print("🧪 Testing AI Integration Module...")

    # Initialize manager
    manager = initialize_ai_manager()

    # Check model availability
    info = manager.get_model_info()
    print(f"Device: {info['device']}")
    print(f"Cache dir: {info['cache_dir']}")

    for model_key, model_info in info['models'].items():
        status = "✅ Available" if model_info['available'] else "❌ Not downloaded"
        print(f"{model_key}: {status} ({model_info['size_mb']}MB)")

    print("\nAI Integration module initialized successfully!")
    print("Note: Models will be downloaded on first use with user consent.")