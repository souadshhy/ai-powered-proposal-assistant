import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import Base, engine
from app.core.config import settings
from app.models.entities import Product, KnowledgeEntry, Customer, PriceRule, Quote, QuoteItem

MODEL_MAP = [
    ("products.json", Product),
    ("knowledge_entries.json", KnowledgeEntry),
    ("customers.json", Customer),
    ("price_rules.json", PriceRule),
    ("quotes.json", Quote),
    ("quote_items.json", QuoteItem),
]

def init_db():
    Base.metadata.create_all(bind=engine)

def seed_if_empty(db: Session):
    if db.query(Product).first():
        return {"seeded": False, "reason": "database already has products"}
    data_dir = Path(settings.data_dir)
    counts = {}
    for filename, model in MODEL_MAP:
        rows = json.loads((data_dir / filename).read_text(encoding="utf-8"))
        for row in rows:
            db.merge(model(**row))
        counts[filename] = len(rows)
    db.commit()
    return {"seeded": True, "counts": counts}
