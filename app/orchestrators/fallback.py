import re
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from app.orchestrators.text_utils import normalize, cosine_rank
from app.services.product_service import search_products
from app.services.knowledge_service import get_knowledge_entries
from app.services.quote_service import add_to_quote, update_quote_item, replace_with_alternative, get_quote, BusinessRuleError

INTENT_DOCS = {
    "PRODUCT_SEARCH": "ürün göster ürün ara seçenekleri listele barkod okuyucu scanner yazıcı terminal lisans aksesuar stokta fiyat altında öner hangi ürünler var",
    "ADD_TO_QUOTE": "teklife ekle ekler misin ekle bunu istiyorum alalım sepete koy teklif taslağına koy adet ekle",
    "KNOWLEDGE_QUERY": "iade garanti teslimat politika şartları uyumluluk kurulum servis backorder stok kuralı indirim fiyat politikası kaynak bilgi nedir",
    "UPDATE_QUOTE_ITEM": "miktar güncelle adedi değiştir adet yap azalt artır sil kaldır quantity update miktarını",
    "REPLACE_ALTERNATIVE": "alternatif değiştir daha ucuz yerine koy stokta olanla değiştir muadil pahalı stok dışı alternatif",
}
CATEGORY_ALIASES = {
    "barcode_scanner": ["barkod", "okuyucu", "scanner", "qr", "2d", "1d"],
    "pos_terminal": ["pos", "terminal", "el terminali", "saha"],
    "receipt_printer": ["fiş", "fis", "termal", "yazıcı", "yazici", "printer", "mobil yazıcı"],
    "label_printer": ["etiket", "label"],
    "software": ["lisans", "yazılım", "yazilim", "modül", "modul", "stok programı"],
    "service": ["kurulum", "servis", "hizmet", "acil"],
    "accessory": ["aksesuar", "şarj", "sarj", "batarya", "kılıf", "kilif", "usb-c", "araç"],
    "bundle": ["kit", "paket", "başlangıç", "saha satış kiti"],
}
TOPIC_ALIASES = {
    "return_policy": ["iade", "geri gönder", "return"],
    "warranty": ["garanti", "warranty"],
    "delivery_policy": ["teslimat", "kargo", "delivery"],
    "stock_rule": ["stok", "backorder", "bekleyebilirim", "stok dışı"],
    "compatibility": ["uyumluluk", "gerekli", "çalışması için", "beraber", "required"],
    "discount_policy": ["indirim", "iskonto", "partner", "iş ortağı"],
    "service_policy": ["kurulum", "servis", "acil"],
    "price_ceiling": ["fiyat", "limit", "altında", "ucuz"],
    "fallback": ["fallback", "llm", "openai"],
}

@dataclass
class ParsedRequest:
    intent: str
    max_price_try: float | None = None
    quantity: int = 1
    category: str | None = None
    required_tags: list[str] = field(default_factory=list)
    min_warranty_months: int | None = None
    topic: str | None = None
    user_accepts_waiting: bool = False
    query: str = ""

def detect_intent(message: str) -> str:
    ranked = cosine_rank(message, list(INTENT_DOCS.values()))
    if not ranked:
        return "PRODUCT_SEARCH"
    return list(INTENT_DOCS.keys())[ranked[0][0]]

def parse_request(message: str) -> ParsedRequest:
    n = normalize(message)
    intent = detect_intent(message)
    # explicit mutation words override search intent
    if any(w in n for w in ["ekle", "alalim", "koy", "istiyorum"]):
        intent = "ADD_TO_QUOTE"
    if any(w in n for w in ["degistir", "alternatif", "muadil", "daha ucuz"]):
        intent = "REPLACE_ALTERNATIVE"
    if any(w in n for w in ["miktar", "adet yap", "adedi", "guncelle", "kaldir", "sil"]):
        intent = "UPDATE_QUOTE_ITEM"
    max_price = None
    m = re.search(r"(\d{1,3}(?:[\.,]?\d{3})+|\d+)\s*(?:tl|try)?\s*(?:alt|altinda|den az|den ucuz|e kadar)", n)
    if not m:
        m = re.search(r"(?:max|maksimum|limit)\s*(\d{1,3}(?:[\.,]?\d{3})+|\d+)", n)
    if m:
        max_price = float(m.group(1).replace(".", "").replace(",", ""))
    quantity = 1
    qm = re.search(r"(\d+)\s*(?:adet|tane|qty)", n)
    if qm:
        quantity = int(qm.group(1))
    cat = None
    for c, aliases in CATEGORY_ALIASES.items():
        if any(a in n for a in aliases):
            cat = c; break
    tags=[]
    for t in ["kablosuz", "bluetooth", "qr", "2d", "usb", "wifi", "4g", "acil", "offline", "plus", "usb-c"]:
        if normalize(t) in n:
            tags.append(t)
    min_warranty=None
    wm = re.search(r"(\d+)\s*(?:yil|yıl)\s*garanti", n)
    if wm: min_warranty = int(wm.group(1))*12
    topic = None
    for top, aliases in TOPIC_ALIASES.items():
        if any(normalize(a) in n for a in aliases):
            topic = top; break
    explicit_add = any(w in n for w in ["ekle", "alalim", "koy", "istiyorum"])
    explicit_update = any(w in n for w in ["miktar", "adet yap", "adedi", "guncelle", "kaldir", "sil"])
    explicit_replace = any(w in n for w in ["degistir", "alternatif", "muadil", "daha ucuz"])
    if topic and not (explicit_add or explicit_update or explicit_replace):
        intent = "KNOWLEDGE_QUERY"
    user_wait = any(w in n for w in ["bekleyebilirim", "beklerim", "beklemeyi kabul", "backorder"])
    return ParsedRequest(intent, max_price, quantity, cat, tags, min_warranty, topic, user_wait, message)

