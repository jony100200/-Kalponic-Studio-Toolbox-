#!/usr/bin/env python3
"""
🖼️ Image Analysis Service - Local Integration
===========================================
Connects to Universal Model Launcher V4 for local vision model analysis
Local-first: Uses locally loaded CLIP/vision models, no external API calls
"""

import requests
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class LocalImageAnalyzer:
    """👁️ Local image analysis using UML V4 loaded models"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.vision_model = None
        
    def find_vision_model(self) -> Optional[str]:
        """🔍 Find available vision model from UML V4"""
        try:
            response = requests.get(f"{self.base_url}/models")
            if response.status_code == 200:
                models = response.json()
                # Look for loaded vision models
                for model in models.get('data', []):
                    model_id = model['id'].lower()
                    if any(keyword in model_id for keyword in ['clip', 'vision', 'llava', 'cogvlm']):
                        return model['id']
            return None
        except Exception as e:
            logger.error(f"Failed to find vision model: {e}")
            return None
    
    def analyze_image(self, image_file: Path, prompt: str = "Describe this image in detail") -> Dict[str, Any]:
        """📸 Analyze image using local vision model"""
        try:
            # Ensure we have a vision model loaded
            if not self.vision_model:
                self.vision_model = self.find_vision_model()
                if not self.vision_model:
                    return {"error": "No vision model loaded in Universal Model Launcher"}
            
            # Encode image to base64
            with open(image_file, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Prepare vision request
            payload = {
                "model": self.vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            # Send to local UML V4 vision endpoint
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                description = result['choices'][0]['message']['content']
                
                return {
                    "description": description,
                    "model_used": self.vision_model,
                    "image_file": str(image_file)
                }
            else:
                return {"error": f"Vision analysis failed: {response.text}"}
                
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return {"error": str(e)}
    
    def classify_image(self, image_file: Path, categories: List[str]) -> Dict[str, Any]:
        """🏷️ Classify image into categories"""
        categories_text = ", ".join(categories)
        prompt = f"Classify this image into one of these categories: {categories_text}. Respond with just the category name."
        
        result = self.analyze_image(image_file, prompt)
        if "error" not in result:
            result["classification"] = result["description"].strip()
        return result
    
    def extract_text_from_image(self, image_file: Path) -> Dict[str, Any]:
        """📝 Extract text from image (OCR)"""
        prompt = "Extract and transcribe all text visible in this image. If no text is present, respond with 'No text found'."
        return self.analyze_image(image_file, prompt)

# Example usage
if __name__ == "__main__":
    # Initialize local image analyzer
    analyzer = LocalImageAnalyzer()
    
    # Test with your image file
    image_file = Path("../Testing/image test.png")
    if image_file.exists():
        print(f"🖼️ Analyzing: {image_file.name}")
        
        # Get detailed description
        result = analyzer.analyze_image(image_file, "Describe this image in detail")
        
        if "error" not in result:
            print(f"✅ Success!")
            print(f"🤖 Model: {result.get('model_used')}")
            print(f"📝 Description: {result.get('description')}")
            
            # Try classification
            categories = ["screenshot", "photo", "diagram", "text", "chart", "interface"]
            classification = analyzer.classify_image(image_file, categories)
            if "error" not in classification:
                print(f"🏷️ Category: {classification.get('classification')}")
                
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print(f"❌ Image file not found: {image_file}")