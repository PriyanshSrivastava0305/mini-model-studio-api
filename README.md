# mini-model-studio-api

FastAPI backend for *Mini Model Studio*. Provides endpoints to manage model profiles, chats, and messages, and to call LLM providers (OpenAI / Anthropic) using REST.

# Strategy

##  1. Server-Side Persona Injection

 - The backend automatically injects the persona’s system prompt from the model_profiles table on each message request.

##  2. Context Windowing

  - The backend loads the last N messages (default 20) from the chat history to provide context for the AI.

  - Older messages are truncated to optimize API calls and stay within token limits.

## 3. Unified AI Provider Calls

  - The system supports multiple AI providers.

  - All requests go through a single call_model(provider, model, messages) function for consistency.

  - Handles errors gracefully and supports a local mock mode for development without API keys.

## 4. Optimistic Frontend Updates

 - User messages are appended immediately to the chat UI.
  
 - AI replies are returned asynchronously and updated once the API call completes.

## 5. Model Profile Flexibility

  - Each chat can be linked to a model_profile.
  
  - Changing a model profile immediately affects subsequent AI calls without modifying previous messages.
  
## 6. Security & Reliability
  
  - System prompts and AI calls are controlled server-side.
  
  - API keys are never exposed to the frontend.

# Setup
 - Install requirements
 - run
   ``
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ``
