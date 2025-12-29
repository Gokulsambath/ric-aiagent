import httpx
from app.services.chat_strategy import ChatStrategy
from app.schema.chat_schema import ChatResponse
from app.configs.settings import settings
import logging

logger = logging.getLogger(__name__)

class BotpressService(ChatStrategy):
    def __init__(self):
        self.base_url = settings.botpress.botpress_url
        self.bot_id = settings.botpress.bot_id
        # Webhook ID is not strictly needed for the Converse API unless verified via that channel
        
    async def send_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None) -> ChatResponse:
        """
        Sends a message to the Botpress Converse API.
        POST /api/v1/bots/{botId}/converse/{userId}
        """
        # Use passed bot_id or fallback to default
        target_bot_id = bot_id or self.bot_id
        url = f"{self.base_url}/api/v1/bots/{target_bot_id}/converse/{session_id}"
        
        payload = {
            "type": "text",
            "text": message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                
                # Botpress returns a list of responses with different types
                # Common types: text, choice (buttons), carousel, image, etc.
                responses = data.get("responses", [])
                
                bot_parts = []
                for r in responses:
                    resp_type = r.get("type", "")
                    
                    if resp_type == "text" or "text" in r:
                        bot_parts.append(r.get("text", ""))
                    
                    elif resp_type == "choice":
                        # Handle choice/button responses
                        choice_text = r.get("text", "")
                        if choice_text:
                            bot_parts.append(choice_text)
                        
                        # Format choices as markdown buttons/list
                        choices = r.get("choices", [])
                        if choices:
                            bot_parts.append("\n**Options:**")
                            for idx, choice in enumerate(choices, 1):
                                title = choice.get("title", choice.get("value", f"Option {idx}"))
                                bot_parts.append(f"{idx}. {title}")
                    
                    elif resp_type == "carousel":
                        # Handle carousel (multiple cards)
                        items = r.get("items", [])
                        if items:
                            bot_parts.append("\n**Options:**")
                            for idx, item in enumerate(items, 1):
                                title = item.get("title", f"Option {idx}")
                                bot_parts.append(f"{idx}. {title}")
                
                bot_text = "\n".join(bot_parts) if bot_parts else "No response from bot"
                
                return ChatResponse(
                    session_id=session_id,
                    role="assistant",
                    content=bot_text,
                    provider="botpress",
                    metadata={"raw_response": data}
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Botpress API Error: {str(e)}")
            raise Exception(f"Failed to communicate with Botpress: {str(e)}")
    
    async def stream_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None):
        """
        Stream a message to Botpress and yield text chunks.
        Botpress doesn't natively support streaming, so we fetch the full response
        and simulate streaming by yielding it character by character or word by word.
        """
        # Use passed bot_id or fallback to default
        target_bot_id = bot_id or self.bot_id
        url = f"{self.base_url}/api/v1/bots/{target_bot_id}/converse/{session_id}"
        
        print(f"BotpressService: Sending message to bot_id: {target_bot_id} (requested: {bot_id}, default: {self.bot_id})", flush=True)
        print(f"BotpressService: Target URL: {url}", flush=True)
        
        payload = {
            "type": "text",
            "text": message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                responses = data.get("responses", [])
                
                logger.info(f"Botpress raw response: {data}")
                
                # Build full response and collect choices
                bot_parts = []
                all_choices = []
                
                for r in responses:
                    resp_type = r.get("type", "")
                    logger.info(f"Processing response type: {resp_type}, data: {r}")
                    
                    
                    if resp_type == "text":
                        bot_parts.append(r.get("text", ""))
                    
                    elif resp_type == "choice" or resp_type == "single-choice":
                        choice_text = r.get("text", "")
                        if choice_text:
                            bot_parts.append(choice_text)
                        
                        choices = r.get("choices", [])
                        logger.info(f"Found {len(choices)} choices: {choices}")
                        if choices:
                            # Store choices for later
                            all_choices.extend(choices)
                    
                    elif resp_type == "carousel":
                        items = r.get("items", [])
                        if items:
                            bot_parts.append("\n**Options:**")
                            for idx, item in enumerate(items, 1):
                                title = item.get("title", f"Option {idx}")
                                bot_parts.append(f"{idx}. {title}")
                
                logger.info(f"Final bot_parts: {bot_parts}")
                logger.info(f"All choices: {all_choices}")
                
                full_text = "\n".join(bot_parts) if bot_parts else "No response from bot"
                
                # Stream text content line by line
                lines = full_text.split("\n")
                for i, line in enumerate(lines):
                    if i == 0:
                        yield line
                    else:
                        yield "\n" + line
                
                # If we have choices, yield them as a special marker
                if all_choices:
                    import json as json_lib
                    choices_json = json_lib.dumps(all_choices)
                    yield f"\n__CHOICES__{choices_json}__END_CHOICES__"
                
        except httpx.HTTPError as e:
            logger.error(f"Botpress API Error: {str(e)}")
            raise Exception(f"Failed to communicate with Botpress: {str(e)}")
