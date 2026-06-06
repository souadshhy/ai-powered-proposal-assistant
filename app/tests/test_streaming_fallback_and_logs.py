from app.tests.conftest import assert_tool_logged, parse_sse, post_chat, quote, source_ids_from_stream, tool_names_from_stream


def test_chat_stream_contains_required_observable_events(client):
    r = post_chat(
        client,
        "STREAM-001",
        "Q-1002",
        "9.000 TL altında, stokta olan kablosuz QR barkod okuyucu ekler misin?",
    )
    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e["event"] for e in events]
    assert "message_start" in names
    assert "tool_start" in names
    assert "tool_result" in names
    assert "sources" in names
    assert "text_chunk" in names
    assert names[-1] == "done"
    assert "PRD-BC-110" in source_ids_from_stream(r.text)


def test_tool_call_logs_are_persisted_and_visible_to_admin(client):
    session_id = "TEST-LOGS-001"
    r = client.post(
        "/chat/stream",
        json={
            "quote_id": "Q-1002",
            "message": "9.000 TL altında, stokta olan kablosuz QR barkod okuyucu ekler misin?",
            "session_id": session_id,
            "idempotency_key": "LOGS-001",
        },
    )
    assert r.status_code == 200
    logged = assert_tool_logged(session_id, "search_products", "add_to_quote", "get_quote")
    assert logged[:3] == ["search_products", "add_to_quote", "get_quote"]
    admin = client.get("/admin/tool-logs")
    assert admin.status_code == 200
    assert any(row["session_id"] == session_id for row in admin.json()["logs"])


def test_fallback_mode_without_openai_key_returns_grounded_turkish_policy_answer(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = post_chat(
        client,
        "SCN-021",
        "Q-2003",
        "Yedek teslimat politikasını Türkçe ve kaynaklı açıklar mısın?",
    )
    assert r.status_code == 200
    assert "fallback" in r.text
    tools = tool_names_from_stream(r.text)
    assert "get_knowledge_entries" in tools
    assert not {"add_to_quote", "update_quote_item", "replace_with_alternative"}.intersection(tools)
    assert source_ids_from_stream(r.text) & {"KNE-SHIP-001", "KNE-SHIP-001-SUP"}


def test_streaming_retry_with_same_idempotency_key_does_not_double_mutate(client):
    payload = {
        "quote_id": "Q-1002",
        "message": "stokta olan kablosuz QR barkod okuyucu ekle",
        "session_id": "TEST-RETRY-001",
        "idempotency_key": "retry-same-key",
    }
    assert client.post("/chat/stream", json=payload).status_code == 200
    q1 = quote(client, "Q-1002")
    qty1 = sum(i["quantity"] for i in q1["items"] if i["product_id"] == "PRD-BC-110")
    payload["session_id"] = "TEST-RETRY-002"
    assert client.post("/chat/stream", json=payload).status_code == 200
    q2 = quote(client, "Q-1002")
    qty2 = sum(i["quantity"] for i in q2["items"] if i["product_id"] == "PRD-BC-110")
    assert qty2 == qty1


def test_web_and_mobile_quote_reads_share_same_persistent_state(client):
    mobile = client.post(
        "/chat/stream",
        json={
            "quote_id": "Q-1002",
            "message": "9.000 TL altında kablosuz barkod okuyucu ekle",
            "session_id": "TEST-MOBILE-STATE",
            "channel": "mobile",
            "idempotency_key": "shared-state-001",
        },
    )
    assert mobile.status_code == 200
    web_quote = client.get("/quotes/Q-1002").json()
    assert any(i["product_id"] == "PRD-BC-110" for i in web_quote["items"])
    mobile_quote = client.get("/quotes/Q-1002").json()
    assert web_quote == mobile_quote
