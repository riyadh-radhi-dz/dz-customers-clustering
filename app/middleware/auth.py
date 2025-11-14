"""Authentication middleware."""
import secrets
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware


security = HTTPBearer(auto_error=False)


class APIKeyAuth(BaseHTTPMiddleware):
    """
    API Key authentication middleware.
    
    Supports two methods:
    1. Bearer token in Authorization header
    2. X-API-Key header
    """
    
    def __init__(self, app, api_keys: Optional[list[str]] = None, enabled: bool = True):
        super().__init__(app)
        self.api_keys = set(api_keys or [])
        self.enabled = enabled
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key using constant-time comparison."""
        if not self.api_keys:
            return True  # No keys configured, allow all
        
        return any(
            secrets.compare_digest(api_key, valid_key)
            for valid_key in self.api_keys
        )
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Validate API key before processing request."""
        if not self.enabled:
            return await call_next(request)
        
        # Skip authentication for public endpoints
        public_endpoints = ["/", "/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in public_endpoints:
            return await call_next(request)
        
        # Try Bearer token first
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            if self._validate_api_key(token):
                return await call_next(request)
        
        # Try X-API-Key header
        api_key_header = request.headers.get("x-api-key", "")
        if api_key_header and self._validate_api_key(api_key_header):
            return await call_next(request)
        
        # Authentication failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)

