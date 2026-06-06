from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Quote, ToolCallLog
from app.schemas.api import AddQuoteItemRequest, UpdateQuoteItemRequest, ReplaceQuoteItemRequest
from app.services.quote_service import get_quote, add_to_quote, update_quote_item, replace_with_alternative, BusinessRuleError

router = APIRouter(prefix="/quotes", tags=["quotes"])

@router.get("")
def list_quotes(customer_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Quote)
    if customer_id: q = q.filter(Quote.customer_id == customer_id)
    return {"quotes": [{"quote_id": x.quote_id, "customer_id": x.customer_id, "status": x.status, "notes": x.notes} for x in q.all()]}

@router.get("/{quote_id}")
def read_quote(quote_id: str, db: Session = Depends(get_db)):
    try: return get_quote(db, quote_id)
    except BusinessRuleError as e: raise HTTPException(404, str(e))

@router.post("/{quote_id}/items")
def add_item(quote_id: str, req: AddQuoteItemRequest, db: Session = Depends(get_db)):
    try: return add_to_quote(db, quote_id, **req.model_dump())
    except BusinessRuleError as e: raise HTTPException(400, str(e))

@router.patch("/{quote_id}/items")
def update_item(quote_id: str, req: UpdateQuoteItemRequest, db: Session = Depends(get_db)):
    try: return update_quote_item(db, quote_id, req.quote_item_id, req.quantity)
    except BusinessRuleError as e: raise HTTPException(400, str(e))

@router.post("/{quote_id}/replace")
def replace_item(quote_id: str, req: ReplaceQuoteItemRequest, db: Session = Depends(get_db)):
    try: return replace_with_alternative(db, quote_id, **req.model_dump())
    except BusinessRuleError as e: raise HTTPException(400, str(e))

@router.get("/{quote_id}/tool-logs")
def quote_logs(quote_id: str, db: Session = Depends(get_db)):
    logs = db.query(ToolCallLog).filter(ToolCallLog.quote_id == quote_id).order_by(ToolCallLog.id.desc()).limit(100).all()
    return {"logs": [{"id": l.id, "session_id": l.session_id, "sequence": l.sequence, "tool_name": l.tool_name, "success": l.success, "input_payload": l.input_payload, "quote_delta": l.quote_delta} for l in logs]}
