import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DATA = Path(__file__).resolve().parents[2] / 'data' / 'golden_test_scenarios.json'

def test_golden_file_is_present_and_loaded():
    scenarios = json.loads(DATA.read_text(encoding='utf-8'))
    assert len(scenarios) == 22
    assert scenarios[0]['scenario_id'] == 'SCN-001'

def test_representative_golden_scenarios_stream_and_log_tools():
    scenarios = json.loads(DATA.read_text(encoding='utf-8'))
    for scn in [s for s in scenarios if s['scenario_id'] in {'SCN-001','SCN-007','SCN-012'}]:
        r = client.post('/chat/stream', json={
            'quote_id': scn['quote_id'],
            'message': scn['user_message'],
            'session_id': 'TEST-' + scn['scenario_id'],
            'idempotency_key': 'idem-' + scn['scenario_id']
        })
        assert r.status_code == 200
        body = r.text
        assert 'event: done' in body or 'event: controlled_error' in body
        for expected in scn['expected_tool_calls'][:1]:
            assert expected['name'] in body
