from app.services.chat_strategy import ChatStrategy
from app.schema.chat_schema import ChatResponse
from app.constants import ENTERPRISE_COMPLIANCE_SYSTEM_PROMPT, DEFAULT_TEMPERATURE
from typing import AsyncGenerator, List
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
        
    async def send_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None, system_prompt: str = None) -> ChatResponse:
        """
        Send message (non-streaming)
        """
        full_response = ""
        async for chunk in self.stream_message(message, session_id, metadata, bot_id, system_prompt):
            full_response += chunk
            
        return ChatResponse(
            session_id=session_id,
            thread_id=session_id,
            role="assistant",
            content=full_response,
            provider="openai"
        )

    async def stream_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None, system_prompt: str = None) -> AsyncGenerator[str, None]:
        """
        Stream message using OpenAI-compatible API
        """
        logger.info(f"OpenAIService.stream_message called with message: {message[:50]}...")
        logger.info(f"OpenAIService API URL: {self.api_url}")
        logger.info(f"OpenAIService API Key: {self.api_key[:20]}...")
        
        base_endpoint = self.api_url.rstrip('/')
        if "openai.com" in base_endpoint or "v1" in base_endpoint:
            url = f"{base_endpoint}/chat/completions"
        else:
            url = f"{base_endpoint}/api/chat"
            
        logger.info(f"Using model: {self.model}, Full URL: {url}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Determine payload format
        is_openai = "completions" in url
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or ENTERPRISE_COMPLIANCE_SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            "stream": True,
            "temperature": DEFAULT_TEMPERATURE
        }
        
        try:
            chunk_count = 0
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    logger.info(f"Provider API response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Provider API error: {error_text}")
                        yield f"Error: API returned status {response.status}"
                        return
                    
                    async for line in response.content:
                        if not line:
                            continue
                            
                        decoded_line = line.decode('utf-8').strip()
                        if not decoded_line:
                            continue
                            
                        # Handle SSE format (data: {...})
                        if decoded_line.startswith("data: "):
                            if decoded_line == "data: [DONE]":
                                break
                            decoded_line = decoded_line[6:].strip()
                            
                        try:
                            data = json.loads(decoded_line)
                            content = None
                            
                            # Standard OpenAI format
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                            # Ollama / Custom format
                            elif 'message' in data and 'content' in data['message']:
                                content = data['message']['content']
                            elif 'response' in data: # Some providers use top-level 'response'
                                content = data['response']
                                
                            if content:
                                chunk_count += 1
                                yield content
                                
                            if data.get('done', False):
                                break
                                
                        except json.JSONDecodeError:
                            continue
                    
                    logger.debug(f"Stream ended, total chunks: {chunk_count}")
                                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error: {e}")
            yield f"Error: Connection failed - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            yield f"Error: {str(e)}"

