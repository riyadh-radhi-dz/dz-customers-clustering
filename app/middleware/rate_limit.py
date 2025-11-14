"""Rate limiting middleware."""
import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    
    Args:
        requests_per_minute: Maximum number of requests per minute per client
        requests_per_hour: Maximum number of requests per hour per client
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store: {client_ip: [(timestamp, count), ...]}
        self.minute_window: Dict[str, list] = defaultdict(list)
        self.hour_window: Dict[str, list] = defaultdict(list)
    
    def _clean_old_requests(
        self, 
        client_ip: str, 
        current_time: float,
        window: Dict[str, list],
        window_size: int
    ) -> int:
        """Remove old requests and return current count."""
        cutoff_time = current_time - window_size
        
        # Remove old requests
        window[client_ip] = [
            (ts, count) for ts, count in window[client_ip]
            if ts > cutoff_time
        ]
        
        # Calculate total count
        return sum(count for _, count in window[client_ip])
    
    def _check_rate_limit(
        self, 
        client_ip: str, 
        current_time: float
    ) -> Tuple[bool, str]:
        """
        Check if client has exceeded rate limits.
        
        Returns:
            (is_allowed, error_message)
        """
        # Check minute window
        minute_count = self._clean_old_requests(
            client_ip, current_time, self.minute_window, 60
        )
        
        if minute_count >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        # Check hour window
        hour_count = self._clean_old_requests(
            client_ip, current_time, self.hour_window, 3600
        )
        
        if hour_count >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        return True, ""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Apply rate limiting to requests."""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for X-Forwarded-For header (proxy support)
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        current_time = time.time()
        
        # Check rate limits
        is_allowed, error_message = self._check_rate_limit(client_ip, current_time)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_message,
                headers={"Retry-After": "60"}
            )
        
        # Add to windows
        self.minute_window[client_ip].append((current_time, 1))
        self.hour_window[client_ip].append((current_time, 1))
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        minute_count = sum(count for _, count in self.minute_window[client_ip])
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, self.requests_per_minute - minute_count)
        )
        
        hour_count = sum(count for _, count in self.hour_window[client_ip])
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, self.requests_per_hour - hour_count)
        )
        
        return response

