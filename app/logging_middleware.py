# app/logging_middleware.py
from fastapi import Request
import time
import json

async def timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    # minimal log: method path status duration
    print(json.dumps({
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_s": round(duration, 3)
    }))
    return response


# Why: Minimal observability. Chat-specific logs will be inside routers when provider is used.