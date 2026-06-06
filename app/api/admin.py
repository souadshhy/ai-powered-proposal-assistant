from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import ToolCallLog, ChatSession

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/tool-logs")
def tool_logs(db: Session = Depends(get_db)):
    logs = db.query(ToolCallLog).order_by(ToolCallLog.id.desc()).limit(200).all()
    return {"logs": [{"id": l.id, "session_id": l.session_id, "quote_id": l.quote_id, "sequence": l.sequence, "tool_name": l.tool_name, "success": l.success, "input_payload": l.input_payload, "output_payload": l.output_payload, "quote_delta": l.quote_delta} for l in logs]}

@router.get("/chat-sessions")
def chat_sessions(db: Session = Depends(get_db)):
    rows = db.query(ChatSession).order_by(ChatSession.created_at.desc()).limit(200).all()
    return {"sessions": [{"session_id": r.session_id, "quote_id": r.quote_id, "customer_id": r.customer_id, "channel": r.channel, "created_at": str(r.created_at)} for r in rows]}
