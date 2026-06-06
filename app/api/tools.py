from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.product_service import search_products
from app.services.knowledge_service import get_knowledge_entries
from app.services.quote_service import get_quote, add_to_quote, update_quote_item, replace_with_alternative

router = APIRouter(prefix="/tools", tags=["tool-contracts"])

@router.post("/search_products")
def tool_search_products(payload: dict, db: Session = Depends(get_db)):
    return {"products": search_products(db, **payload)}

@router.post("/get_knowledge_entries")
def tool_get_knowledge(payload: dict, db: Session = Depends(get_db)):
    return {"entries": get_knowledge_entries(db, **payload)}

@router.post("/get_quote")
def tool_get_quote(payload: dict, db: Session = Depends(get_db)):
    return get_quote(db, payload["quote_id"])
