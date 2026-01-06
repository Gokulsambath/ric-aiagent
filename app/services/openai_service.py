from app.services.chat_strategy import ChatStrategy
from app.schema.chat_schema import ChatResponse
from typing import AsyncGenerator
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

class OpenAIService(ChatStrategy):
    def __init__(self):
        from app.configs.settings import settings
        self.api_key = settings.openai.api_key
        self.api_url = settings.openai.api_url
        self.model = settings.openai.model
        
    async def send_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None) -> ChatResponse:
        """
        Send message (non-streaming)
        """
        full_response = ""
        async for chunk in self.stream_message(message, session_id, metadata, bot_id):
            full_response += chunk
            
        return ChatResponse(
            session_id=session_id,
            role="assistant",
            content=full_response,
            provider="openai"
        )

    async def stream_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None) -> AsyncGenerator[str, None]:
        """
        Stream message using OpenAI-compatible API
        """
        logger.info(f"OpenAIService.stream_message called with message: {message[:50]}...")
        logger.info(f"Using model: {self.model}, API: {self.api_url}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "stream": True,
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/chat",  # Ollama Cloud uses /api/chat not /chat/completions
                    headers=headers,
                    json=payload
                ) as response:
                    logger.info(f"OpenAI API response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {error_text}")
                        yield f"Error: API returned status {response.status}"
                        return
                    
                    # Read SSE stream
                    async for line in response.content:
                        if line:
                            decoded_line = line.decode('utf-8').strip()
                            
                            if decoded_line.startswith('data: '):
                                data_str = decoded_line[6:]
                                
                                if data_str == '[DONE]':
                                    logger.info("Stream complete")
                                    break
                                    
                                try:
                                    data = json.loads(data_str)
                                    
                                    # Ollama Cloud uses 'message' format like local Ollama
                                    if 'message' in data:
                                        content = data['message'].get('content', '')
                                        if content:
                                            logger.debug(f"Yielding content: {content[:50]}")
                                            yield content
                                    # Fallback to OpenAI format
                                    elif 'choices' in data and len(data['choices']) > 0:
                                        delta = data['choices'][0].get('delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            logger.debug(f"Yielding content: {content[:50]}")
                                            yield content
                                            
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse JSON: {e}, line: {data_str[:100]}")
                                    continue
                                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error: {e}")
            yield f"Error: Connection failed - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            yield f"Error: {str(e)}"
