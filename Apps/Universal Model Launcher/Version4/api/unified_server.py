"""
🌐 Unified Server - All-in-One FastAPI Server

Features:
- Native endpoints (/load_model, /unload_model)
- OpenAI-compatible endpoints (/v1/chat/completions)
- WebSocket streaming
- Request routing
- Health monitoring
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("FastAPI dependencies not installed. Run: pip install fastapi uvicorn pydantic")
    exit(1)

# Import our components
import sys
sys.path.append(str(Path(__file__).parent.parent))
from loader.universal_loader import UniversalLoader
from loader.health_monitor import HealthMonitor
from loader.process_manager import ProcessManager
from api.security_middleware import SecurityMiddleware, create_fastapi_middleware

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class LoadModelRequest(BaseModel):
    model_name: str = Field(..., description="Name of the model to load")
    model_path: str = Field(..., description="Path to the model file")
    backend: Optional[str] = Field("auto", description="Backend to use (auto, llama.cpp, transformers)")
    context_length: Optional[int] = Field(4096, description="Context length")
    gpu_layers: Optional[int] = Field(-1, description="Number of GPU layers (-1 for auto)")
    quantization: Optional[str] = Field("auto", description="Quantization type")

class UnloadModelRequest(BaseModel):
    model_name: str = Field(..., description="Name of the model to unload")

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")

class OpenAIChatRequest(BaseModel):
    model: str = Field(..., description="Model to use")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(2048, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Enable streaming")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")

class OpenAICompletionRequest(BaseModel):
    model: str = Field(..., description="Model to use")
    prompt: str = Field(..., description="Text prompt")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(2048, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Enable streaming")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")

@dataclass
class WebSocketConnection:
    """WebSocket connection tracking"""
    websocket: WebSocket
    client_id: str
    connected_at: float

class UnifiedServer:
    """
    Unified FastAPI server with native and OpenAI-compatible endpoints.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        
        # Initialize core components
        self.loader = UniversalLoader()
        self.health_monitor = HealthMonitor()
        self.process_manager = ProcessManager()
        self.security = SecurityMiddleware()
        
        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocketConnection] = {}
        
        # Initialize FastAPI app
        self.app = self._create_app()
        
        logger.info("🌐 Unified Server initialized")
    
    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        app = FastAPI(
            title="Universal Model Launcher API",
            description="Unified API for model loading and inference",
            version="4.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add security middleware
        app.middleware("http")(create_fastapi_middleware(self.security))
        
        self._setup_routes(app)
        return app
    
    def _setup_routes(self, app: FastAPI):
        """Setup all API routes"""
        
        # Health endpoints
        @app.get("/health")
        async def health_check():
            """System health check"""
            health_status = self.health_monitor.get_current_status()
            return {"status": "healthy", "timestamp": time.time(), "details": health_status}
        
        @app.get("/models")
        async def list_models():
            """List available models"""
            # This would typically query a model registry
            return {
                "object": "list",
                "data": [
                    {"id": "llama-7b", "object": "model", "created": int(time.time())},
                    {"id": "mistral-7b", "object": "model", "created": int(time.time())}
                ]
            }
        
        # Native model management endpoints
        @app.post("/load_model")
        async def load_model(request: LoadModelRequest):
            """Load a model"""
            try:
                result = await self._load_model_async(
                    request.model_name,
                    request.model_path,
                    request.backend,
                    request.context_length,
                    request.gpu_layers,
                    request.quantization
                )
                return {"success": True, "data": result}
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/unload_model")
        async def unload_model(request: UnloadModelRequest):
            """Unload a model"""
            try:
                result = await self._unload_model_async(request.model_name)
                return {"success": True, "data": result}
            except Exception as e:
                logger.error(f"Failed to unload model: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/active_model")
        async def get_active_model():
            """Get information about currently active model"""
            try:
                active_models = self.loader.get_loaded_models()
                process_summary = self.process_manager.get_process_summary()
                
                return {
                    "active_models": active_models,
                    "process_summary": process_summary,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Failed to get active model info: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # OpenAI-compatible endpoints
        @app.get("/v1/models")
        async def openai_list_models():
            """OpenAI-compatible model listing"""
            return await list_models()
        
        @app.post("/v1/chat/completions")
        async def openai_chat_completions(request: OpenAIChatRequest):
            """OpenAI-compatible chat completions"""
            try:
                if request.stream:
                    return StreamingResponse(
                        self._stream_chat_completion(request),
                        media_type="text/plain"
                    )
                else:
                    response = await self._chat_completion(request)
                    return response
            except Exception as e:
                logger.error(f"Chat completion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/v1/completions")
        async def openai_completions(request: OpenAICompletionRequest):
            """OpenAI-compatible text completions"""
            try:
                if request.stream:
                    return StreamingResponse(
                        self._stream_completion(request),
                        media_type="text/plain"
                    )
                else:
                    response = await self._completion(request)
                    return response
            except Exception as e:
                logger.error(f"Completion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # WebSocket endpoint for real-time streaming
        @app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """WebSocket endpoint for real-time communication"""
            await self._handle_websocket(websocket, client_id)
        
        # Management endpoints
        @app.get("/stats")
        async def get_stats():
            """Get server statistics"""
            return {
                "websocket_connections": len(self.websocket_connections),
                "health_status": self.health_monitor.get_current_status(),
                "process_summary": self.process_manager.get_process_summary(),
                "security_status": {
                    "api_keys_configured": len(self.security.config.api_keys) > 0,
                    "rate_limiting_enabled": True
                }
            }
    
    async def _load_model_async(self, model_name: str, model_path: str, 
                               backend: str, context_length: int, 
                               gpu_layers: int, quantization: str) -> Dict:
        """Async model loading"""
        # This would interface with our loader components
        result = self.loader.load_model(
            model_path=model_path,
            backend=backend,
            context_length=context_length,
            gpu_layers=gpu_layers,
            quantization=quantization
        )
        return {"model_name": model_name, "status": "loaded", "result": result}
    
    async def _unload_model_async(self, model_name: str) -> Dict:
        """Async model unloading"""
        result = self.loader.unload_model(model_name)
        return {"model_name": model_name, "status": "unloaded", "result": result}
    
    async def _chat_completion(self, request: OpenAIChatRequest) -> Dict:
        """Process chat completion request"""
        # Convert messages to prompt format
        prompt = self._messages_to_prompt(request.messages)
        
        # This would interface with the loaded model
        response_text = f"This is a simulated response to: {prompt[:100]}..."
        
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split())
            }
        }
    
    async def _completion(self, request: OpenAICompletionRequest) -> Dict:
        """Process completion request"""
        # This would interface with the loaded model
        response_text = f"Completion for: {request.prompt[:50]}..."
        
        return {
            "id": f"cmpl-{int(time.time())}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "text": response_text,
                "index": 0,
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(request.prompt.split()) + len(response_text.split())
            }
        }
    
    async def _stream_chat_completion(self, request: OpenAIChatRequest) -> AsyncGenerator[str, None]:
        """Stream chat completion response"""
        prompt = self._messages_to_prompt(request.messages)
        
        # Simulate streaming response
        response_text = f"Streaming response to: {prompt[:100]}..."
        words = response_text.split()
        
        for i, word in enumerate(words):
            chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": word + " "},
                    "finish_reason": None if i < len(words) - 1 else "stop"
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.1)  # Simulate processing time
        
        yield "data: [DONE]\n\n"
    
    async def _stream_completion(self, request: OpenAICompletionRequest) -> AsyncGenerator[str, None]:
        """Stream completion response"""
        response_text = f"Streaming completion for: {request.prompt[:50]}..."
        words = response_text.split()
        
        for i, word in enumerate(words):
            chunk = {
                "id": f"cmpl-{int(time.time())}",
                "object": "text_completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "text": word + " ",
                    "index": 0,
                    "finish_reason": None if i < len(words) - 1 else "stop"
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.1)
        
        yield "data: [DONE]\n\n"
    
    def _messages_to_prompt(self, messages: List[ChatMessage]) -> str:
        """Convert chat messages to prompt format"""
        prompt_parts = []
        for message in messages:
            prompt_parts.append(f"{message.role}: {message.content}")
        return "\n".join(prompt_parts)
    
    async def _handle_websocket(self, websocket: WebSocket, client_id: str):
        """Handle WebSocket connection"""
        await websocket.accept()
        
        connection = WebSocketConnection(
            websocket=websocket,
            client_id=client_id,
            connected_at=time.time()
        )
        self.websocket_connections[client_id] = connection
        
        logger.info(f"WebSocket connected: {client_id}")
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "chat":
                    # Process chat message
                    response = {
                        "type": "chat_response",
                        "content": f"Echo: {message.get('content', '')}",
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(response))
                
                elif message.get("type") == "health_check":
                    # Send health status
                    health_status = self.health_monitor.get_current_status()
                    response = {
                        "type": "health_status",
                        "data": health_status,
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(response))
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {client_id}")
            del self.websocket_connections[client_id]
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]
    
    async def broadcast_to_websockets(self, message: Dict):
        """Broadcast message to all connected WebSockets"""
        if not self.websocket_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for client_id, connection in self.websocket_connections.items():
            try:
                await connection.websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            del self.websocket_connections[client_id]
    
    def start_server(self):
        """Start the server"""
        logger.info(f"🚀 Starting Unified Server on {self.host}:{self.port}")
        
        # Start health monitoring
        self.health_monitor.start_monitoring()
        
        try:
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        finally:
            self.health_monitor.stop_monitoring()
    
    def stop_server(self):
        """Stop the server gracefully"""
        logger.info("🛑 Stopping Unified Server")
        self.health_monitor.stop_monitoring()

if __name__ == "__main__":
    # Example usage
    server = UnifiedServer(host="127.0.0.1", port=8000)
    server.start_server()