def first_active_item_id(quote: dict, category: str | None = None):
    for item in quote.get("items", []):
        if category is None or item.get("category") == category:
            return item["quote_item_id"]
    return quote.get("items", [{}])[0].get("quote_item_id") if quote.get("items") else None

async def run_fallback_steps(db: Session, quote_id: str, message: str, idempotency_key: str, logger):
    parsed = parse_request(message)
    sources=[]
    chunks=[]
    # Need policy source for price/stock/discount/compatibility contexts
    def log_tool(name, inp, fn):
        try:
            out = fn()
            logger.log(name, inp, True, out if isinstance(out, dict) else {"result": out}, out.get("quote_delta") if isinstance(out, dict) else None)
            return out
        except Exception as e:
            logger.log(name, inp, False, {"error": str(e)})
            raise
    if parsed.intent == "KNOWLEDGE_QUERY":
        inp={"query": message, "topic": parsed.topic, "limit": 3}
        entries=log_tool("get_knowledge_entries", inp, lambda: {"entries": get_knowledge_entries(db, **inp)})["entries"]
        sources += [e["knowledge_id"] for e in entries]
        text = "\n".join([f"{e['title']}: {e['body']} (Kaynak: {e['knowledge_id']})" for e in entries])
        return {"text": text or "Uygun bilgi kaydı bulunamadı.", "sources": sources, "parsed": parsed}
    if parsed.intent in {"PRODUCT_SEARCH", "ADD_TO_QUOTE"}:
        inp={"query": message, "category": parsed.category, "max_price_try": parsed.max_price_try, "in_stock_only": not parsed.user_accepts_waiting, "required_tags": parsed.required_tags, "limit": 5, "min_warranty_months": parsed.min_warranty_months}
        products=log_tool("search_products", inp, lambda: {"products": search_products(db, **inp)})["products"]
        sources += [p["product_id"] for p in products]
        # Cite price rule if price ceiling exists
        if parsed.max_price_try is not None:
            entries = get_knowledge_entries(db, topic="price_ceiling", limit=1)
            sources += [e["knowledge_id"] for e in entries]
        if parsed.intent == "PRODUCT_SEARCH" or not products:
            if not products:
                return {"text": "Belirttiğiniz koşullara uygun stoklu ürün bulunamadı.", "sources": sources, "parsed": parsed}
            text = "Uygun ürünler:\n" + "\n".join([f"- {p['name_tr']} ({p['product_id']}), {p['price_try']} TRY, stok: {p['stock_qty']}" for p in products])
            return {"text": text, "sources": sources, "parsed": parsed}
        chosen=products[0]
        add_inp={"quote_id": quote_id, "product_id": chosen["product_id"], "quantity": parsed.quantity, "idempotency_key": idempotency_key, "max_price_try": parsed.max_price_try, "user_accepts_waiting": parsed.user_accepts_waiting}
        result=log_tool("add_to_quote", add_inp, lambda: add_to_quote(db, **add_inp))
        q=log_tool("get_quote", {"quote_id": quote_id}, lambda: get_quote(db, quote_id))
        text=f"{chosen['name_tr']} ürününü teklifinize ekledim. Güncel toplam: {q['total_try']} TRY."
        return {"text": text, "sources": sources, "parsed": parsed, "quote": q}
    if parsed.intent == "REPLACE_ALTERNATIVE":
        q=log_tool("get_quote", {"quote_id": quote_id}, lambda: get_quote(db, quote_id))
        old_id=first_active_item_id(q, parsed.category)
        if not old_id:
            return {"text":"Değiştirilecek aktif teklif kalemi bulunamadı.", "sources": sources, "parsed": parsed}
        inp={"quote_id": quote_id, "old_quote_item_id": old_id, "max_price_try": parsed.max_price_try, "user_accepts_waiting": parsed.user_accepts_waiting}
        result=log_tool("replace_with_alternative", inp, lambda: replace_with_alternative(db, **inp))
        q=log_tool("get_quote", {"quote_id": quote_id}, lambda: get_quote(db, quote_id))
        text=f"Ürün kurallara uygun alternatifle değiştirildi. Güncel toplam: {q['total_try']} TRY."
        return {"text": text, "sources": sources, "parsed": parsed, "quote": q}
    if parsed.intent == "UPDATE_QUOTE_ITEM":
        q=log_tool("get_quote", {"quote_id": quote_id}, lambda: get_quote(db, quote_id))
        item_id=first_active_item_id(q, parsed.category)
        if not item_id:
            return {"text":"Güncellenecek aktif teklif kalemi bulunamadı.", "sources": sources, "parsed": parsed}
        inp={"quote_id": quote_id, "quote_item_id": item_id, "quantity": parsed.quantity}
        result=log_tool("update_quote_item", inp, lambda: update_quote_item(db, **inp))
        q=log_tool("get_quote", {"quote_id": quote_id}, lambda: get_quote(db, quote_id))
        text=f"Teklif kalemi miktarı {parsed.quantity} olarak güncellendi. Güncel toplam: {q['total_try']} TRY."
        return {"text": text, "sources": sources, "parsed": parsed, "quote": q}
    return {"text": "İsteğinizi güvenli şekilde işleyemedim.", "sources": sources, "parsed": parsed}
