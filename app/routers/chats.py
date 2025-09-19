# app/routers/chats.py
from fastapi import APIRouter, Request, HTTPException
from ..schemas import ChatCreate, ChatOut, MessageIn
from ..db import get_db_pool
from .. import crud, providers, utils
from typing import List
import os
import uuid

router = APIRouter(prefix="/chats", tags=["chats"])


from pydantic import BaseModel
from typing import Optional

# add near top of file with the other imports
class ChatPatchPayload(BaseModel):
    title: Optional[str] = None
    model_profile_id: Optional[str] = None

@router.patch("/{chat_id}", response_model=ChatOut)
async def patch_chat(chat_id: str, payload: ChatPatchPayload, request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        # ensure chat exists
        chat = await crud.get_chat(conn, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # If model_profile_id provided, validate it exists
        if payload.model_profile_id is not None:
            mp = await crud.get_model_profile(conn, payload.model_profile_id)
            if not mp:
                raise HTTPException(status_code=404, detail="Model profile not found")

        # Build dynamic update clause
        set_parts = []
        params = []

        if payload.title is not None:
            params.append(payload.title)
            set_parts.append(f"title = ${len(params)}")
        if payload.model_profile_id is not None:
            params.append(payload.model_profile_id)
            set_parts.append(f"model_profile_id = ${len(params)}")

        if not set_parts:
            # nothing to update
            raise HTTPException(status_code=400, detail="No updatable fields provided")

        # append updated_at via SQL directly
        set_sql = ", ".join(set_parts) + ", updated_at = NOW()"

        # add chat_id as last param
        params.append(chat_id)
        sql = f"UPDATE chats SET {set_sql} WHERE id = ${len(params)} RETURNING id;"

        row = await conn.fetchrow(sql, *params)
        if not row:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Return the canonical chat object using your existing crud getter
        updated_chat = await crud.get_chat(conn, chat_id)
        if not updated_chat:
            # should not happen, but guard
            raise HTTPException(status_code=500, detail="Failed to fetch updated chat")
        return updated_chat


@router.post("/", response_model=ChatOut)
async def create_chat(payload: ChatCreate, request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        row = await crud.create_chat(conn, payload.title, payload.model_profile_id)
        return row

@router.get("/", response_model=List[ChatOut])
async def list_chats(request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        rows = await crud.list_chats(conn)
        return rows

@router.get("/{chat_id}/messages")
async def get_messages(chat_id: str, request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        rows = await crud.list_messages(conn, chat_id)
        return {"messages": rows}

@router.post("/{chat_id}/messages")
async def post_message(chat_id: str, payload: MessageIn, request: Request):
    """
    POST a user message to a chat. Flow:
    1) Persist user's message
    2) Load model_profile (server-side) — prefer payload.model_profile_id if provided (allows overriding)
    3) Load last N messages (context window)
    4) Prepend system prompt (server-side)
    5) Call provider REST API
    6) Persist assistant reply and return it
    """
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        # ensure chat exists
        chat = await crud.get_chat(conn, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # choose profile id: payload override or chat's linked profile
        profile_id = payload.model_profile_id or chat.get("model_profile_id")
        if not profile_id:
            raise HTTPException(status_code=400, detail="No model_profile_id provided or linked to chat")

        model_profile = await crud.get_model_profile(conn, profile_id)
        if not model_profile:
            raise HTTPException(status_code=404, detail="Model profile not found")

        # persist user's message
        user_msg = await crud.append_message(conn, chat_id, "user", payload.content)

        # load last N messages for context
        N = int(os.getenv("CONTEXT_WINDOW", "20"))
        prior_messages = await crud.get_last_n_messages(conn, chat_id, N)
        # Build messages for provider (OpenAI expects list with system)
        messages = utils.messages_for_openai(model_profile["system_prompt"], prior_messages)

        # call provider
        provider = model_profile["provider"]
        model_name = model_profile["base_model"]

        # Log which provider/model used
        print(f"CHAT_CALL chat_id={chat_id} provider={provider} model={model_name}")

        # Call provider (may raise HTTPException if provider disabled or error)
        assistant_text = await providers.call_model(provider, model_name, messages)

        # persist assistant message
        assistant_msg = await crud.append_message(conn, chat_id, "assistant", assistant_text)

        return {
            "chat_id": chat_id,
            "reply": assistant_text,
            "assistant_message_id": assistant_msg["id"]
        }


# Important behavior (matches spec)

# System prompt is loaded server-side from model_profiles and prepended on each request (never trust client).

# Context windowing: we fetch last N messages (default 20).

#  When a model profile is edited: because we load model_profiles row at call time, subsequent messages after editing use updated provider/base model per spec.