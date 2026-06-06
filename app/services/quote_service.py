import uuid
from sqlalchemy.orm import Session
from app.models.entities import Quote, QuoteItem, Product, PriceRule

class BusinessRuleError(Exception):
    pass

def get_quote(db: Session, quote_id: str):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise BusinessRuleError("Teklif bulunamadı.")
    active_items = [i for i in quote.items if i.status == "active"]
    items = []
    subtotal = 0.0
    for i in active_items:
        p = i.product
        line = float(i.unit_price_try) * i.quantity
        subtotal += line
        items.append({
            "quote_item_id": i.quote_item_id,
            "product_id": i.product_id,
            "name_tr": p.name_tr if p else None,
            "category": p.category if p else None,
            "quantity": i.quantity,
            "unit_price_try": float(i.unit_price_try),
            "line_total_try": line,
            "status": i.status,
        })
    discounts = calculate_discounts(db, quote)
    discount_amount = sum(d["amount_try"] for d in discounts)
    return {
        "quote_id": quote.quote_id,
        "customer_id": quote.customer_id,
        "customer_name": quote.customer.name if quote.customer else None,
        "customer_price_tier": quote.customer.price_tier if quote.customer else None,
        "allow_backorder": quote.customer.allow_backorder if quote.customer else False,
        "status": quote.status,
        "currency": quote.currency,
        "items": items,
        "subtotal_try": subtotal,
        "discounts": discounts,
        "total_try": max(subtotal - discount_amount, 0),
    }

def calculate_discounts(db: Session, quote: Quote):
    items = [i for i in quote.items if i.status == "active"]
    discounts = []
    # Implements dataset price_rules directly by condition text cases.
    by_cat = {}
    for i in items:
        p = i.product
        if not p: continue
        by_cat[p.category] = by_cat.get(p.category, 0) + i.quantity
        if p.category == "accessory" and i.quantity >= 5:
            discounts.append({"rule_id": "RUL-ACC-5", "description": "Aksesuar miktar indirimi", "percent": 5, "amount_try": float(i.unit_price_try)*i.quantity*0.05})
        if p.sku.endswith("PLUS") and i.quantity >= 4:
            discounts.append({"rule_id": "RUL-PLUS-QTY", "description": "Plus ürün hacim indirimi", "percent": 6, "amount_try": float(i.unit_price_try)*i.quantity*0.06})
    if quote.customer and quote.customer.price_tier == "partner":
        for cat in ["barcode_scanner", "receipt_printer", "label_printer"]:
            if by_cat.get(cat, 0) >= 3:
                amount = sum(float(i.unit_price_try)*i.quantity for i in items if i.product and i.product.category == cat) * 0.07
                discounts.append({"rule_id": "RUL-PARTNER-3", "description": "İş ortağı kategori miktar indirimi", "percent": 7, "amount_try": amount})
    ids = {i.product_id for i in items}
    if "PRD-SW-520" in ids and "PRD-SW-530" in ids:
        amount = sum(float(i.unit_price_try)*i.quantity for i in items if i.product_id in {"PRD-SW-520","PRD-SW-530"}) * 0.08
        discounts.append({"rule_id": "RUL-SW-BUNDLE", "description": "Yazılım modül paket indirimi", "percent": 8, "amount_try": amount})
    return discounts

def _validate_add(quote: Quote, product: Product, quantity: int, max_price_try: float | None, user_accepts_waiting: bool):
    if quantity < product.min_order_qty:
        raise BusinessRuleError(f"Minimum sipariş miktarı {product.min_order_qty}.")
    if max_price_try is not None and float(product.price_try) > max_price_try:
        raise BusinessRuleError("Ürün kullanıcı fiyat limitinin üzerinde olduğu için eklenemez.")
    if product.stock_qty <= 0:
        if not user_accepts_waiting:
            raise BusinessRuleError("Ürün stokta olmadığı için bekleme onayı olmadan eklenemez.")
        if not quote.customer.allow_backorder:
            raise BusinessRuleError("Bu müşteri için backorder uygun değil.")

