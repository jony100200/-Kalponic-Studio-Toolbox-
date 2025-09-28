#!/usr/bin/env python3
"""
🔊 Audio Transcription Service - Local Integration
=================================================
Connects to Universal Model Launcher V4 for local Whisper transcription
Local-first: Uses locally loaded models, no external API calls
"""

import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class LocalAudioTranscriber:
    """🎵 Local audio transcription using UML V4 loaded models"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.whisper_model = None
        
    def find_whisper_model(self) -> Optional[str]:
        """🔍 Find available Whisper model from UML V4"""
        try:
            response = requests.get(f"{self.base_url}/models")
            if response.status_code == 200:
                models = response.json()
                # Look for loaded Whisper models
                for model in models.get('data', []):
                    if 'whisper' in model['id'].lower():
                        return model['id']
            return None
        except Exception as e:
            logger.error(f"Failed to find Whisper model: {e}")
            return None
    
    def transcribe_audio(self, audio_file: Path, output_format: str = "srt") -> Dict[str, Any]:
        """🎤 Transcribe audio file to text/SRT locally"""
        try:
            # Ensure we have a Whisper model loaded
            if not self.whisper_model:
                self.whisper_model = self.find_whisper_model()
                if not self.whisper_model:
                    return {"error": "No Whisper model loaded in Universal Model Launcher"}
            
            # Prepare transcription request
            with open(audio_file, 'rb') as f:
                files = {'file': f}
                data = {
                    'model': self.whisper_model,
                    'response_format': output_format,
                    'language': 'auto'  # Auto-detect language
                }
                
                # Send to local UML V4 transcription endpoint
                response = requests.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files=files,
                    data=data,
                    timeout=300  # 5 minutes for long audio
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Save SRT file if requested
                    if output_format == "srt" and "text" in result:
                        srt_file = audio_file.with_suffix('.srt')
                        with open(srt_file, 'w', encoding='utf-8') as f:
                            f.write(self._convert_to_srt(result))
                        result['srt_file'] = str(srt_file)
                    
                    return result
                else:
                    return {"error": f"Transcription failed: {response.text}"}
                    
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {"error": str(e)}
    
    def _convert_to_srt(self, transcription_result: Dict) -> str:
        """📝 Convert transcription to SRT format"""
        # This would convert the timestamp data to SRT format
        # Simplified example - you'd need to implement proper SRT formatting
        text = transcription_result.get('text', '')
        return f"1\n00:00:00,000 --> 00:00:10,000\n{text}\n\n"

# Example usage
if __name__ == "__main__":
    # Initialize local transcriber
    transcriber = LocalAudioTranscriber()
    
    # Test with your audio file
    audio_file = Path("../Testing/6.Local AI Model Launcher.mp3")
    if audio_file.exists():
        print(f"🎵 Transcribing: {audio_file.name}")
        result = transcriber.transcribe_audio(audio_file, "srt")
        
        if "error" not in result:
            print(f"✅ Success! SRT saved to: {result.get('srt_file')}")
            print(f"📝 Text: {result.get('text', '')[:200]}...")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print(f"❌ Audio file not found: {audio_file}")