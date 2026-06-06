# AI_USAGE

This implementation uses AI only as an orchestration layer.

## AI Mode

When `OPENAI_API_KEY` is configured, the backend sends the user message plus tool definitions to the model. The model may call:

- `search_products`
- `get_knowledge_entries`
- `get_quote`
- `add_to_quote`
- `update_quote_item`
- `replace_with_alternative`

The model does not directly access the database. The backend executes all tool calls through the service layer.

## Fallback Mode

When `OPENAI_API_KEY` is missing or a placeholder, the system uses deterministic fallback.

Fallback uses:

- intent documents for each tool/workflow
- TF-IDF and cosine similarity
- regex/dictionary-based constraint extraction
- the same service functions as AI mode

## Safety / Validation

The backend validates business rules independently from the model:

- strict price ceiling
- stock and backorder rules
- idempotency
- duplicate item behavior
- quote mutation persistence
- source requirements for knowledge answers

The AI understands user language; the backend enforces correctness.
