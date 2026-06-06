from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_login():
    assert client.get('/health').status_code == 200
    r = client.post('/auth/login', json={'username':'CUST-ANK-002'})
    assert r.status_code == 200
    body = r.json()
    assert body['customer']['price_tier'] == 'partner'
    assert any(q['quote_id'] == 'Q-1002' for q in body['quotes'])

def test_search_and_quote_read():
    r = client.get('/products', params={'q':'kablosuz barkod okuyucu', 'category':'barcode_scanner', 'max_price_try':9000, 'in_stock_only':True})
    assert r.status_code == 200
    ids = [p['product_id'] for p in r.json()['products']]
    assert 'PRD-BC-110' in ids
    q = client.get('/quotes/Q-1002')
    assert q.status_code == 200
    assert q.json()['quote_id'] == 'Q-1002'

def test_chat_stream_add_product():
    r = client.post('/chat/stream', json={
        'quote_id':'Q-1002',
        'message':'9.000 TL altında, stokta olan kablosuz QR barkod okuyucu ekler misin?',
        'session_id':'TEST-SCN-001',
        'idempotency_key':'TEST-SCN-001-key'
    })
    assert r.status_code == 200
    text = r.text
    assert 'event: message_start' in text
    assert 'event: tool_start' in text
    assert 'event: tool_result' in text
    assert 'event: done' in text
    q = client.get('/quotes/Q-1002').json()
    assert any(i['product_id']=='PRD-BC-110' for i in q['items'])
