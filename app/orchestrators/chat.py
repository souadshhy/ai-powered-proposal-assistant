import json, uuid, asyncio
from sqlalchemy.orm import Session
from app.models.entities import Quote, ChatSession
from app.orchestrators.ai import ai_available, run_ai_steps
from app.orchestrators.fallback import run_fallback_steps
from app.services.log_service import ToolLogger

def sse(event: str, data: dict):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

def _planned_progress_events(message: str):
    """
    Lightweight demo-safe progress events.
    These are UI progress hints only; real persisted tool-call logs are still
    produced by ToolLogger during orchestration.
    """
    m = (message or "").lower()
    steps = [
        (1, "get_quote", "Teklif durumu okunuyor"),
    ]
    if any(w in m for w in ["iade", "garanti", "teslimat", "uyumluluk", "politika", "stok", "indirim", "lisans"]):
        steps.append((len(steps)+1, "get_knowledge_entries", "Bilgi kaynakları kontrol ediliyor"))
    if any(w in m for w in ["ürün", "urun", "okuyucu", "scanner", "yazıcı", "yazici", "terminal", "aksesuar", "alternatif", "değiştir", "degistir", "ekle"]):
        steps.append((len(steps)+1, "search_products", "Uygun ürünler aranıyor"))
    if any(w in m for w in ["alternatif", "değiştir", "degistir", "muadil", "daha ucuz"]):
        steps.append((len(steps)+1, "replace_with_alternative", "Teklif alternatifi hazırlanıyor"))
    elif any(w in m for w in ["ekle", "adet", "tane", "alalım", "alalim"]):
        steps.append((len(steps)+1, "add_to_quote", "Teklif güncellemesi hazırlanıyor"))
    return steps

async def stream_chat(db: Session, quote_id: str, message: str, channel: str = "mobile", session_id: str | None = None, idempotency_key: str | None = None):
    quote = db.get(Quote, quote_id)
    if not quote:
        yield sse("controlled_error", {"success": False, "error": "Teklif bulunamadı."})
        return
    sid = session_id or f"S-{uuid.uuid4().hex[:12]}"
    idem = idempotency_key or f"{sid}:{hash(message)}"
    if not db.get(ChatSession, sid):
        db.add(ChatSession(session_id=sid, quote_id=quote_id, customer_id=quote.customer_id, channel=channel))
        db.commit()
    logger = ToolLogger(db, sid, quote_id)
    yield sse("message_start", {"session_id": sid, "quote_id": quote_id, "customer_id": quote.customer_id, "mode": "ai" if ai_available() else "fallback"})

    # Make progress visible immediately in mobile before the final answer starts.
    # This does not mutate data and does not replace persisted ToolLogger rows.
    for seq, tool, summary in _planned_progress_events(message):
        yield sse("tool_start", {"sequence": seq, "tool": tool, "input_summary": summary, "preview": True})
        await asyncio.sleep(0.35)

    try:
        # AI placeholder currently falls through to fallback if unavailable. If AI is enabled but not yet implemented,
        # fallback still keeps the product usable.
        if ai_available():
            try:
                result = await run_ai_steps(db, quote_id, message, idem, logger)
            except Exception:
                result = await run_fallback_steps(db, quote_id, message, idem, logger)
        else:
            result = await run_fallback_steps(db, quote_id, message, idem, logger)

        # Real auditable tool-call events, produced from DB-backed ToolLogger.
        for ev in logger.events:
            yield sse(ev["type"], ev["data"])
            await asyncio.sleep(0.12)

        parsed = result.get("parsed")
        if parsed:
            yield sse("intent", {"intent": parsed.intent, "max_price_try": parsed.max_price_try, "category": parsed.category, "quantity": parsed.quantity})
        if result.get("sources"):
            yield sse("sources", {"sources": sorted(set(result["sources"]))})
        text = result.get("text", "İşlem tamamlandı.")
        # Small chunks to satisfy streaming requirement and to be easy to consume in mobile.
        for token in text.split(" "):
            yield sse("text_chunk", {"text": token + " "})
            await asyncio.sleep(0.04)
        yield sse("done", {"success": True, "session_id": sid})
    except Exception as e:
        yield sse("controlled_error", {"success": False, "session_id": sid, "error": str(e)})
