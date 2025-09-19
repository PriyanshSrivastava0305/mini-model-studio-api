FastAPI backend using asyncpg connection pool to Postgres (Supabase). Key components:
- Routers: /providers, /models, /model_profiles (CRUD), /chat
- DB: model_profiles, chats, messages
- Chat flow: server loads model_profile -> loads last N messages -> prepends system prompt -> calls provider REST API -> persists assistant reply
- Provider keys live only in environment variables on server
- Logging: minimal console logs for chat_id, provider, base_model to verify which model was used
- Async HTTP calls to LLM providers via httpx