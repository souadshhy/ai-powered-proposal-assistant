
def product_ids(response):
    return [p["product_id"] for p in response.json()["products"]]


def knowledge_ids(response):
    return [k["knowledge_id"] for k in response.json()["entries"]]


def test_search_products_respects_price_ceiling_and_stock_rule(client):
    r = client.get(
        "/products",
        params={
            "q": "kablosuz QR barkod okuyucu",
            "category": "barcode_scanner",
            "max_price_try": 9000,
            "in_stock_only": True,
        },
    )
    assert r.status_code == 200
    ids = product_ids(r)
    assert "PRD-BC-110" in ids
    assert "PRD-BC-120" not in ids  # above max_price_try
    assert "PRD-BC-130" not in ids  # stock_qty is 0
    for p in r.json()["products"]:
        assert p["price_try"] <= 9000
        assert p["stock_qty"] > 0


def test_search_products_can_find_stocked_alternatives_for_out_of_stock_items(client):
    r = client.get(
        "/products",
        params={"q": "USB-C şarj", "category": "accessory", "in_stock_only": True},
    )
    assert r.status_code == 200
    ids = product_ids(r)
    assert "PRD-ACC-740" in ids
    assert "PRD-ACC-730" not in ids


def test_policy_and_compatibility_answers_are_grounded_with_knowledge_ids(client):
    for topic, required_id in [
        ("return_policy", "KNE-RET-001"),
        ("delivery_policy", "KNE-SHIP-001"),
        ("stock_rule", "KNE-STOCK-001"),
        ("compatibility", "KNE-COMP-001"),
        ("service_policy", "KNE-SVC-001"),
        ("discount_policy", "KNE-DIS-001"),
        ("fallback", "KNE-FALL-001"),
        ("price_ceiling", "KNE-PRICE-001"),
    ]:
        r = client.get("/knowledge", params={"topic": topic})
        assert r.status_code == 200
        ids = knowledge_ids(r)
        assert required_id in ids
        assert all(k["knowledge_id"] for k in r.json()["entries"])
