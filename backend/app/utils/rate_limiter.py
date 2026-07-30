"""Rate limiting utilities."""

from typing import Callable

from fastapi import HTTPException, Request, status

from app.utils.security import get_rate_limiter


def rate_limit_dependency() -> Callable:
    """FastAPI dependency for rate limiting."""

    async def rate_limit(request: Request) -> None:
        rate_limiter = get_rate_limiter()

        # Use client IP as identifier
        client_ip = request.client.host if request.client else "unknown"

        if not rate_limiter.is_allowed(client_ip):
            remaining = rate_limiter.get_remaining(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. {remaining} requests remaining.",
                headers={"Retry-After": "60"},
            )

    return rate_limit
