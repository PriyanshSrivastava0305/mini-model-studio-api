# app/db.py
import os
import asyncpg
from fastapi import FastAPI

from dotenv import load_dotenv
load_dotenv()


async def init_db_pool(app: FastAPI):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL env var is required")
    app.state.db_pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)

async def close_db_pool(app: FastAPI):
    pool = getattr(app.state, "db_pool", None)
    if pool:
        await pool.close()

# convenience helper
def get_db_pool(app: FastAPI):
    return app.state.db_pool


# Explanation

#  init_db_pool runs at app startup. It creates a connection pool used across requests.

#  close_db_pool closes pool on shutdown.

#  We set min_size and max_size to reasonable defaults. You can tune them.