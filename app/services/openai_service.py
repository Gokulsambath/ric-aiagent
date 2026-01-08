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
        logger.info(f"Using model: {self.model}, API: {self.api_url}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
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
            # Disable SSL verification for testing/internal calls
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
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
                    
                    # Read response stream
                    logger.debug("Starting to read response stream...")
                    chunk_count = 0
                    async for line in response.content:
                        if line:
                            chunk_count += 1
                            decoded_line = line.decode('utf-8').strip()
                            
                            if not decoded_line:
                                continue
                            
                            # Ollama Cloud returns raw JSON, not SSE format
                            try:
                                data = json.loads(decoded_line)
                                logger.debug(f"Parsed JSON chunk {chunk_count}")
                                
                                # Check if done
                                if data.get('done', False):
                                    logger.debug("Stream complete (done=true)")
                                    break
                                
                                # Extract content from various possible fields
                                content = None
                                
                                # Try 'content' field first (actual response)
                                if 'message' in data and 'content' in data['message']:
                                    content = data['message']['content']
                                    if content:
                                        logger.debug(f"Found content: {content[:50]}")
                                # Try OpenAI format
                                elif 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        logger.debug(f"Found content: {content[:50]}")
                                # Note: We intentionally skip 'thinking' field as it's internal reasoning
                                
                                if content:
                                    yield content
                                    
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON: {e}, line: {decoded_line[:100]}")
                                continue
                    
                    logger.debug(f"Stream ended, total chunks: {chunk_count}")
                                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error: {e}")
            yield f"Error: Connection failed - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            yield f"Error: {str(e)}"

