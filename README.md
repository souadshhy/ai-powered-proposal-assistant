# The Blue Red — Backend Implementation

Backend-only implementation for the AI-powered proposal assistant case.

## Implemented Scope

- FastAPI backend
- PostgreSQL-ready SQLAlchemy data model
- Automatic seed loading from provided dataset JSON files
- Simple customer login by `customer_id` or customer name
- Customer quote listing after login
- Quote read and mutation APIs
- Product list/create APIs
- Knowledge list/create APIs
- Admin APIs for chat sessions and tool-call logs
- SSE chat streaming endpoint
- AI tool-calling route when `OPENAI_API_KEY` is set
- Deterministic fallback route when API key is missing/placeholder
- TF-IDF + cosine-similarity intent router for fallback
- Business-rule validation in service layer
- Tool-call logging
- Representative pytest tests, including golden scenario fixture loading

## Run Locally Without Docker

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

The app uses SQLite by default for local backend-only testing.

## Run With Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

The default Docker database URL uses PostgreSQL:

```text
postgresql+psycopg2://postgres:postgres@db:5432/tbr
```

## Simple Login Flow

```http
POST /auth/login
```

```json
{
  "username": "CUST-ANK-002"
}
```

This returns the customer and their quotes. The frontend can then let the user select a quote and start chat with that `quote_id`.

## Chat Stream

```http
POST /chat/stream
```

```json
{
  "quote_id": "Q-1002",
  "message": "9.000 TL altında, stokta olan kablosuz QR barkod okuyucu ekler misin?",
  "session_id": "demo-session-1",
  "idempotency_key": "demo-session-1-msg-1"
}
```

The response is Server-Sent Events:

```text
event: message_start
event: tool_start
event: tool_result
event: sources
event: text_chunk
event: done
```

Test with curl:

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"quote_id":"Q-1002","message":"9.000 TL altında kablosuz QR barkod okuyucu ekler misin?","session_id":"demo","idempotency_key":"demo-1"}'
```

## AI and Fallback Behavior

If `OPENAI_API_KEY` is missing or equals `changeme`, the backend automatically uses fallback.

Fallback pipeline:

```text
User message
→ TF-IDF/cosine intent router
→ constraint extraction
→ same tool/service layer
→ business validation
→ SSE response
```

If `OPENAI_API_KEY` is set, the backend uses OpenAI tool calling. The model receives the six required tool definitions and the backend maps tool calls to the same service functions.

## Validation Strategy

The backend does not try to hardcode every possible conversation flow. It validates atomic rules:

- Product exists
- Quote exists
- Quantity is valid
- User price limit is strict
- Out-of-stock products require both user wait acceptance and `customer.allow_backorder=true`
- Duplicate product lines increase quantity instead of creating a second active line
- Same idempotency key does not mutate twice
- Replace marks old item as `replaced`
- Policy/knowledge responses include `knowledge_id` sources

## Test Commands

```bash
pytest -q
```

Current local test result at generation time:

```text
5 passed
```

## Main Endpoints

```text
GET  /health
POST /seed
POST /auth/login
GET  /products
POST /products
GET  /knowledge
POST /knowledge
GET  /quotes
GET  /quotes/{quote_id}
POST /quotes/{quote_id}/items
PATCH /quotes/{quote_id}/items
POST /quotes/{quote_id}/replace
POST /chat/stream
GET  /admin/tool-logs
GET  /admin/chat-sessions
```
