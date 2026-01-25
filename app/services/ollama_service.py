from app.services.chat_strategy import ChatStrategy
from app.services.ollama_serv import OllamaStreamChat
from app.schema.chat_schema import ChatResponse
from app.schema.ollama_dto import OllamaChatRequest, Message
from app.repository.ollama_repo import OllamaStreamChat as OllamaRepo
from typing import AsyncGenerator
import json
import logging

class OllamaService(ChatStrategy):
    def __init__(self):
         # We need to instantiate the existing service. 
         # It requires a repo, but the repo class seems stateless/empty init based on imports.
         # Let's check if we can instantiate it easily.
         self.repo = OllamaRepo() # Repo init is empty
         self.inner_service = OllamaStreamChat(self.repo)

    async def send_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None, **kwargs) -> ChatResponse:
        """
        Send message (non-streaming)
        """
        # ... existing implementation ...
        # Build request
        # For simple chat strategy, we might strictly just send the message. 
        # But OllamaStreamChat logic is complex (history, etc).
        # We should use its handle_non_streaming_chat if possible, but that needs history management.
        # The ChatStrategy implies the caller manages the high-level flow, or the strategy does.
        # In chat_router.py, the router manages DB persistence of history. 
        # Does proper Ollama usage require sending full history? Yes.
        # So we need to fetch history?
        # ChatRouter saves the NEW message to DB *before* calling stream_message.
        # So fetching from DB/Redis inside here is possible.
        
        # However, for simplicity and to match the 'stateless' provider interface often expected:
        # We will retrieve history from Redis using the inner_service's methods if available.
        # The inner service has 'get_message_history' but it needs session_id/thread_id.
        # The 'session_id' arg here might be thread_id? The router calls it with `str(thread.id)`!
        # See chat_router.py line 92: `strategy.stream_message(request.message, str(thread.id))`
        
        thread_id = session_id # Mapping router's usage
        # session_id (actual chat session) is not passed! This is a minor issue in ChatRouter design for Ollama context.
        # But wait, ChatRouter saves to DB/Redis.
        # If we rely on Redis being up to date, we can fetch history using thread_id if key structure supports it.
        # But inner_service uses `chat_history:{session_id}:{thread_id}`. It needs real session_id.
        # ChatRouter passes `str(thread.id)` as 2nd arg.
        
        # Let's assume for now we just send the current message + maybe simple context if possible.
        # Or, we update ChatRouter to pass both?
        # The user said "adjust the api code". This is a good adjustment.
        # But first, let's implement the basic forwarding.
        
        # Construct messages payload
        messages = [{"role": "user", "content": message}]
        
        request = OllamaChatRequest(
            model=None, # use default
            messages=[Message(**m) for m in messages],
            stream=False
        )
        
        response = await self.inner_service.handle_non_streaming_chat(request)
        
        return ChatResponse(
            session_id=session_id,
            role="assistant",
            content=response.get("response", ""),
            provider="ollama"
        )

    async def stream_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream message
        """
        logger = logging.getLogger(__name__)
        logger.info(f"OllamaService.stream_message called with message: {message[:50]}...")
        
        # Again, ChatRouter passes thread_id as session_id.
        
        # To make Ollama 'aware' of context without changing Router signature yet:
        # We can try to fetch history if we can derive keys, OR just be stateless for this turn.
        # Ideally, we should fetch history.
        # But 'session_id' arg is just one string.
        
        messages = [{"role": "user", "content": message}]
        
        request = OllamaChatRequest(
            model=None,
            messages=[Message(**m) for m in messages],
            stream=True,
            # We can't easily populate these without real session_id
            session_id=None,
            thread_id=None 
        )
        
        logger.info(f"Calling inner_service.generate_chat with model: {self.inner_service.model_name}")
        chunk_count = 0
        
        async for chunk in self.inner_service.generate_chat(request):
            chunk_count += 1
            logger.info(f"Received chunk #{chunk_count}: {chunk[:100]}")
            
            # chunk format from inner_service: "data: {...}\n\n"
            # ChatRouter expects raw text chunks or standard stream?
            # ChatRouter: 
            #   `if "__CHOICES__" ...`
            #   `full_content += chunk` 
            #   `yield f"data: ..."`
            # Wait, line 92 in chat_router iterates `strategy.stream_message`.
            # Line 107 `full_content += chunk`.
            # It expects `chunk` to be the TEXT CONTENT, not "data: json".
            # BotpressService yields text lines.
            
            # OllamaServ.generate_chat yields "data: {json}\n\n".
            # We need to parse it and yield just the text.
            
            if chunk.startswith("data: "):
                try:
                    data_str = chunk[6:].strip()
                    if data_str:
                         data = json.loads(data_str)
                         if 'response' in data:
                             text_content = data['response']
                             logger.info(f"Yielding text: {text_content}")
                             yield text_content
                         else:
                             logger.warning(f"No 'response' in data: {data}")
                except Exception as e:
                    logger.error(f"Error parsing chunk: {e}, chunk: {chunk}")
                    pass
            else:
                logger.warning(f"Chunk doesn't start with 'data: ': {chunk[:50]}")
        
        logger.info(f"Finished streaming, total chunks: {chunk_count}")
