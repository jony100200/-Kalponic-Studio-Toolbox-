"""
📡 Universal Client - OpenAI-Compatible Python Client

Features:
- OpenAI SDK-compatible interface
- Async support
- Streaming support
- Error handling
- Connection management
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, AsyncGenerator, Any, Union
from dataclasses import dataclass
import aiohttp
import requests
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str
    content: str

@dataclass
class ModelInfo:
    """Model information structure"""
    id: str
    object: str
    created: int
    owned_by: str = "local"

class UniversalClientError(Exception):
    """Base exception for client errors"""
    pass

class AuthenticationError(UniversalClientError):
    """Authentication failed"""
    pass

class RateLimitError(UniversalClientError):
    """Rate limit exceeded"""
    pass

class ModelNotFoundError(UniversalClientError):
    """Model not found"""
    pass

class UniversalClient:
    """
    Universal client for model launcher API with OpenAI compatibility.
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", 
                 api_key: Optional[str] = None, timeout: int = 60):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
        # OpenAI compatibility
        self.api_base = self.base_url
        self.api_version = "v1"
        
        logger.info(f"📡 Universal Client initialized for {self.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Universal-Model-Launcher-Client/4.0.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle HTTP response and errors"""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 404:
            raise ModelNotFoundError("Model not found")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        else:
            try:
                error_data = response.json()
                raise UniversalClientError(f"API Error: {error_data.get('detail', 'Unknown error')}")
            except json.JSONDecodeError:
                raise UniversalClientError(f"HTTP {response.status_code}: {response.text}")
    
    async def _handle_async_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle async HTTP response and errors"""
        if response.status == 200:
            return await response.json()
        elif response.status == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status == 404:
            raise ModelNotFoundError("Model not found")
        elif response.status == 429:
            raise RateLimitError("Rate limit exceeded")
        else:
            try:
                error_data = await response.json()
                raise UniversalClientError(f"API Error: {error_data.get('detail', 'Unknown error')}")
            except:
                text = await response.text()
                raise UniversalClientError(f"HTTP {response.status}: {text}")
    
    # Synchronous methods
    def list_models(self) -> List[ModelInfo]:
        """List available models"""
        response = requests.get(
            f"{self.base_url}/models",
            headers=self._get_headers(),
            timeout=self.timeout
        )
        
        data = self._handle_response(response)
        return [ModelInfo(**model) for model in data.get("data", [])]
    
    def load_model(self, model_name: str, model_path: str, 
                  backend: str = "auto", **kwargs) -> Dict[str, Any]:
        """Load a model"""
        payload = {
            "model_name": model_name,
            "model_path": model_path,
            "backend": backend,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/load_model",
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def unload_model(self, model_name: str) -> Dict[str, Any]:
        """Unload a model"""
        payload = {"model_name": model_name}
        
        response = requests.post(
            f"{self.base_url}/unload_model",
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def get_active_model(self) -> Dict[str, Any]:
        """Get active model information"""
        response = requests.get(
            f"{self.base_url}/active_model",
            headers=self._get_headers(),
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        response = requests.get(
            f"{self.base_url}/health",
            headers=self._get_headers(),
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def chat_completion(self, model: str, messages: List[ChatMessage], 
                       temperature: float = 0.7, max_tokens: int = 2048,
                       stream: bool = False, **kwargs) -> Union[Dict[str, Any], requests.Response]:
        """Create chat completion (OpenAI-compatible)"""
        payload = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout,
            stream=stream
        )
        
        if stream:
            return response  # Return response object for streaming
        else:
            return self._handle_response(response)
    
    def completion(self, model: str, prompt: str, temperature: float = 0.7,
                  max_tokens: int = 2048, stream: bool = False, **kwargs) -> Union[Dict[str, Any], requests.Response]:
        """Create text completion (OpenAI-compatible)"""
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/v1/completions",
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout,
            stream=stream
        )
        
        if stream:
            return response
        else:
            return self._handle_response(response)
    
    def stream_chat_completion(self, model: str, messages: List[ChatMessage], 
                              **kwargs) -> requests.Response:
        """Stream chat completion"""
        return self.chat_completion(model, messages, stream=True, **kwargs)
    
    def stream_completion(self, model: str, prompt: str, **kwargs) -> requests.Response:
        """Stream text completion"""
        return self.completion(model, prompt, stream=True, **kwargs)
    
    # Async methods
    async def _ensure_session(self):
        """Ensure async session is created"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close async session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def list_models_async(self) -> List[ModelInfo]:
        """List available models (async)"""
        await self._ensure_session()
        
        async with self.session.get(
            f"{self.base_url}/models",
            headers=self._get_headers()
        ) as response:
            data = await self._handle_async_response(response)
            return [ModelInfo(**model) for model in data.get("data", [])]
    
    async def load_model_async(self, model_name: str, model_path: str,
                              backend: str = "auto", **kwargs) -> Dict[str, Any]:
        """Load a model (async)"""
        await self._ensure_session()
        
        payload = {
            "model_name": model_name,
            "model_path": model_path,
            "backend": backend,
            **kwargs
        }
        
        async with self.session.post(
            f"{self.base_url}/load_model",
            headers=self._get_headers(),
            json=payload
        ) as response:
            return await self._handle_async_response(response)
    
    async def unload_model_async(self, model_name: str) -> Dict[str, Any]:
        """Unload a model (async)"""
        await self._ensure_session()
        
        payload = {"model_name": model_name}
        
        async with self.session.post(
            f"{self.base_url}/unload_model",
            headers=self._get_headers(),
            json=payload
        ) as response:
            return await self._handle_async_response(response)
    
    async def chat_completion_async(self, model: str, messages: List[ChatMessage],
                                   temperature: float = 0.7, max_tokens: int = 2048,
                                   **kwargs) -> Dict[str, Any]:
        """Create chat completion (async)"""
        await self._ensure_session()
        
        payload = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs
        }
        
        async with self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._get_headers(),
            json=payload
        ) as response:
            return await self._handle_async_response(response)
    
    async def stream_chat_completion_async(self, model: str, messages: List[ChatMessage],
                                          **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion (async)"""
        await self._ensure_session()
        
        payload = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": True,
            **kwargs
        }
        
        async with self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._get_headers(),
            json=payload
        ) as response:
            if response.status != 200:
                await self._handle_async_response(response)
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

# OpenAI-compatible wrapper classes
class Completions:
    """OpenAI-compatible completions interface"""
    
    def __init__(self, client: UniversalClient):
        self.client = client
    
    def create(self, model: str, prompt: str, **kwargs):
        """Create completion"""
        return self.client.completion(model, prompt, **kwargs)

class ChatCompletions:
    """OpenAI-compatible chat completions interface"""
    
    def __init__(self, client: UniversalClient):
        self.client = client
    
    def create(self, model: str, messages: List[Dict[str, str]], **kwargs):
        """Create chat completion"""
        chat_messages = [ChatMessage(role=msg["role"], content=msg["content"]) 
                        for msg in messages]
        return self.client.chat_completion(model, chat_messages, **kwargs)

class Chat:
    """OpenAI-compatible chat interface"""
    
    def __init__(self, client: UniversalClient):
        self.completions = ChatCompletions(client)

class OpenAICompatibleClient:
    """OpenAI-compatible client wrapper"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://127.0.0.1:8000"):
        self.client = UniversalClient(base_url=base_url, api_key=api_key)
        self.completions = Completions(self.client)
        self.chat = Chat(self.client)
    
    def list_models(self):
        """List models"""
        return self.client.list_models()

