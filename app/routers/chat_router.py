from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.services.chat_factory import ChatFactory
from app.schema.chat_schema import ChatRequest, ChatResponse, ChatThreadResponse, ThreadListResponse, ChatMessageResponse
from app.models.chat_models import ChatSession, ChatMessage, ChatThread
from app.models.user_model import User
from app.configs.database import get_db
from sqlalchemy.orm import Session
from typing import List
import logging
import json

from app.services.redis_service import redis_service

chat_router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

@chat_router.post("/")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 1. Upsert User
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            user = User(
                email=request.email,
                name=request.email.split("@")[0]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        # 2. Upsert Session
        session = None
        if request.session_id and request.session_id.lower() != "new":
             if request.session_id.isdigit():
                session = db.query(ChatSession).filter(ChatSession.id == int(request.session_id), ChatSession.user_id == user.id).first()
        
        if not session:
            session = ChatSession(
                user_id=user.id,
                title=f"Chat {request.email}"
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        # 3. Upsert Thread
        thread = None
        if request.thread_id and request.thread_id.lower() != "new" and not request.is_new_chat:
            if request.thread_id.isdigit():
                thread = db.query(ChatThread).filter(ChatThread.id == int(request.thread_id), ChatThread.session_id == session.id).first()
        
        if not thread:
            thread = ChatThread(
                session_id=session.id,
                title=f"Thread {len(session.threads) + 1}"
            )
            db.add(thread)
            db.commit()
            db.refresh(thread)
            
        # 4. Save User Message
        user_msg = ChatMessage(
            thread_id=thread.id,
            role="user",
            content=request.message
        )
        db.add(user_msg)
        db.commit()

        # Cache User Message to Redis
        try:
            redis_key = f"chat_history:{session.id}"
            if thread.id:
                redis_key = f"chat_history:{session.id}:{thread.id}"
            
            # Helper dict for redis storage
            redis_msg = {"role": "user", "content": request.message}
            await redis_service.rpush(redis_key, redis_msg, max_len=50, ttl=86400)
        except Exception as e:
            logger.error(f"Redis Cache Error (User): {e}")
        
        # 5. Get appropriate strategy
        strategy = ChatFactory.get_strategy(request.provider)
        
        # 6. Stream response
        async def event_generator():
            try:
                full_content = ""
                choices_data = None
                
                # Stream from provider
                async for chunk in strategy.stream_message(request.message, str(thread.id)): # Use thread.id for provider session if appropriate
                    # Check if this chunk contains choices marker
                    if "__CHOICES__" in chunk and "__END_CHOICES__" in chunk:
                        # Extract choices JSON
                        start = chunk.index("__CHOICES__") + len("__CHOICES__")
                        end = chunk.index("__END_CHOICES__")
                        choices_json = chunk[start:end]
                        
                        try:
                            choices_data = json.loads(choices_json)
                            # Don't include the marker in the content
                            chunk = chunk[:chunk.index("__CHOICES__")]
                        except:
                            pass
                    
                    full_content += chunk
                    # Send SSE formatted chunk with choices if available
                    sse_data = {
                        'response': chunk, 
                        'session_id': str(session.id),
                        'thread_id': str(thread.id)
                    }
                    if choices_data:
                        sse_data['choices'] = choices_data
                    yield f"data: {json.dumps(sse_data)}\n\n"
                
                # 7. Save Assistant Message after streaming completes
                if full_content:
                    assistant_msg = ChatMessage(
                        thread_id=thread.id,
                        role="assistant",
                        content=full_content
                    )
                    db.add(assistant_msg)
                    db.commit()

                    # Cache Assistant Message to Redis
                    try:
                        redis_key = f"chat_history:{session.id}"
                        if thread.id:
                            redis_key = f"chat_history:{session.id}:{thread.id}"
                        
                        redis_msg = {"role": "assistant", "content": full_content}
                        await redis_service.rpush(redis_key, redis_msg, max_len=50, ttl=86400)
                    except Exception as e:
                        logger.error(f"Redis Cache Error (Assistant): {e}")

            except Exception as e:
                logger.error(f"Streaming Error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/sessions/{session_id}/threads", response_model=ThreadListResponse)
async def list_threads(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ThreadListResponse(
        session_id=session.id,
        threads=session.threads
    )

@chat_router.get("/threads/{thread_id}/messages", response_model=List[ChatMessageResponse])
async def list_messages(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return thread.messages
