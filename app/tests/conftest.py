import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, SessionLocal, engine
from app.models.entities import ToolCallLog
from app.services.seed_service import seed_if_empty

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


@pytest.fixture(autouse=True)
def clean_seeded_database():
    """Each requirement test starts from the official seeded dataset."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def scenarios():
    return json.loads((DATA_DIR / "golden_test_scenarios.json").read_text(encoding="utf-8"))


def post_chat(client, scenario_id, quote_id, message, *, idempotency_key=None, channel="mobile"):
    return client.post(
        "/chat/stream",
        json={
            "quote_id": quote_id,
            "message": message,
            "session_id": f"TEST-{scenario_id}",
            "idempotency_key": idempotency_key or f"idem-{scenario_id}",
            "channel": channel,
        },
    )


def parse_sse(text: str):
    events = []
    current = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if current:
                events.append(current)
                current = {}
            continue
        if line.startswith("event:"):
            current["event"] = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            current["data"] = json.loads(line.split(":", 1)[1].strip())
    if current:
        events.append(current)
    return events


def tool_names_from_stream(text: str):
    return [e["data"].get("tool") for e in parse_sse(text) if e.get("event") == "tool_result"]


def source_ids_from_stream(text: str):
    ids = set()
    for ev in parse_sse(text):
        data = ev.get("data", {})
        if ev.get("event") == "sources":
            ids.update(data.get("sources", []))
        if ev.get("event") == "tool_result":
            ids.update(data.get("sources", []))
    return ids


def quote(client, quote_id):
    r = client.get(f"/quotes/{quote_id}")
    assert r.status_code == 200, r.text
    return r.json()


def active_items(q, product_id=None):
    items = q["items"]
    if product_id is not None:
        items = [i for i in items if i["product_id"] == product_id]
    return items


def active_quantity(q, product_id):
    return sum(i["quantity"] for i in active_items(q, product_id))


def active_count(q, product_id):
    return len(active_items(q, product_id))


def item_id(q, product_id):
    matches = active_items(q, product_id)
    assert matches, f"No active item for {product_id} in quote {q['quote_id']}"
    return matches[0]["quote_item_id"]


def assert_tool_logged(session_id: str, *tool_names: str):
    db = SessionLocal()
    try:
        logged = [
            row.tool_name
            for row in db.query(ToolCallLog)
            .filter(ToolCallLog.session_id == session_id)
            .order_by(ToolCallLog.sequence)
            .all()
        ]
    finally:
        db.close()
    for expected in tool_names:
        assert expected in logged
    return logged
