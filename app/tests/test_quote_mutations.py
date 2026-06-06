from app.tests.conftest import active_count, active_quantity, item_id, quote


def test_scn_001_add_price_limited_in_stock_scanner(client):
    r = client.post(
        "/quotes/Q-1002/items",
        json={
            "product_id": "PRD-BC-110",
            "quantity": 1,
            "idempotency_key": "SCN-001",
            "max_price_try": 9000,
        },
    )
    assert r.status_code == 200, r.text
    q = quote(client, "Q-1002")
    assert active_count(q, "PRD-BC-110") == 1
    assert active_quantity(q, "PRD-BC-110") == 1


def test_scn_002_out_of_stock_product_not_added_without_backorder_permission(client):
    r = client.post(
        "/quotes/Q-1001/items",
        json={"product_id": "PRD-BC-130", "quantity": 1, "idempotency_key": "SCN-002"},
    )
    assert r.status_code == 400
    q = quote(client, "Q-1001")
    assert active_count(q, "PRD-BC-130") == 0


def test_scn_003_duplicate_product_increases_quantity_without_second_active_line(client):
    r = client.post(
        "/quotes/Q-1001/items",
        json={"product_id": "PRD-BC-110", "quantity": 2, "idempotency_key": "SCN-003"},
    )
    assert r.status_code == 200, r.text
    q = quote(client, "Q-1001")
    assert active_count(q, "PRD-BC-110") == 1
    assert active_quantity(q, "PRD-BC-110") == 3


def test_scn_004_update_existing_quote_item_quantity(client):
    q0 = quote(client, "Q-1003")
    qi = item_id(q0, "PRD-PRN-320")
    r = client.patch("/quotes/Q-1003/items", json={"quote_item_id": qi, "quantity": 4})
    assert r.status_code == 200, r.text
    q = quote(client, "Q-1003")
    assert active_quantity(q, "PRD-PRN-320") == 4


def test_scn_005_replace_expensive_scanner_with_cheaper_in_stock_alternative(client):
    q0 = quote(client, "Q-1004")
    old = item_id(q0, "PRD-BC-120")
    r = client.post(
        "/quotes/Q-1004/replace",
        json={"old_quote_item_id": old, "new_product_id": "PRD-BC-110", "max_price_try": 9000},
    )
    assert r.status_code == 200, r.text
    q = quote(client, "Q-1004")
    assert active_count(q, "PRD-BC-120") == 0
    assert active_count(q, "PRD-BC-110") == 1


def test_scn_006_replace_out_of_stock_scanner_with_stocked_alternative(client):
    q0 = quote(client, "Q-1005")
    old = item_id(q0, "PRD-BC-130")
    r = client.post(
        "/quotes/Q-1005/replace",
        json={"old_quote_item_id": old, "new_product_id": "PRD-BC-140"},
    )
    assert r.status_code == 200, r.text
    q = quote(client, "Q-1005")
    assert active_count(q, "PRD-BC-130") == 0
    assert active_quantity(q, "PRD-BC-140") == 2


def test_scn_010_repeated_idempotency_key_does_not_increase_quantity_twice(client):
    payload = {"product_id": "PRD-BC-110", "quantity": 1, "idempotency_key": "SCN-010-SAME"}
    assert client.post("/quotes/Q-1002/items", json=payload).status_code == 200
    q1 = quote(client, "Q-1002")
    assert client.post("/quotes/Q-1002/items", json=payload).status_code == 200
    q2 = quote(client, "Q-1002")
    assert active_quantity(q2, "PRD-BC-110") == active_quantity(q1, "PRD-BC-110")


def test_scn_011_partner_quantity_discount_is_recalculated_after_add(client):
    r = client.post(
        "/quotes/Q-1002/items",
        json={"product_id": "PRD-BC-110", "quantity": 3, "idempotency_key": "SCN-011"},
    )
    assert r.status_code == 200, r.text
    q = quote(client, "Q-1002")
    assert active_quantity(q, "PRD-BC-110") == 3
    assert any(d["rule_id"] == "RUL-PARTNER-3" for d in q["discounts"])


def test_scn_012_turkish_price_limited_accessory_add(client):
    r = client.post(
        "/quotes/Q-2003/items",
        json={
            "product_id": "PRD-ACC-710",
            "quantity": 1,
            "idempotency_key": "SCN-012",
            "max_price_try": 1500,
        },
    )
    assert r.status_code == 200, r.text
    q = quote(client, "Q-2003")
    assert active_count(q, "PRD-ACC-710") == 1


