from sqlalchemy import String, Integer, Numeric, Boolean, Date, ForeignKey, Text, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String, primary_key=True)
    sku: Mapped[str] = mapped_column(String, nullable=False)
    name_tr: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    price_try: Mapped[float] = mapped_column(Numeric, nullable=False)
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    min_order_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_days: Mapped[int] = mapped_column(Integer, nullable=False)
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, nullable=False)
    aliases: Mapped[dict] = mapped_column(JSON, nullable=False)
    substitute_product_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)

class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"
    knowledge_id: Mapped[str] = mapped_column(String, primary_key=True)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    locale: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    applies_to: Mapped[list] = mapped_column(JSON, nullable=False)
    effective_from: Mapped[str] = mapped_column(String, nullable=False)

class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    segment: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    price_tier: Mapped[str] = mapped_column(String, nullable=False)
    credit_limit_try: Mapped[float] = mapped_column(Numeric, nullable=False)
    allow_backorder: Mapped[bool] = mapped_column(Boolean, nullable=False)
    default_locale: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    quotes = relationship("Quote", back_populates="customer")

class PriceRule(Base):
    __tablename__ = "price_rules"
    rule_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    condition: Mapped[str] = mapped_column(Text, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Numeric, nullable=False)

class Quote(Base):
    __tablename__ = "quotes"
    quote_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.customer_id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    created_by_channel: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="TRY")
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    customer = relationship("Customer", back_populates="quotes")
    items = relationship("QuoteItem", back_populates="quote")

class QuoteItem(Base):
    __tablename__ = "quote_items"
    quote_item_id: Mapped[str] = mapped_column(String, primary_key=True)
    quote_id: Mapped[str] = mapped_column(String, ForeignKey("quotes.quote_id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String, ForeignKey("products.product_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_try: Mapped[float] = mapped_column(Numeric, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    source_message_id: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    quote = relationship("Quote", back_populates="items")
    product = relationship("Product")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    quote_id: Mapped[str] = mapped_column(String, ForeignKey("quotes.quote_id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.customer_id"), nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False, default="mobile")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ToolCallLog(Base):
    __tablename__ = "tool_call_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    quote_id: Mapped[str | None] = mapped_column(String, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    output_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    quote_delta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
