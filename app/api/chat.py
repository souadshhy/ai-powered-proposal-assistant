from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api import ChatRequest
from app.orchestrators.chat import stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    return StreamingResponse(stream_chat(db, req.quote_id, req.message, req.channel, req.session_id, req.idempotency_key), media_type="text/event-stream")
