import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def verify_api_key_middleware(request: Request, call_next):
    """FastAPI middleware to verify X-API-Key header matches configured A2A_API_KEY."""
    path = request.url.path
    # Exclude typical health endpoints and documentation pages
    if path in ("/health", "/docs", "/openapi.json", "/redoc") or path.startswith("/.well-known/agent.json"):
        return await call_next(request)

    expected_api_key = os.getenv("A2A_API_KEY", "secret-a2a-key")
    provided_key = request.headers.get("X-API-Key")

    if not provided_key or provided_key != expected_api_key:
        logger.warning(
            "Unauthorized access attempt to %s: %s header",
            path,
            "missing" if not provided_key else "invalid"
        )
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized: Invalid or missing X-API-Key header"}
        )

    return await call_next(request)
