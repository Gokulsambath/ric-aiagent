from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.services.chat_factory import ChatFactory
from app.schema.chat_schema import ChatRequest, ChatResponse, ChatThreadResponse, ThreadListResponse, ChatMessageResponse, UserUpdateRequest
from app.models.chat_models import ChatSession, ChatMessage, ChatThread
from app.models.user_model import User
from app.models.widget_config_model import WidgetConfig
from app.configs.database import get_db
from sqlalchemy.orm import Session
from typing import List
import logging
import json

from app.services.redis_service import redis_service
from app.constants import REDIS_CHAT_HISTORY_MAX_LEN, REDIS_CHAT_HISTORY_TTL_SECONDS

chat_router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Depends, Header
from app.repository.widget_config_repo import WidgetConfigRepository

@chat_router.post("/")
async def chat_endpoint(
    request: ChatRequest, 
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    # Validate API Key (Widget Key or System Key)
    if not x_api_key:
        # Check if auth middleware already validated it (system key)
        # But since we exempted it, we must check manually or rely on 'request.state' if middleware ran partially?
        # Middleware skips entirely. So check here.
         raise HTTPException(status_code=401, detail="Missing API Key")

    # Check Widget Config
    repo = WidgetConfigRepository(db)
    widget_config = repo.get_by_secret_key(x_api_key)
    
    # If not a widget key, check system keys as fallback (optional, but good for testing)
    # If not a widget key, check system keys as fallback (optional, but good for testing)
    # If not a widget key, check system keys as fallback (optional, but good for testing)
    is_valid = False
    if widget_config and widget_config.active:
        is_valid = True
        print(f"DEBUG: Found WidgetConfig for tenant: {widget_config.tenant_id}, bot_id: {widget_config.bot_id}", flush=True)
    else:
        # Simple check against system settings if needed, or fail
        from app.configs.settings import settings
        import secrets
        for stored_key in settings.security.api_keys:
             if secrets.compare_digest(x_api_key, stored_key.key) and stored_key.enabled:
                 is_valid = True
                 print("DEBUG: Authenticated with System Key", flush=True)
                 break
    
    if not is_valid:
        print(f"DEBUG: Authentication Failed for key: {x_api_key}", flush=True)
        raise HTTPException(status_code=401, detail="Invalid API Key")

    print("=" * 80, flush=True)
    print("📨 /CHAT ENDPOINT HIT!", flush=True)
    print(f"📨 Message: {request.message}", flush=True)
    print(f"📨 Provider: {request.provider}", flush=True)
    print(f"📨 Email: {request.email}", flush=True)
    print("=" * 80, flush=True)

    try:
        # Resolve Bot ID
        bot_id = None
        if widget_config and widget_config.bot_id:
             bot_id = widget_config.bot_id
        
        # Override with app_id from request if needed/logic permits (or verify they match)
        if request.app_id:
             print(f"DEBUG: Request app_id: {request.app_id}", flush=True)
             # In future, you might want to look up config by request.app_id if header key is different?
             # For now, we assume key resolves to config which contains bot_id
        
        print(f"DEBUG: Using bot_id: {bot_id} for strategy", flush=True)

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
            await redis_service.rpush(redis_key, redis_msg, max_len=REDIS_CHAT_HISTORY_MAX_LEN, ttl=REDIS_CHAT_HISTORY_TTL_SECONDS)
        except Exception as e:
            logger.error(f"Redis Cache Error (User): {e}")
        
        # 5. Get appropriate strategy
        print(f"🔍 Request provider: {request.provider}", flush=True)
        strategy = ChatFactory.get_strategy(request.provider)
        print(f"🔍 Selected strategy: {type(strategy).__name__}", flush=True)
        
        # Resolve Bot ID if available
        if request.app_id:
            # Try to find config by tenant_id or secret_key
            config = db.query(WidgetConfig).filter(WidgetConfig.tenant_id == request.app_id).first()
            if not config:
                config = db.query(WidgetConfig).filter(WidgetConfig.secret_key == request.app_id).first()
            
            if config and config.bot_id:
                bot_id = config.bot_id
                print(f"DEBUG: Resolved bot_id: {bot_id} for app_id: {request.app_id}", flush=True)

        # 6. Stream response
        async def event_generator():
            full_content = ""
            choices_data = None
            acts_data = None
            
            try:
                # Stream from provider
                async for chunk in strategy.stream_message(request.message, str(thread.id), bot_id=bot_id): # Use thread.id for provider session if appropriate
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
                    
                    # Check if this chunk contains acts data marker
                    if "__ACTS_DATA__" in chunk and "__END_ACTS__" in chunk:
                        # Extract acts JSON
                        start = chunk.index("__ACTS_DATA__") + len("__ACTS_DATA__")
                        end = chunk.index("__END_ACTS__")
                        acts_json = chunk[start:end]
                        
                        try:
                            acts_data = json.loads(acts_json)
                            # Don't include the marker in the content
                            chunk = chunk[:chunk.index("__ACTS_DATA__")]
                            if acts_data:
                                 pass
                        except Exception as e:
                            logger.error(f"Failed to parse acts data: {e}")
                    
                    # Check if this chunk contains daily updates data marker
                    daily_updates_data = None
                    if "__DAILY_UPDATES__" in chunk and "__END_DAILY__" in chunk:
                        # Extract daily updates JSON
                        start = chunk.index("__DAILY_UPDATES__") + len("__DAILY_UPDATES__")
                        end = chunk.index("__END_DAILY__")
                        daily_json = chunk[start:end]
                        
                        try:
                            daily_updates_data = json.loads(daily_json)
                            # Don't include the marker in the content
                            chunk = chunk[:chunk.index("__DAILY_UPDATES__")]
                            logger.info(f"Parsed daily updates data: {len(daily_updates_data.get('updates', []))} updates")
                        except Exception as e:
                            logger.error(f"Failed to parse daily updates data: {e}")
                    
                    # Check if this chunk contains provider switch marker
                    if "__SWITCH_PROVIDER__" in chunk and "__END_SWITCH__" in chunk:
                        # Don't include the marker in the content - just strip it out
                        chunk = chunk[:chunk.index("__SWITCH_PROVIDER__")]
                    
                    full_content += chunk
                    # Send SSE formatted chunk with choices, acts, and daily updates if available
                    sse_data = {
                        'response': chunk, 
                        'session_id': str(session.id),
                        'thread_id': str(thread.id)
                    }
                    if choices_data:
                        sse_data['choices'] = choices_data
                    if acts_data:
                        sse_data['acts'] = acts_data
                    if daily_updates_data:
                        sse_data['dailyUpdates'] = daily_updates_data
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
                        await redis_service.rpush(redis_key, redis_msg, max_len=REDIS_CHAT_HISTORY_MAX_LEN, ttl=REDIS_CHAT_HISTORY_TTL_SECONDS)
                    except Exception as e:
                        logger.error(f"Redis Cache Error (Assistant): {e}")

            except Exception as e:
                 print(f"ERROR: Streaming Error: {e}", flush=True)
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
        print(f"Chat Error: {str(e)}", flush=True)
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

@chat_router.put("/user/update")
async def update_user(request: UserUpdateRequest, db: Session = Depends(get_db)):
    # Find existing user (Guest)
    user = db.query(User).filter(User.email == request.current_email).first()
    if not user:
        # If no guest user found, maybe they are already the new user?
        existing_new = db.query(User).filter(User.email == request.new_email).first()
        if existing_new:
             return {"message": "User already exists", "user_id": existing_new.id}
        raise HTTPException(status_code=404, detail="Current user not found")
    
    # Check if new email already exists (edge case)
    existing_new = db.query(User).filter(User.email == request.new_email).first()
    if existing_new:
        # Move sessions from Guest to Real.
        sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).all()
        for s in sessions:
            s.user_id = existing_new.id
        
        # Delete the guest user since we migrated their sessions
        db.delete(user)
        db.commit()
        return {"message": "Merged guest session to existing user", "user_id": existing_new.id}
        
    # Just update email
    user.email = request.new_email
    if request.name:
        user.name = request.name
        
    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully", "user_id": user.id}
