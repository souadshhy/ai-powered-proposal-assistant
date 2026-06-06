from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Product
from app.schemas.api import ProductCreate
from app.services.product_service import product_to_dict, search_products

router = APIRouter(prefix="/products", tags=["products"])

@router.get("")
def list_products(q: str = "", category: str | None = None, max_price_try: float | None = None, in_stock_only: bool = False, db: Session = Depends(get_db)):
    return {"products": search_products(db, query=q, category=category, max_price_try=max_price_try, in_stock_only=in_stock_only, limit=100)}

@router.post("")
def create_product(req: ProductCreate, db: Session = Depends(get_db)):
    if db.get(Product, req.product_id):
        raise HTTPException(409, "Ürün zaten mevcut")
    p = Product(**req.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return product_to_dict(p)

@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p: raise HTTPException(404, "Ürün bulunamadı")
    return product_to_dict(p)
