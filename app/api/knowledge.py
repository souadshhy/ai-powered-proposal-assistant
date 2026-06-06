from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import KnowledgeEntry
from app.schemas.api import KnowledgeCreate
from app.services.knowledge_service import knowledge_to_dict, get_knowledge_entries

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.get("")
def list_knowledge(q: str = "", topic: str | None = None, db: Session = Depends(get_db)):
    return {"entries": get_knowledge_entries(db, query=q, topic=topic, limit=100)}

@router.post("")
def create_knowledge(req: KnowledgeCreate, db: Session = Depends(get_db)):
    if db.get(KnowledgeEntry, req.knowledge_id):
        raise HTTPException(409, "Bilgi kaydı zaten mevcut")
    k = KnowledgeEntry(**req.model_dump())
    db.add(k); db.commit(); db.refresh(k)
    return knowledge_to_dict(k)