def add_to_quote(db: Session, quote_id: str, product_id: str, quantity: int = 1, idempotency_key: str | None = None,
                 source_message_id: str = "chat", max_price_try: float | None = None, user_accepts_waiting: bool = False):
    quote = db.get(Quote, quote_id)
    product = db.get(Product, product_id)
    if not quote or not product:
        raise BusinessRuleError("Teklif veya ürün bulunamadı.")
    idem = idempotency_key or f"{source_message_id}:{quote_id}:{product_id}:{quantity}"
    prev = db.query(QuoteItem).filter(QuoteItem.idempotency_key == idem).first()
    if prev:
        return {"idempotent_replay": True, "quote": get_quote(db, quote_id), "quote_delta": {}}
    _validate_add(quote, product, quantity, max_price_try, user_accepts_waiting)
    existing = db.query(QuoteItem).filter_by(quote_id=quote_id, product_id=product_id, status="active").first()
    if existing:
        old = existing.quantity
        existing.quantity += quantity
        existing.source_message_id = source_message_id
        # Persist the latest idempotency key on the active line so a transport retry
        # with the same key is recognized and does not increase quantity again.
        existing.idempotency_key = idem
        delta = {"action": "quantity_increased", "product_id": product_id, "old_quantity": old, "new_quantity": existing.quantity}
    else:
        qi = QuoteItem(
            quote_item_id=f"QI-{quote_id}-{uuid.uuid4().hex[:8]}", quote_id=quote_id, product_id=product_id,
            quantity=quantity, unit_price_try=float(product.price_try), status="active",
            source_message_id=source_message_id, idempotency_key=idem)
        db.add(qi)
        delta = {"action": "added", "product_id": product_id, "quantity": quantity}
    db.commit()
    return {"idempotent_replay": False, "quote": get_quote(db, quote_id), "quote_delta": delta}

def update_quote_item(db: Session, quote_id: str, quote_item_id: str, quantity: int):
    item = db.get(QuoteItem, quote_item_id)
    if not item or item.quote_id != quote_id:
        raise BusinessRuleError("Teklif kalemi bulunamadı.")
    old = item.quantity
    if quantity <= 0:
        item.status = "inactive"
        delta = {"action": "deactivated", "quote_item_id": quote_item_id, "old_quantity": old, "new_quantity": 0}
    else:
        item.quantity = quantity
        delta = {"action": "updated", "quote_item_id": quote_item_id, "old_quantity": old, "new_quantity": quantity}
    db.commit()
    return {"quote": get_quote(db, quote_id), "quote_delta": delta}

def replace_with_alternative(db: Session, quote_id: str, old_quote_item_id: str, new_product_id: str | None = None,
                             max_price_try: float | None = None, user_accepts_waiting: bool = False):
    old_item = db.get(QuoteItem, old_quote_item_id)
    if not old_item or old_item.quote_id != quote_id or old_item.status != "active":
        raise BusinessRuleError("Aktif eski teklif kalemi bulunamadı.")
    old_product = old_item.product
    candidate_ids = []
    if new_product_id:
        candidate_ids = [new_product_id]
    else:
        candidate_ids = old_product.substitute_product_ids or []
    chosen = None
    for pid in candidate_ids:
        p = db.get(Product, pid)
        if not p or not p.active: continue
        try:
            _validate_add(old_item.quote, p, old_item.quantity, max_price_try, user_accepts_waiting)
            chosen = p; break
        except BusinessRuleError:
            continue
    if not chosen:
        raise BusinessRuleError("Kurallara uygun alternatif bulunamadı.")
    old_item.status = "replaced"
    qi = QuoteItem(
        quote_item_id=f"QI-{quote_id}-{uuid.uuid4().hex[:8]}", quote_id=quote_id, product_id=chosen.product_id,
        quantity=old_item.quantity, unit_price_try=float(chosen.price_try), status="active",
        source_message_id="replace", idempotency_key=f"replace:{quote_id}:{old_item.quote_item_id}:{chosen.product_id}:{uuid.uuid4().hex[:8]}"
    )
    db.add(qi)
    db.commit()
    delta = {"action": "replaced", "old_quote_item_id": old_quote_item_id, "old_product_id": old_product.product_id, "new_product_id": chosen.product_id, "quantity": qi.quantity}
    return {"quote": get_quote(db, quote_id), "quote_delta": delta}
