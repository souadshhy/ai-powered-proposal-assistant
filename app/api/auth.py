from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Customer, Quote
from app.schemas.api import LoginRequest

router = APIRouter(prefix="/auth", tags=["simple-auth"])

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == req.username).first()
    if not customer:
        customer = db.query(Customer).filter(Customer.name.ilike(f"%{req.username}%")).first()
    if not customer:
        raise HTTPException(404, "Müşteri bulunamadı")
    quotes = db.query(Quote).filter(Quote.customer_id == customer.customer_id).all()
    return {"customer": {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "segment": customer.segment,
        "city": customer.city,
        "price_tier": customer.price_tier,
        "allow_backorder": customer.allow_backorder,
    }, "quotes": [{"quote_id": q.quote_id, "status": q.status, "notes": q.notes, "created_by_channel": q.created_by_channel} for q in quotes]}