# WebSocket client for real-time communication
class WebSocketClient:
    """WebSocket client for real-time communication"""
    
    def __init__(self, base_url: str, client_id: str):
        self.base_url = base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        self.client_id = client_id
        self.websocket = None
    
    async def connect(self):
        """Connect to WebSocket"""
        import websockets
        self.websocket = await websockets.connect(f"{self.base_url}/ws/{self.client_id}")
        logger.info(f"WebSocket connected as {self.client_id}")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message via WebSocket"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
    
    async def receive_message(self) -> Dict[str, Any]:
        """Receive message from WebSocket"""
        if self.websocket:
            data = await self.websocket.recv()
            return json.loads(data)
    
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()

if __name__ == "__main__":
    # Example usage
    async def main():
        # Test basic client
        client = UniversalClient(base_url="http://127.0.0.1:8000")
        
        try:
            # Test health check
            health = client.health_check()
            print(f"Health: {health['status']}")
            
            # Test model listing
            models = client.list_models()
            print(f"Available models: {[model.id for model in models]}")
            
            # Test chat completion
            messages = [
                ChatMessage(role="user", content="Hello, how are you?")
            ]
            
            response = client.chat_completion(
                model="llama-7b",
                messages=messages,
                temperature=0.7
            )
            print(f"Chat response: {response['choices'][0]['message']['content']}")
            
            # Test OpenAI-compatible interface
            openai_client = OpenAICompatibleClient()
            openai_response = openai_client.chat.completions.create(
                model="llama-7b",
                messages=[{"role": "user", "content": "What is AI?"}]
            )
            print(f"OpenAI-compatible response: {openai_response['choices'][0]['message']['content']}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Run async example
    asyncio.run(main())
