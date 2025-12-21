from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.services.chat_factory import ChatFactory
from app.schema.chat_schema import ChatRequest, ChatResponse
from app.models.chat_models import ChatSession, ChatMessage
from app.models.user_model import User
from app.configs.database import get_db
from sqlalchemy.orm import Session
import logging
import json

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
        if request.session_id and request.session_id.lower() != "new" and not request.is_new_chat:
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
            
        # 3. Save User Message
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.message
        )
        db.add(user_msg)
        db.commit()
        
        # 4. Get appropriate strategy
        strategy = ChatFactory.get_strategy(request.provider)
        
        # 5. Stream response
        async def event_generator():
            full_content = ""
            choices_data = None
            
            # Stream from provider
            async for chunk in strategy.stream_message(request.message, str(session.id)):
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
                sse_data = {'response': chunk, 'session_id': str(session.id)}
                if choices_data:
                    sse_data['choices'] = choices_data
                yield f"data: {json.dumps(sse_data)}\n\n"
            
            # 6. Save Assistant Message after streaming completes
            if full_content:
                assistant_msg = ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=full_content
                )
                db.add(assistant_msg)
                db.commit()
        
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
