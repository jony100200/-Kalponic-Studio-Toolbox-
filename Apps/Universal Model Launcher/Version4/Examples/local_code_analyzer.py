#!/usr/bin/env python3
"""
💻 Code Analysis Service - Local Integration
==========================================
Connects to Universal Model Launcher V4 for local code analysis
Local-first: Uses locally loaded code models (CodeLlama, etc.), no external API calls
"""

import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class LocalCodeAnalyzer:
    """🔍 Local code analysis using UML V4 loaded models"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.code_model = None
        
    def find_code_model(self) -> Optional[str]:
        """🔍 Find available code model from UML V4"""
        try:
            response = requests.get(f"{self.base_url}/models")
            if response.status_code == 200:
                models = response.json()
                # Look for loaded code models (prioritize code-specific models)
                code_keywords = ['code', 'codellama', 'starcoder', 'deepseek-coder', 'codeqwen']
                
                for model in models.get('data', []):
                    model_id = model['id'].lower()
                    if any(keyword in model_id for keyword in code_keywords):
                        return model['id']
                
                # Fallback to any text model if no code-specific model found
                for model in models.get('data', []):
                    if model.get('object') == 'model':
                        return model['id']
                        
            return None
        except Exception as e:
            logger.error(f"Failed to find code model: {e}")
            return None
    
    def analyze_code(self, code_file: Path, task: str = "analyze") -> Dict[str, Any]:
        """🔍 Analyze code file using local model"""
        try:
            # Ensure we have a code model loaded
            if not self.code_model:
                self.code_model = self.find_code_model()
                if not self.code_model:
                    return {"error": "No suitable model loaded in Universal Model Launcher"}
            
            # Read code file
            with open(code_file, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # Prepare analysis prompt based on task
            prompts = {
                "analyze": "Analyze this code and provide a detailed explanation of what it does, its structure, and key functionality:",
                "explain": "Explain this code step by step in simple terms:",
                "review": "Review this code for potential issues, improvements, and best practices:",
                "document": "Generate comprehensive documentation for this code:",
                "refactor": "Suggest refactoring improvements for this code:",
                "debug": "Help debug this code by identifying potential issues:"
            }
            
            prompt = prompts.get(task, prompts["analyze"])
            
            # Prepare request
            payload = {
                "model": self.code_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert code analyst. Provide clear, detailed analysis of code."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\n```{code_file.suffix[1:]}\n{code_content}\n```"
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            # Send to local UML V4 completion endpoint
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                
                return {
                    "analysis": analysis,
                    "task": task,
                    "model_used": self.code_model,
                    "file_analyzed": str(code_file),
                    "language": code_file.suffix[1:] if code_file.suffix else "unknown"
                }
            else:
                return {"error": f"Code analysis failed: {response.text}"}
                
        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return {"error": str(e)}
    
    def get_code_summary(self, code_file: Path) -> Dict[str, Any]:
        """📋 Get brief summary of code functionality"""
        return self.analyze_code(code_file, "analyze")
    
    def review_code(self, code_file: Path) -> Dict[str, Any]:
        """👀 Review code for issues and improvements"""
        return self.analyze_code(code_file, "review")
    
    def explain_code(self, code_file: Path) -> Dict[str, Any]:
        """🎓 Get step-by-step explanation"""
        return self.analyze_code(code_file, "explain")
    
    def generate_docs(self, code_file: Path) -> Dict[str, Any]:
        """📚 Generate documentation"""
        result = self.analyze_code(code_file, "document")
        
        # Save documentation to file if successful
        if "error" not in result:
            doc_file = code_file.with_suffix('.md')
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(f"# Documentation for {code_file.name}\n\n")
                f.write(result.get('analysis', ''))
            result['doc_file'] = str(doc_file)
        
        return result

# Example usage
if __name__ == "__main__":
    # Initialize local code analyzer
    analyzer = LocalCodeAnalyzer()
    
    # Test with your code file
    code_file = Path("../Testing/PlayerMovement.cs")
    if code_file.exists():
        print(f"💻 Analyzing: {code_file.name}")
        
        # Get code analysis
        result = analyzer.get_code_summary(code_file)
        
        if "error" not in result:
            print(f"✅ Success!")
            print(f"🤖 Model: {result.get('model_used')}")
            print(f"🔍 Language: {result.get('language')}")
            print(f"📝 Analysis:\n{result.get('analysis')}")
            
            # Generate documentation
            print(f"\n📚 Generating documentation...")
            doc_result = analyzer.generate_docs(code_file)
            if "error" not in doc_result:
                print(f"✅ Documentation saved to: {doc_result.get('doc_file')}")
                
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print(f"❌ Code file not found: {code_file}")