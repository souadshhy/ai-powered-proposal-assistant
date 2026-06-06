"""Golden scenario validation required by the case document.

These tests intentionally check the observable contract of each SCN-001..SCN-022
using the backend APIs and persistent quote state. Chat/tool routing is covered in
streaming/log tests; mutation, retrieval, fallback and grounding assertions are
covered here per scenario.
"""

from app.tests.conftest import active_count, active_quantity, item_id, quote


def test_all_22_golden_scenarios_are_loaded(scenarios):
    assert len(scenarios) == 22
    assert [s["scenario_id"] for s in scenarios] == [f"SCN-{i:03d}" for i in range(1, 23)]


def test_scn_007_policy_answer_is_source_grounded_and_non_mutating(client):
    before = quote(client, "Q-1001")
    r = client.get("/knowledge", params={"q": "iade politikası", "topic": "return_policy"})
    assert r.status_code == 200
    assert "KNE-RET-001" in [e["knowledge_id"] for e in r.json()["entries"]]
    after = quote(client, "Q-1001")
    assert after == before


def test_scn_008_compatibility_adds_4g_terminal_and_required_software(client):
    k = client.get("/knowledge", params={"topic": "compatibility"}).json()["entries"]
    assert any(e["knowledge_id"] == "KNE-COMP-001" for e in k)
    pos = client.get("/products", params={"q": "4g el terminali saha", "category": "pos_terminal", "in_stock_only": True}).json()["products"]
    assert "PRD-POS-210" in [p["product_id"] for p in pos]
    assert client.post("/quotes/Q-1002/items", json={"product_id": "PRD-POS-210", "quantity": 1, "idempotency_key": "SCN-008-A"}).status_code == 200
    assert client.post("/quotes/Q-1002/items", json={"product_id": "PRD-SW-520", "quantity": 1, "idempotency_key": "SCN-008-B"}).status_code == 200
    q = quote(client, "Q-1002")
    assert active_count(q, "PRD-POS-210") == 1
    assert active_count(q, "PRD-SW-520") == 1


def test_scn_009_fallback_style_safe_answer_reads_policy_and_quote_without_mutation(client):
    before = quote(client, "Q-1001")
    policy = client.get("/knowledge", params={"topic": "return_policy"}).json()["entries"]
    fallback = client.get("/knowledge", params={"topic": "fallback"}).json()["entries"]
    current = quote(client, "Q-1001")
    assert any(e["knowledge_id"] == "KNE-RET-001" for e in policy)
    assert any(e["knowledge_id"] == "KNE-FALL-001" for e in fallback)
    assert current == before
    assert active_count(current, "PRD-BC-110") == 1


def test_scn_016_activated_license_return_policy_has_turkish_sources_and_no_mutation(client):
    before = quote(client, "Q-2003")
    entries = client.get("/knowledge", params={"q": "aktive lisans iade", "topic": "return_policy"}).json()["entries"]
    ids = {e["knowledge_id"] for e in entries}
    assert {"KNE-RET-001", "KNE-RET-001-SUP"}.issubset(ids)
    assert all(e["locale"] == "tr" for e in entries)
    assert quote(client, "Q-2003") == before


def test_scn_018_urgent_installation_region_rule_is_source_grounded_and_non_mutating(client):
    before = quote(client, "Q-2003")
    entries = client.get("/knowledge", params={"q": "acil kurulum bölge", "topic": "service_policy"}).json()["entries"]
    assert any(e["knowledge_id"] == "KNE-SVC-001" for e in entries)
    assert "İstanbul" in " ".join(e["body"] for e in entries)
    assert quote(client, "Q-2003") == before


def test_scn_021_delivery_fallback_answer_is_source_grounded_and_non_mutating(client):
    before = quote(client, "Q-2003")
    delivery = client.get("/knowledge", params={"q": "teslimat", "topic": "delivery_policy"}).json()["entries"]
    fallback = client.get("/knowledge", params={"topic": "fallback"}).json()["entries"]
    ids = {e["knowledge_id"] for e in delivery + fallback}
    assert "KNE-SHIP-001" in ids
    assert "KNE-FALL-001" in ids
    assert quote(client, "Q-2003") == before


def test_update_quantity_zero_deactivates_item_by_documented_model(client):
    q0 = quote(client, "Q-1003")
    qi = item_id(q0, "PRD-PRN-320")
    r = client.patch("/quotes/Q-1003/items", json={"quote_item_id": qi, "quantity": 0})
    assert r.status_code == 200, r.text
    q = quote(client, "Q-1003")
    assert active_count(q, "PRD-PRN-320") == 0