def test_scn_013_plus_product_idempotent_replay(client):
    payload = {"product_id": "PRD-BC-110-PLUS", "quantity": 1, "idempotency_key": "SCN-013-SAME"}
    assert client.post("/quotes/Q-2001/items", json=payload).status_code == 200
    q1 = quote(client, "Q-2001")
    assert client.post("/quotes/Q-2001/items", json=payload).status_code == 200
    q2 = quote(client, "Q-2001")
    assert active_quantity(q2, "PRD-BC-110-PLUS") == active_quantity(q1, "PRD-BC-110-PLUS")


def test_scn_014_replace_out_of_stock_mobile_printer_with_stocked_printer(client):
    q0 = quote(client, "Q-2004")
    old = item_id(q0, "PRD-PRN-330")
    r = client.post(
        "/quotes/Q-2004/replace",
        json={"old_quote_item_id": old, "new_product_id": "PRD-PRN-320"},
    )
    assert r.status_code == 200, r.text
    q = quote(client, "Q-2004")
    assert active_count(q, "PRD-PRN-330") == 0
    assert active_count(q, "PRD-PRN-320") == 1


def test_scn_015_update_installation_service_quantity(client):
    q0 = quote(client, "Q-2005")
    qi = item_id(q0, "PRD-SVC-810")
    r = client.patch("/quotes/Q-2005/items", json={"quote_item_id": qi, "quantity": 2})
    assert r.status_code == 200, r.text
    q = quote(client, "Q-2005")
    assert active_quantity(q, "PRD-SVC-810") == 2


def test_scn_017_add_required_software_modules_and_bundle_discount(client):
    assert client.post("/quotes/Q-2002/items", json={"product_id": "PRD-SW-520", "quantity": 1, "idempotency_key": "SCN-017-A"}).status_code == 200
    assert client.post("/quotes/Q-2002/items", json={"product_id": "PRD-SW-530", "quantity": 1, "idempotency_key": "SCN-017-B"}).status_code == 200
    q = quote(client, "Q-2002")
    assert active_count(q, "PRD-SW-520") == 1
    assert active_count(q, "PRD-SW-530") == 1
    assert any(d["rule_id"] == "RUL-SW-BUNDLE" for d in q["discounts"])


def test_scn_019_plus_volume_discount_after_quantity_add(client):
    r = client.post(
        "/quotes/Q-2001/items",
        json={"product_id": "PRD-BC-110-PLUS", "quantity": 3, "idempotency_key": "SCN-019"},
    )
    assert r.status_code == 200, r.text
    q = quote(client, "Q-2001")
    assert active_quantity(q, "PRD-BC-110-PLUS") == 4
    assert any(d["rule_id"] == "RUL-PLUS-QTY" for d in q["discounts"])


def test_scn_020_price_ceiling_selects_basic_product_not_plus_or_expensive(client):
    r = client.get(
        "/products",
        params={"q": "kablosuz barkod okuyucu plus", "category": "barcode_scanner", "max_price_try": 8500, "in_stock_only": True},
    )
    ids = [p["product_id"] for p in r.json()["products"]]
    assert "PRD-BC-110" in ids
    assert "PRD-BC-110-PLUS" not in ids
    assert "PRD-BC-120" not in ids
    assert client.post(
        "/quotes/Q-1002/items",
        json={"product_id": "PRD-BC-110", "quantity": 1, "idempotency_key": "SCN-020", "max_price_try": 8500},
    ).status_code == 200


def test_scn_022_vehicle_charger_out_of_stock_then_usb_c_alternative_added(client):
    blocked = client.post(
        "/quotes/Q-2002/items",
        json={"product_id": "PRD-ACC-730", "quantity": 1, "idempotency_key": "SCN-022-BLOCKED"},
    )
    assert blocked.status_code == 400
    added = client.post(
        "/quotes/Q-2002/items",
        json={"product_id": "PRD-ACC-740", "quantity": 1, "idempotency_key": "SCN-022"},
    )
    assert added.status_code == 200, added.text
    q = quote(client, "Q-2002")
    assert active_count(q, "PRD-ACC-730") == 0
    assert active_count(q, "PRD-ACC-740") == 1
