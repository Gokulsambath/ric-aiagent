import aiohttp
from app.schema.ollama_dto import OllamaPrompt as OllamaDTO, OllamaChatRequest as ChatRequestDTO, Message as MsgDTO
from app.repository.ollama_repo import OllamaStreamChat as OllamaRepo
from typing import AsyncGenerator, Dict, Any, List
import json
from app.configs.settings import settings

class OllamaStreamChat:
    _msgHistory: List[Dict[str, str]] = []

    def __init__(self, repo: OllamaRepo):
        self.model_name = settings.ollama.default_model
        self.messages = []
        self.ollama_url_genapi = settings.ollama.ollama_api_url + "/api/generate"
        self.ollama_url_chatapi = settings.ollama.ollama_api_url + "/api/chat"

    @classmethod
    def getMessageHistory(cls):
        return cls._msgHistory
    
    def getModelName(self):
        return self.model_name
    
    def setModelName(self, model):
        self.model_name = model

    @classmethod
    def appendMessageHistory(cls, usr_role: str, usr_msg: str):
        cls._msgHistory.append(MsgDTO(role=usr_role, content=usr_msg))
    
    ######################################################################################################################
    #                                   Methods related to Ollama Generate API                                           #
    ######################################################################################################################
    async def stream_generate(self, ollamaPrompt: OllamaDTO, session: aiohttp.ClientSession) -> AsyncGenerator[str, None]:
        """Stream chat response using REST API"""
        #print("In Service - ", ollamaPrompt)
        payload = {
            "model": self.model_name,
            "prompt": ollamaPrompt.prompt,
            "stream": True
        }
        #print("Ollama Service - Streaming chat with payload: ", payload)
        try:
            async with session.post(self.ollama_url_genapi, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line:
                            chunk = json.loads(decoded_line)
                            
                            if 'response' in chunk:
                                yield f"data: {json.dumps({'response': chunk['response']})}\n\n"
                            
                            if chunk.get('done', False):
                                yield f"data: {json.dumps({'done': True})}\n\n"
                                break
                
        except Exception as e:
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    def _build_prompt(self, new_message: str) -> str:
        """Build prompt from conversation history"""
        if not self.messages:
            return new_message
        
        # Combine history with new message
        history = "\n".join(self.messages)
        return f"{history}\nYou: {new_message}\nAssistant:"
    
    async def handle_non_streaming(self, prompt: str) -> Dict[str, Any]:
        """Handle non-streaming requests"""
        async with aiohttp.ClientSession() as session:
            full_response = ""
            async for chunk in self.stream_generate(prompt, session):
                # Parse the SSE data
                if chunk.startswith("data: "):
                    data_str = chunk[6:].strip()
                    if data_str:
                        try:
                            data = json.loads(data_str)
                            if 'response' in data:
                                full_response += data['response']
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
            
            return {
                "model": self.model_name,
                "response": full_response,
                "done": True
            }

    # Create async generator for streaming
    async def generate(self, prompt:OllamaDTO):
        #print("Ollama Service - Generating stream response...", prompt)
        async with aiohttp.ClientSession() as session:
            async for chunk in self.stream_generate(prompt, session):
                yield chunk
    

    ######################################################################################################################
    #                                   Methods related to Ollama Chat API                                               #
    ######################################################################################################################
    async def stream_chat(self, chat_request: ChatRequestDTO, session: aiohttp.ClientSession) -> AsyncGenerator[str, None]:
        """Stream chat completion with history"""
        
        # Use provided model or default
        model = self.model_name #chat_request.model or self.model_name
        
        # Prepare payload for Ollama chat API
        payload = {
            "model": model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in chat_request.messages
            ],
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        try:
            async with session.post(self.ollama_url_chatapi, json=payload) as response:
                response.raise_for_status()
                
                assistant_response_parts = []
                async for line in response.content:
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line:
                            try:
                                chunk = json.loads(decoded_line)
                                
                                # Check for different response formats
                                if 'message' in chunk and 'content' in chunk['message']:
                                    content = chunk['message']['content']
                                    if content:  # Only yield non-empty content
                                        assistant_response_parts.append(content)
                                        yield f"data: {json.dumps({'response': content})}\n\n"
                                
                                elif 'response' in chunk:
                                    assistant_response_parts.append(chunk['response'])
                                    yield f"data: {json.dumps({'response': chunk['response']})}\n\n"
                                
                                # Handle final chunk
                                if chunk.get('done', False):

                                    if assistant_response_parts:
                                        full_assistant_response = "".join(assistant_response_parts)
                                        # Store user message and assistant response in history
                                        self.appendMessageHistory("assistant", full_assistant_response)

                                    # Include metadata if available
                                    metadata = {}
                                    if 'model' in chunk:
                                        metadata['model'] = chunk['model']
                                    if 'total_duration' in chunk:
                                        metadata['total_duration'] = chunk['total_duration']
                                    
                                    yield f"data: {json.dumps({'done': True, 'metadata': metadata})}\n\n"
                                    break
                                    
                            except json.JSONDecodeError as e:
                                error_data = {"error": f"Failed to parse response: {str(e)}"}
                                yield f"data: {json.dumps(error_data)}\n\n"
                                break
                
        except aiohttp.ClientError as e:
            error_data = {"error": f"HTTP error: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"
        
        except Exception as e:
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
     # Public generator methods
    async def generate_chat(self, chat_request: ChatRequestDTO) -> AsyncGenerator[str, None]:
        """Public method for streaming chat completion"""
        if chat_request.model is None and chat_request.model == "":
            chat_request.model = self.model_name

        async with aiohttp.ClientSession() as session:
            async for chunk in self.stream_chat(chat_request, session):
                yield chunk

    # Helper methods for building chat history
    @staticmethod
    def build_messages_from_history(history: List[Dict[str, str]], new_prompt: str,system_prompt: str = None) -> List[MsgDTO]:
        """Convert history dictionary to Message objects"""
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append(MsgDTO(role="system", content=system_prompt))
            
        # Add history
        for entry in history:
            if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                messages.append(MsgDTO(role=entry['role'], content=entry['content']))
            elif isinstance(entry, MsgDTO):
                messages.append(entry)
        
        # Add new user message
        messages.append(MsgDTO(role="user", content=new_prompt))
        
        return messages
    
    @staticmethod
    def format_chat_history(user_messages: List[str],assistant_messages: List[str],system_prompt: str = None) -> List[MsgDTO]:
        """Format alternating user/assistant messages into chat history"""
        messages = []

        if system_prompt:
            messages.append(MsgDTO(role="system", content=system_prompt))
        
        for user_msg, assistant_msg in zip(user_messages, assistant_messages):
            messages.append(MsgDTO(role="user", content=user_msg))
            messages.append(MsgDTO(role="assistant", content=assistant_msg))
        
        return messages
    
    # Non-streaming version for chat
    async def handle_non_streaming_chat(self, chat_request: ChatRequestDTO) -> Dict[str, Any]:
        """Non-streaming chat completion"""
        model = self.model_name #chat_request.model or self.model_name
        
        payload = {
            "model": model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in chat_request.messages
            ],
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.chat_url, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    return {
                        "model": model,
                        "message": result.get("message", {}),
                        "response": result.get("message", {}).get("content", ""),
                        "done": True
                    }
        
        except Exception as e:
            return {"error": str(e)}




    # Create async Model health check for streaming
    async def health_check(self):
        try:
            # Test connection to Ollama
            ollamaUrl = settings.ollama.ollama_api_url +  "/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(ollamaUrl) as response:
                    if response.status == 200:
                        return {"status": "healthy", "ollama": "connected"}
                    else:
                        return {"status": "degraded", "ollama": "unavailable"}
        except:
            return {"status": "unhealthy", "ollama": "disconnected"}
        
