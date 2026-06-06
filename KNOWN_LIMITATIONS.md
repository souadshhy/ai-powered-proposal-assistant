# Known Limitations

- Backend-only implementation; web and mobile UIs are intentionally not generated.
- Fallback Turkish understanding is retrieval/rule based and may not cover every natural phrasing.
- Tests include representative golden scenarios and fixture loading, not a full assertion implementation for all 22 golden scenarios.
- AI mode requires a real OpenAI API key and internet access at runtime.
- The local non-Docker default uses SQLite for easier backend-only testing; Docker Compose is PostgreSQL-ready.
- Quote creation and approval workflows are not implemented because they are not required by the case description.
