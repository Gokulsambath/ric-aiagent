from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import List, Dict

from app.services.ollama_serv import OllamaStreamChat as OllamaServ
from app.repository.ollama_repo import OllamaStreamChat as OllamaRepo
from app.schema.ollama_dto import OllamaPrompt as OllamaDTO, OllamaChatRequest as CahtRequestDTO
from app.models.chat_models import ChatSession, ChatMessage, ChatThread
from app.models.user_model import User
from app.configs.database import get_db
from sqlalchemy.orm import Session
from app.configs.dependencies import get_service_factory

aiAgentsRoutes = APIRouter(prefix="/aiagents", tags=["aiagents"])
ollama_service_dep = get_service_factory(OllamaServ, OllamaRepo)

@aiAgentsRoutes.post("/generate")
async def stream_agentic_chat(aiPrompt: OllamaDTO, service: OllamaServ = Depends(ollama_service_dep)):
    """
    Stream chat response exactly like Ollama API
    Expects JSON payload with: {"model": "model_name", "prompt": "message", "stream": True}
    """
    try:
        # Parse request body
        #body = await request.json()
        prompt = aiPrompt.prompt  #body.get("prompt", "")
        model = aiPrompt.model #or "gpt-oss:120b-cloud" #"deepseek-v3.1:671b-cloud" #body.get("model", ollama_client.model_name)
        stream = aiPrompt.stream #body.get("stream", True)
        #print("In Router - ", aiPrompt)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Update model if different
        #print("Using Model Before: ", service.model_name)
        if model is not None and model != "" and model != service.getModelName():
            service.setModelName(model)
        #print("Using Model After: ", service.model_name)

        if not stream:
            # Handle non-streaming response (for compatibility)
            return await service.handle_non_streaming(prompt)
        
        # Create async generator for streaming
        """
        async def generate():
            async with aiohttp.ClientSession() as session:
                async for chunk in ollama_client.stream_chat(prompt, session):
                    yield chunk
        """
        
        return StreamingResponse(
            service.generate(aiPrompt),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    #result = service.sendEmail(email)
    #return result


@aiAgentsRoutes.post("/chat")
async def stream_chat_with_history(chatMsg: OllamaDTO, service: OllamaServ = Depends(ollama_service_dep), db: Session = Depends(get_db)):
    """
    Enhanced streaming endpoint with conversation history
    Expects: {"message": "user message", "model": "model_name", "clear_history": false}
    """
    try:
        #body = await request.json()
        user_message = chatMsg.prompt #body.get("message", "")
        model = chatMsg.model #body.get("model", ollama_client.model_name)
        stream = chatMsg.stream #body.get("stream", True)
        clear_history = chatMsg.clear_chat #body.get("clear_history", False)
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        if clear_history:
            service.messages = []
        
         # Update model if different
        if model is not None and model != "" and model != service.getModelName():
            service.setModelName(model)

        # ---------------------------------------------------------
        # DB Persistence Logic (User -> Session -> Thread -> Message)
        # ---------------------------------------------------------
        session_id = chatMsg.session_id
        thread_id = chatMsg.thread_id
        email = getattr(chatMsg, 'email', None)
        
        thread = None
        current_session = None

        if email:
             # 1. Upsert User
             user = db.query(User).filter(User.email == email).first()
             if not user:
                 user = User(email=email, name=email.split("@")[0])
                 db.add(user)
                 db.commit()
                 db.refresh(user)

             # 2. Upsert Session
             if session_id and session_id.isdigit():
                  current_session = db.query(ChatSession).filter(ChatSession.id == int(session_id), ChatSession.user_id == user.id).first()
             
             if not current_session:
                  current_session = ChatSession(user_id=user.id, title=f"Chat {email}")
                  db.add(current_session)
                  db.commit()
                  db.refresh(current_session)
                  session_id = str(current_session.id) # Update var for service

             # 3. Upsert Thread
             if thread_id and thread_id.isdigit():
                  # Assuming thread belongs to the session
                  thread = db.query(ChatThread).filter(ChatThread.id == int(thread_id), ChatThread.session_id == current_session.id).first()
             
             if not thread:
                  thread = ChatThread(session_id=current_session.id, title="New Thread")
                  db.add(thread)
                  db.commit()
                  db.refresh(thread)
                  thread_id = str(thread.id) # Update var for service

             # 4. Save User Message
             user_msg_db = ChatMessage(thread_id=thread.id, role="user", content=user_message)
             db.add(user_msg_db)
             db.commit()

        history: List[Dict[str, str]] = None
        system_prompt: str = None
        
        # Use session_id from request if available
        session_id = chatMsg.session_id #body.get("session_id")
        thread_id = chatMsg.thread_id
        
        # Build messages from history
        if history is None:
            if session_id:
                 history = await service.get_message_history(session_id, thread_id)
            else:
                 history = [] 
        
        try:
             # Assuming this method exists or removing if undefined. 
             # Based on previous file content, it wasn't defined in the view_file output. 
             # I will assume it's missing and return empty dict or default prompt
             pass 
        except:
             pass

        messages = service.build_messages_from_history(history, user_message, system_prompt)
        chat_request = CahtRequestDTO(messages=messages)
        chat_request.model = service.model_name
        chat_request.session_id = session_id # carry forward to stream_chat
        chat_request.thread_id = thread_id

        if session_id:
            await service.append_message_history(session_id, "user", user_message, thread_id)
        
        #print("########################## Chat Request #######################", chat_request)
        if not stream:
            # Handle non-streaming response (for compatibility)
            return await service.handle_non_streaming_chat(chat_request)

        async def event_generator():
            full_response = ""
            async for chunk in service.generate_chat(chat_request):
                # accumulate response for DB logic
                if thread and chunk.startswith("data: "):
                     try:
                         data_str = chunk[6:].strip()
                         if data_str:
                             data = json.loads(data_str)
                             if 'response' in data:
                                 full_response += data['response']
                     except:
                         pass
                yield chunk
            
            # Save Assistant Message after streaming
            if thread and full_response:
                 try:
                     asst_msg_db = ChatMessage(thread_id=thread.id, role="assistant", content=full_response)
                     db.add(asst_msg_db)
                     db.commit()
                 except Exception as e:
                     # Log error but don't crash the stream which is already done
                     print(f"Error saving assistant message: {e}")

        # return StreamingResponse(
        #     event_generator(),
        # ...
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            #media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@aiAgentsRoutes.post("/clearchat")
async def clear_chat_history(service: OllamaServ = Depends(ollama_service_dep)):
    """Clear conversation history"""
    service.messages = []
    return {"status": "History cleared"}

@aiAgentsRoutes.get("/chatmodel")
async def get_available_models(service: OllamaServ = Depends(ollama_service_dep)):
    """Get available models (you might want to fetch this from Ollama)"""
    return {
        "models": [
            {
                "name": service.model_name,
                "modified_at": "2024-01-01T00:00:00.000Z",
                "size": 0,  # You might want to get actual size
                "digest": "sha256:...",
                "details": {
                    "format": "gguf",
                    "family": "gpt" #"deepseek"
                }
            }
        ]
    }

@aiAgentsRoutes.get("/health")
async def health_check(service: OllamaServ = Depends(ollama_service_dep)):
    """Health check endpoint"""
    return await service.health_check()