# app/crud.py
from typing import List, Optional
from uuid import UUID
import asyncpg
from fastapi import HTTPException

# ModelProfiles
async def create_model_profile(conn: asyncpg.Connection, name: str, provider: str, base_model: str, system_prompt: str):
    row = await conn.fetchrow(
        """
        INSERT INTO model_profiles (name, provider, base_model, system_prompt)
        VALUES ($1, $2, $3, $4) RETURNING *
        """,
        name, provider, base_model, system_prompt
    )
    return dict(row)

async def get_model_profile(conn: asyncpg.Connection, profile_id: UUID):
    row = await conn.fetchrow("SELECT * FROM model_profiles WHERE id = $1", profile_id)
    return dict(row) if row else None

async def list_model_profiles(conn: asyncpg.Connection) -> List[dict]:
    rows = await conn.fetch("SELECT * FROM model_profiles ORDER BY updated_at DESC")
    return [dict(r) for r in rows]

async def update_model_profile(conn: asyncpg.Connection, profile_id: UUID, **fields):
    set_clauses = []
    values = []
    i = 1
    for k, v in fields.items():
        if v is not None:
            set_clauses.append(f"{k} = ${i}")
            values.append(v)
            i += 1
    if not set_clauses:
        return await get_model_profile(conn, profile_id)
    query = f"UPDATE model_profiles SET {', '.join(set_clauses)}, updated_at = now() WHERE id = ${i} RETURNING *"
    values.append(profile_id)
    row = await conn.fetchrow(query, *values)
    return dict(row) if row else None

async def delete_model_profile(conn: asyncpg.Connection, profile_id: UUID):
    await conn.execute("DELETE FROM model_profiles WHERE id = $1", profile_id)

# Chats
async def create_chat(conn: asyncpg.Connection, title: Optional[str], model_profile_id: Optional[UUID]):
    row = await conn.fetchrow(
        "INSERT INTO chats (title, model_profile_id) VALUES ($1, $2) RETURNING *",
        title, model_profile_id
    )
    return dict(row)

async def list_chats(conn: asyncpg.Connection):
    rows = await conn.fetch("SELECT * FROM chats ORDER BY updated_at DESC")
    return [dict(r) for r in rows]

async def get_chat(conn: asyncpg.Connection, chat_id: UUID):
    row = await conn.fetchrow("SELECT * FROM chats WHERE id = $1", chat_id)
    return dict(row) if row else None

async def update_chat_title(conn: asyncpg.Connection, chat_id: UUID, title: str):
    row = await conn.fetchrow("UPDATE chats SET title = $1, updated_at = now() WHERE id = $2 RETURNING *", title, chat_id)
    return dict(row)

# Messages
async def append_message(conn: asyncpg.Connection, chat_id: UUID, role: str, content: str):
    row = await conn.fetchrow("INSERT INTO messages (chat_id, role, content) VALUES ($1, $2, $3) RETURNING *", chat_id, role, content)
    # update chats.updated_at
    await conn.execute("UPDATE chats SET updated_at = now() WHERE id = $1", chat_id)
    return dict(row)

async def get_last_n_messages(conn: asyncpg.Connection, chat_id: UUID, n: int):
    rows = await conn.fetch(
        "SELECT role, content, created_at FROM messages WHERE chat_id = $1 ORDER BY created_at DESC LIMIT $2",
        chat_id, n
    )
    # return as chronological (oldest -> newest)
    return [dict(r) for r in reversed(rows)]

async def list_messages(conn: asyncpg.Connection, chat_id: UUID, limit: int = 100):
    rows = await conn.fetch("SELECT * FROM messages WHERE chat_id = $1 ORDER BY created_at ASC LIMIT $2", chat_id, limit)
    return [dict(r) for r in rows]



# Explanation & important points

#  create_model_profile returns the full row (including id).

#  update_model_profile builds an update statement for passed fields only.

#  append_message also updates chats.updated_at.

#  get_last_n_messages returns messages in chronological order (oldest -> newest), which the model expects.