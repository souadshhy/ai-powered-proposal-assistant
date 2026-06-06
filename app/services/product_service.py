from sqlalchemy.orm import Session
from app.models.entities import Product
from app.orchestrators.text_utils import normalize, cosine_rank

HARDWARE_CATEGORIES = {"barcode_scanner", "pos_terminal", "receipt_printer", "label_printer", "bundle"}

def product_to_dict(p: Product, score: float | None = None):
    d = {
        "product_id": p.product_id,
        "sku": p.sku,
        "name_tr": p.name_tr,
        "category": p.category,
        "brand": p.brand,
        "price_try": float(p.price_try),
        "stock_qty": p.stock_qty,
        "active": p.active,
        "min_order_qty": p.min_order_qty,
        "delivery_days": p.delivery_days,
        "warranty_months": p.warranty_months,
        "tags": p.tags,
        "aliases": p.aliases,
        "substitute_product_ids": p.substitute_product_ids,
        "notes": p.notes,
    }
    if score is not None:
        d["match_score"] = score
    return d

def product_text(p: Product) -> str:
    aliases = " ".join(p.aliases.get("tr", [])) if isinstance(p.aliases, dict) else ""
    return " ".join([p.name_tr, p.category, p.brand, " ".join(p.tags or []), aliases, p.notes])

def search_products(db: Session, query: str = "", category: str | None = None, max_price_try: float | None = None,
                    in_stock_only: bool = True, required_tags: list[str] | None = None, limit: int = 5,
                    min_warranty_months: int | None = None, include_inactive: bool = False):
    q = db.query(Product)
    if not include_inactive:
        q = q.filter(Product.active == True)
    if category:
        q = q.filter(Product.category == category)
    if max_price_try is not None:
        q = q.filter(Product.price_try <= max_price_try)
    if in_stock_only:
        q = q.filter(Product.stock_qty > 0)
    if min_warranty_months is not None:
        q = q.filter(Product.warranty_months >= min_warranty_months)
    rows = q.all()
    if required_tags:
        req = {normalize(t) for t in required_tags}
        rows = [p for p in rows if req.issubset({normalize(t) for t in (p.tags or [])})]
    if query:
        ranked = cosine_rank(query, [product_text(p) for p in rows])
        out = [(rows[i], s) for i, s in ranked if s > 0]
        if not out:
            out = [(p, 0.0) for p in rows]
    else:
        out = [(p, 0.0) for p in rows]
    out = sorted(out, key=lambda ps: (-ps[1], float(ps[0].price_try)))[:limit]
    return [product_to_dict(p, score) for p, score in out]
