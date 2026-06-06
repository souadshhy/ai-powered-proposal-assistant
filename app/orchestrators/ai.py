import json
from app.core.config import settings
from app.services.product_service import search_products
from app.services.knowledge_service import get_knowledge_entries
from app.services.quote_service import get_quote, add_to_quote, update_quote_item, replace_with_alternative

PLACEHOLDERS = {None, "", "changeme", "placeholder", "YOUR_API_KEY"}

def ai_available() -> bool:
    key = (settings.openai_api_key or "").strip()
    return settings.use_ai_when_key_present and key not in PLACEHOLDERS

TOOLS = [
    {"type":"function","function":{"name":"search_products","description":"Ürünleri Türkçe metin, kategori, fiyat limiti, stok durumu, etiketler ve garantiye göre bulur.","parameters":{"type":"object","properties":{"query":{"type":"string"},"category":{"type":["string","null"]},"max_price_try":{"type":["number","null"]},"in_stock_only":{"type":"boolean"},"required_tags":{"type":"array","items":{"type":"string"}},"limit":{"type":"integer"},"min_warranty_months":{"type":["integer","null"]}},"required":["query"]}}},
    {"type":"function","function":{"name":"get_knowledge_entries","description":"İade, teslimat, garanti, fiyat, stok, uyumluluk, servis ve fallback bilgi kayıtlarını kaynak olarak döndürür.","parameters":{"type":"object","properties":{"query":{"type":"string"},"topic":{"type":["string","null"]},"applies_to":{"type":["string","null"]},"limit":{"type":"integer"}},"required":["query"]}}},
    {"type":"function","function":{"name":"get_quote","description":"Aktif quote_id için web ve mobilin ortak teklif durumunu okur.","parameters":{"type":"object","properties":{},"additionalProperties":False}}},
    {"type":"function","function":{"name":"add_to_quote","description":"Ürünü mevcut teklif taslağına ekler veya aynı ürün varsa miktarı artırır. Fiyat/stok/backorder/idempotency backend tarafından doğrulanır.","parameters":{"type":"object","properties":{"product_id":{"type":"string"},"quantity":{"type":"integer"},"max_price_try":{"type":["number","null"]},"user_accepts_waiting":{"type":"boolean"}},"required":["product_id","quantity"]}}},
    {"type":"function","function":{"name":"update_quote_item","description":"Mevcut teklif kaleminin miktarını değiştirir. quantity=0 pasifleştirme olarak uygulanır.","parameters":{"type":"object","properties":{"quote_item_id":{"type":"string"},"quantity":{"type":"integer"}},"required":["quote_item_id","quantity"]}}},
    {"type":"function","function":{"name":"replace_with_alternative","description":"Mevcut teklif kalemini stoklu ve kurallara uygun alternatifle değiştirir.","parameters":{"type":"object","properties":{"old_quote_item_id":{"type":"string"},"new_product_id":{"type":["string","null"]},"max_price_try":{"type":["number","null"]},"user_accepts_waiting":{"type":"boolean"}},"required":["old_quote_item_id"]}}},
]

SYSTEM_PROMPT = """
Sen The Blue Red için Türkçe çalışan teklif asistanısın.
Sadece verilen tool'ları kullanarak ürün, bilgi ve teklif durumuna erişebilirsin.
Kullanıcı açıkça ekle/güncelle/değiştir demiyorsa teklif mutasyonu yapma.
Fiyat limiti varsa max_price_try olarak geçir ve asla limit üstü ürünü otomatik ekleme.
Politika/uyumluluk/stok/teslimat/garanti cevaplarında get_knowledge_entries ile knowledge_id kaynağı kullan.
quote_id backend context'inden gelir; tool argümanlarında quote_id isteme veya uydurma.
Son cevap Türkçe, kısa ve kaynakları anlaşılır olmalıdır.
"""

def _safe_args(raw: str):
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}

async def run_ai_steps(db, quote_id: str, message: str, idempotency_key: str, logger):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)
    messages = [
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":f"quote_id={quote_id}\nKullanıcı mesajı: {message}"},
    ]
    sources=[]
    final_text=None
    for _ in range(8):

        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            final_text = msg.content or "İşlem tamamlandı."
            break
        for tc in msg.tool_calls:
            name = tc.function.name
            args = _safe_args(tc.function.arguments)
            result = None
            success = True
            try:
                if name == "search_products":
                    result = {"products": search_products(db, **args)}
                elif name == "get_knowledge_entries":
                    result = {"entries": get_knowledge_entries(db, **args)}
                elif name == "get_quote":
                    result = get_quote(db, quote_id)
                elif name == "add_to_quote":
                    result = add_to_quote(db, quote_id=quote_id, idempotency_key=idempotency_key, **args)
                elif name == "update_quote_item":
                    result = update_quote_item(db, quote_id=quote_id, **args)
                elif name == "replace_with_alternative":
                    result = replace_with_alternative(db, quote_id=quote_id, **args)
                else:
                    success=False; result={"error":"Bilinmeyen tool"}
            except Exception as e:
                success=False; result={"error":str(e)}
            logger.log(name, args, success, result if isinstance(result, dict) else {"result": result}, result.get("quote_delta") if isinstance(result, dict) else None)
            sources += _collect_sources(result)
            messages.append({"role":"tool", "tool_call_id": tc.id, "content": json.dumps(result, ensure_ascii=False, default=str)})
    if final_text is None:
        final_text = "İsteğinizi tamamlamak için gerekli tool çağrıları sınırı aşıldı; lütfen daha kısa bir istek gönderin."
    return {"text": final_text, "sources": sources}

def _collect_sources(x):
    out=[]
    def walk(v):
        if isinstance(v, dict):
            for k,val in v.items():
                if k in {"product_id","knowledge_id"}: out.append(str(val))
                walk(val)
        elif isinstance(v, list):
            for y in v: walk(y)
    walk(x)
    return sorted(set(out))
