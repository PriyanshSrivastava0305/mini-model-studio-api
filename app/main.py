# app/main.py
from fastapi import FastAPI
from .db import init_db_pool, close_db_pool
from .routers import providers as providers_router
from .routers import model_profiles as model_profiles_router
from .routers import chats as chats_router
from .logging_middleware import timing_middleware
import os
from fastapi.middleware.cors import CORSMiddleware

def create_app():
    app = FastAPI(title="mini-model-studio-api")

    # CORS - allow the Next.js front-end origin in dev
    origins = [os.getenv("NEXT_ORIGIN", "http://localhost:3000")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(timing_middleware)

    app.include_router(providers_router.router)
    app.include_router(model_profiles_router.router)
    app.include_router(chats_router.router)

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app

app = create_app()

@app.on_event("startup")
async def startup_event():
    await init_db_pool(app)

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_pool(app)



#Notes

# CORS allows the Next.js dev server origin.

# All routers are included.

# startup_event initializes asyncpg pool. 
