import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_official_dataset_package_counts_match_case_description(scenarios):
    """Project description requires 48 products, 22 knowledge rows and 22 scenarios."""
    assert len(load("products.json")) == 48
    assert len(load("knowledge_entries.json")) == 22
    assert len(load("customers.json")) == 6
    assert len(load("quotes.json")) == 10
    assert len(load("quote_items.json")) == 8
    assert len(load("price_rules.json")) == 6
    assert len(scenarios) == 22


def test_required_tool_contracts_are_present():
    contracts = load("tool_contracts.json")
    names = {c["name"] for c in contracts}
    assert names == {
        "search_products",
        "get_knowledge_entries",
        "get_quote",
        "add_to_quote",
        "update_quote_item",
        "replace_with_alternative",
    }


def test_golden_scenarios_reference_only_required_tools(scenarios):
    required = {
        "search_products",
        "get_knowledge_entries",
        "get_quote",
        "add_to_quote",
        "update_quote_item",
        "replace_with_alternative",
    }
    assert {s["scenario_id"] for s in scenarios} == {f"SCN-{i:03d}" for i in range(1, 23)}
    for scn in scenarios:
        for call in scn["expected_tool_calls"]:
            assert call["name"] in required
