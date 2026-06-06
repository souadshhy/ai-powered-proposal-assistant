from pydantic import BaseModel, Field
from typing import Any

class LoginRequest(BaseModel):
    username: str = Field(..., description="customer_id or customer name")

class ChatRequest(BaseModel):
    quote_id: str
    message: str
    session_id: str | None = None
    channel: str = "mobile"
    idempotency_key: str | None = None

class ProductCreate(BaseModel):
    product_id: str
    sku: str
    name_tr: str
    category: str
    brand: str
    price_try: float
    stock_qty: int
    active: bool = True
    min_order_qty: int = 1
    delivery_days: int = 0
    warranty_months: int = 0
    tags: list[str] = []
    aliases: dict[str, list[str]] = {"tr": []}
    substitute_product_ids: list[str] = []
    notes: str = ""

class KnowledgeCreate(BaseModel):
    knowledge_id: str
    topic: str
    locale: str = "tr"
    title: str
    body: str
    source: str
    applies_to: list[str] = []
    effective_from: str

class AddQuoteItemRequest(BaseModel):
    product_id: str
    quantity: int = 1
    idempotency_key: str | None = None
    user_accepts_waiting: bool = False
    max_price_try: float | None = None

class UpdateQuoteItemRequest(BaseModel):
    quote_item_id: str
    quantity: int

class ReplaceQuoteItemRequest(BaseModel):
    old_quote_item_id: str
    new_product_id: str | None = None
    max_price_try: float | None = None
    user_accepts_waiting: bool = False
