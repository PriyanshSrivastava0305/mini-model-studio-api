# app/routers/model_profiles.py
from fastapi import APIRouter, Depends, Request, HTTPException
from ..schemas import ModelProfileCreate, ModelProfileUpdate, ModelProfileOut
from ..db import get_db_pool
from .. import crud
from typing import List
import asyncpg

router = APIRouter(prefix="/model-profiles", tags=["model-profiles"])

@router.post("/", response_model=ModelProfileOut)
async def create_profile(payload: ModelProfileCreate, request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        row = await crud.create_model_profile(conn, payload.name, payload.provider, payload.base_model, payload.system_prompt)
        return row

@router.get("/", response_model=List[ModelProfileOut])
async def list_profiles(request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        rows = await crud.list_model_profiles(conn)
        return rows

@router.get("/{profile_id}", response_model=ModelProfileOut)
async def get_profile(profile_id: str, request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        r = await crud.get_model_profile(conn, profile_id)
        if not r:
            raise HTTPException(status_code=404, detail="Model profile not found")
        return r

@router.put("/{profile_id}", response_model=ModelProfileOut)
async def update_profile(profile_id: str, payload: ModelProfileUpdate, request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        r = await crud.update_model_profile(conn, profile_id, name=payload.name, provider=payload.provider, base_model=payload.base_model, system_prompt=payload.system_prompt)
        if not r:
            raise HTTPException(status_code=404, detail="Not found")
        return r

@router.delete("/{profile_id}")
async def delete_profile(profile_id: str, request: Request):
    pool = get_db_pool(request.app)
    async with pool.acquire() as conn:
        await crud.delete_model_profile(conn, profile_id)
        return {"deleted": True}

# Notes

# Uses DB pool via get_db_pool.

# Returns pydantic-validated models.