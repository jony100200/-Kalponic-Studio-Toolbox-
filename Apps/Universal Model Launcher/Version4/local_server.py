#!/usr/bin/env python3
"""
Minimal FastAPI server for local-first task processing
"""

import time
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(title="Local-First Task Processor")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    task_type: str
    input_path: str
    output_path: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "local_first": True}

@app.post("/process_task")
async def process_task(request: TaskRequest):
    """Local-first task processing"""
    start_time = time.time()

    input_path = Path(request.input_path)
    if not input_path.exists():
        raise HTTPException(status_code=404, detail=f"Input file not found: {request.input_path}")

    # Local processing based on task type
    if request.task_type == "code_analysis":
        try:
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            lines = len(content.split('\n'))
            chars = len(content)
            keywords = ['def ', 'class ', 'function ', 'if ', 'for ', 'while ']
            keyword_count = sum(content.count(kw) for kw in keywords)

            result = {
                "analysis": f"Local scan: {lines} lines, {chars:,} chars, ~{keyword_count} keywords in {input_path.suffix}",
                "language": input_path.suffix[1:],
                "lines": lines,
                "characters": chars,
                "estimated_complexity": "Low" if lines < 100 else "Medium" if lines < 500 else "High",
                "local_processing": True,
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            result = {"error": f"Local processing failed: {str(e)}"}

    elif request.task_type == "image_analysis":
        file_size = input_path.stat().st_size
        result = {
            "analysis": f"Local image scan: {input_path.name} ({file_size:,} bytes {input_path.suffix})",
            "format": input_path.suffix,
            "size_bytes": file_size,
            "local_processing": True,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }

    elif request.task_type == "audio_transcription":
        file_size = input_path.stat().st_size
        result = {
            "transcription": f"Local audio scan: {input_path.name} ({file_size:,} bytes)",
            "format": input_path.suffix,
            "estimated_duration": f"{file_size // 16000}s",
            "local_processing": True,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }

    else:
        result = {"error": f"Unsupported task type: {request.task_type}"}

    # Save output if requested
    if request.output_path:
        output_dir = Path(request.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(request.output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    return {
        "task_type": request.task_type,
        "input_path": str(input_path),
        "output_path": request.output_path,
        "model_used": "local_fast_mode",
        "result": result,
        "timestamp": time.time(),
        "local_first": True,
        "total_time_ms": int((time.time() - start_time) * 1000)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Local-First Task Processor...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")